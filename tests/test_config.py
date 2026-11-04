from config import normalize_db_url


def test_railway_url_gets_pymysql_driver_and_charset():
    url = normalize_db_url("mysql://u:p@host:3306/railway")
    assert url == "mysql+pymysql://u:p@host:3306/railway?charset=utf8mb4"


def test_existing_query_string_is_kept():
    url = normalize_db_url("mysql+pymysql://u:p@host/db?ssl=true")
    assert url == "mysql+pymysql://u:p@host/db?ssl=true&charset=utf8mb4"


def test_explicit_charset_is_not_duplicated():
    url = "mysql+pymysql://u:p@host/db?charset=utf8mb4"
    assert normalize_db_url(url) == url
