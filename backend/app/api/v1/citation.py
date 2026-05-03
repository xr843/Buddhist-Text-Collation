"""
引用与永久链接 API。

给前端的"引用此视图"功能提供 BibTeX / Chicago / CFF / RIS 字符串，
内含项目版本、当前 git commit、底本与校本标识、行号区间与访问日期。
确保学术论文 cite 出去的 URL 可复现回同一窗口。
"""
from __future__ import annotations

import os
import subprocess
from datetime import datetime, timezone
from functools import lru_cache
from typing import List, Optional
from urllib.parse import urlencode, urlparse

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

router = APIRouter()

PROJECT_TITLE = "Buddhist Text Collation Workbench"
PROJECT_REPO = "https://github.com/xr843/Buddhist-Text-Collation"


@lru_cache(maxsize=1)
def _git_commit_short() -> str:
    """优先 env，其次 git 命令；找不到时返回 'dev'。镜像/容器里通常用 env 注入。"""
    for key in ("GIT_COMMIT", "VCS_REF", "SOURCE_COMMIT"):
        value = os.environ.get(key)
        if value:
            return value[:7]
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            timeout=2,
        )
        return out.stdout.strip() or "dev"
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        return "dev"


def _build_permalink(
    base_url: str,
    sutra: Optional[str],
    editions: List[str],
    line_start: Optional[int],
    line_end: Optional[int],
    view: Optional[str],
) -> str:
    params: List[tuple[str, str]] = []
    if view:
        params.append(("view", view))
    if sutra:
        params.append(("sutra", sutra))
    if editions:
        params.append(("editions", ",".join(editions)))
    if line_start is not None:
        if line_end is not None and line_end != line_start:
            params.append(("line", f"{line_start}-{line_end}"))
        else:
            params.append(("line", str(line_start)))
    query = urlencode(params)
    sep = "&" if "?" in base_url else "?"
    return f"{base_url}{sep}{query}" if query else base_url


def _bibtex_key(sutra: Optional[str], editions: List[str], commit: str) -> str:
    """BibTeX key 不含特殊字符。"""
    parts = ["btc"]
    if sutra:
        parts.append("".join(c for c in sutra if c.isalnum()) or "view")
    if editions:
        parts.append("".join(e[0] for e in editions if e))
    parts.append(commit)
    return "_".join(p for p in parts if p)


class CitationResponse(BaseModel):
    permalink: str
    accessed: str = Field(..., description="ISO-8601 访问日期")
    commit: str
    formats: dict[str, str] = Field(
        ..., description="键为 bibtex/chicago/cff/ris/markdown，值为可直接复制的字符串"
    )


@router.get("/citation", response_model=CitationResponse)
async def get_citation(
    base_url: str = Query(..., description="前端视图基础 URL，如 https://example.org/comparison"),
    sutra: Optional[str] = Query(None, description="经号或文档 ID，如 T0220"),
    editions: Optional[str] = Query(None, description="逗号分隔的版本编号，如 T,Q,J"),
    line_start: Optional[int] = Query(None, ge=0, description="起始行号"),
    line_end: Optional[int] = Query(None, ge=0, description="结束行号"),
    view: Optional[str] = Query(None, description="视图类型: comparison/multi-collation/phylogeny"),
    title: Optional[str] = Query(None, max_length=200, description="自定义标题，省略时按 sutra/view 自动生成"),
    authors: Optional[str] = Query(None, max_length=200, description="作者，逗号分隔；省略时使用项目标题"),
):
    """生成可粘贴到论文的引用块（BibTeX / Chicago / CFF / RIS / Markdown）。"""
    # Reject non-http(s) schemes — citation strings get pasted into other people's
    # docs, so a `javascript:`/`data:` URL would be a stored XSS vector.
    parsed = urlparse(base_url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="base_url must be an http(s) URL",
        )
    if line_end is not None and line_start is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="line_end requires line_start",
        )
    if line_end is not None and line_end < (line_start or 0):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="line_end must be >= line_start",
        )

    edition_list = [e.strip() for e in (editions or "").split(",") if e.strip()]
    accessed = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    commit = _git_commit_short()
    permalink = _build_permalink(base_url, sutra, edition_list, line_start, line_end, view)

    auto_title_parts: List[str] = []
    if sutra:
        auto_title_parts.append(sutra)
    if edition_list:
        auto_title_parts.append("校勘 " + "/".join(edition_list))
    if line_start is not None:
        auto_title_parts.append(
            f"行 {line_start}" if line_end in (None, line_start) else f"行 {line_start}-{line_end}"
        )
    auto_title = "，".join(auto_title_parts) if auto_title_parts else "校勘视图"
    cite_title = title or f"{PROJECT_TITLE}: {auto_title}"
    cite_authors = authors or "Buddhist Text Collation Contributors"

    key = _bibtex_key(sutra, edition_list, commit)
    year = accessed[:4]

    bibtex = (
        f"@misc{{{key},\n"
        f"  title  = {{{cite_title}}},\n"
        f"  author = {{{cite_authors}}},\n"
        f"  year   = {{{year}}},\n"
        f"  note   = {{commit {commit}}},\n"
        f"  url    = {{{permalink}}},\n"
        f"  urldate= {{{accessed}}}\n"
        f"}}\n"
    )

    chicago = (
        f"{cite_authors}. \"{cite_title}.\" "
        f"{PROJECT_TITLE}, commit {commit} ({year}). "
        f"Accessed {accessed}. {permalink}.\n"
    )

    cff = (
        "cff-version: 1.2.0\n"
        f"title: \"{cite_title}\"\n"
        "type: software\n"
        "authors:\n"
        f"  - name: \"{cite_authors}\"\n"
        f"date-released: \"{accessed}\"\n"
        f"url: \"{permalink}\"\n"
        "identifiers:\n"
        "  - type: other\n"
        f"    value: \"{commit}\"\n"
        "    description: \"git commit short SHA\"\n"
        f"repository-code: \"{PROJECT_REPO}\"\n"
    )

    ris = (
        "TY  - COMP\n"
        f"TI  - {cite_title}\n"
        f"AU  - {cite_authors}\n"
        f"PY  - {year}\n"
        f"UR  - {permalink}\n"
        f"N1  - commit {commit}\n"
        f"DA  - {accessed}\n"
        "ER  - \n"
    )

    markdown = (
        f"[{cite_title}]({permalink}) "
        f"({PROJECT_TITLE}, commit `{commit}`, accessed {accessed})"
    )

    return CitationResponse(
        permalink=permalink,
        accessed=accessed,
        commit=commit,
        formats={
            "bibtex": bibtex,
            "chicago": chicago,
            "cff": cff,
            "ris": ris,
            "markdown": markdown,
        },
    )
