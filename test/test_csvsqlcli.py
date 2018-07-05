import pytest
import os
import io
import sqlite3
import csv
import pathlib
import csvsqlcli


def test_split_statements_when_theres_just_one():
    contents = "SELECT * FROM mytable;"
    expected = [ contents ]
    result = csvsqlcli.split_statements(contents)
    assert result == expected


def test_split_statements_when_theres_just_one_and_requires_trimming():
    statement = "SELECT * FROM mytable;"
    contents = "     %s     "%statement
    expected = [ statement ]
    result = csvsqlcli.split_statements(contents)
    assert result == expected


def test_split_statements_when_multiple():
    statements = [ "SELECT * FROM mytable;", "select col1 FROM mytable;", "select col1,col2 FROM mytable where col1=col2;" ]
    contents = "\n".join(statements)
    expected = statements
    result = csvsqlcli.split_statements(contents)
    assert result == expected


def test_split_statements_ignoring_comments():
    statements = [ "SELECT * FROM mytable;", "select col1 FROM mytable;", "select col1,col2 FROM mytable where col1=col2;" ]
    contents = "-- SELECT * FROM anyothertable;\n" + "\n".join(statements[:-1]) + "    -- another comment to ignore\n" + statements[-1]
    expected = statements
    result = csvsqlcli.split_statements(contents)
    assert result == expected


def test_split_statements_ignoring_newlines_within():
    statements = [ "SELECT *\nFROM mytable\n;", "select\ncol1 FROM mytable\n\n;", "select col1,\n\ncol2 FROM mytable where col1=\ncol2;" ]
    statements_clean = [ s.replace('\n', ' ') for s in statements ]
    contents = "-- SELECT * FROM anyothertable;\n" + "\n".join(statements[:-1]) + "    -- another comment to ignore\n" + statements[-1]
    expected = statements_clean
    result = csvsqlcli.split_statements(contents)
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


def test_process_cml_args_when_non_existing_unheaded_output_file(capsys, tmpdir):
    contents = 'one,two,three\n1,2,3\n4,5,6'
    mysubdir = tmpdir.mkdir('subdir')
    fd = mysubdir.join('myfile.csv')
    fd.write(contents)
    output_file_path = pathlib.Path(str(mysubdir.realpath())) / 'outputfile.csv'
    clargs = [ 'csvsqlcli.py', '-i', str(fd.realpath()),
                               '--unheadedOutput', str(output_file_path),
                               '-s', 'select one from myfile;' ]
    expected_output = '1\n4\n'
    csvsqlcli.csvsql_process_cml_args(clargs)
    assert output_file_path.read_text() == expected_output
    captured = capsys.readouterr()
    assert captured[0] == ''
    assert captured[1] == ''


def test_process_cml_args_when_unheaded_output_already_exists_and_forced(capsys, tmpdir):
    contents = 'one,two,three\n1,2,3\n4,5,6'
    mysubdir = tmpdir.mkdir('subdir')
    fin = mysubdir.join('myfile.csv')
    fout = mysubdir.join('outputfile.csv')
    fin.write(contents)
    output_file_path = pathlib.Path(str(mysubdir.realpath())) / 'outputfile.csv'
    clargs = [ 'csvsqlcli.py', '-i', str(fin.realpath()),
                               '-O', str(output_file_path),
                               '--force',
                               '-s', 'select one from myfile;' ]
    expected_output = '1\n4\n'
    csvsqlcli.csvsql_process_cml_args(clargs)
    assert output_file_path.read_text() == expected_output
    captured = capsys.readouterr()
    assert captured[0] == ''
    assert captured[1] == ''


def test_process_cml_args_when_unheaded_output_already_exists_and_not_forced(capsys, tmpdir):
    contents = 'one,two,three\n1,2,3\n4,5,6'
    mysubdir = tmpdir.mkdir('subdir')
    fin = mysubdir.join('myfile.csv')
    fout = mysubdir.join('outputfile.csv')
    fin.write(contents)
    fout.write("anything")
    clargs = [ 'csvsqlcli.py',
               '-i', str(fin.realpath()),
               '--unheadedOutput', str(fout.realpath()),
               '-s', 'select one from myfile;' ]
    with pytest.raises(SystemExit):
        csvsqlcli.csvsql_process_cml_args(clargs)
    captured = capsys.readouterr()
    assert captured[0] == ''
    assert captured[1] != ''


def test_process_cml_args_when_both_headed_and_unheaded_outputs_do_not_exist(capsys, tmpdir):
    contents = 'one,two,three\n1,2,3\n4,5,6'
    mysubdir = tmpdir.mkdir('subdir')
    fd = mysubdir.join('myfile.csv')
    fd.write(contents)
    headed_output_file_path = pathlib.Path(str(mysubdir.realpath())) / 'headed.csv'
    unheaded_output_file_path = pathlib.Path(str(mysubdir.realpath())) / 'unheaded.csv'
    clargs = [ 'csvsqlcli.py', '-i', str(fd.realpath()),
                               '-o', str(headed_output_file_path), 
                               '-O', str(unheaded_output_file_path),
                               '-s', 'select one,three from myfile;' ]
    expected_headed = 'one,three\n1,3\n4,6\n'
    expected_unheaded = '1,3\n4,6\n'
    csvsqlcli.csvsql_process_cml_args(clargs)
    assert headed_output_file_path.read_text() == expected_headed
    assert unheaded_output_file_path.read_text() == expected_unheaded
    captured = capsys.readouterr()
    assert captured[0] == ''
    assert captured[1] == ''


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


