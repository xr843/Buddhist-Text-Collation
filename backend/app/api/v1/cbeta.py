"""
CBETA平台对接API
"""
import asyncio
import io
import urllib.parse
import zipfile
import time
import httpx
from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel
from typing import List, Dict, Optional, Any

from app.services.cbeta_service import CBETAService

router = APIRouter()

# 内存缓存（用于在 Redis 不可用时提供缓存支持）
# 格式: { key: { 'data': Any, 'expires': timestamp } }
_memory_cache: Dict[str, Dict[str, Any]] = {}
_CACHE_TTL = 3600  # 缓存1小时


def _get_cache(key: str) -> Optional[Any]:
    """从内存缓存获取数据"""
    if key in _memory_cache:
        entry = _memory_cache[key]
        if entry['expires'] > time.time():
            return entry['data']
        else:
            # 过期，删除
            del _memory_cache[key]
    return None


def _set_cache(key: str, data: Any, ttl: int = _CACHE_TTL):
    """设置内存缓存"""
    _memory_cache[key] = {
        'data': data,
        'expires': time.time() + ttl
    }
    # 简单的缓存清理：如果缓存超过100个条目，删除最旧的
    if len(_memory_cache) > 100:
        oldest_key = min(_memory_cache.keys(), key=lambda k: _memory_cache[k]['expires'])
        del _memory_cache[oldest_key]


