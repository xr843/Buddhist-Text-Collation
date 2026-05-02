"""
冒烟测试：验证 FastAPI 应用能成功 import 与启动，关键路由可达。
不验证业务逻辑——业务测试请放到独立文件。
"""
from __future__ import annotations


def test_app_imports():
    """app.main 能成功 import（=> 所有路由模块语法/import 正确）。"""
    from app.main import app

    assert app is not None
    assert hasattr(app, "routes")


def test_health_endpoint(client):
    """`/health` 返回 200 + 关键字段。"""
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("status") in {"healthy", "degraded"}
    assert "version" in body


def test_openapi_schema(client):
    """`/openapi.json` 可达（确保所有路由能被 OpenAPI 收集）。"""
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    spec = resp.json()
    assert spec.get("openapi", "").startswith("3.")
    assert "paths" in spec
    # 至少应当有标点对比与对勘相关路径之一
    paths = list(spec["paths"].keys())
    assert any("/comparison" in p or "/multi-collation" in p for p in paths)


def test_no_ocr_routes_left(client):
    """OCR 模块在 v0.1.0 已下线——确保对应路由不存在。"""
    resp = client.get("/openapi.json")
    paths = resp.json().get("paths", {})
    for p in paths:
        assert "/ocr/" not in p, f"unexpected OCR route still present: {p}"
