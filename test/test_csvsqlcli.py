import pytest
import os
import io
import sqlite3
import csv
import pathlib
import csvsqlcli


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


def test_process_cml_args_no_args_provided(capsys):
    clargs = [ 'csvsqlcli.py' ]
    with pytest.raises(SystemExit):
        csvsqlcli.csvsql_process_cml_args(clargs)

def test_process_cml_args_simple_query(capsys, tmpdir):
    contents = 'one,two,three\n1,2,3\n4,5,6'
    fd = tmpdir.mkdir('subdir').join('myfile.csv')
    fd.write(contents)
    clargs = [ 'csvsqlcli.py', '-i', str(fd.realpath()), '-s', 'select one from myfile;' ]
    expected_output = 'one\n1\n4\n'
    csvsqlcli.csvsql_process_cml_args(clargs)
    captured = capsys.readouterr()
    assert captured[0].replace('\r','') == expected_output
    assert captured[1] == ''

def test_process_cml_args_when_non_existing_output_file(capsys, tmpdir):
    contents = 'one,two,three\n1,2,3\n4,5,6'
    mysubdir = tmpdir.mkdir('subdir')
    fd = mysubdir.join('myfile.csv')
    fd.write(contents)
    output_file_path = pathlib.Path(str(mysubdir.realpath())) / 'outputfile.csv'
    clargs = [ 'csvsqlcli.py', '-i', str(fd.realpath()), 
                               '-o', str(output_file_path),
                               '-s', 'select one from myfile;' ]
    expected_output = 'one\n1\n4\n'
    csvsqlcli.csvsql_process_cml_args(clargs)
    assert output_file_path.read_text() == expected_output
    captured = capsys.readouterr()
    assert captured[0] == ''
    assert captured[1] == ''

def test_process_cml_args_when_output_already_exists_and_forced(capsys, tmpdir):
    contents = 'one,two,three\n1,2,3\n4,5,6'
    mysubdir = tmpdir.mkdir('subdir')
    fin = mysubdir.join('myfile.csv')
    fout = mysubdir.join('outputfile.csv')
    fin.write(contents)
    output_file_path = pathlib.Path(str(mysubdir.realpath())) / 'outputfile.csv'
    clargs = [ 'csvsqlcli.py', '-i', str(fin.realpath()), 
                               '-o', str(output_file_path),
                               '--force',
                               '-s', 'select one from myfile;' ]
    expected_output = 'one\n1\n4\n'
    csvsqlcli.csvsql_process_cml_args(clargs)
    assert output_file_path.read_text() == expected_output
    captured = capsys.readouterr()
    assert captured[0] == ''
    assert captured[1] == ''

def test_process_cml_args_when_output_already_exists_and_not_forced(capsys, tmpdir):
    contents = 'one,two,three\n1,2,3\n4,5,6'
    mysubdir = tmpdir.mkdir('subdir')
    fin = mysubdir.join('myfile.csv')
    fout = mysubdir.join('outputfile.csv')
    fin.write(contents)
    fout.write("anything")
    clargs = [ 'csvsqlcli.py', 
               '-i', str(fin.realpath()),
               '-o', str(fout.realpath()), 
               '-s', 'select one from myfile;' ]
    with pytest.raises(SystemExit):
        csvsqlcli.csvsql_process_cml_args(clargs)
    captured = capsys.readouterr()
    assert captured[0] == ''
    assert captured[1] != ''

def test_process_cml_args_when_no_input_file(capsys):
    clargs = [ 'csvsqlcli.py', '-s', 'select tbl_name from sqlite_master;' ]
    expected_output = 'tbl_name\n'
    csvsqlcli.csvsql_process_cml_args(clargs)
    captured = capsys.readouterr()
    assert captured[0].replace('\r','') == expected_output
    assert captured[1] == ''

def test_process_cml_args_when_statement_error(capsys):
    clargs = [ 'csvsqlcli.py', '-s', 'select foo from bar;' ]
    with pytest.raises(SystemExit):
        csvsqlcli.csvsql_process_cml_args(clargs)
    captured = capsys.readouterr()
    assert captured[0] == ''
    assert 'error' in captured[1].lower()


def test_process_cml_args_when_multiple_input_entries(tmpdir):
    contents_en = 'one,two,three\n1,2,3\n4,5,6\n'
    contents_nh = 'ichi,ni,san\n3,2,1\n6,5,4\n'
    fin_en = tmpdir.join('file_en.csv')
    fin_nh = tmpdir.join('file_nh.csv')
    fout = tmpdir.join('outputfile.csv')
    output_file_path = pathlib.Path(str(tmpdir.realpath())) / 'outputfile.csv'
    fin_en.write(contents_en)
    fin_nh.write(contents_nh)
    clargs = [ 'csvsqlcli.py', 
               '-i', str(fin_en.realpath()), 
               '-i', str(fin_nh.realpath()), 
               '-o', str(fout.realpath()), 
               '-s', 'select one+ichi as oneichi from file_en, file_nh where two = ni' ]
    expected_output = 'oneichi\n4\n10\n'
    csvsqlcli.csvsql_process_cml_args(clargs)
    assert output_file_path.read_text() == expected_output


def test_process_cml_args_when_multiple_entries_on_same_input_option(tmpdir):
    contents_en = 'one,two,three\n1,2,3\n4,5,6\n'
    contents_nh = 'ichi,ni,san\n3,2,1\n6,5,4\n'
    fin_en = tmpdir.join('file_en.csv')
    fin_nh = tmpdir.join('file_nh.csv')
    fout = tmpdir.join('outputfile.csv')
    output_file_path = pathlib.Path(str(tmpdir.realpath())) / 'outputfile.csv'
    fin_en.write(contents_en)
    fin_nh.write(contents_nh)
    clargs = [ 'csvsqlcli.py', 
                '-i', str(fin_en.realpath()), str(fin_nh.realpath()), 
                '-o', str(fout.realpath()), 
                '-s', 'select one+ichi as oneichi from file_en, file_nh where two = ni' ]
    expected_output = 'oneichi\n4\n10\n'
    csvsqlcli.csvsql_process_cml_args(clargs)
    assert output_file_path.read_text() == expected_output


def test_process_cml_args_with_database(tmpdir):
    tmppath = pathlib.Path(str(tmpdir.realpath()))
    db_path = pathlib.Path(tmppath) / 'mydb.sqlite3'
    out_path = pathlib.Path(tmppath) / 'outputfile.csv'
    clargs = [ 'csvsqlcli.py',
               '-d', str(db_path),
               '-s', 'create table mytable (one, two, three);', 
               '-s', 'insert into mytable values (1, 2, 3);' ]
    csvsqlcli.csvsql_process_cml_args(clargs)
    clargs = [ 'csvsqlcli.py',
               '-d', str(db_path),
               '-s', 'select one from mytable;',
               '-o', str(out_path)]
    csvsqlcli.csvsql_process_cml_args(clargs)
    expected_output = 'one\n1\n'
    assert out_path.read_text() == expected_output


def test_process_cml_args_with_non_a_database(tmpdir):
    db_path = tmpdir.join('fake.sqlite3')
    db_path.write("Some non sqlite3 contents")
    clargs = [ 'csvsqlcli.py', '-d', str(db_path.realpath()), '-s', 'pragma integrity_check;' ]
    with pytest.raises(SystemExit):
        csvsqlcli.csvsql_process_cml_args(clargs)

