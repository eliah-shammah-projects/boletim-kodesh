"""Dados fictícios do protótipo (Fase 1). Nada aqui vai para o banco.

Os nomes são inventados. Quando os modelos existirem (Fase 2a), o protótipo
some e as telas reais passam a ler do banco.
"""

from decimal import Decimal

D = Decimal

YEAR = "2027"
TERM = {"number": 1, "name": "1º Trimestre", "days_left": 12}
SCALE_MAX = D("10")

RABBIS = {
    "levi": "Rav Moshe Levi",
    "cohen": "Rav David Cohen",
    "azulay": "Rav Yaakov Azulay",
    "hazan": "Rav Shimon Hazan",
    "klein": "Rav Avraham Klein",
    "sasson": "Rav Eliyahu Sasson",
}

CLASSES = [
    {
        "slug": "alef",
        "name": "Shiur Alef",
        "level": "1º colegial",
        "rabbi": "levi",
        "status": "open",
        "students": 12,
        "grades_done": 75,
        "attendance_done": False,
        "comments_done": 8,
    },
    {
        "slug": "bet",
        "name": "Shiur Bet",
        "level": "2º colegial",
        "rabbi": "cohen",
        "status": "ready_for_review",
        "students": 11,
        "grades_done": 100,
        "attendance_done": True,
        "comments_done": 11,
    },
    {
        "slug": "gimel",
        "name": "Shiur Gimel",
        "level": "3º colegial",
        "rabbi": "azulay",
        "status": "approved",
        "students": 10,
        "grades_done": 100,
        "attendance_done": True,
        "comments_done": 10,
    },
    {
        "slug": "dalet",
        "name": "Shiur Dalet",
        "level": "9º ano",
        "rabbi": "hazan",
        "status": "open",
        "students": 14,
        "grades_done": 40,
        "attendance_done": False,
        "comments_done": 0,
    },
    {
        "slug": "he",
        "name": "Shiur He",
        "level": "8º ano",
        "rabbi": "klein",
        "status": "open",
        "students": 15,
        "grades_done": 90,
        "attendance_done": True,
        "comments_done": 12,
    },
    {
        "slug": "vav",
        "name": "Shiur Vav",
        "level": "1º colegial",
        "rabbi": "sasson",
        "status": "ready_for_review",
        "students": 13,
        "grades_done": 100,
        "attendance_done": True,
        "comments_done": 13,
    },
]

# Paleta das cores de fita dos shiurim. Escolhidas para combinar entre si e com o azul do logo,
# todas com contraste suficiente para texto branco.
SHIUR_COLORS = {
    "azul": ("Azul", "#2F6FA3"),
    "verde": ("Verde", "#2E7D4F"),
    "vinho": ("Vinho", "#8E2C48"),
    "laranja": ("Laranja", "#B4561F"),
    "roxo": ("Roxo", "#6B4FA0"),
    "dourado": ("Dourado", "#8F6B12"),
    "petroleo": ("Petróleo", "#1F6F73"),
    "grafite": ("Grafite", "#4A5560"),
}
_COLORS = ["azul", "vinho", "verde", "laranja", "roxo", "petroleo"]
for _c, _color in zip(CLASSES, _COLORS, strict=True):
    _c["color"] = _color

CLASS_OPTIONS = [(c["slug"], c["name"]) for c in CLASSES]

STATUS_LABELS = {
    "open": ("warning", "Em lançamento"),
    "ready_for_review": ("primary", "Pronto para revisão"),
    "approved": ("success", "Liberado"),
}

# Alunos do Shiur Alef. hebrew_name é opcional.
STUDENTS = [
    {
        "id": 1012,
        "name": "Ariel Szwarc",
        "hebrew": "אריאל",
        "grade": "1º colegial",
        "secular": "1º A",
    },
    {
        "id": 1015,
        "name": "Binyamin Klein",
        "hebrew": "בנימין",
        "grade": "1º colegial",
        "secular": "1º A",
    },
    {
        "id": 1003,
        "name": "Daniel Abramovich",
        "hebrew": "דניאל",
        "grade": "1º colegial",
        "secular": "1º B",
    },
    {
        "id": 1021,
        "name": "David Zaguri",
        "hebrew": "דוד",
        "grade": "1º colegial",
        "secular": "1º A",
    },
    {
        "id": 1007,
        "name": "Eliahu Sasson",
        "hebrew": "אליהו",
        "grade": "1º colegial",
        "secular": "1º B",
    },
    {"id": 1009, "name": "Gabriel Cohen", "hebrew": "", "grade": "1º colegial", "secular": "1º A"},
    {
        "id": 1030,
        "name": "Moshe Azulay",
        "hebrew": "משה",
        "grade": "1º colegial",
        "secular": "1º B",
    },
    {
        "id": 1018,
        "name": "Natan Rosenberg",
        "hebrew": "נתן",
        "grade": "1º colegial",
        "secular": "1º A",
    },
    {
        "id": 1001,
        "name": "Rafael Levy",
        "hebrew": "רפאל",
        "grade": "1º colegial",
        "secular": "1º B",
    },
    {
        "id": 1025,
        "name": "Shlomo Hazan",
        "hebrew": "שלמה",
        "grade": "1º colegial",
        "secular": "1º A",
    },
    {
        "id": 1011,
        "name": "Yaakov Benchimol",
        "hebrew": "יעקב",
        "grade": "1º colegial",
        "secular": "1º B",
    },
    {
        "id": 1027,
        "name": "Yosef Toledano",
        "hebrew": "יוסף",
        "grade": "1º colegial",
        "secular": "1º A",
    },
]

