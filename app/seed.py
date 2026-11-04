"""Dados fictícios para desenvolvimento e demonstração (`flask seed`). Nunca em produção.

Gera, sempre igual (semente fixa):
- 1 ano arquivado (2026) e 1 ativo (2027), 3 trimestres cada
- 6 shiurim por ano, 75 alunos no ano ativo (dois com o mesmo nome)
- 4 matérias, com rabinos trocando de matéria entre trimestres
- 2 a 4 provas por matéria e trimestre, notas com decimal, ausentes e dispensados
- frequência, comentários, uma troca de turma e shiurs em fases diferentes da revisão

Grava pelas regras de app/services, então o seed também passa pelas validações.
"""

import random
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select

from app.extensions import db
from app.models import (
    AcademicYear,
    ClassSubject,
    ClassSubjectTerm,
    CommentCategory,
    KodeshClass,
    Student,
    StudentYear,
    Subject,
    Term,
    User,
    UserRole,
)
from app.services import attendance, comments, grades, review, years
from app.services.classes import effective_teacher, enroll, transfer

SEED = 5787

FIRST_NAMES = [
    "Ariel",
    "Binyamin",
    "Daniel",
    "David",
    "Eliahu",
    "Gabriel",
    "Moshe",
    "Natan",
    "Rafael",
    "Shlomo",
    "Yaakov",
    "Yosef",
    "Avraham",
    "Itzhak",
    "Menachem",
    "Mordechai",
    "Shmuel",
    "Yehuda",
    "Chaim",
    "Eliezer",
    "Uriel",
    "Meir",
    "Aharon",
    "Levi",
    "Nissim",
]
LAST_NAMES = [
    "Abramovich",
    "Azulay",
    "Benchimol",
    "Cohen",
    "Hazan",
    "Klein",
    "Levy",
    "Rosenberg",
    "Sasson",
    "Szwarc",
    "Toledano",
    "Zaguri",
    "Bitton",
    "Elbaz",
    "Goldstein",
    "Katz",
    "Mizrahi",
    "Ohana",
    "Peretz",
    "Schwartz",
    "Weiss",
    "Amar",
    "Dahan",
    "Friedman",
]
HEBREW = {
    "Ariel": "אריאל",
    "Binyamin": "בנימין",
    "Daniel": "דניאל",
    "David": "דוד",
    "Eliahu": "אליהו",
    "Gabriel": "גבריאל",
    "Moshe": "משה",
    "Natan": "נתן",
    "Rafael": "רפאל",
    "Shlomo": "שלמה",
    "Yaakov": "יעקב",
    "Yosef": "יוסף",
    "Avraham": "אברהם",
    "Itzhak": "יצחק",
    "Menachem": "מנחם",
    "Mordechai": "מרדכי",
    "Shmuel": "שמואל",
    "Yehuda": "יהודה",
    "Chaim": "חיים",
    "Eliezer": "אליעזר",
    "Uriel": "אוריאל",
    "Meir": "מאיר",
    "Aharon": "אהרן",
    "Levi": "לוי",
    "Nissim": "ניסים",
}
RABBIS = [
    "Rav Moshe Levi",
    "Rav David Cohen",
    "Rav Yaakov Azulay",
    "Rav Shimon Hazan",
    "Rav Avraham Klein",
    "Rav Eliyahu Sasson",
    "Rav Meir Toledano",
]
SUBJECTS = ["Gemara", "Chumash", "Halachá", "Navi"]
# (nome, nível, série escolar, cor)
CLASSES = [
    ("Shiur Alef", "1º colegial", 10, "azul"),
    ("Shiur Bet", "2º colegial", 11, "vinho"),
    ("Shiur Gimel", "3º colegial", 12, "verde"),
    ("Shiur Dalet", "9º ano", 9, "laranja"),
    ("Shiur He", "8º ano", 8, "marrom"),
    ("Shiur Vav", "1º colegial", 10, "petroleo"),
]
TERM_DATES = {
    1: ((2, 1), (5, 31)),
    2: ((6, 1), (8, 31)),
    3: ((9, 1), (11, 30)),
}
GENERAL = [
    "Teve um trimestre muito bom. Participa das aulas com perguntas boas.",
    "Mostrou dedicação ao estudo e boa evolução na leitura da Gemara.",
    "Pode render mais. Precisa revisar a matéria em casa com mais regularidade.",
    "Ótimo trimestre. É um exemplo de esforço para os colegas.",
]
BEHAVIOR = [
    "Respeitoso com os colegas e com os rabinos.",
    "Educado, mas precisa chegar no horário da tefilá.",
    "Muito participativo e prestativo com os colegas.",
    "Precisa conversar menos durante a aula.",
]