def test_process_cml_args_with_multiple_statements_not_ended_by_semicolon(tmpdir):
    tmppath = pathlib.Path(str(tmpdir.realpath()))
    out_path = pathlib.Path(tmppath) / 'outputfile.csv'
    clargs = [ 'csvsqlcli.py',
               '-s', 'create table mytable (one, two, three)',
               '-s', 'insert into mytable values (1, 2, 3)',
               '-s', 'select one from mytable',
               '-o', str(out_path)]
    csvsqlcli.csvsql_process_cml_args(clargs)
    expected_output = 'one\n1\n'
    assert out_path.read_text() == expected_output


def test_process_cml_args_with_multiple_statements_in_one_s(tmpdir):
    tmppath = pathlib.Path(str(tmpdir.realpath()))
    out_path = pathlib.Path(tmppath) / 'outputfile.csv'
    clargs = [ 'csvsqlcli.py',
               '-s', 'create table mytable (one, two, three); insert into mytable values (1, 2, 3); select one from mytable',
               '-o', str(out_path)]
    csvsqlcli.csvsql_process_cml_args(clargs)
    expected_output = 'one\n1\n'
    assert out_path.read_text() == expected_output


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


def test_process_cml_args_with_database_expanded_options(tmpdir):
    fin_contents = "one,two,three\n4,5,6\n"
    fin = tmpdir.join('myoutertable.csv')
    fin.write(fin_contents)
    tmppath = pathlib.Path(str(tmpdir.realpath()))
    db_path = pathlib.Path(tmppath) / 'mydb.sqlite3'
    out_path = pathlib.Path(tmppath) / 'outputfile.csv'
    clargs = [ 'csvsqlcli.py',
               '--database', str(db_path),
               '--statement', 'create table myinnertable (one, two, three);',
               '--statement', 'insert into myinnertable values (1, 2, 3);' ]
    csvsqlcli.csvsql_process_cml_args(clargs)
    clargs = [ 'csvsqlcli.py',
               '--database', str(db_path),
               '--input', str(fin.realpath()),
               '--statement', 'select * from myinnertable union all select * from myoutertable',
               '--output', str(out_path)]
    csvsqlcli.csvsql_process_cml_args(clargs)
    expected_output = 'one,two,three\n1,2,3\n4,5,6\n'
    assert out_path.read_text() == expected_output


def test_process_cml_args_with_non_a_database(tmpdir):
    db_path = tmpdir.join('fake.sqlite3')
    db_path.write("Some non sqlite3 contents")
    clargs = [ 'csvsqlcli.py', '-d', str(db_path.realpath()), '-s', 'pragma integrity_check;' ]
    with pytest.raises(SystemExit):
        csvsqlcli.csvsql_process_cml_args(clargs)


def test_process_cml_args_multiple_statement_sources(tmpdir):
    fin_contents = "one,two,three\n1,2,3\n"
    fin = tmpdir.join('mytable.csv')
    fin.write(fin_contents)
    contents_f1 = "insert into mytable values (4, 5, 6);"
    fstatements1 = tmpdir.join('statements01.sql')
    fstatements1.write(contents_f1)
    contents_f2 = "create table anothertable (one, two);" \
                  "insert into anothertable select one, two from mytable;"
    fstatements2 = tmpdir.join('statements02.sql')
    fstatements2.write(contents_f2)
    fout = tmpdir.join('outputfile.csv')
    clargs = [ 'csvsqlcli.py',
               '-o', str(fout.realpath()),
               '-i', str(fin.realpath()),
               '-f', str(fstatements1.realpath()),
               '-f', str(fstatements2.realpath()),
               '-s', 'select * from anothertable;',
               ]
    expected_output = 'one,two\n1,2\n4,5\n'
    csvsqlcli.csvsql_process_cml_args(clargs)
    assert pathlib.Path(str(fout.realpath())).read_text() == expected_output


def test_process_cml_args_multiple_files_in_same_f(tmpdir):
    fin_contents = "one,two,three\n1,2,3\n"
    fin = tmpdir.join('mytable.csv')
    fin.write(fin_contents)
    contents_f1 = "insert into mytable values (4, 5, 6);"
    fstatements1 = tmpdir.join('statements01.sql')
    fstatements1.write(contents_f1)
    contents_f2 = "create table anothertable (one, two);" \
                  "insert into anothertable select one, two from mytable;"
    fstatements2 = tmpdir.join('statements02.sql')
    fstatements2.write(contents_f2)
    fout = tmpdir.join('outputfile.csv')
    clargs = [ 'csvsqlcli.py',
               '-o', str(fout.realpath()),
               '-i', str(fin.realpath()),
               '-f', str(fstatements1.realpath()), str(fstatements2.realpath()),
               '-s', 'select * from anothertable;',
               ]
    expected_output = 'one,two\n1,2\n4,5\n'
    csvsqlcli.csvsql_process_cml_args(clargs)
    assert pathlib.Path(str(fout.realpath())).read_text() == expected_output


