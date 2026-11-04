"""Fábricas de dados de teste (factory_boy). Usam o db.session do teste, desfeito no fim."""

from datetime import date
from decimal import Decimal

import factory
from factory.alchemy import SQLAlchemyModelFactory

from app.extensions import db
from app.models import (
    AcademicYear,
    Assessment,
    ClassSubject,
    Enrollment,
    KodeshClass,
    Student,
    StudentYear,
    Subject,
    Term,
    User,
    UserRole,
    YearStatus,
)


class Base(SQLAlchemyModelFactory):
    class Meta:
        abstract = True
        sqlalchemy_session_factory = lambda: db.session  # noqa: E731
        sqlalchemy_session_persistence = "flush"


class UserFactory(Base):
    class Meta:
        model = User

    name = factory.Sequence(lambda n: f"Rav Teste {n}")
    email = factory.Sequence(lambda n: f"rav{n}@teste.local")
    role = UserRole.RABBI


class AdminFactory(UserFactory):
    name = factory.Sequence(lambda n: f"Direção {n}")
    role = UserRole.ADMIN


class YearFactory(Base):
    class Meta:
        model = AcademicYear

    name = factory.Sequence(lambda n: f"{2100 + n}")
    start_date = date(2100, 2, 1)
    status = YearStatus.ACTIVE
    grade_scale_max = Decimal("10.0")


class TermFactory(Base):
    class Meta:
        model = Term

    academic_year = factory.SubFactory(YearFactory)
    number = factory.Sequence(lambda n: n + 1)
    name = factory.LazyAttribute(lambda t: f"{t.number}º trimestre")


class ClassFactory(Base):
    class Meta:
        model = KodeshClass

    academic_year = factory.SubFactory(YearFactory)
    name = factory.Sequence(lambda n: f"Shiur {n}")
    homeroom_rabbi = factory.SubFactory(UserFactory)


class SubjectFactory(Base):
    class Meta:
        model = Subject

    name = factory.Sequence(lambda n: f"Matéria {n}")


class ClassSubjectFactory(Base):
    class Meta:
        model = ClassSubject

    kodesh_class = factory.SubFactory(ClassFactory)
    subject = factory.SubFactory(SubjectFactory)


class StudentFactory(Base):
    class Meta:
        model = Student

    first_name = factory.Sequence(lambda n: f"Aluno{n}")
    last_name = "Teste"


class StudentYearFactory(Base):
    class Meta:
        model = StudentYear

    student = factory.SubFactory(StudentFactory)
    academic_year = factory.SubFactory(YearFactory)
    school_grade = 10


class EnrollmentFactory(Base):
    class Meta:
        model = Enrollment

    kodesh_class = factory.SubFactory(ClassFactory)
    student_year = factory.SubFactory(
        StudentYearFactory, academic_year=factory.SelfAttribute("..kodesh_class.academic_year")
    )
    start_date = date(2100, 2, 1)


class AssessmentFactory(Base):
    class Meta:
        model = Assessment

    class_subject = factory.SubFactory(ClassSubjectFactory)
    term = factory.SubFactory(
        TermFactory,
        academic_year=factory.SelfAttribute("..class_subject.kodesh_class.academic_year"),
    )
    name = factory.Sequence(lambda n: f"Prova {n}")
    max_score = Decimal("10.0")
    sort_order = factory.Sequence(lambda n: n)
