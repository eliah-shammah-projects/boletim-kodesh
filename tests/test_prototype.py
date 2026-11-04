import pytest

from app import create_app

PAGES = ["/prototipo/", "/prototipo/componentes"]


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
