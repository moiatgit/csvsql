import pytest
import io
import sqlite3
import csv
from csvsql import csvsql



def test_get_statements_from_contents_when_theres_just_one():
    contents = "SELECT * FROM mytable;"
    expected = [ contents ]
    result = csvsql.get_sql_statements_from_contents(contents)
    assert result == expected


def test_get_statements_from_contents_when_theres_just_one_and_requires_trimming():
    statement = "SELECT * FROM mytable;"
    contents = "     %s     "%statement
    expected = [ statement ]
    result = csvsql.get_sql_statements_from_contents(contents)
    assert result == expected

def test_get_statements_from_contents_when_multiple():
    statements = [ "SELECT * FROM mytable;", "select col1 FROM mytable;", "select col1,col2 FROM mytable where col1=col2;" ]
    contents = "\n".join(statements)
    expected = statements
    result = csvsql.get_sql_statements_from_contents(contents)
    assert result == expected

def test_get_statements_from_contents_ignoring_comments():
    statements = [ "SELECT * FROM mytable;", "select col1 FROM mytable;", "select col1,col2 FROM mytable where col1=col2;" ]
    contents = "-- SELECT * FROM anyothertable;\n" + "\n".join(statements[:-1]) + "    -- another comment to ignore\n" + statements[-1]
    expected = statements
    result = csvsql.get_sql_statements_from_contents(contents)
    assert result == expected

def test_get_statements_from_contents_ignoring_newlines_within():
    statements = [ "SELECT *\nFROM mytable\n;", "select\ncol1 FROM mytable\n\n;", "select col1,\n\ncol2 FROM mytable where col1=\ncol2;" ]
    statements_clean = [ s.replace('\n', ' ') for s in statements ]
    contents = "-- SELECT * FROM anyothertable;\n" + "\n".join(statements[:-1]) + "    -- another comment to ignore\n" + statements[-1]
    expected = statements_clean
    result = csvsql.get_sql_statements_from_contents(contents)
    assert result == expected


def test_import_csv_basic_usage():
    headers = ['un', 'dos', 'tres' ]
    rows = [ ( '1', '2', '3' ), ( '4', '5', '6' ) ]
    contents = "%s\n%s"%(",".join(headers), "\n".join((",".join(row) for row in rows)))
    contents_fileobject = io.StringIO(contents)
    table_name = "my_table"
    db = sqlite3.connect(':memory:')
    dialect = csv.excel
    csvsql.import_csv(db, contents_fileobject, table_name, dialect=dialect)
    curs = db.execute('select * from my_table')
    assert len(curs.description) == len(headers)
    assert all(found[0] == expected for found , expected in zip( curs.description, headers)), "headers don't match"
    assert curs.fetchall() == rows
