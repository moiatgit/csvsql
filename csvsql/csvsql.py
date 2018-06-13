"""
    This module contains utilities to interface with csv files with SQL statements
"""
import os
import itertools
import re
import csv

def get_sql_statements_from_contents(contents):
    """ returns a list of SQL statements found in contents

        A valid SQL statement in this context is a string started by a non whitespace and ended by ';'

        Lines starting by ^\s*-- are considered comments and ignored

        In case there's no valid SELECT statement, it returns None
    """
    contents_without_comments = " ".join(re.sub('--.*', '', s) for s in contents.split(os.linesep))
    sentences_from_semicolon = [ s + ';' for s in contents_without_comments.split(';') if len(s.strip())>0 ]
    sentences_from_newline = [ s.split(os.linesep) for s in sentences_from_semicolon ]
    return [ s.strip() for s in itertools.chain.from_iterable(sentences_from_newline) if len(s.strip())>0 ]


def get_sql_statements_from_file(path):
    """ returns the last SELECT statement from the specified file in path.
        In case there's not such a statement, it returns None
        It is assumed the file does exist """
    contents = pathlib.Path(path).read_text()
    statements = get_sql_statements_from_contents(contents)
    return statements[-1] if statements else None


def import_csv(db, contents_fileobject, table_name, dialect=csv.excel):
    """ Imports the contents into a table named table_name in db

        db: a connection to the database
        contents_fileobject: a file object containing the csv contents
        table_name: the name of the table where to store the contents. If the table already
                    exists, its former contents will be overwritten
    """
    reader = csv.reader(contents_fileobject, dialect)
    column_names = next(reader, None)
    colstr = ",".join('[{0}]'.format(col) for col in column_names)
    db.execute('drop table if exists %s;' % table_name)
    db.execute('create table %s (%s);' % (table_name, colstr))
    for row in reader:
        params = ','.join('?' for i in range(len(row)))
        sql = 'insert into %s values (%s);' % (table_name, params)
        db.execute(sql, row)
    db.commit()

