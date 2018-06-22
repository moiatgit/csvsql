#! /usr/bin/env python3

"""
    csvsqlcli is a program that allows executing SQL statements on csv files.

    Licensed under the GNU General Public License version 3.

    Description:

    csvsqlcli creates sqlite3 tables named after csv filenames, with fields named after csv headers
    (first row) and then, it makes sqlite3 to execute the required SQL statements on the resulting
    database.

    Run it with -h  (or check get_args() method) to see available options

    This project is based on R. Dreas Nielsen's querycsv forked on version 4.0.0
    The main difference with R. Dreas' program is that csvsqlcli is just a byproduct. The main
    target of this project is csvsql, a library to allow the use of SQL in csv programatically.

"""

import sys
import os
import argparse
import pathlib
import re
import itertools
import io
import tempfile
import csv
import sqlite3

import csvsql

# Current version of this cli
_VERSION = "0.1.0"


def csvsql_process_cml_args(clargs):
    """ This method interprets the commandline arguments in clargs (typically the contents of sys.args) and
    executes the required statements on the required data.
    Finally, it writes out the results of the last statement to the required output destination.
    """
    args = get_args(clargs)
    assert_valid_args(args)
    statements = get_statements(args)
    db = get_db(args)
    results = csvsql.execute_statements(db, statements)[-1] # just results for the last statement
    destination = args.get('output', None)
    write_output(results, destination)
    db.close()


def get_args(clargs):
    """ processes the arguments in clargs and returns a dictionary with the parsed arguments.

        clargs: a list of arguments as recollected by sys.argv. i.e. clargs[0] is the program name

    """

    program_name = clargs[0]
    p = argparse.ArgumentParser(prog=program_name, description="This program allows the execution of SQL on csv files")
    p.add_argument("-i", "--input",
            action="append", 
            help="Input csv filename. Multiple -i options can be used to specify more than one input file")
    p.add_argument("-d", "--database",
            help="Use the specified sqlite file as intermediate storage. If the file does not exist, it will be created.")
    p.add_argument("-o", "--output",
            help="Send output to this csv file. The file must not exist unleast --force is specified.")
    p.add_argument("--force", default=False, action='store_false')
    p.add_argument("-s", "--script",
            help="Execute a SQL script from the given file. If -q is provided, this one is ignored."
              "Only the last SELECT command in the file will be processed.")
    p.add_argument("statement", help="SQL statement. i.e. the SELECT statement. If not specified, --script must be provided.")
    p.add_argument('-V', '--version', action='version', version='%s %s'%(program_name, _VERSION))
    args = p.parse_args(clargs[1:])
    return vars(args)


def assert_valid_args(args):
    """ Asserts the processed arguments are valid

        args: a dictionary containing arguments and values.

        In case the combination of arguments is not vàlid, it shows a message and stops execution.
    """
    if args.get('use', None):
        assert_file_exists(args['use'])
    else:
        if not args.get('input', None):
            print_error_and_exit("Either --input or --use must be defined")
        for path in args['input']:
            assert_file_exists(path)
        if args.get('db', None):
            assert_file_exists(args['db'])
    if args.get('output', None):
        if pathlib.Path(args['output']).is_file() and not args['force']:
            print_error_and_exit("File %s already exists. Remove it or use --force option"%args['output'])

    if not args.get('statement', None):
        if args.get('script', None):
            print_error_and_exit("Either statement or --script options must be specified")
        assert_file_exists(args['script'])


def assert_file_exists(path):
    """ Asserts path is an existing file. Otherwise, displays an error and stops execution """
    if not pathlib.Path(path).is_file():
        print_error_and_exit("File %s not found"%path)


def get_statements(args):
    """ given the arguments already validated, it returns the list of statements to be executed.

        args: a dictionary containing arguments and values.

        The statements can be defined in 'statement' or in 'script' keys of args.

        In case, there are no statements it displays an error and stops execution.

        Note: this method doesn't check for sintactically nor semantically valid SQL statements. It
        will accept as a "valid" statement any string starting with a non whitespace and ended by ';' 
    """
    if args.get('statement', None):
        statements = get_sql_statements_from_contents(args['statement'])
    else:
        statements = get_sql_statements_from_file(args['script'])
    if statements:
        return statements
    print_error_and_exit("Not proper SQL statement has been specified")


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


def query_sqlite(sqlcmd, sqlfilename=None):
    """
    Run a SQL command on a sqlite database in the specified file
    (or in memory if sqlfilename is None).
    """
    database = sqlfilename if sqlfilename else ':memory:'
    with as_connection(database) as conn:
        return execute_sql(conn, as_list(sqlcmd))

def get_sql_statements_from_file(path):
    """ returns the last SELECT statement from the specified file in path.
        In case there's not such a statement, it returns None
        It is assumed the file does exist """
    contents = pathlib.Path(path).read_text()
    statements = get_sql_statements_from_contents(contents)
    return statements[-1] if statements else None


def get_db(args):
    """ given the arguments already validated, it returns the db connection containing all the data """
    if args.get('use', None):
         db_name = args['use']
    else:
         db_name = args.get('db', None)
         if not db_name:
             db_name = ':memory:'
    db = sqlite3.connect(db_name)
    csvsql.import_csv_list(db, args['input'])
    return db


def write_output(results, destination=None, dialect=csv.excel):
    """ Writes results to output file.

        results: is a list of csv rows
        destination: is the name of the file where to store the results. When None, standard output
        is assumed
    """
    fs = open(destination, 'w') if destination else sys.stdout
    csv.writer(fs, dialect=dialect).writerows(results)
    if destination:
        fs.close()


def print_error_and_exit(msg):
    """ prints msg to the standard error output and exists """
    print(msg, file=sys.stderr)
    sys.exit(1)

if __name__ == '__main__':
    csvsql_process_cml_args(sys.argv)