@router.get("/cbeta/search")
async def search_cbeta_sutra(keyword: str, limit: int = 20):
    """
    搜索CBETA经文

    Args:
        keyword: 搜索关键词（经名或经号）
        limit: 返回结果数量

    Returns:
        经文列表
    """
    try:
        results = await CBETAService.search_sutra(keyword, limit)
        return {
            'success': True,
            'results': results,
            'total': len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@router.get("/cbeta/fetch/{sutra_id}")
async def fetch_cbeta_sutra(sutra_id: str, strip_punctuation: bool = True):
    """
    获取CBETA经文详情

    Args:
        sutra_id: 经号（如T0235）

    Returns:
        经文内容和校勘记
    """
    try:
        # 检查内存缓存
        cache_key = f"cbeta_fetch:{sutra_id}:{strip_punctuation}"
        cached_data = _get_cache(cache_key)
        if cached_data is not None:
            return cached_data

        try:
            data = await CBETAService.import_from_cbeta(sutra_id, strip_punctuation=strip_punctuation)
        except RuntimeError as e:
            raise HTTPException(
                status_code=502,
                detail=f"获取CBETA源数据失败（可能无法访问CBETA XML仓库/镜像）：{str(e)}"
            )

        if not data:
            raise HTTPException(
                status_code=404,
                detail=f"未找到经文 {sutra_id}（可能是经号格式不支持，或对应XML文件不存在/无法访问）"
            )

        result = {
            'success': True,
            'sutra': data
        }

        # 缓存结果
        _set_cache(cache_key, result)

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.get("/cbeta/xml/{sutra_id}")
async def fetch_cbeta_sutra_xml(sutra_id: str):
    """
    获取CBETA经文原始 TEI XML

    Args:
        sutra_id: 经号（如 T1558_001）

    Returns:
        TEI XML 文本（application/xml）
    """
    try:
        try:
            xml_content = await CBETAService.fetch_sutra_xml(sutra_id)
        except RuntimeError as e:
            raise HTTPException(
                status_code=502,
                detail=f"获取CBETA源数据失败（可能无法访问CBETA XML仓库/镜像）：{str(e)}"
            )

        if not xml_content:
            raise HTTPException(
                status_code=404,
                detail=f"未找到经文 {sutra_id}（可能是经号格式不支持，或对应XML文件不存在/无法访问）"
            )

        return Response(content=xml_content, media_type="application/xml; charset=utf-8")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")

def _content_disposition_attachment(filename: str) -> str:
    safe = "".join([c if 32 <= ord(c) < 127 and c not in ['"', "\\\\"] else "_" for c in filename])
    encoded = urllib.parse.quote(filename, safe="")
    return f'attachment; filename="{safe}"; filename*=UTF-8\'\'{encoded}'

async def _download_cbdata_txt(sutra_id: str, kind: str) -> bytes:
    """
    直接复用 CBETA Online 的官方 TXT 导出（cbdata catalogAPI）。

    kind:
      - text
      - text-with-notes
    """
    sid = (sutra_id or "").strip().upper()
    if not sid:
        raise HTTPException(status_code=400, detail="sutra_id 不能为空")
    if kind not in {"text", "text-with-notes"}:
        raise HTTPException(status_code=400, detail="kind 仅支持 text/text-with-notes")

    # 使用 CBETAService 的全局 HTTP 客户端
    client = CBETAService._get_http_client()
    last_error: Optional[Exception] = None
    for i in range(3):
        try:
            url = f"{CBETAService.CBETA_CATALOG_API.rstrip('/')}/download/{kind}/{sid}.txt.zip"
            resp = await client.get(url)
            if resp.status_code != 200:
                raise RuntimeError(f"HTTP {resp.status_code}")

            # zip 文件应以 PK 开头；避免被 HTML/错误页误判
            if not resp.content.startswith(b"PK"):
                raise RuntimeError("下载内容不是 zip（可能被网关/代理替换）")

            z = zipfile.ZipFile(io.BytesIO(resp.content))
            txt_names = [n for n in z.namelist() if n.lower().endswith(".txt")]
            if not txt_names:
                raise RuntimeError("zip 中未找到 .txt 文件")

            # 约定：只导出第一份 txt（cbdata 的 zip 一般只包含一个 txt）
            return z.read(txt_names[0])
        except httpx.TimeoutException:
            last_error = TimeoutError(f"下载超时: {url}")
            if i < 2:
                await asyncio.sleep(0.1 * (i + 1))
            continue
        except Exception as e:
            last_error = e
            if i < 2:
                await asyncio.sleep(0.1 * (i + 1))
            continue

    raise HTTPException(status_code=502, detail=f"下载CBETA官方TXT失败：{last_error}")


@router.get("/cbeta/export/txt/{sutra_id}")
async def export_cbeta_txt(sutra_id: str, variant: str = "plain"):
    """
    导出 TXT（用于对勘/整理）

    variant:
      - plain: 纯文本（默认去标点）
      - punct: 含标点
      - punct_notes: 含标点 + 校勘记（校注）
    """
    try:
        variant = (variant or "").strip().lower()
        if variant not in {"plain", "punct", "punct_notes"}:
            raise HTTPException(status_code=400, detail="variant 仅支持 plain/punct/punct_notes")

        # punct / punct_notes：严格对齐 CBETA Online 官方导出格式
        if variant in {"punct", "punct_notes"}:
            kind = "text" if variant == "punct" else "text-with-notes"
            payload = await _download_cbdata_txt(sutra_id, kind=kind)

            filename = f"{(sutra_id or '').strip().upper()}.txt"
            headers = {"Content-Disposition": _content_disposition_attachment(filename)}
            return Response(content=payload, media_type="text/plain; charset=utf-8", headers=headers)

        try:
            # plain：对勘用纯文本（去标点、跳过校注）
            data = await CBETAService.import_from_cbeta(sutra_id, strip_punctuation=True)
        except RuntimeError as e:
            raise HTTPException(
                status_code=502,
                detail=f"获取CBETA源数据失败（可能无法访问CBETA XML仓库/镜像）：{str(e)}"
            )

        if not data:
            raise HTTPException(
                status_code=404,
                detail=f"未找到经文 {sutra_id}（可能是经号格式不支持，或对应XML文件不存在/无法访问）"
            )

        title = (data.get("title") or "").strip()
        # 更优先使用 works 元数据的 title（避免 TEI 头部取到英文总名）
        parsed = CBETAService._parse_sutra_id(sutra_id)
        if parsed:
            meta = await CBETAService._fetch_work_meta(CBETAService._work_id_from_parsed(parsed))
            meta_title = (meta or {}).get("title", "").strip()
            if meta_title:
                title = meta_title
        title = title or sutra_id

        part = ""
        if parsed and parsed.get("part"):
            part = str(parsed["part"]).zfill(3)

        base_name = f"CBETA_《{title}》"
        if part:
            base_name = f"{base_name}_{part}"

        suffix = {
            "plain": "纯文本",
            "punct": "含标点",
            "punct_notes": "含标点_校勘记",
        }[variant]

        filename = f"{base_name}_{suffix}.txt"

        text = (data.get("text") or "").rstrip()

        # 加 BOM，方便 Windows 直接用记事本打开
        payload = "\ufeff" + text + "\n"
        headers = {"Content-Disposition": _content_disposition_attachment(filename)}
        return Response(content=payload, media_type="text/plain; charset=utf-8", headers=headers)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


class ContributionReportRequest(BaseModel):
    """勘误报告请求"""
    sutra_id: str
    contributor_name: str = "研究者"
    new_findings: List[Dict]


@router.post("/cbeta/contribution-report")
async def generate_contribution_report(request: ContributionReportRequest):
    """
    生成CBETA勘误贡献报告

    Args:
        request: 包含经号、贡献者姓名和新发现异文的请求

    Returns:
        勘误报告文本
    """
    try:
        report = CBETAService.generate_cbeta_contribution_report(
            new_findings=request.new_findings,
            sutra_id=request.sutra_id,
            contributor_name=request.contributor_name
        )

        return {
            'success': True,
            'report': report
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成报告失败: {str(e)}")
