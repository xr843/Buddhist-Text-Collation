"""
pytest 共享 fixture
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def client() -> TestClient:
    """构建一个 TestClient，包装 FastAPI app。"""
    # 延迟导入：让测试也能在没安装 redis 等可选依赖时跑（fallback 到 in-memory cache）
    from app.main import app

    with TestClient(app) as c:
        yield c
