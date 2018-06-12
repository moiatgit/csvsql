import pytest
from querycsv import querycsv


#def test_query_with_a_single_table():
#    results = querycsv.query_csv('select * from foo', 

def test_get_last_select_statement_from_contents_when_theres_one():
    last_statement = "SELECT * from mytable;"
    contents = last_statement
    result = querycsv.get_last_select_statement_from_file(contents)
    assert result == last_statement

