import pytest
import io
import sqlite3
import csv
import pathlib
from csvsql import csvsql



def test_import_csv_basic_usage():
    headers = ['un', 'dos', 'tres' ]
    rows = [ ( '1', '2', '3' ), ( '4', '5', '6' ) ]
    contents = "%s\n%s"%(",".join(headers), "\n".join((",".join(row) for row in rows)))
    contents_fileobject = io.StringIO(contents)
    table_name = "my_table"
    db = sqlite3.connect(':memory:')
    dialect = csv.excel
    csvsql.import_csv(db, contents_fileobject, table_name, dialect=dialect)
    assert_table_contains_csv_contents(db, 'my_table', contents)


def test_import_csv_unheaded_cols():
    headers = ['un', '' , 'tres', '', '', '', '', '', '', '', '', 'dotze' ]
    rows = [ ( '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12' ) ]
    contents = "%s\n%s"%(",".join(headers), "\n".join((",".join(row) for row in rows)))
    contents_fileobject = io.StringIO(contents)
    expected_headers = [ 'un', '__COL02', 'tres' ] + [ '__COL%02d'%i for i in range(4, 12) ] + [ 'dotze']
    expected_contents = "%s\n%s"%(",".join(expected_headers), "\n".join((",".join(row) for row in rows)))
    table_name = "my_table"
    db = sqlite3.connect(':memory:')
    dialect = csv.excel
    csvsql.import_csv(db, contents_fileobject, table_name, dialect=dialect)
    assert_table_contains_csv_contents(db, 'my_table', expected_contents)


def test_import_csv_list(monkeypatch):
    files ={ 
            'f1.csv': 'a,b,c\n1,2,3\n4,5,6', 
            'f2.csv': 'one,two,three\na,b,c\nd,e,f', 
            'f3.csv': 'un,dos,tres\na,2,3\nb,2,3'     
            }
    monkeypatch.setattr(pathlib.Path, 'open', lambda self_: io.StringIO(files[self_.name]))
    db = sqlite3.connect(':memory:')
    dialect = csv.excel
    csvsql.import_csv_list(db, files.keys())
    for filename in files.keys():
        assert_table_contains_csv_contents(db, filename[:-4], files[filename])


def test_execute_statement_basic():
    db = sqlite3.connect(':memory:')
    db.execute('create table my_table (un, dos)')
    db.execute('insert into my_table values (1, 2)')
    db.execute('insert into my_table values (3, 4)')
    statement = 'select * from my_table'
    results = csvsql.execute_statement(db, statement)
    assert results == [ ('un', 'dos'), (1, 2), (3, 4) ]


def test_execute_statements_basic():
    db = sqlite3.connect(':memory:')
    statements = [
            'create table my_table (un, dos)',
            'insert into my_table values (1, 2)',
            'insert into my_table values (3, 4)',
            'select * from my_table'
            ]
    results = csvsql.execute_statements(db, statements)
    assert results == [ [], [], [], [ ('un', 'dos'), (1, 2), (3, 4) ] ]



# Helping functions


def assert_table_contains_csv_contents(db, table_name, csv_contents):
    """ given a sqlite3 table and a string with the csv contents, it checks whether there's a table in db
    named as table_name and containing the csv_contents (with the first row as headers) """
    curs = db.execute('select * from %s'%table_name)
    contents_found = [ tuple(row) for row in (csv.reader(io.StringIO(csv_contents))) ]
    assert [ found[0] for found in curs.description ] == list(contents_found[0]), "headers don't match"
    assert curs.fetchall() == contents_found[1:]
