#! /usr/bin/env python3

"""
    csvsqlcli is a command line program that allows executing SQL statements on csv files.

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

    class StatementCollector(argparse.Action):
        """ This class defines an action that composes a list of tuples
        (option_string, value) and appends them to the attribute name 'pairs_'
        in the received order.
        path values are converted to pathlib.Path
        """
        def __call__(self, parser, namespace, values, option_string=None):
            items = getattr(namespace, self.dest) or []
            items.extend((option_string, pathlib.Path(v) if option_string == '-f' else v ) for v in values)
            setattr(namespace, self.dest, items)

    class InputCollector(argparse.Action):
        """ This class defines an action, similar to StatementCollector but removing repeated input.
        It preserves the original order.
        Values are converted to pathlib.Path
        """
        def __call__(self, parser, namespace, values, option_string=None):
            items = getattr(namespace, self.dest) or []
            items.extend( (option_string, pathlib.Path(v)) for v in values if (option_string, v) not in items)
            setattr(namespace, self.dest, items)

    class PathCollector(argparse.Action):
        """ This class defines an action, that considers the value as a string containing a path
            and stores the value as a pathlib.Path
        """
        def __call__(self, parser, namespace, values, option_string=None):
            path = pathlib.Path(values)
            setattr(namespace, self.dest, path)



    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.register('action', 'collect_path', CsvSqlArgParser.PathCollector)
        self.register('action', 'collect_statements', CsvSqlArgParser.StatementCollector)
        self.register('action', 'collect_inputs', CsvSqlArgParser.InputCollector)

    def error(self, message):
        """ Prints help message on parsing error """
        print_error_run_function_and_exit("Error: %s"%message, self.print_help)



def csvsql_process_cml_args(clargs):
    """ This method interprets the commandline arguments in clargs (typically the contents of sys.args) and
    executes the required statements on the required data.
    Finally, it writes out the results of the last statement to the required output destination.
    """
    parser = get_argparse(program_name=clargs[0])
    args = get_args(parser, clargs[1:])
    statements = get_statements(args.statements)
    db = get_db(args)
    load_input(db, args.input)
    try:
        results = csvsql.execute_statements(db, statements)[-1] # just results for the last statement
    except sqlite3.OperationalError as err:
        print_error_and_exit("Problems with the statements %s Error: %s"%(statements, err))
    destination = args.output
    write_output(results, destination)
    db.close()


def get_argparse(program_name):
    """ constructs an argument parser for this CLI and returns it.
        program_name: a str containing the name of this CLI
    """
    parser = CsvSqlArgParser(prog=program_name, description="This program allows the execution of "
                                                            "SQL statements on csv files.")
    parser.add_argument('-v', '--version', action='version', version='%s version %s'%(program_name, _VERSION))
    parser.add_argument("-d", "--database",
            action="collect_path",
            help="Use the specified sqlite file as intermediate storage. If the file does not exist, it will be created.")
    parser.add_argument("-i", "--input",
            action="collect_inputs", 
            dest="input",
            nargs='+',
            default = [],
            help="Input csv filename. Multiple -i options can be used to specify more than one input file."
                 "Duplications will be ignored. In case --database is specified, the contents of "
                 "--input files will be stored in the database, as tables named after the file name"
                 ". On pre-existing tables, the previous contents will be overriden (not merged) "
                 "without warning.")
    parser.add_argument("-o", "--output",
            action="collect_path",
            help="Send output to this csv file. The file must not exist unleast --force is specified.")
    parser.add_argument("--force", 
                        default=False,
                        action='store_false',
                        help="Allows to override --output filename if already present.")
    parser.add_argument("-f", "--file",
            action = "collect_statements",
            dest = 'statements',
            nargs='+',
            default = [],
            help="Execute SQL statements stored in the given file. Multiple -f options can be used to "
                 "specify more than one statement sources. Each statement will be executed sequentially in the "
                 "specified order.")
    parser.add_argument("-s", "--statement",
            action = "collect_statements",
            dest = 'statements',
            nargs='+',
            default = [],
            help="Execute one or more SQL statements. Multiple -s options can be used to specify "
                 "more than one statement. Each statement will be executed sequentially in the "
                 "specified order.")

    return parser


def get_args(parser, clargs):
    """ given an argument parser (ArgumentParser) it processes

        parser: a ArgumentParser with all the options already defined

        clargs: a list of arguments as recollected by sys.argv (without the program name)

        In case the combination of arguments is not vàlid, it shows a message and stops execution.

        returns: the namespace with the arguments

    """
    args = parser.parse_args(clargs)

    if not (args.statements):
        print_error_run_function_and_exit("Nothing to do", parser.print_help)

    if args.output:
        if pathlib.Path(args.output).is_file() and not args.force:
            print_error_and_exit("File %s already exists. Remove it or use --force option"%args.output)

    paths = [ path for _, path in args.input ] +    \
            [ path for option, path in args.statements if option == '-f']
    for path in paths:
        if not path.is_file():
            print_error_and_exit("File %s not found"%path)

    return args


def get_statements(pairs):
    """ given the arguments already validated, it returns a list with the statements to be executed.

        pairs: a list of tuples (option_string, value) where option_string can be -f to indicate the value
              is a path, or -s to indicate the value is a statement.

        In case, there are no statements it displays an error and stops execution.

        Note: this method doesn't check for sintactically nor semantically valid SQL statements.
    """
    statements = []
    for option_string, value in pairs:
        assert option_string in [ '-s', '-f' ]
        raw_statement = value if option_string == '-s' else pathlib.Path(value).read_text()
        statements.extend(split_statements(raw_statement))
    return statements

def split_statements(contents):
    """ given a string containing zero or more SQL statements, it returns a list with each statement.
        Have into account that:
        - substrings starting by -- are ignored up to \n or $
        - statements are considered to end with ; or $
        - resulting statements will be strimmed (whitespaces removed from start+end) and always will end by ;
        - no further sintactic nor semantic analisys will be performed on the statements
    """
    contents_without_comments = " ".join(re.sub('--.*', '', s) for s in contents.split(os.linesep))
    sentences_from_semicolon = [ s + ';' for s in contents_without_comments.split(';') if len(s.strip())>0 ]
    sentences_from_newline = [ s.split(os.linesep) for s in sentences_from_semicolon ]
    return [ s.strip() for s in itertools.chain.from_iterable(sentences_from_newline) if len(s.strip())>0 ]

def get_db(args):
    """  given the arguments namespace, it returns the corresponding db connection.
         In case db_spec doesn't correspond to a valid sqlite3 database, it issues an error and stops execution
         In case db_spec == None, the connection is on memory """
    if args.database:
        db_name = str(args.database)
        db = sqlite3.connect(db_name)
        try:
            result = csvsql.execute_statement(db, 'pragma integrity_check;')
        except sqlite3.DatabaseError as err:
            print_error_and_exit("Problems found with %s: %s"%(db_name, err))
    else:
        db_name = ':memory:'
        db = sqlite3.connect(db_name)
    return db

def load_input(db, files=None):
    """ given an open connection to a database and a list of input files (pairs
    option_string, pathlib.Path), it loads the data contained in the files onto
    the database """
    if files:
        csvsql.import_csv_list(db, files)
    return db


def write_output(results, destination=None, dialect=csv.excel):
    """ Writes results to output file.

        results: is a list of csv rows
        destination: is the name of the file where to store the results. When None, standard output
        is assumed
    """
    fs = destination.open('w') if destination else sys.stdout
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