@dataclass
class SeedSummary:
    years: int = 0
    classes: int = 0
    students: int = 0
    assessments: int = 0
    scores: int = 0
    notes: list[str] = field(default_factory=list)


class SeedError(Exception):
    pass


def seed_demo() -> SeedSummary:
    """Popula um banco vazio. Não roda se já houver dados."""
    if db.session.scalar(select(func.count()).select_from(AcademicYear)):
        raise SeedError(
            "O banco já tem dados. Rode o seed num banco vazio "
            "(flask db downgrade base && flask db upgrade)."
        )
    rng = random.Random(SEED)
    summary = SeedSummary()

    admin = User(name="Direção", email="direcao@exemplo.local", role=UserRole.ADMIN)
    rabbis = [
        User(name=name, email=f"rav{i + 1}@exemplo.local", role=UserRole.RABBI)
        for i, name in enumerate(RABBIS)
    ]
    rabbis[-1].is_active = False  # rabino ainda sem acesso ativado
    subjects = [Subject(name=name, sort_order=i) for i, name in enumerate(SUBJECTS)]
    db.session.add_all([admin, *rabbis, *subjects])
    db.session.flush()

    students = _make_students(rng)
    summary.students = sum(1 for _, g in students if g <= 12)

    # Ano anterior, já fechado (só leitura).
    past = years.create_year("2026", date(2026, 2, 1), date(2026, 11, 30))
    _set_term_dates(past, 2026)
    _populate_year(
        rng, past, students, rabbis, admin, subjects, summary, grade_shift=-1, terms_done=3
    )
    years.archive_year(past)

    # Ano ativo, no meio do 2º trimestre.
    current = years.create_year("2027", date(2027, 2, 1), date(2027, 11, 30))
    _set_term_dates(current, 2027)
    _populate_year(
        rng,
        current,
        students,
        rabbis,
        admin,
        subjects,
        summary,
        grade_shift=0,
        terms_done=1,
        term_in_progress=2,
        transfer_one=True,
    )

    summary.years = 2
    db.session.commit()
    return summary


# ---------- Partes ----------


def _make_students(rng: random.Random) -> list[tuple[Student, int]]:
    """75 alunos com a série de 2027 e 12 formandos de 2026 (já inativos).

    Dois têm o mesmo nome (Gabriel Cohen). Formandos ficam com série 13 em "2027".
    """
    result = []
    used = set()
    grades_cycle = [10, 11, 12, 9, 8, 10]  # mesma ordem de CLASSES
    for i in range(75 + 12):
        if i in (5, 40):
            first, last = "Gabriel", "Cohen"
        else:
            while True:
                first, last = rng.choice(FIRST_NAMES), rng.choice(LAST_NAMES)
                if (first, last) not in used and (first, last) != ("Gabriel", "Cohen"):
                    break
        used.add((first, last))
        student = Student(
            first_name=first,
            last_name=last,
            hebrew_name=HEBREW.get(first) if rng.random() < 0.8 else None,
            external_id=f"2027{i + 1:03d}" if rng.random() < 0.6 else None,  # nem todos têm
            birth_date=date(2010 + rng.randint(0, 4), rng.randint(1, 12), rng.randint(1, 28)),
            parent_name=f"Família {last}",
            parent_email=f"familia.{last.lower()}{i}@exemplo.local",
        )
        graduate = i >= 75
        if graduate:
            student.is_active = False
            student.external_id = None
        db.session.add(student)
        result.append((student, 13 if graduate else grades_cycle[i % len(grades_cycle)]))
    db.session.flush()
    return result


