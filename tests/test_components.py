"""Componentes Jinja (macros) da Fase 1."""

import pytest

from app import create_app


@pytest.fixture
def render():
    app = create_app("testing")

    def _render(source: str) -> str:
        with app.test_request_context():
            return app.jinja_env.from_string(source).render()

    return _render


def test_button_variants_and_attrs(render):
    html = render(
        '{% from "components/ui.html" import button %}'
        '{{ button("Apagar", variant="danger", attrs={"data-open-dialog": "x"}) }}'
    )
    assert "bg-danger" in html
    assert 'data-open-dialog="x"' in html
    assert 'type="button"' in html


def test_button_as_link(render):
    html = render('{% from "components/ui.html" import button %}{{ button("Ver", href="/a") }}')
    assert html.startswith('<a href="/a"')


def test_button_attrs_are_escaped(render):
    html = render(
        '{% from "components/ui.html" import button %}'
        '{{ button("X", attrs={"title": "<script>"}) }}'
    )
    assert "<script>" not in html


def test_status_always_has_icon_and_text(render):
    html = render(
        '{% from "components/ui.html" import status %}{{ status("success", "Liberado") }}'
    )
    assert "<svg" in html
    assert "Liberado" in html


def test_alert_danger_is_announced(render):
    html = render('{% from "components/ui.html" import alert %}{{ alert("danger", "Erro") }}')
    assert 'role="alert"' in html


def test_text_input_with_error_is_linked_to_message(render):
    html = render(
        '{% from "components/forms.html" import text_input %}'
        '{{ text_input("nota", "Nota", error="Máximo 10") }}'
    )
    assert 'aria-invalid="true"' in html
    assert 'aria-describedby="nota-error"' in html
    assert 'id="nota-error"' in html
    assert 'for="nota"' in html


def test_confirm_dialog_with_action_posts_with_csrf(render):
    html = render(
        '{% from "components/dialog.html" import confirm_dialog %}'
        '{{ confirm_dialog("d", "Apagar?", "Não volta.", "Apagar", action="/x") }}'
    )
    assert '<dialog id="d"' in html
    assert 'action="/x"' in html
    assert 'name="csrf_token"' in html
    assert "Cancelar" in html


def test_wtf_field_renders_label_and_error(render):
    from flask_wtf import FlaskForm
    from wtforms import StringField
    from wtforms.validators import DataRequired

    class StudentForm(FlaskForm):
        name = StringField("Nome", validators=[DataRequired(message="Preencha o nome.")])

    app = create_app("testing")
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_request_context(method="POST", data={"name": ""}):
        form = StudentForm()
        form.validate()
        html = app.jinja_env.from_string(
            '{% from "components/forms.html" import wtf_field %}{{ wtf_field(form.name) }}'
        ).render(form=form)
    assert "Nome" in html
    assert "Preencha o nome." in html
    assert 'aria-invalid="true"' in html
    assert "border-danger" in html
