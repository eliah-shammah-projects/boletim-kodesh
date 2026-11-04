from pathlib import Path

from app import create_app

STATIC = Path(__file__).resolve().parent.parent / "app" / "static"


def test_home_loads_css_htmx_and_alpine():
    response = create_app("testing").test_client().get("/")
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert 'lang="pt-BR"' in html
    assert "/static/dist/app.css" in html
    assert "/static/vendor/htmx.min.js" in html
    assert "/static/vendor/alpine.min.js" in html


def test_htmx_sends_csrf_token():
    html = create_app("testing").test_client().get("/").get_data(as_text=True)
    assert "X-CSRFToken" in html


def test_vendored_scripts_exist():
    assert (STATIC / "vendor" / "htmx.min.js").stat().st_size > 10_000
    assert (STATIC / "vendor" / "alpine.min.js").stat().st_size > 10_000
