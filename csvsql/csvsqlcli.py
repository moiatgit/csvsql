#! /usr/bin/env python3

"""
    csvsqlcli is a program that allows executing SQL statements on csv files.

    Licensed under the GNU General Public License version 3.

    Description:

    csvsqlcli creates sqlite3 tables named after csv filenames, with fields named after csv headers
    (first row) and then, it makes sqlite3 to execute the required SQL statements on the resulting
    database.

    Run it with -h  (or check get_argparse() method) to see available options

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


class CsvSqlArgParser(argparse.ArgumentParser):
    """ This class defines the parsing of the arguments for the csvsqlcli

        It defines two actions: 'extend' and 'extend_unique' """

    class ExtendAction(argparse.Action):
        """ This class defines an action, similar to 'append' that allows argparse to collect multiple
        args for the same option in a flat list. i.e.

        Example: "-i one two -i three" would generate with 'append' the list [['one', 'two'], ['three']]
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
        Example: "-i one two one -i two three -i three four" would generate [ 'one', 'two', 'three', 'four' ]
        """
        def __call__(self, parser, namespace, values, option_string=None):
            items = getattr(namespace, self.dest) or []
            items.extend(v for v in values if v not in items)
            setattr(namespace, self.dest, items)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.register('action', 'extend', CsvSqlArgParser.ExtendAction)
        self.register('action', 'extend_unique', CsvSqlArgParser.ExtendActionUnique)

    def error(self, message):
        """ Prints help message on parsing error """
        print_error_run_function_and_exit("Error: %s"%message, self.print_help)



def csvsql_process_cml_args(clargs):
    """ This method interprets the commandline arguments in clargs (typically the contents of sys.args) and
    executes the required statements on the required data.
    Finally, it writes out the results of the last statement to the required output destination.
    """
    parser = get_argparse(clargs[0])
    args = get_args(parser, clargs[1:])
    statements = get_statements(args)
    db = get_db(args)
    try:
        results = csvsql.execute_statements(db, statements)[-1] # just results for the last statement
    except sqlite3.OperationalError as err:
        print_error_and_exit("Problems with the statements %s Error: %s"%(statements, err))
    destination = args.get('output', None)
    write_output(results, destination)
    db.close()


def get_argparse(program_name):
    """ constructs an argument parser for this CLI and returns it.
        program_name: a str containing the name of this CLI
    """
    parser = CsvSqlArgParser(prog=program_name, description="This program allows the execution of SQL on csv files")
    parser.add_argument('-v', '--version', action='version', version='%s version %s'%(program_name, _VERSION))
    parser.add_argument("-d", "--database",
            help="Use the specified sqlite file as intermediate storage. If the file does not exist, it will be created.")
    parser.add_argument("-i", "--input",
            action="extend_unique", 
            nargs='+',
            default = [],
            help="Input csv filename. Multiple -i options can be used to specify more than one input file."
                 "Duplications will be ignored.")
    parser.add_argument("-o", "--output",
            help="Send output to this csv file. The file must not exist unleast --force is specified.")
    parser.add_argument("--force", default=False, action='store_false')
    parser.add_argument("-f", "--file",
            action = "extend",
            nargs='+',
            default = [],
            help="Execute SQL statements stored in the given file. Multiple -f options can be used to "
                 "specify more than one statement sources. Each statement will be executed sequentially in the "
                 "specified order. Statements specified with -s will be executed before -f ones.")
    parser.add_argument("-s", "--statement",
            action = "extend",
            default = [],
            help="Execute one or more SQL statements. Multiple -s options can be used to specify "
                 "more than one statement. They can also be specified separated by ';'. Statements "
                 "specified with -f option, will be executed after -s ones.",
            nargs='+')

    return parser


def get_args(parser, clargs):
    """ given an argument parser (ArgumentParser) it processes

        parser: a ArgumentParser with all the options already defined

        clargs: a list of arguments as recollected by sys.argv (without the program name)

        In case the combination of arguments is not vàlid, it shows a message and stops execution.

        returns: a dictionary containing arguments and values.

    """
    args = parser.parse_args(clargs)
    if args.database:
        assert_file_exists(args['database'])

    if args.output:
        if pathlib.Path(args.output).is_file() and not args.force:
            print_error_and_exit("File %s already exists. Remove it or use --force option"%args.output)

    for path in args.input + args.file:
        assert_file_exists(path)

    if not (args.file + args.statement):
        print_error_run_function_and_exit("Nothing to do", parser.print_help)

    return vars(args)



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
    direct_statement = [ get_sql_statements_from_contents(sts) for sts in args['statement'] ]
    filed_statement =  [ get_sql_statements_from_file(sts) for sts in args['file'] ]
    statements = []
    for sts in direct_statement + filed_statement:
        statements.extend(sts)
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

def print_error_run_function_and_exit(msg, function):
    """ prints msg to the standard error output, executes a function and exists """
    print(msg, file=sys.stderr)
    function()
    sys.exit(1)


if __name__ == '__main__':
    csvsql_process_cml_args(sys.argv)


