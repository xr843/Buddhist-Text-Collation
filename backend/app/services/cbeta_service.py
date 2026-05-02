"""
CBETA平台数据对接服务
中华电子佛典协会（Chinese Buddhist Electronic Text Association）
"""
import asyncio
import httpx
from lxml import etree
from typing import Dict, List, Optional, Tuple, Iterable
import re
import os
import unicodedata
from app.services.export_tei_service import TEIExportService


class CBETAService:
    """CBETA数据接口服务"""

    # CBETA在线平台URL
    CBETA_ONLINE = "https://cbetaonline.dila.edu.tw"
    # CBETA 目录/元数据 API（CBETA Online 前端使用）
    CBETA_CATALOG_API = os.environ.get("CBETA_CATALOG_API", "https://cbdata.dila.edu.tw/stable/").rstrip("/") + "/"

    # XML 仓库：默认先用 xml-p5（目前更完整），再回退 xml-p5a；也可用环境变量覆盖（便于国内镜像/自建镜像）
    _env_xml_repo = os.environ.get("CBETA_XML_REPO", "").strip()
    CBETA_XML_REPOS = (
        [_env_xml_repo]
        if _env_xml_repo
        else [
            "https://raw.githubusercontent.com/cbeta-org/xml-p5/master",
            "https://raw.githubusercontent.com/cbeta-org/xml-p5a/master",
        ]
    )
    # 可选：本地 XML 仓库路径（如已提前下载/镜像）
    CBETA_XML_LOCAL_ROOT = os.environ.get("CBETA_XML_LOCAL_ROOT", "").strip()
    # 简单缓存：sutra_id -> volume（减少多次扫描）
    _volume_cache: Dict[str, str] = {}
    # work_id -> {volume,file}（减少目录 API 请求）
    _work_meta_cache: Dict[str, Dict[str, str]] = {}

    # 全局 HTTP 客户端（复用连接池，避免每次请求创建新连接）
    _http_client: Optional[httpx.AsyncClient] = None

    @classmethod
    def _get_http_client(cls) -> httpx.AsyncClient:
        """获取全局 HTTP 客户端（懒加载，复用连接池）"""
        if cls._http_client is None or cls._http_client.is_closed:
            cls._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(
                    connect=5.0,    # 连接超时 5 秒
                    read=15.0,      # 读取超时 15 秒
                    write=10.0,     # 写入超时 10 秒
                    pool=5.0,       # 连接池等待超时 5 秒
                ),
                limits=httpx.Limits(
                    max_connections=20,          # 最大连接数
                    max_keepalive_connections=10, # 最大保持连接数
                ),
                follow_redirects=True,
                # 禁用环境变量代理（避免被系统代理干扰）
                trust_env=False,
            )
        return cls._http_client

    @classmethod
    async def close_http_client(cls):
        """关闭全局 HTTP 客户端（应用关闭时调用）"""
        if cls._http_client is not None and not cls._http_client.is_closed:
            await cls._http_client.aclose()
            cls._http_client = None
    @staticmethod
    def _maybe_strip_punctuation(text: str, enabled: bool) -> str:
        if not text:
            return ""
        if not enabled:
            return text
        out: List[str] = []
        for ch in text:
            # 处理全角/不换行空格
            if ch in ("\u3000", "\u00A0"):
                continue
            # 去掉数字（常见于脚注标号：[1] -> 1；避免对勘被“残留的脚注数字”干扰）
            # 这里移除所有 Unicode Number 类字符（含全角数字/圈号等），但不影响“一二三”等汉字数字（它们是 Lo）。
            if unicodedata.category(ch).startswith("N"):
                continue
            # Unicode 标点符号（P*）
            if unicodedata.category(ch).startswith("P"):
                continue
            out.append(ch)
        return "".join(out)

    @staticmethod
    def _iter_volume_candidates(canon: str, explicit_volume: Optional[str]) -> Iterable[str]:
        if explicit_volume:
            yield explicit_volume
            return

        canon = (canon or "").upper()
        if canon == "T":
            for i in range(1, 56):
                yield f"T{i:02d}"
            return
        if canon == "X":
            for i in range(1, 31):
                yield f"X{i:02d}"
            return

        # 其他藏经：兜底尝试 1-99（不会穷举太多）
        for i in range(1, 100):
            yield f"{canon}{i:02d}"

    @staticmethod
    def _parse_sutra_id(sutra_id: str) -> Optional[Dict[str, str]]:
        """
        支持多种输入：
        - T0235
        - T1558_001
        - T08n0235
        - T08n0235_001
        - 允许末尾字母：T12n0374a / T0374a
        """
        s = (sutra_id or "").strip()
        if not s:
            return None

        m = re.match(
            r'^([A-Za-z])(?:(\d{2})n)?\s*(\d{3,5})([A-Za-z]?)(?:_(\d{3}))?$',
            s,
        )
        if not m:
            return None

        canon = m.group(1).upper()
        vol2 = (m.group(2) or "").strip()  # 形如 08（来自 T08n0235）
        number_raw = m.group(3)
        letter = (m.group(4) or "").strip()
        part = (m.group(5) or "").strip()

        sutra_no = number_raw.zfill(4)
        explicit_volume = f"{canon}{vol2}" if vol2 else ""

        return {
            "canon": canon,
            "sutra_no": sutra_no,
            "letter": letter,
            "part": part,
            "explicit_volume": explicit_volume,
        }

    @staticmethod
    def _work_id_from_parsed(parsed: Dict[str, str]) -> str:
        canon = (parsed.get("canon") or "").upper()
        sutra_no = (parsed.get("sutra_no") or "").strip()
        letter = (parsed.get("letter") or "").strip()
        return f"{canon}{sutra_no}{letter}".upper()

    @staticmethod
    def _normalize_volume(volume: str) -> str:
        """
        规范化卷号（例如 T1 -> T01, T29 -> T29）。
        """
        v = (volume or "").strip().upper()
        m = re.match(r"^([A-Z])(\d+)$", v)
        if not m:
            return v
        canon, num = m.group(1), int(m.group(2))
        return f"{canon}{num:02d}"

    @staticmethod
    def _parse_volume_range(vol_str: str) -> List[str]:
        """
        解析卷号范围字符串，返回所有册号列表。
        例如：
        - "T05" -> ["T05"]
        - "T05..T07" -> ["T05", "T06", "T07"]
        - "T29" -> ["T29"]
        """
        v = (vol_str or "").strip().upper()
        if not v:
            return []

        # 检查是否是范围格式：T05..T07
        range_match = re.match(r"^([A-Z])(\d+)\.\.([A-Z])(\d+)$", v)
        if range_match:
            canon1, num1, canon2, num2 = range_match.groups()
            if canon1 != canon2:
                # 不同藏经，返回两端
                return [f"{canon1}{int(num1):02d}", f"{canon2}{int(num2):02d}"]
            # 同一藏经，展开范围
            start, end = int(num1), int(num2)
            return [f"{canon1}{i:02d}" for i in range(start, end + 1)]

        # 单一册号
        normalized = CBETAService._normalize_volume(v)
        return [normalized] if normalized else []

    @staticmethod
    def _parse_chinese_numeral(s: str) -> Optional[int]:
        """
        解析常见中文数字（用于“卷第一/卷一/第一卷”等）。
        支持：零/〇、一二三四五六七八九、两/兩、十百千；也支持纯阿拉伯数字。
        """
        raw = (s or "").strip()
        if not raw:
            return None
        if raw.isdigit():
            n = int(raw)
            return n if n > 0 else None

        digits = {
            "零": 0,
            "〇": 0,
            "一": 1,
            "二": 2,
            "三": 3,
            "四": 4,
            "五": 5,
            "六": 6,
            "七": 7,
            "八": 8,
            "九": 9,
            "两": 2,
            "兩": 2,
        }
        units = {"十": 10, "百": 100, "千": 1000}

        total = 0
        num = 0
        seen = False
        for ch in raw:
            if ch in digits:
                num = digits[ch]
                seen = True
                continue
            if ch in units:
                seen = True
                u = units[ch]
                if num == 0:
                    num = 1
                total += num * u
                num = 0
                continue
            # 其它字符忽略

        total += num
        return total if seen and total > 0 else None

    @staticmethod
    def _int_to_chinese_numeral(n: int) -> str:
        """
        将阿拉伯数字转换为中文数字（用于生成卷号）。
        支持 1-999。
        """
        if n <= 0 or n >= 1000:
            return str(n)

        digits = ["零", "一", "二", "三", "四", "五", "六", "七", "八", "九"]

        if n < 10:
            return digits[n]
        if n == 10:
            return "十"
        if n < 20:
            return f"十{digits[n % 10]}"
        if n < 100:
            tens = n // 10
            ones = n % 10
            if ones == 0:
                return f"{digits[tens]}十"
            return f"{digits[tens]}十{digits[ones]}"
        # 100-999
        hundreds = n // 100
        remainder = n % 100
        if remainder == 0:
            return f"{digits[hundreds]}百"
        if remainder < 10:
            return f"{digits[hundreds]}百零{digits[remainder]}"
        return f"{digits[hundreds]}百{CBETAService._int_to_chinese_numeral(remainder)}"

    @staticmethod
    def _replace_juan_in_title(title: str, target_juan: int) -> str:
        """
        替换标题中的卷号。
        如 "阿毘達磨順正理論卷第一" -> "阿毘達磨順正理論卷第二十五"
        """
        if not title or target_juan <= 0:
            return title

        # 匹配常见的卷号模式
        patterns = [
            # 卷第X
            (r"(卷第)([0-9]+|[零〇一二三四五六七八九十百千两兩]+)", r"\g<1>"),
            # 第X卷
            (r"(第)([0-9]+|[零〇一二三四五六七八九十百千两兩]+)(卷)", r"\g<1>"),
            # 卷X
            (r"(卷)([0-9]+|[零〇一二三四五六七八九十百千两兩]+)$", r"\g<1>"),
        ]

        chinese_num = CBETAService._int_to_chinese_numeral(target_juan)

        for pattern, replacement_prefix in patterns:
            m = re.search(pattern, title)
            if m:
                if "第" in pattern and pattern.endswith("(卷)"):
                    # 第X卷 模式
                    new_title = re.sub(pattern, f"第{chinese_num}卷", title)
                elif pattern.startswith(r"(卷第)"):
                    # 卷第X 模式
                    new_title = re.sub(pattern, f"卷第{chinese_num}", title)
                else:
                    # 卷X 模式
                    new_title = re.sub(pattern, f"卷{chinese_num}", title)
                return new_title

        return title

    @staticmethod
    def _extract_juan_from_query(query: str) -> Tuple[str, Optional[int]]:
        """
        从输入中提取卷号（如“瑜伽師地論卷第一/第1卷/卷2”等），并返回“去掉卷号后的查询词 + 卷号”。
        """
        q = (query or "").strip()
        if not q:
            return "", None
        q = re.sub(r"\s+", "", q)

        patterns = [
            r"^(?P<title>.+?)卷第?(?P<juan>[0-9]+|[零〇一二三四五六七八九十百千两兩]+)$",
            r"^(?P<title>.+?)第(?P<juan>[0-9]+|[零〇一二三四五六七八九十百千两兩]+)卷$",
            r"^(?P<title>.+?)卷(?P<juan>[0-9]+|[零〇一二三四五六七八九十百千两兩]+)$",
        ]
        for pat in patterns:
            m = re.match(pat, q)
            if not m:
                continue
            title = (m.group("title") or "").strip()
            juan_raw = (m.group("juan") or "").strip()
            juan = CBETAService._parse_chinese_numeral(juan_raw)
            if title and juan:
                return title, juan

        return q, None

    @staticmethod
    async def _fetch_work_meta(work_id: str) -> Optional[Dict[str, str]]:
        """
        通过 CBETA 目录 API 获取 work 的元数据（例如 vol=T29, file=T29n1558, title/byline 等）。

        注意：该接口偶发 SSL/网络抖动，做少量重试；失败时返回 None，让上层走其它路径（如扫描卷号）。
        """
        w = (work_id or "").strip().upper()
        if not w:
            return None
        cached = CBETAService._work_meta_cache.get(w)
        if cached:
            return cached

        url = f"{CBETAService.CBETA_CATALOG_API}works?work={w}"
        last_error: Optional[Exception] = None
        client = CBETAService._get_http_client()
        for i in range(3):
            try:
                resp = await client.get(url)
                if resp.status_code != 200:
                    last_error = RuntimeError(f"HTTP {resp.status_code}")
                    if i < 2:  # 最后一次不等待
                        await asyncio.sleep(0.1 * (i + 1))  # 指数退避: 0.1s, 0.2s
                    continue
                data = resp.json()
                if isinstance(data, dict) and data.get("num_found") and data.get("results"):
                    r0 = data["results"][0] or {}
                    vol_raw = str(r0.get("vol", "")).strip()  # 保留原始值，可能是 "T05..T07"
                    vol = CBETAService._normalize_volume(vol_raw)
                    file_base = str(r0.get("file", "")).strip()
                    if vol_raw and file_base:
                        meta = {
                            "volume": vol,            # 规范化后的单一册号（用于兼容）
                            "vol_raw": vol_raw,       # 原始值，可能是范围 "T05..T07"
                            "file": file_base,
                            "title": str(r0.get("title", "")).strip(),
                            "byline": str(r0.get("byline", "")).strip(),
                            "dynasty": str(r0.get("time_dynasty", "")).strip(),
                            "category": str(r0.get("category", "")).strip(),
                            "juan": str(r0.get("juan", "")).strip(),
                        }
                        CBETAService._work_meta_cache[w] = meta
                        return meta
                return None
            except httpx.TimeoutException:
                last_error = TimeoutError(f"请求超时: {url}")
                if i < 2:
                    await asyncio.sleep(0.1 * (i + 1))
                continue
            except Exception as e:
                last_error = e
                if i < 2:
                    await asyncio.sleep(0.1 * (i + 1))
                continue

        # 不在这里抛错：让上层继续尝试其它来源
        _ = last_error
        return None

    @staticmethod
    def _local_read_xml(canon: str, volume: str, filename: str) -> Optional[str]:
        root = CBETAService.CBETA_XML_LOCAL_ROOT
        if not root:
            return None
        try:
            p = os.path.join(root, canon.upper(), volume, filename)
            if not os.path.isfile(p):
                return None
            with open(p, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return None

    @staticmethod
    async def search_sutra(keyword: str, limit: int = 20) -> List[Dict]:
        """
        搜索经文

        Args:
            keyword: 搜索关键词（经名或经号）
            limit: 返回结果数量限制

        Returns:
            经文列表 [{'id': 'T0235', 'title': '金刚经', 'dynasty': '后秦', 'translator': '鸠摩罗什', ...}, ...]
        """
        q = (keyword or "").strip()
        if not q:
            return []

        q_title, requested_juan = CBETAService._extract_juan_from_query(q)

        def parse_translator(byline: str) -> str:
            s = (byline or "").strip()
            if not s:
                return "未知"
            # 常见格式：... 唐 玄奘譯 / ... 唐 玄奘译 / ... 失譯
            # CJK 不适用 \\b；取最后一个“译/譯”前的姓名片段
            m = re.findall(r"([\u4e00-\u9fffA-Za-z·．・]{1,20})(?:譯|译)", s)
            if m:
                return (m[-1] or "").strip() or "未知"
            if "失譯" in s or "失译" in s:
                return "失译"
            # 兜底：取最后一个“译/譯”前的词，或 creators 的最后一位
            return "未知"

        def parse_author(byline: str) -> str:
            s = (byline or "").strip()
            if not s:
                return "未知"
            # 常见格式：尊者世亲造 / 某某撰 / 某某述 / 某某集
            m = re.findall(r"([\u4e00-\u9fffA-Za-z·．・]{1,30})(?:造|撰|作|述|集|說|说|注|註|疏|記|记)", s)
            if m:
                return (m[-1] or "").strip() or "未知"
            return "未知"

        # 经号匹配（如 T0235 / T1558_001）
        parsed_id = CBETAService._parse_sutra_id(q)
        if parsed_id:
            work_id = CBETAService._work_id_from_parsed(parsed_id)
            part = (parsed_id.get("part") or "").strip()
            sutra_id = f"{work_id}_{part}" if part else f"{work_id}_001"

            meta = await CBETAService._fetch_work_meta(work_id)
            title = (meta or {}).get("title", "").strip()
            byline = (meta or {}).get("byline", "").strip()

            dynasty = ((meta or {}).get("dynasty", "") or "").strip() or "未知"
            try:
                juan = int(((meta or {}).get("juan", "") or "").strip() or "1")
            except Exception:
                juan = 1

            category = ((meta or {}).get("category", "") or "").strip() or "未分类"

            return [
                {
                    "id": sutra_id.upper(),
                    "title": title or f"经典{sutra_id.upper()}",
                    "full_title": title or f"经典{sutra_id.upper()}",
                    "dynasty": dynasty,
                    "translator": parse_translator(byline),
                    "author": parse_author(byline),
                    "byline": byline,
                    "juan": juan,
                    "category": category,
                }
            ]

        # 通过 CBETA 目录 API 搜索（CBETA Online 使用 search/toc?q=）
        url = f"{CBETAService.CBETA_CATALOG_API}search/toc?q={httpx.QueryParams({'q': q_title})['q']}"
        last_error: Optional[Exception] = None
        client = CBETAService._get_http_client()
        for i in range(3):
            try:
                resp = await client.get(url)
                if resp.status_code != 200:
                    last_error = RuntimeError(f"HTTP {resp.status_code}")
                    if i < 2:
                        await asyncio.sleep(0.1 * (i + 1))
                    continue
                data = resp.json()
                items = []
                for r in (data or {}).get("results", []) or []:
                    if not isinstance(r, dict):
                        continue
                    if r.get("type") != "work":
                        continue
                    work = (r.get("work") or "").strip().upper()
                    title = (r.get("title") or "").strip() or work
                    if not work:
                        continue

                    byline = (r.get("byline") or "").strip()

                    # 默认返回第一卷；若用户输入"卷第X"，则返回对应卷号（_001/_002/...）
                    total_juan = int(r.get("juan") or 1)
                    target_juan = requested_juan or 1
                    if target_juan < 1:
                        target_juan = 1
                    if target_juan > total_juan:
                        # 超过范围则忽略请求，回退到第一卷（避免"搜到但导入失败"）
                        target_juan = 1

                    sutra_id = f"{work}_{target_juan:03d}"

                    items.append(
                        {
                            "id": sutra_id,
                            "title": title,
                            "full_title": title,
                            "dynasty": (r.get("time_dynasty") or "未知").strip() or "未知",
                            "translator": parse_translator(byline),
                            "author": parse_author(byline),
                            "byline": byline,
                            "juan": int(r.get("juan") or 1),
                            "category": (r.get("category") or "").strip() or "未分类",
                        }
                    )

                return items[:limit]
            except httpx.TimeoutException:
                last_error = TimeoutError(f"搜索请求超时: {url}")
                if i < 2:
                    await asyncio.sleep(0.1 * (i + 1))
                continue
            except Exception as e:
                last_error = e
                if i < 2:
                    await asyncio.sleep(0.1 * (i + 1))
                continue

        # 搜索失败：降级为空，避免前端误导
        _ = last_error
        return []

    @staticmethod
    def _xml_contains_juan(xml_text: str, target_juan: int) -> bool:
        """
        快速检查 XML 文本是否包含指定的卷号。
        用于在多分卷经典（如 T0220）中定位正确的文件。
        """
        if not xml_text or target_juan <= 0:
            return True  # 不指定卷号时，任何文件都可以

        # 快速正则匹配：cb:juan n="579" 或 milestone unit="juan" n="579"
        import re
        # 匹配 cb:juan n="579" 或类似格式
        pattern = rf'(?:cb:juan[^>]*n="{target_juan}")|(?:milestone[^>]*unit="juan"[^>]*n="{target_juan}")'
        return bool(re.search(pattern, xml_text))

    @staticmethod
    async def fetch_sutra_xml(sutra_id: str) -> Optional[str]:
        """
        获取经文XML（TEI格式）

        Args:
            sutra_id: 经号（如T0235）

        Returns:
            XML字符串，如果获取失败返回None
        """
        parsed = CBETAService._parse_sutra_id(sutra_id)
        if not parsed:
            return None

        canon = parsed["canon"]
        sutra_no = parsed["sutra_no"]
        letter = parsed["letter"]
        part = parsed["part"]

        explicit_volume = parsed["explicit_volume"] or None
        work_id = CBETAService._work_id_from_parsed(parsed)

        # 1) 优先通过目录 API 定位卷号/文件名（避免全卷扫描）
        catalog_meta: Optional[Dict[str, str]] = None
        if not explicit_volume:
            catalog_meta = await CBETAService._fetch_work_meta(work_id)

        # 2) 缓存命中：优先尝试历史成功的卷号
        cache_key = (sutra_id or "").strip().upper()
        cached_volume = CBETAService._volume_cache.get(cache_key)
        volume_candidates = [cached_volume] if cached_volume else []

        # 如果目录 API 返回了卷号范围（如 "T05..T07"），展开为候选列表
        if catalog_meta and catalog_meta.get("vol_raw"):
            vol_range = CBETAService._parse_volume_range(catalog_meta["vol_raw"])
            # 智能排序：根据目标卷号在总卷数中的位置决定搜索方向
            # 例如：T0220 共 600 卷，第 579 卷应从 T07 开始搜索，第 1 卷应从 T05 开始
            if part and vol_range:
                try:
                    target_juan = int(str(part).lstrip("0") or "0")
                    total_juan = int(catalog_meta.get("juan", "1") or "1")
                    # 如果目标卷号在后半部分，倒序搜索
                    if total_juan > 0 and target_juan > total_juan // 2:
                        vol_range = list(reversed(vol_range))
                except (ValueError, TypeError):
                    pass
            for v in vol_range:
                if v not in volume_candidates:
                    volume_candidates.append(v)
        elif catalog_meta and catalog_meta.get("volume"):
            v = catalog_meta["volume"]
            if v not in volume_candidates:
                volume_candidates.insert(0, v)

        # 兜底：遍历所有可能的册号
        for v in CBETAService._iter_volume_candidates(canon, explicit_volume):
            if v not in volume_candidates:
                volume_candidates.append(v)

        # 扩展字母后缀：T0220（大般若波罗蜜多经）等巨型经典分布在 a-o 共 15 个文件中
        letters = [letter] if letter else ["", "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o"]

        # 使用全局 HTTP 客户端
        client = CBETAService._get_http_client()

        async def _get_xml_text(xml_url: str) -> Optional[str]:
            last_err: Optional[Exception] = None
            for i in range(3):
                try:
                    response = await client.get(xml_url)
                    if response.status_code == 200 and response.text:
                        return response.text
                    return None
                except httpx.TimeoutException:
                    last_err = TimeoutError(f"获取XML超时: {xml_url}")
                    if i < 2:
                        await asyncio.sleep(0.1 * (i + 1))
                    continue
                except Exception as e:
                    last_err = e
                    if i < 2:
                        await asyncio.sleep(0.1 * (i + 1))
                    continue
            raise RuntimeError(str(last_err) if last_err else "Network error")

        # 解析目标卷号用于验证
        target_juan = 0
        if part:
            try:
                target_juan = int(str(part).lstrip("0") or "0")
            except Exception:
                target_juan = 0

        try:
            last_request_error: Optional[Exception] = None
            for volume in volume_candidates:
                # 目录 API 已给出 file（例如 T29n1558）时，直接优先尝试该文件
                # 但如果指定了特定卷号（part），需要跳过这个快捷路径，因为巨型经典（如 T0220）
                # 分布在多个文件中，目录返回的只是第一个文件
                if catalog_meta and catalog_meta.get("file") and not part:
                    file_base = catalog_meta["file"].strip()
                    for filename in [f"{file_base}.xml"]:
                        local_xml = CBETAService._local_read_xml(canon, volume, filename)
                        if local_xml:
                            CBETAService._volume_cache[cache_key] = volume
                            return local_xml
                        xml_path = f"{canon}/{volume}/{filename}"
                        for repo in CBETAService.CBETA_XML_REPOS:
                            xml_url = f"{repo}/{xml_path}"
                            try:
                                text = await _get_xml_text(xml_url)
                                if text:
                                    CBETAService._volume_cache[cache_key] = volume
                                    return text
                            except Exception as e:
                                last_request_error = e
                                # 目录 API 已定位到具体文件，但网络异常：直接退出，交给上层报 502
                                raise RuntimeError(str(e))

                # 无目录信息时，或指定了特定卷号时，按常规命名尝试（支持 _001 等和字母后缀）
                for suf in letters:
                    base_filename = f"{volume}n{sutra_no}{suf}"
                    candidate_filenames = [f"{base_filename}.xml"]
                    if part:
                        candidate_filenames.insert(0, f"{base_filename}_{part}.xml")

                    for filename in candidate_filenames:
                        # 1) 本地优先
                        local_xml = CBETAService._local_read_xml(canon, volume, filename)
                        if local_xml:
                            # 如果指定了卷号，检查文件是否包含该卷
                            if target_juan > 0 and not CBETAService._xml_contains_juan(local_xml, target_juan):
                                continue  # 不包含目标卷，继续搜索下一个文件
                            CBETAService._volume_cache[cache_key] = volume
                            return local_xml

                        # 2) 远程拉取（多仓库回退）
                        xml_path = f"{canon}/{volume}/{filename}"
                        for repo in CBETAService.CBETA_XML_REPOS:
                            xml_url = f"{repo}/{xml_path}"
                            try:
                                text = await _get_xml_text(xml_url)
                                if text:
                                    # 如果指定了卷号，检查文件是否包含该卷
                                    if target_juan > 0 and not CBETAService._xml_contains_juan(text, target_juan):
                                        break  # 该仓库的此文件不包含目标卷，跳到下一个 suf
                                    CBETAService._volume_cache[cache_key] = volume
                                    return text
                            except Exception as e:
                                last_request_error = e
                                # 网络层异常：对于指定卷号的请求，继续尝试其他文件
                                if target_juan > 0:
                                    break  # 跳到下一个 suf
                                # 否则直接退出（避免长时间卡住）
                                raise RuntimeError(str(e))

            # 若尝试过但遇到可用性问题，抛出便于上层返回 502/503
            if last_request_error:
                raise RuntimeError(str(last_request_error))
            return None
        except RuntimeError:
            raise
        except Exception as e:
            # 兜底：统一包装成 RuntimeError，方便 API 返回 502
            raise RuntimeError(f"Failed to fetch CBETA XML: {e}")

    @staticmethod
    def parse_cbeta_xml(
        xml_content: str,
        juan_part: Optional[str] = None,
        strip_punctuation: bool = True,
    ) -> Dict:
        """
        解析CBETA XML，提取纯文本和校勘记

        Args:
            xml_content: CBETA TEI XML字符串
            juan_part: 可选，卷号（如 "001"），仅提取该卷内容

        Returns:
            {
                'text': str,  # 纯文本
                'title': str,
                'author': str,
                'collations': [  # 校勘记
                    {
                        'position': int,
                        'lemma': str,  # 底本
                        'readings': [{'wit': str, 'text': str, 'type': str}],  # 校本
                        'note': str
                    },
                    ...
                ]
            }
        """
        try:
            root = etree.fromstring(xml_content.encode('utf-8'))

            # 定义命名空间
            TEI_NS = "http://www.tei-c.org/ns/1.0"
            ns = {'tei': TEI_NS}

            # 解析 witness 映射表（wit1 -> 【宋】等）
            witness_map: Dict[str, str] = {}
            for witness in root.findall('.//tei:witness', ns):
                wit_id = witness.get("{http://www.w3.org/XML/1998/namespace}id") or ""
                wit_name = "".join(witness.itertext()).strip()
                if wit_id and wit_name:
                    witness_map[wit_id] = wit_name
                    # 也映射 #wit1 格式
                    witness_map[f"#{wit_id}"] = wit_name

            def resolve_wit(wit_raw: str) -> str:
                """将 witness ID 转换为可读名称"""
                if not wit_raw:
                    return ""
                # wit 可能是 "#wit1 #wit2" 这样的多个ID
                parts = wit_raw.strip().split()
                names = []
                for p in parts:
                    p = p.strip()
                    if p in witness_map:
                        names.append(witness_map[p])
                    elif p.lstrip("#") in witness_map:
                        names.append(witness_map[p.lstrip("#")])
                    else:
                        # 保留原始值
                        names.append(p.lstrip("#"))
                return "".join(names)

            # 提取标题 - 优先使用 cb:jhead（卷头，如"瑜伽師地論卷第一"）
            # 避免使用 TEI header 中的藏经总名（如 "Taishō Tripiṭaka"）
            CB_NS_TITLE = "http://www.cbeta.org/ns/1.0"
            title = None

            # 解析目标卷号
            target_juan_for_title: Optional[int] = None
            if juan_part:
                try:
                    target_juan_for_title = int(str(juan_part).lstrip("0") or "0")
                except Exception:
                    target_juan_for_title = None
                if target_juan_for_title == 0:
                    target_juan_for_title = None

            # 1) 首先尝试 cb:jhead（卷头标题，最具体）
            # 如果指定了卷号，需要找到对应卷的 jhead
            if target_juan_for_title is not None:
                # 遍历所有 cb:juan 元素，找到对应卷号的 jhead
                body_elem = root.find('.//tei:body', ns)
                if body_elem is not None:
                    current_juan = 0
                    for elem in body_elem.iter():
                        # 检查 milestone 标记卷号
                        if elem.tag == f"{{{TEI_NS}}}milestone" and elem.get("unit") == "juan":
                            n = (elem.get("n") or "").strip()
                            if n.isdigit():
                                current_juan = int(n)
                        # 检查 cb:juan 元素
                        elif elem.tag == f"{{{CB_NS_TITLE}}}juan":
                            n = (elem.get("n") or "").strip()
                            if n.isdigit():
                                current_juan = int(n)
                        # 找到目标卷的 jhead
                        elif elem.tag == f"{{{CB_NS_TITLE}}}jhead" and current_juan == target_juan_for_title:
                            jhead_text = "".join(elem.itertext()).strip()
                            if jhead_text:
                                title = jhead_text
                                break

            # 如果没找到指定卷的 jhead，尝试第一个 jhead
            if not title:
                jhead_elem = root.find(f'.//{{{CB_NS_TITLE}}}jhead', ns)
                if jhead_elem is not None:
                    jhead_text = "".join(jhead_elem.itertext()).strip()
                    if jhead_text:
                        # 如果指定了卷号，替换标题中的卷号
                        if target_juan_for_title is not None:
                            # 尝试替换卷号，如 "卷第一" -> "卷第二十五"
                            title = CBETAService._replace_juan_in_title(jhead_text, target_juan_for_title)
                        else:
                            title = jhead_text

            # 2) 如果没有 jhead，尝试找 titleStmt 中的中文标题
            if not title:
                for title_elem in root.findall('.//tei:titleStmt/tei:title', ns):
                    t = (title_elem.text or "").strip()
                    # 跳过英文/罗马化标题（如 Taishō Tripiṭaka）
                    if t and any('\u4e00' <= c <= '\u9fff' for c in t):
                        title = t
                        break

            # 3) 后备：使用第一个 title 元素
            if not title:
                title_elem = root.find('.//tei:title', ns)
                title = (title_elem.text if title_elem is not None else None) or '未命名'

            # 提取作者/译者
            author_elem = root.find('.//tei:author', ns)
            author = author_elem.text if author_elem is not None else '未知'

            # 提取正文
            body = root.find('.//tei:body', ns)
            if body is None:
                return {
                    'text': '',
                    'title': title,
                    'author': author,
                    'collations': []
                }

            # 递归提取文本，并记录锚点位置（供 back/apparatus 里的 <app from="#beg..." to="#end..."> 定位）
            text_parts = []
            current_position = 0
            anchors: Dict[str, int] = {}

            target_juan: Optional[int] = None
            if juan_part:
                try:
                    target_juan = int(str(juan_part).lstrip("0") or "0")
                except Exception:
                    target_juan = None
                if target_juan == 0:
                    target_juan = None

            collecting = target_juan is None
            done = False

            def norm(s: str) -> str:
                return CBETAService._maybe_strip_punctuation(s, strip_punctuation)

            # CBETA 命名空间
            CB_NS = "http://www.cbeta.org/ns/1.0"

            def extract_text_recursive(elem):
                nonlocal current_position
                nonlocal collecting, done

                if done:
                    return

                # 主文本提取时跳过 <note> 内容（校注/旁注），避免混入对勘文本
                if elem.tag == f"{{{TEI_NS}}}note":
                    return

                # 跳过 CBETA 特有的非正文元素
                # cb:docNumber - 文档编号（如 "No. 1579 [cf. Nos. 1580-1584]"）
                # cb:mulu - 目录标记（如 "1章"、"2節" 等章节编号）
                # cb:jhead - 卷头（通常包含标题，已在其他地方处理）
                # cb:juan - 卷标记
                if elem.tag in (
                    f"{{{CB_NS}}}docNumber",
                    f"{{{CB_NS}}}mulu",
                    f"{{{CB_NS}}}jhead",
                    f"{{{CB_NS}}}juan",
                ):
                    return

                # 以 milestone(unit=juan, n=1/2/...) 划分卷
                if (
                    target_juan is not None
                    and elem.tag == f"{{{TEI_NS}}}milestone"
                    and elem.get("unit") == "juan"
                ):
                    n = (elem.get("n") or "").strip()
                    if n.isdigit():
                        cur = int(n)
                        if cur == target_juan:
                            collecting = True
                        elif collecting:
                            done = True
                            return

                # 记录锚点：anchor/@xml:id
                if elem.tag == f"{{{TEI_NS}}}anchor":
                    anchor_id = elem.get("{http://www.w3.org/XML/1998/namespace}id") or ""
                    anchor_id = anchor_id.strip()
                    if anchor_id:
                        anchors[anchor_id] = current_position

                if elem.tag == f"{{{TEI_NS}}}app":
                    # 这是一个校勘条目
                    lem_elem = elem.find('tei:lem', ns)
                    elem.findall('tei:rdg', ns)
                    elem.find('tei:note', ns)

                    if collecting and lem_elem is not None:
                        lem_text = norm(''.join(lem_elem.itertext()))
                        text_parts.append(lem_text)

                        current_position += len(lem_text)
                else:
                    # 普通文本
                    if collecting and elem.text:
                        t = norm(elem.text)
                        if t:
                            text_parts.append(t)
                            current_position += len(t)

                    for child in elem:
                        extract_text_recursive(child)
                        if done:
                            return
                        if collecting and child.tail:
                            t = norm(child.tail)
                            if t:
                                text_parts.append(t)
                                current_position += len(t)

            extract_text_recursive(body)

            full_text = ''.join(text_parts)

            def extract_text_excluding_notes(e: Optional[etree._Element]) -> str:
                if e is None:
                    return ""
                # 仅取不在 <note> 内的文本
                parts = e.xpath(".//text()[not(ancestor::tei:note)]", namespaces=ns)
                return norm("".join([p for p in parts if p]))

            # 从 back/apparatus 中解析校勘记（CBETA XML 常将 <app> 放在 <back>）
            collations = []
            back = root.find(".//tei:back", ns)
            if back is not None:
                for app in back.findall(".//tei:app", ns):
                    from_ref = (app.get("from") or "").strip()
                    to_ref = (app.get("to") or "").strip()
                    if not from_ref.startswith("#") or not to_ref.startswith("#"):
                        continue
                    from_id = from_ref[1:]
                    to_id = to_ref[1:]
                    start = anchors.get(from_id)
                    end = anchors.get(to_id)
                    if start is None or end is None or end < start:
                        continue

                    lemma = full_text[start:end]
                    if not lemma:
                        continue

                    readings = []
                    for rdg in app.findall("tei:rdg", ns):
                        wit_raw = rdg.get("wit", "") or ""
                        readings.append(
                            {
                                "wit": resolve_wit(wit_raw),
                                "text": extract_text_excluding_notes(rdg),
                                "type": rdg.get("type", "") or "",
                            }
                        )

                    notes = [n.strip() for n in app.xpath(".//tei:note//text()", namespaces=ns) if n and n.strip()]
                    collations.append(
                        {
                            "position": start,
                            "lemma": lemma,
                            "readings": readings,
                            "note": "；".join(notes),
                        }
                    )

            collations.sort(key=lambda x: x.get("position", 0))

            return {
                'text': full_text,
                'title': title,
                'author': author,
                'collations': collations
            }

        except Exception as e:
            print(f"Failed to parse CBETA XML: {e}")
            return {
                'text': '',
                'title': '解析失败',
                'author': '',
                'collations': []
            }

    @staticmethod
    async def import_from_cbeta(sutra_id: str, strip_punctuation: bool = True) -> Optional[Dict]:
        """
        从CBETA导入经文

        Args:
            sutra_id: 经号

        Returns:
            解析后的经文数据
        """
        xml_content = await CBETAService.fetch_sutra_xml(sutra_id)
        if not xml_content:
            return None

        parsed = CBETAService._parse_sutra_id(sutra_id)
        parsed_data = CBETAService.parse_cbeta_xml(
            xml_content,
            juan_part=(parsed or {}).get("part"),
            strip_punctuation=strip_punctuation,
        )
        parsed_data['sutra_id'] = sutra_id

        return parsed_data

    @staticmethod
    def export_to_cbeta_format(collation_data: Dict) -> str:
        """
        将校勘数据导出为CBETA兼容的TEI XML格式

        这个功能实际上就是调用我们已有的TEI导出服务
        """
        return TEIExportService.export_collation_tei(collation_data)

    @staticmethod
    def generate_cbeta_contribution_report(
        new_findings: List[Dict],
        sutra_id: str,
        contributor_name: str = "研究者"
    ) -> str:
        """
        生成CBETA勘误报告（可提交给CBETA编辑部）

        Args:
            new_findings: 新发现的异文列表
            sutra_id: 经号
            contributor_name: 贡献者姓名

        Returns:
            勘误报告文本
        """
        from datetime import datetime

        report_lines = [
            "致CBETA编辑部：\n",
            f"在使用贵站《大正新脩大藏经》{sutra_id}号经典进行校勘研究时，",
            "发现以下异文未被收录或与现有校勘记有出入，特此报告：\n",
            f"经号：{sutra_id}",
            f"校勘者：{contributor_name}",
            f"日期：{datetime.now().strftime('%Y年%m月%d日')}\n",
            "新发现异文：\n"
        ]

        for i, finding in enumerate(new_findings, 1):
            pos = finding.get('position', '?')
            base_char = finding.get('base_char', '')
            variant_char = finding.get('variant_char', '')
            source = finding.get('source', '未知版本')
            category = finding.get('category', '差异')

            category_names = {
                'error': '讹误',
                'variant': '异体字',
                'yanwen': '衍文',
                'tuowen': '脱文',
                'daowen': '倒文'
            }
            cat_name = category_names.get(category, category)

            report_lines.append(
                f'{i}. 位置{pos}：底本作"{base_char}"，'
                f'{source}作"{variant_char}"（{cat_name}）'
            )

        report_lines.extend([
            "\n以上异文均经仔细核对确认。",
            "如有疑问，欢迎来信讨论。\n",
            "感谢贵站为佛典数字化做出的卓越贡献！\n",
            f"此致\n敬礼\n\n{contributor_name}",
            f"{datetime.now().strftime('%Y年%m月%d日')}"
        ])

        return '\n'.join(report_lines)
