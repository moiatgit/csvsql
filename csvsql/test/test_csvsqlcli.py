import pytest
import io
import sqlite3
import csv
import pathlib
from csvsql import csvsqlcli


def test_get_statements_from_contents_when_theres_just_one():
    contents = "SELECT * FROM mytable;"
    expected = [ contents ]
    result = csvsqlcli.get_sql_statements_from_contents(contents)
    assert result == expected


def test_get_statements_from_contents_when_theres_just_one_and_requires_trimming():
    statement = "SELECT * FROM mytable;"
    contents = "     %s     "%statement
    expected = [ statement ]
    result = csvsqlcli.get_sql_statements_from_contents(contents)
    assert result == expected


def test_get_statements_from_contents_when_multiple():
    statements = [ "SELECT * FROM mytable;", "select col1 FROM mytable;", "select col1,col2 FROM mytable where col1=col2;" ]
    contents = "\n".join(statements)
    expected = statements
    result = csvsqlcli.get_sql_statements_from_contents(contents)
    assert result == expected


def test_get_statements_from_contents_ignoring_comments():
    statements = [ "SELECT * FROM mytable;", "select col1 FROM mytable;", "select col1,col2 FROM mytable where col1=col2;" ]
    contents = "-- SELECT * FROM anyothertable;\n" + "\n".join(statements[:-1]) + "    -- another comment to ignore\n" + statements[-1]
    expected = statements
    result = csvsqlcli.get_sql_statements_from_contents(contents)
    assert result == expected


def test_get_statements_from_contents_ignoring_newlines_within():
    statements = [ "SELECT *\nFROM mytable\n;", "select\ncol1 FROM mytable\n\n;", "select col1,\n\ncol2 FROM mytable where col1=\ncol2;" ]
    statements_clean = [ s.replace('\n', ' ') for s in statements ]
    contents = "-- SELECT * FROM anyothertable;\n" + "\n".join(statements[:-1]) + "    -- another comment to ignore\n" + statements[-1]
    expected = statements_clean
    result = csvsqlcli.get_sql_statements_from_contents(contents)
    assert result == expected


def test_csvsql_process_cml_args():
    assert False, 'Time to test command line arguments. You might want to simulate a whole FS'
