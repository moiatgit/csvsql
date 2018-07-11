"""
    This module contains utilities to interface with csv files with SQL
    statements
"""
import os
import itertools
import csv
import pathlib

_DEFAULT_COLUMN_NAME = '__COL'


def import_csv(db, contents_fileobject, table_name,
               dialect=csv.excel, header=None):
    """ Imports the contents into a table named table_name in db

        db: a connection to the database

        contents_fileobject: a file object containing the csv contents

        header is a str that defines the headers when different to None

        table_name: the name of the table where to store the contents. If the
                    table already exists, its former contents will be
                    overwritten
    """

    reader = csv.reader(contents_fileobject, dialect)
    source_headers = next(reader, None) if header is None else header.split(',')
    column_counter = 0
    default_column_name = _DEFAULT_COLUMN_NAME + "%d"

    def normalize_column_name(source_column_name=''):
        """ given the name of the column as found in the csv source, it
            returns a normalized version. This normalization consists on:
            - if the source_column_name is not empty, it is accepted as the
              normalized name
            - otherwise, _DEFAULT_COLUMN_NAME is placed instead
            This method increments column_counter every time it is called.
        """
        nonlocal column_counter
        column_counter += 1
        return source_column_name if source_column_name else default_column_name % column_counter

    colstr = ','.join(normalize_column_name(col) for col in source_headers)
    db.execute('drop table if exists %s;' % table_name)
    db.execute('create table %s (%s);' % (table_name, colstr))
    for row in reader:
        while len(row) > column_counter:
            new_column = normalize_column_name()
            db.execute('alter table %s add column %s' % (table_name,
                                                         new_column))
        values = row + [''] * (column_counter - len(row))
        params = ','.join('?' for i in range(column_counter))
        sql = 'insert into %s values (%s);' % (table_name, params)
        db.execute(sql, values)
    db.commit()


def import_csv_list(db, pairs_type_path):
    """ imports the contents of the paths in pairs

        pairs_type_path: a list of tuples (option_string, path) where path is
        a pathlib expected to corresponds to a csv files, and option_string
        allows to decide whether the file contains '-i' or not '-u' a header
        row
    """
    for option_string, path in pairs_type_path:
        assert option_string in ['-i', '-u']
        table_name = path.stem
        header = '' if option_string == '-u' else None
        with path.open() as fo:
            import_csv(db, fo, table_name, header=header)


def execute_statement(db, statement):
    """ executes an sql statement on db and returns the results """
    curs = db.execute(statement)
    return [
            tuple([item[0] for item in curs.description])
           ] + list(curs) if curs.description else []


def execute_statements(db, statements):
    """ executes a list of sql statements on db and returns the list of
        results """
    results = [execute_statement(db, statement) for statement in statements]
    db.commit()
    return results