def test_process_cml_args_for_input_containing_less_headers_than_columns(tmpdir):
    contents = "one,two,three\n1,2,3\n4,5,6,7\n8,9,10,11,12\n13,14"
    fin = tmpdir.join('mytable.csv')
    fin.write(contents)
    expected_output = "one,two,three,__COL4,__COL5\n1,2,3,,\n4,5,6,7,\n8,9,10,11,12\n13,14,,,\n"
    fout = tmpdir.join('outputfile.csv')
    clargs = [ 'csvsqlcli.py',
               '-o', str(fout.realpath()),
               '-i', str(fin.realpath()),
               '-s', 'select * from mytable' ]
    csvsqlcli.csvsql_process_cml_args(clargs)
    assert pathlib.Path(str(fout.realpath())).read_text() == expected_output


def test_process_cml_args_for_union_of_two_inputs(tmpdir):
    """ This test case is addapted from querycsv original tests test_query_csv2 """
    contents_foo = 'a, b, c\n1,2,3\n'
    contents_bar = 'a, b, c\n4,5,6\n'
    fin_foo = tmpdir.join('foo.csv')
    fin_bar = tmpdir.join('bar.csv')
    fout = tmpdir.join('outputfile.csv')
    output_file_path = pathlib.Path(str(tmpdir.realpath())) / 'outputfile.csv'
    fin_foo.write(contents_foo)
    fin_bar.write(contents_bar)
    clargs = [ 'csvsqlcli.py',
               '-i', str(fin_foo.realpath()), str(fin_bar.realpath()),
               '-o', str(fout.realpath()),
               '-s', 'select * from foo union all select * from bar' ]
    expected_output = 'a,b,c\n1,2,3\n4,5,6\n'
    csvsqlcli.csvsql_process_cml_args(clargs)
    assert output_file_path.read_text() == expected_output


def test_process_cml_args_for_union_of_two_inputs(tmpdir):
    """ This test case is addapted from querycsv original tests test_query_csv3 """
    contents_foo = 'a, b, c\n1,2,3\n4,5,6\n'
    fin_foo = tmpdir.join('foo.csv')
    fout = tmpdir.join('outputfile.csv')
    output_file_path = pathlib.Path(str(tmpdir.realpath())) / 'outputfile.csv'
    fin_foo.write(contents_foo)
    clargs = [ 'csvsqlcli.py',
               '-i', str(fin_foo.realpath()),
               '-o', str(fout.realpath()),
               '-s', 'update foo set a=(a+b+c); select a from foo;' ]
    expected_output = 'a\n6\n15\n'
    csvsqlcli.csvsql_process_cml_args(clargs)
    assert output_file_path.read_text() == expected_output


def test_process_cml_args_for_unheaded_input(tmpdir):
    contents= '1,2,3\n4,5,6\n'
    fin = tmpdir.join('mytable.csv')
    fout = tmpdir.join('outputfile.csv')
    output_file_path = pathlib.Path(str(tmpdir.realpath())) / 'outputfile.csv'
    fin.write(contents)
    clargs = [ 'csvsqlcli.py',
               '-u', str(fin.realpath()),
               '-o', str(fout.realpath()),
               '-s', 'select * from mytable;' ]
    expected_output = '__COL1,__COL2,__COL3\n1,2,3\n4,5,6\n'
    csvsqlcli.csvsql_process_cml_args(clargs)
    assert output_file_path.read_text() == expected_output


def test_process_cml_args_for_mixed_headed_and_unheaded_inputs(tmpdir):
    contents_headed = 'one,two,three\n1,2,3\n4,5,6\n'
    contents_unheaded = '1,10\n2,20\n'
    fin_headed = tmpdir.join('headed.csv')
    fin_unheaded = tmpdir.join('unheaded.csv')
    fout = tmpdir.join('outputfile.csv')
    output_file_path = pathlib.Path(str(tmpdir.realpath())) / 'outputfile.csv'
    fin_headed.write(contents_headed)
    fin_unheaded.write(contents_unheaded)
    clargs = [ 'csvsqlcli.py',
               '--input', str(fin_headed.realpath()),
               '--unheaded', str(fin_unheaded.realpath()),
               '--output', str(fout.realpath()),
               '--statement', 'select two, __COL2 as dos from headed, unheaded where one=__COL1;' ]
    expected_output = 'two,dos\n2,10\n'
    csvsqlcli.csvsql_process_cml_args(clargs)
    assert output_file_path.read_text() == expected_output


