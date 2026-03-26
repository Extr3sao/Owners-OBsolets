from app.services.sql_parser import split_sql_statements


def test_split_sql_statements_basic():
    sql = "select * from a;\n\nselect * from b;"
    out = split_sql_statements(sql)
    assert out == ["select * from a", "select * from b"]
