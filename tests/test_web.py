"""Telas de verdade da Fase 5 (cadastros), contra MySQL.

O CSRF fica desligado só aqui, para os testes enviarem formulários direto.
"""

from datetime import date

import pytest
from sqlalchemy import select

from app.models import (
    AcademicYear,
    ClassSubject,
    Enrollment,
    KodeshClass,
    Student,
    Subject,
    YearStatus,
)
from tests.factories import (
    AdminFactory,
    ClassFactory,
    EnrollmentFactory,
    StudentFactory,
    SubjectFactory,
    UserFactory,
    YearFactory,
)

pytestmark = pytest.mark.usefixtures("_database")


@pytest.fixture
def client(app, db_session):
    app.config["WTF_CSRF_ENABLED"] = False
    yield app.test_client()
    app.config["WTF_CSRF_ENABLED"] = True


def login(client, user):
    return client.post("/entrar-como", data={"user_id": user.id})


@pytest.fixture
def setup(db_session):
    year = YearFactory(name="2100", start_date=date(2100, 2, 1))
    admin = AdminFactory(name="Direção Teste")
    rabbi = UserFactory(name="Rav Teste")
    kclass = ClassFactory(academic_year=year, name="Shiur Alef", homeroom_rabbi=rabbi)
    return {"s": db_session, "year": year, "admin": admin, "rabbi": rabbi, "class": kclass}


def test_pages_open_for_admin(client, setup):
    login(client, setup["admin"])
    for path in [
        "/",
        "/alunos/",
        "/cadastros/",
        f"/cadastros/anos/{setup['year'].id}",
        "/shiurim/novo",
        f"/shiurim/{setup['class'].id}",
    ]:
        response = client.get(path)
        assert response.status_code == 200, path
        assert "Or Yossef" in response.get_data(as_text=True)


def test_rabbi_cannot_open_admin_pages(client, setup):
    login(client, setup["rabbi"])
    assert client.get("/").status_code == 200
    assert client.get("/cadastros/").status_code == 403
    assert client.get("/shiurim/novo").status_code == 403
    assert (
        client.post("/alunos/novo", data={"first_name": "X", "last_name": "Y"}).status_code == 403
    )


def test_home_lists_classes_with_what_is_missing(client, setup):
    login(client, setup["admin"])
    html = client.get("/").get_data(as_text=True)
    assert "Shiur Alef" in html
    assert "Nenhum aluno no shiur ainda" in html


def test_create_student_into_class(client, setup):
    login(client, setup["admin"])
    response = client.post(
        "/alunos/novo",
        data={
            "first_name": "Ariel",
            "last_name": "Szwarc",
            "hebrew_name": "אריאל",
            "school_grade": "10",
            "class_id": str(setup["class"].id),
        },
        follow_redirects=True,
    )
    assert "Ariel Szwarc foi cadastrado no Shiur Alef." in response.get_data(as_text=True)
    student = setup["s"].scalar(select(Student).where(Student.last_name == "Szwarc"))
    assert student.hebrew_name == "אריאל"
    enrollment = setup["s"].scalar(
        select(Enrollment).where(Enrollment.kodesh_class_id == setup["class"].id)
    )
    assert enrollment.student_year.student_id == student.id


def test_same_name_asks_for_confirmation(client, setup):
    StudentFactory(first_name="Gabriel", last_name="Cohen")
    login(client, setup["admin"])
    data = {"first_name": "Gabriel", "last_name": "Cohen", "school_grade": "10", "class_id": ""}
    html = client.post("/alunos/novo", data=data).get_data(as_text=True)
    assert "Já existe um aluno com este nome" in html

    def count():
        return len(list(setup["s"].scalars(select(Student).where(Student.last_name == "Cohen"))))

    assert count() == 1
    client.post("/alunos/novo", data={**data, "confirm_same_name": "1"})
    assert count() == 2


def test_search_students(client, setup):
    StudentFactory(first_name="Yosef", last_name="Toledano", external_id="M-77")
    login(client, setup["rabbi"])
    assert "Yosef Toledano" in client.get("/alunos/?q=tole").get_data(as_text=True)
    assert "Yosef Toledano" in client.get("/alunos/?q=M-77").get_data(as_text=True)
    assert "Nenhum aluno encontrado" in client.get("/alunos/?q=zzz").get_data(as_text=True)


def test_create_class_with_subjects(client, setup):
    gemara = SubjectFactory(name="Gemara")
    login(client, setup["admin"])
    response = client.post(
        "/shiurim/novo",
        data={
            "name": "Shiur Bet",
            "level": "2º colegial",
            "homeroom_rabbi_id": str(setup["rabbi"].id),
            "color": "vinho",
            "subject_ids": [str(gemara.id)],
        },
        follow_redirects=True,
    )
    assert "Shiur Bet criado." in response.get_data(as_text=True)
    bet = setup["s"].scalar(select(KodeshClass).where(KodeshClass.name == "Shiur Bet"))
    assert bet.color == "vinho"
    assert [cs.subject.name for cs in bet.subjects] == ["Gemara"]


