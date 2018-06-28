"""
    This module contains utilities to interface with csv files with SQL statements
"""
import os
import itertools
import csv
import pathlib

_DEFAULT_COLUMN_NAME = '__COL'


def import_csv(db, contents_fileobject, table_name, dialect=csv.excel):
    """ Imports the contents into a table named table_name in db

        db: a connection to the database
        contents_fileobject: a file object containing the csv contents
        table_name: the name of the table where to store the contents. If the table already
                    exists, its former contents will be overwritten
    """

    reader = csv.reader(contents_fileobject, dialect)
    source_headers = next(reader, None)
    column_counter = 0
    default_column_name = _DEFAULT_COLUMN_NAME + "%%0%sd"%len(str(len(source_headers)))
    def normalize_column_name(source_column_name):
        """ given the name of the column as found in the csv source, it returns a normalized
            version. This normalization consists on:
            - if the source_column_name is not empty, it is accepted as the normalized name
            - otherwise, _DEFAULT_COLUMN_NAME is placed instead
            This method increments column_counter every time it is called.
        """
        nonlocal column_counter
        column_counter += 1
        return source_column_name if source_column_name else default_column_name%column_counter

    colstr = ','.join( normalize_column_name(col) for col in source_headers )
    db.execute('drop table if exists %s;' % table_name)
    db.execute('create table %s (%s);' % (table_name, colstr))
    for row in reader:
        print("XXX considering row", row)
        params = ','.join('?' for i in range(len(row)))
        sql = 'insert into %s values (%s);' % (table_name, params)
        print("XXX sql: ", sql)
        db.execute(sql, row)
    db.commit()


def import_csv_list(db, filenames):
    """ imports the contents of the filenames 
        Filenames is a list of paths to csv files
    """
    for filename in filenames:
        path = pathlib.Path(filename)
        table_name = path.stem
        with path.open() as fo:
            import_csv(db, fo, table_name)

def execute_statement(db, statement):
    """ executes an sql statement on db and returns the results """
    curs = db.execute(statement)
    return [tuple([item[0] for item in curs.description])] + list(curs) if curs.description else []

def execute_statements(db, statements):
    """ executes a list of sql statements on db and returns the list of results """
    return [ execute_statement(db, statement) for statement in statements ]


