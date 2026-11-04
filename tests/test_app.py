from app import create_app

EXPECTED_BLUEPRINTS = {
    "main",
    "auth",
    "admin",
    "students",
    "classes",
    "grades",
    "attendance",
    "files",
    "imports",
    "reports",
}


def test_factory_uses_testing_config():
    app = create_app("testing")
    assert app.testing


def test_all_blueprints_registered():
    app = create_app("testing")
    assert set(app.blueprints) >= EXPECTED_BLUEPRINTS


def test_csrf_enabled():
    app = create_app("testing")
    assert "csrf" in app.extensions
    assert app.config["WTF_CSRF_ENABLED"]


def test_healthz():
    client = create_app("testing").test_client()
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}