def test_duplicate_class_name_is_rejected(client, setup):
    login(client, setup["admin"])
    html = client.post("/shiurim/novo", data={"name": "Shiur Alef", "color": "azul"}).get_data(
        as_text=True
    )
    assert "Já existe um Shiur Alef" in html


def test_add_and_configure_subject(client, setup):
    subject = SubjectFactory(name="Navi")
    other = UserFactory(name="Rav Cohen")
    login(client, setup["admin"])
    client.post(f"/shiurim/{setup['class'].id}/materias", data={"subject_id": str(subject.id)})
    cs = setup["s"].scalar(select(ClassSubject).where(ClassSubject.subject_id == subject.id))
    terms = list(setup["year"].terms)
    form = {"default_teacher_id": str(other.id), "report_label": "Neviim"}
    for t in terms:
        form[f"term_teacher_{t.id}"] = ""
    client.post(f"/shiurim/materia/{cs.id}", data=form)
    setup["s"].refresh(cs)
    assert cs.default_teacher_id == other.id
    assert cs.report_label == "Neviim"
    client.post(f"/shiurim/materia/{cs.id}/ativa")
    setup["s"].refresh(cs)
    assert cs.is_active is False


def test_put_existing_student_in_class_and_remove(client, setup):
    student = StudentFactory(first_name="Natan", last_name="Rosenberg")
    login(client, setup["admin"])
    response = client.post(
        f"/shiurim/{setup['class'].id}/alunos",
        data={"student_id": str(student.id)},
        follow_redirects=True,
    )
    assert "Natan Rosenberg entrou no Shiur Alef." in response.get_data(as_text=True)
    enrollment = setup["s"].scalar(
        select(Enrollment).where(Enrollment.kodesh_class_id == setup["class"].id)
    )
    response = client.post(f"/shiurim/matricula/{enrollment.id}/sair", follow_redirects=True)
    assert "continuam guardadas" in response.get_data(as_text=True)
    setup["s"].refresh(enrollment)
    assert enrollment.end_date is not None


def test_create_subject_and_year_flow(client, setup):
    login(client, setup["admin"])
    client.post("/cadastros/materias", data={"name": "Mishná"})
    assert setup["s"].scalar(select(Subject).where(Subject.name == "Mishná"))
    # com um ano aberto, não cria outro
    html = client.post(
        "/cadastros/anos",
        data={"name": "2101", "start_date": "2101-02-01", "grade_scale_max": "10", "terms": "3"},
        follow_redirects=True,
    ).get_data(as_text=True)
    assert "Feche-o antes" in html
    client.post(f"/cadastros/anos/{setup['year'].id}/fechar")
    setup["s"].refresh(setup["year"])
    assert setup["year"].status == YearStatus.ARCHIVED
    client.post(
        "/cadastros/anos",
        data={"name": "2101", "start_date": "2101-02-01", "grade_scale_max": "10", "terms": "3"},
    )
    new = setup["s"].scalar(select(AcademicYear).where(AcademicYear.name == "2101"))
    assert new.status == YearStatus.ACTIVE
    assert len(new.terms) == 3


def test_archived_year_shows_read_only(client, setup):
    old = YearFactory(name="2099", status=YearStatus.ARCHIVED)
    ClassFactory(academic_year=old, name="Shiur Antigo")
    login(client, setup["admin"])
    client.get(f"/ano/{old.id}")
    html = client.get("/").get_data(as_text=True)
    assert "Shiur Antigo" in html
    assert "só para leitura" in html
    assert "Criar shiur" not in html


def test_transfer_keeps_old_enrollment_when_it_has_records(client, setup):
    from app.services import grades
    from tests.factories import AssessmentFactory, ClassSubjectFactory

    enrollment = EnrollmentFactory(kodesh_class=setup["class"], start_date=date(2100, 2, 1))
    cs = ClassSubjectFactory(kodesh_class=setup["class"])
    prova = AssessmentFactory(class_subject=cs)
    grades.set_score(setup["admin"], prova, enrollment, "8")
    bet = ClassFactory(academic_year=setup["year"], name="Shiur Bet")
    login(client, setup["admin"])
    client.post(
        f"/shiurim/{bet.id}/alunos", data={"student_id": str(enrollment.student_year.student_id)}
    )
    setup["s"].refresh(enrollment)
    assert enrollment.end_date is not None
    assert enrollment.kodesh_class_id == setup["class"].id