SUBJECTS = [
    {"slug": "gemara", "name": "Gemara", "hebrew": "גמרא", "teacher": "levi", "assessments": 3},
    {"slug": "chumash", "name": "Chumash", "hebrew": "חומש", "teacher": "cohen", "assessments": 2},
    {"slug": "halacha", "name": "Halachá", "hebrew": "הלכה", "teacher": "azulay", "assessments": 2},
    {"slug": "navi", "name": "Navi", "hebrew": "נביא", "teacher": "cohen", "assessments": 1},
]

# Provas de Gemara no 1º trimestre.
ASSESSMENTS = [
    {"id": 1, "name": "Prova 1", "date": "12/03", "max": D("10"), "in_report": True},
    {"id": 2, "name": "Prova 2", "date": "09/04", "max": D("10"), "in_report": True},
    {"id": 3, "name": "Trabalho Bava Metzia", "date": "23/04", "max": D("20"), "in_report": False},
]

# Notas: (aluno, prova) -> valor. "A" = ausente, "D" = dispensado, None = sem nota.
_RAW_SCORES = {
    1012: ["9.5", "8", "18"],
    1015: ["7", "6.5", "15.5"],
    1003: ["10", "9.5", "19"],
    1021: ["6.6", "A", None],
    1007: ["8", "8.5", "17"],
    1009: ["5.5", "7", None],
    1030: ["9", "D", "16"],
    1018: ["8.5", None, "18.5"],
    1001: ["7.5", "8", "14"],
    1025: ["A", "6", None],
    1011: ["9", "9", "20"],
    1027: ["8", None, "17.5"],
}
SCORES = {
    (sid, ASSESSMENTS[i]["id"]): (v if v in ("A", "D", None) else D(v))
    for sid, values in _RAW_SCORES.items()
    for i, v in enumerate(values)
}

# Quem tem scan em cada prova (quantidade de páginas).
SCANS = {
    1: {1012: 2, 1015: 2, 1003: 1, 1007: 2, 1009: 2, 1030: 1, 1001: 2},
    2: {1012: 1, 1003: 1},
    3: {},
}
ASSESSMENT_DOCS = {1: {"blank": True, "key": True}, 2: {"blank": True, "key": False}, 3: {}}

CLASSES_HELD = 48
ATTENDANCE = {
    1012: (0, 1),
    1015: (2, 0),
    1003: (0, 0),
    1021: (5, 3),
    1007: (1, 2),
    1009: (3, 1),
    1030: (0, 4),
    1018: (1, 0),
    1001: (2, 2),
    1025: (6, 1),
    1011: (0, 0),
    1027: (1, 1),
}

# Pendências do rabino logado (Rav Moshe Levi).
RABBI_TODO = [
    {
        "kind": "warning",
        "icon": "clipboard-list",
        "title": "Prova 2 de Gemara sem nota",
        "detail": "Shiur Alef · 2 alunos sem nota",
        "action": "Lançar notas",
        "endpoint": "prototype.grades",
    },
    {
        "kind": "warning",
        "icon": "camera",
        "title": "Scans faltando na Prova 1 de Gemara",
        "detail": "Shiur Alef · 5 alunos sem scan",
        "action": "Enviar scans",
        "endpoint": "prototype.scans",
    },
    {
        "kind": "warning",
        "icon": "calendar-check",
        "title": "Frequência do 1º trimestre não lançada",
        "detail": "Shiur Alef",
        "action": "Lançar frequência",
        "endpoint": "prototype.attendance",
    },
    {
        "kind": "warning",
        "icon": "message-square",
        "title": "Comentários do boletim faltando",
        "detail": "Shiur Alef · 4 de 12 alunos sem comentário",
        "action": "Escrever comentários",
        "endpoint": "prototype.shiur",
    },
]

RABBI_DONE = [
    "Notas de Chumash lançadas · Shiur Dalet",
    "Prova 1 de Gemara com todas as notas · Shiur Alef",
]

INACTIVE_RABBIS = ["Rav Shimon Hazan"]

# Um aluno no boletim de exemplo.
REPORT = {
    "student": STUDENTS[0],
    "subjects": [
        {
            "name": "Gemara",
            "teacher": "levi",
            "scores": [("Prova 1", D("9.5"), D("10")), ("Prova 2", D("8"), D("10"))],
        },
        {
            "name": "Chumash",
            "teacher": "cohen",
            "scores": [("Prova 1", D("8.5"), D("10")), ("Recuperação", D("18"), D("20"))],
        },
        {"name": "Halachá", "teacher": "azulay", "scores": [("Prova 1", D("10"), D("10"))]},
        {"name": "Navi", "teacher": "cohen", "scores": [("Prova 1", D("7"), D("10"))]},
    ],
    "attendance": {"held": 48, "absences": 0, "lates": 1},
    "general": (
        "Ariel teve um trimestre muito bom. Participa das aulas com perguntas boas e "
        "se dedicou bastante ao estudo de Bava Metzia."
    ),
    "behavior": "Respeitoso com os colegas e com os rabinos. Precisa chegar no horário da tefilá.",
}
