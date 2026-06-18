"""
古籍酷 OCR API 测试。

不依赖外部服务：通过 monkeypatch 打桩 GjcoolOCRService，
验证路由层的配置门禁、类型/大小校验与正常返回。
"""
from __future__ import annotations

from app.services.gjcool_ocr_service import GjcoolOCRService


def test_status_disabled_when_unconfigured(client, monkeypatch):
    """未配置凭据时 status 返回 enabled=False（用 monkeypatch 强制未配置，避免依赖本地 .env）。"""
    monkeypatch.setattr(GjcoolOCRService, "is_configured", lambda: False)
    resp = client.get("/api/v1/ocr/status")
    assert resp.status_code == 200
    assert resp.json() == {"enabled": False}


def test_recognize_503_when_unconfigured(client, monkeypatch):
    """未配置时 recognize 返回 503。"""
    monkeypatch.setattr(GjcoolOCRService, "is_configured", lambda: False)
    resp = client.post(
        "/api/v1/ocr/recognize",
        files={"img": ("x.png", b"\x89PNG\r\n\x1a\n", "image/png")},
    )
    assert resp.status_code == 503


def test_recognize_success(client, monkeypatch):
    """已配置 + 打桩识别 → 200 并回传文本。"""
    monkeypatch.setattr(GjcoolOCRService, "is_configured", lambda: True)

    async def fake_recognize(img_bytes, filename, content_type):
        assert img_bytes  # 收到了图片字节
        return {
            "text": "如是我聞",
            "char_number": 4,
            "line_number": 1,
            "width": 100,
            "height": 200,
        }

    monkeypatch.setattr(GjcoolOCRService, "recognize", fake_recognize)

    resp = client.post(
        "/api/v1/ocr/recognize",
        files={"img": ("page.png", b"\x89PNG\r\n\x1a\nfakebytes", "image/png")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["text"] == "如是我聞"
    assert body["char_number"] == 4


def test_recognize_rejects_unsupported_type(client, monkeypatch):
    """已配置但上传非图片类型 → 415。"""
    monkeypatch.setattr(GjcoolOCRService, "is_configured", lambda: True)

    resp = client.post(
        "/api/v1/ocr/recognize",
        files={"img": ("notes.txt", b"plain text", "text/plain")},
    )
    assert resp.status_code == 415