def _set_term_dates(year: AcademicYear, y: int) -> None:
    for term in year.terms:
        (m1, d1), (m2, d2) = TERM_DATES[term.number]
        term.start_date = date(y, m1, d1)
        term.end_date = date(y, m2, d2)
    db.session.flush()


def _populate_year(
    rng,
    year,
    students,
    rabbis,
    admin,
    subjects,
    summary,
    grade_shift,
    terms_done,
    term_in_progress=None,
    transfer_one=False,
):
    terms: list[Term] = list(year.terms)
    y = year.start_date.year

    classes = []
    for idx, (name, level, _grade, color) in enumerate(CLASSES):
        kclass = KodeshClass(
            academic_year_id=year.id,
            name=name,
            level=level,
            homeroom_rabbi_id=rabbis[idx].id,
            color=color,
            sort_order=idx,
        )
        db.session.add(kclass)
        classes.append(kclass)
    db.session.flush()
    summary.classes += len(classes)

    # Matérias: Gemara com o rabino da turma; as outras com rabinos de matéria.
    class_subjects = {}
    for idx, kclass in enumerate(classes):
        for s_idx, subject in enumerate(subjects):
            teacher = None if s_idx == 0 else rabbis[(idx + s_idx) % (len(rabbis) - 1)]
            cs = ClassSubject(
                kodesh_class_id=kclass.id,
                subject_id=subject.id,
                default_teacher_id=teacher.id if teacher else None,
                sort_order=s_idx,
            )
            db.session.add(cs)
            class_subjects[(kclass.id, subject.name)] = cs
    db.session.flush()

    # Rabinos trocando de matéria entre trimestres.
    for kclass in classes[:3]:
        cs = class_subjects[(kclass.id, "Navi")]
        substitute = rabbis[(classes.index(kclass) + 3) % (len(rabbis) - 1)]
        db.session.add(
            ClassSubjectTerm(class_subject_id=cs.id, term_id=terms[1].id, teacher_id=substitute.id)
        )
    db.session.flush()

    # Alunos nos shiurs pela série (2026: um ano antes; quem estava no 8º ano entrou em 2027).
    enrollments = []
    split = 0
    for student, grade_2027 in students:
        grade = grade_2027 + grade_shift
        if grade < 8 or grade > 12:
            continue  # ainda não entrou, ou já se formou
        class_idx = next(i for i, c in enumerate(CLASSES) if c[2] == grade)
        if grade == 10:
            split += 1
            if split % 2 == 0:
                class_idx = 5  # 1º colegial dividido em Alef e Vav
        sy = StudentYear(
            student_id=student.id,
            academic_year_id=year.id,
            school_grade=grade,
            secular_class_label=f"{_grade_short(grade)} {'AB'[student.id % 2]}",
        )
        db.session.add(sy)
        db.session.flush()
        enrollments.append(enroll(sy, classes[class_idx], year.start_date))

    if transfer_one:
        moved = next(e for e in enrollments if e.kodesh_class_id == classes[0].id)
        new = transfer(moved.student_year, classes[1], date(y, 4, 15))
        enrollments.append(new)
        summary.notes.append("Um aluno trocou do Shiur Alef para o Shiur Bet em 15/04.")

    active_terms = terms[:terms_done] + ([terms[term_in_progress - 1]] if term_in_progress else [])
    for term in active_terms:
        in_progress = term_in_progress is not None and term.number == term_in_progress
        for kclass in classes:
            members = [
                e for e in enrollments if e.kodesh_class_id == kclass.id and _in_term(e, term)
            ]
            for subject in subjects:
                cs = class_subjects[(kclass.id, subject.name)]
                teacher = effective_teacher(cs, term) or admin
                n = rng.randint(1, 2) if in_progress else rng.randint(2, 4)
                for k in range(n):
                    big = subject.name == "Gemara" and k == n - 1 and not in_progress
                    prova = grades.create_assessment(
                        teacher,
                        cs,
                        term,
                        "Trabalho" if big else ("Recuperação" if k == 3 else f"Prova {k + 1}"),
                        max_score=Decimal("20") if big else None,
                        include_in_report=not (k == 2 and rng.random() < 0.5),
                        when=date(y, term.start_date.month + 1, min(5 + 7 * k, 28)),
                    )
                    summary.assessments += 1
                    for e in members:
                        if in_progress and rng.random() < 0.15:
                            continue  # nota ainda não lançada (pendência)
                        grades.set_score(teacher, prova, e, _random_score(rng, prova.max_score))
                        summary.scores += 1

            held = rng.choice([44, 46, 48]) if not in_progress else 20
            for e in members:
                if in_progress and kclass.sort_order % 2:
                    continue  # frequência ainda não lançada em alguns shiurs
                # Quem trocou de turma no trimestre tem só a parte dele em cada shiur.
                part = held // 2 if _partial_in_term(e, term) else held
                absences = min(part, max(0, int(rng.gauss(2, 2))))
                lates = min(part, max(0, int(rng.gauss(2, 2))))
                attendance.save_attendance(
                    teacher_for(kclass, rabbis), e, term, part, absences, lates
                )

            if not in_progress:
                rabbi = teacher_for(kclass, rabbis)
                for e in members:
                    if rng.random() < 0.9:
                        comments.save_public_comment(
                            rabbi, e, term, CommentCategory.GENERAL, rng.choice(GENERAL)
                        )
                        comments.save_public_comment(
                            rabbi, e, term, CommentCategory.BEHAVIOR, rng.choice(BEHAVIOR)
                        )
                if rng.random() < 0.3 and members:
                    comments.add_internal_note(rabbi, members[0], term, "Conversar com os pais.")

    # Revisão: ano passado todo liberado; no ano ativo, 1º trimestre em fases diferentes.
    for term in terms[:terms_done]:
        for idx, kclass in enumerate(classes):
            rabbi = teacher_for(kclass, rabbis)
            if grade_shift == 0 and idx in (0, 3):
                continue  # ainda em lançamento
            review.submit_for_review(rabbi, kclass, term)
            if grade_shift != 0 or idx in (2, 4):
                review.approve(admin, kclass, term)


def teacher_for(kclass: KodeshClass, rabbis: list[User]) -> User:
    return next(r for r in rabbis if r.id == kclass.homeroom_rabbi_id)


def _in_term(enrollment, term) -> bool:
    if term.end_date and enrollment.start_date > term.end_date:
        return False
    return not (enrollment.end_date and term.start_date and enrollment.end_date < term.start_date)


def _partial_in_term(enrollment, term) -> bool:
    ends_inside = enrollment.end_date and term.end_date and enrollment.end_date < term.end_date
    starts_inside = term.start_date and enrollment.start_date > term.start_date
    return bool(ends_inside or starts_inside)


def _random_score(rng: random.Random, max_score: Decimal) -> str:
    r = rng.random()
    if r < 0.04:
        return "a"
    if r < 0.06:
        return "d"
    value = Decimal(str(round(rng.uniform(0.5, 1.0) * float(max_score), 1)))
    return str(min(value, max_score)).replace(".", ",")


def _grade_short(grade: int) -> str:
    return {8: "8º", 9: "9º", 10: "1º", 11: "2º", 12: "3º"}[grade]
