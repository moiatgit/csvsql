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
_VERSION = "1.0.0"

class ExtendAction(argparse.Action):
    """ This class defines an action, similar to 'append' that allows argparse to collect multiple
    args for the same option in a flat list. i.e.

    "-i one two -i three" would generate with 'append' the list [['one', 'two'], ['three']]
    'ExtendAction will return ['one', 'two', 'three'] instead

    Note: solution found at https://stackoverflow.com/questions/41152799/argparse-flatten-the-result-of-action-append
    """
    def __call__(self, parser, namespace, values, option_string=None):
        items = getattr(namespace, self.dest) or []
        items.extend(values)
        setattr(namespace, self.dest, items)

class ExtendActionUnique(argparse.Action):
    """ This class defines an action, similar to ExtendAction but removing repeated input. It
    preserves the original order.

    "-i one two one -i two three -i three four" would generate [ 'one', 'two', 'three', 'four' ]

    """
    def __call__(self, parser, namespace, values, option_string=None):
        items = getattr(namespace, self.dest) or []
        items.extend(v for v in values if v not in items)
        setattr(namespace, self.dest, items)



def csvsql_process_cml_args(clargs):
    """ This method interprets the commandline arguments in clargs (typically the contents of sys.args) and
    executes the required statements on the required data.
    Finally, it writes out the results of the last statement to the required output destination.
    """
    args = get_args(clargs)
    assert_valid_args(args)
    statements = get_statements(args)
    db = get_db(args)
    try:
        results = csvsql.execute_statements(db, statements)[-1] # just results for the last statement
    except sqlite3.OperationalError as err:
        print_error_and_exit("Problems with the statements %s Error: %s"%(statements, err))
    destination = args.get('output', None)
    write_output(results, destination)
    db.close()


def get_args(clargs):
    """ processes the arguments in clargs and returns a dictionary with the parsed arguments.

        clargs: a list of arguments as recollected by sys.argv. i.e. clargs[0] is the program name

    """

    program_name = clargs[0]
    p = argparse.ArgumentParser(prog=program_name, description="This program allows the execution of SQL on csv files")
    p.register('action', 'extend', ExtendAction)
    p.register('action', 'extend_unique', ExtendActionUnique)
    p.add_argument('-v', '--version', action='version', version='%s version %s'%(program_name, _VERSION))
    p.add_argument("-d", "--database",
            help="Use the specified sqlite file as intermediate storage. If the file does not exist, it will be created.")
    p.add_argument("-i", "--input",
            action="extend_unique", 
            nargs='+',
            help="Input csv filename. Multiple -i options can be used to specify more than one input file."
                 "Duplications will be ignored.")
    p.add_argument("-o", "--output",
            help="Send output to this csv file. The file must not exist unleast --force is specified.")
    p.add_argument("--force", default=False, action='store_false')
    p.add_argument("-f", "--file",
            action = "extend",
            nargs='+',
            help="Execute SQL statements stored in the given file. Multiple -f options can be used to "
                 "specify more than one statement sources. Each statement will be executed sequentially in the "
                 "specified order. Statements specified with -s will be executed before -f ones.")
    p.add_argument("-s", "--statement",
            action = "extend",
            help="Execute one or more SQL statements. Multiple -s options can be used to specify "
                 "more than one statement. They can also be specified separated by ';'. Statements "
                 "specified with -f option, will be executed after -s ones.",
            nargs='+')
    args = p.parse_args(clargs[1:])
    vargs = vars(args)
    #vargs['input'] = flatten_list(XXX now you have to flatten the list to [] if None. Consider 'unique' option for input but not for statement. Then you'll have to retest all cli since the api has changed
    print('XXX', vargs)
    sys.exit(1)
    return vargs


def assert_valid_args(args):
    """ Asserts the processed arguments are valid

        args: a dictionary containing arguments and values.

        In case the combination of arguments is not vàlid, it shows a message and stops execution.
    """
    if args.get('database', None):
        assert_file_exists(args['database'])

    if args.get('input', None):
        for path in args['input']:
            assert_file_exists(path)

    if args.get('output', None):
        if pathlib.Path(args['output']).is_file() and not args['force']:
            print_error_and_exit("File %s already exists. Remove it or use --force option"%args['output'])

    if not args.get('statement', None):
        if args.get('file', None):
            print_error_and_exit("Either statement or --file options must be specified")
        assert_file_exists(args['file'])


def assert_file_exists(path):
    """ Asserts path is an existing file. Otherwise, displays an error and stops execution """
    if not pathlib.Path(path).is_file():
        print_error_and_exit("File %s not found"%path)


def get_statements(args):
    """ given the arguments already validated, it returns the list of statements to be executed.

        args: a dictionary containing arguments and values.

        The statements can be defined in 'statement' or in 'file' keys of args.

        In case, there are no statements it displays an error and stops execution.

        Note: this method doesn't check for sintactically nor semantically valid SQL statements. It
        will accept as a "valid" statement any string starting with a non whitespace and ended by ';' 
    """
    if args.get('statement', None):
        statements = get_sql_statements_from_contents(args['statement'])
    else:
        statements = get_sql_statements_from_file(args['file'])
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
    if args.get('database', None):
         db_name = args['database']
    else:
         db_name = ':memory:'
    db = sqlite3.connect(db_name)
    if args.get('input', None):
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


