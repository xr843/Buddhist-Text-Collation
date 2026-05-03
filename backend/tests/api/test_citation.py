"""引用 / permalink 端点测试。"""
from __future__ import annotations


def test_citation_round_trip(client):
    resp = client.get(
        "/api/v1/citation",
        params={
            "base_url": "https://example.org/comparison",
            "sutra": "T0220",
            "editions": "T,Q,J",
            "line_start": 42,
            "line_end": 58,
            "view": "comparison",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    # permalink wiring
    assert "T0220" in data["permalink"]
    assert "editions=T%2CQ%2CJ" in data["permalink"]
    assert "line=42-58" in data["permalink"]
    assert "view=comparison" in data["permalink"]
    # all five formats must come back populated
    formats = data["formats"]
    for key in ("bibtex", "chicago", "cff", "ris", "markdown"):
        assert key in formats
        assert formats[key].strip()
    # bibtex must include url + commit hint
    assert "@misc" in formats["bibtex"]
    assert "url" in formats["bibtex"].lower()
    assert "commit" in formats["bibtex"].lower()
    # CFF must reference repo
    assert "repository-code" in formats["cff"]


def test_citation_rejects_line_end_without_start(client):
    resp = client.get(
        "/api/v1/citation",
        params={"base_url": "https://x.test/", "line_end": 5},
    )
    assert resp.status_code == 400


def test_citation_rejects_inverted_line_range(client):
    resp = client.get(
        "/api/v1/citation",
        params={"base_url": "https://x.test/", "line_start": 10, "line_end": 5},
    )
    assert resp.status_code == 400


def test_citation_minimal_request(client):
    resp = client.get("/api/v1/citation", params={"base_url": "https://x.test/view"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["permalink"] == "https://x.test/view"
    assert data["accessed"]
    assert data["commit"]


def test_citation_rejects_javascript_scheme(client):
    """base_url 出现在生成的引用块里，必须拒绝 javascript:/data: 等可执行 scheme。"""
    resp = client.get(
        "/api/v1/citation",
        params={"base_url": "javascript:alert(1)", "sutra": "T0220"},
    )
    assert resp.status_code == 400


def test_citation_rejects_relative_url(client):
    resp = client.get("/api/v1/citation", params={"base_url": "/comparison"})
    assert resp.status_code == 400


def test_citation_appends_to_existing_query(client):
    """base_url 已带 ? 时用 & 拼接，不能产生 ??。"""
    resp = client.get(
        "/api/v1/citation",
        params={"base_url": "https://x.test/view?lang=zh", "sutra": "T1"},
    )
    assert resp.status_code == 200
    permalink = resp.json()["permalink"]
    assert permalink.count("?") == 1
    assert "lang=zh" in permalink
    assert "sutra=T1" in permalink
