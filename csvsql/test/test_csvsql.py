import pytest
import io
import sqlite3
import csv
import pathlib
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


def test_import_csv_unheaded_cols():
    headers = ['un', '' , 'tres', '', '', '', '', '', '', '', '', 'dotze' ]
    rows = [ ( '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12' ) ]
    contents = "%s\n%s"%(",".join(headers), "\n".join((",".join(row) for row in rows)))
    contents_fileobject = io.StringIO(contents)
    table_name = "my_table"
    db = sqlite3.connect(':memory:')
    dialect = csv.excel
    expected_headers = [ 'un', '__COL02', 'tres' ] + [ '__COL%02d'%i for i in range(4, 12) ] + [ 'dotze']
    csvsql.import_csv(db, contents_fileobject, table_name, dialect=dialect)
    curs = db.execute('select * from my_table')
    assert len(curs.description) == len(headers)
    #assert all(found[0] == expected for found , expected in zip( curs.description, expected_headers)), "headers don't match"
    assert [ found[0] for found in curs.description ] == expected_headers
    assert curs.fetchall() == rows


def test_import_csv_list(monkeypatch):
    files = [ 
            'f1.csv',
            'f2.csv',
            'f3.csv',
    ]
    contents = [ 
            'a,b,c\n1,2,3\n4,5,6', 
            'one,two,three\na,b,c\nd,e,f', 
            'un,dos,tres\na,2,3\nb,2,3'
    ]
    file_index = 0
    def fake_open(self_):
        """ returns a fileobject of each file """
        nonlocal file_index
        fo = io.StringIO(contents[file_index])
        file_index += 1
        return fo
    monkeypatch.setattr(pathlib.Path, 'open', fake_open)
    db = sqlite3.connect(':memory:')
    dialect = csv.excel
    csvsql.import_csv_list(db, files)
    tables_in_db = set( table[0] for table in db.execute('select name from sqlite_master where type="table";').fetchall() )
    assert set(('f1', 'f2', 'f3')) <= tables_in_db
    assert False, "Check the contents of the tables are the expected"



# Helping functions
def assert_table_contains_csv_contents(db, table_name, csv_contents):
    """ given a sqlite3 table and a string with the csv contents, it checks whether there's a table in db
    named as table_name and containing the csv_contents (with the first row as headers) """
    curs = db.execute('select * from %s'%table_name)
    assert False
    # To be developed
