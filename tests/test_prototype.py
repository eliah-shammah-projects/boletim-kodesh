import pytest

from app import create_app

PAGES = [
    "/prototipo/",
    "/prototipo/componentes",
    "/prototipo/inicio/rabino",
    "/prototipo/inicio/direcao",
    "/prototipo/shiur",
    "/prototipo/notas",
    "/prototipo/scans",
    "/prototipo/frequencia",
    "/prototipo/boletim",
    "/prototipo/boletim?revisao=1",
]


@pytest.mark.parametrize("path", PAGES)
def test_prototype_pages_render(path):
    response = create_app("testing").test_client().get(path)
    assert response.status_code == 200
    assert "Or Yossef" in response.get_data(as_text=True)


def test_prototype_is_off_in_production(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "x")
    from config import ProductionConfig

    monkeypatch.setattr(ProductionConfig, "SQLALCHEMY_DATABASE_URI", "mysql+pymysql://u:p@h/db")
    monkeypatch.setattr(ProductionConfig, "SECRET_KEY", "x")
    app = create_app("production")
    assert "prototype" not in app.blueprints


def test_report_never_shows_scans_or_internal_notes():
    html = create_app("testing").test_client().get("/prototipo/boletim").get_data(as_text=True)
    assert "scan" not in html.lower()
    assert "anotação interna" not in html.lower()


def test_report_shows_own_max_when_different_from_scale():
    html = create_app("testing").test_client().get("/prototipo/boletim").get_data(as_text=True)
    assert "18/20" in html
    assert "RASCUNHO" in html


def test_review_mode_has_release_and_return_with_confirmation():
    html = (
        create_app("testing")
        .test_client()
        .get("/prototipo/boletim?revisao=1")
        .get_data(as_text=True)
    )
    assert 'data-open-dialog="liberar"' in html
    assert '<dialog id="liberar"' in html
    assert '<dialog id="devolver"' in html
