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
    write_output(results, destination )

def get_args(clargs):
    """ processes the arguments in clargs and returns a dictionary with the parsed arguments.

        clargs: a list of arguments as recollected by sys.argv. i.e. clargs[0] is the program name

    """

    program_name = clargs[0]
    p = argparse.ArgumentParser(prog=program_name, description="This program allows the execution of SQL on csv files")
    p.add_argument("-i", "--input",
            action="append", 
            help="Input csv filename. Multiple -i options can be used to specify more than one input file")
    p.add_argument("-u", "--use",
            help="Use the specified sqlite file for input. Options -i and -f are ignored when -u is specified.")
    p.add_argument("-o", "--output",
            help="Send output to this csv file. The file must not exist unleast -f is specified.")
    p.add_argument("-s", "--script",
            help="Execute a SQL script from the given file. If -q is provided, this one is ignored."
              "Only the last SELECT command in the file will be processed.")
    p.add_argument("--db",
            help="Use a sqlite file for intermediate storage. If the file does not exist, it will be created.")
    p.add_argument("query", help="SQL query. i.e. the SELECT statement. If not specified, --script must be provided.")
    p.add_argument('-V', '--version', action='version', version='%s %s'%(program_name, _VERSION))
    args = p.parse_args(clargs[1:])
    return vars(args)

def assert_valid_args(args):
    """ Asserts the processed arguments are valid

        args: a dictionary containing arguments and values.

        In case the combination of arguments is not vàlid, it shows a message and stops execution.
    """
    if 'use' in args:
        assert_file_exists(args['use'])
    else:
        if 'input' not in args:
            print_error_and_exit("Either --input or --use must be defined")
        for path in args['input']:
            assert_file_exists(path)
        if 'db' in args:
            assert_file_exists(args['db'])
    if 'output' in args:
        assert_file_does_not_exist(args['output'])
    if 'query' not in args:
        if 'script' not in args:
            print_error_and_exit("Either --query or --script options must be specified")
        assert_file_exists(args['script'])

def assert_file_exists(path):
    """ Asserts path is an existing file. Otherwise, displays an error and stops execution """
    if not pathlib.Path(path).is_file():
        print_error_and_exit("File %s not found"%path)

def assert_file_does_not_exist(path):
    """ Asserts path is a non existing file. Otherwise, displays an error and stops execution """
    if pathlib.Path(path).is_file():
        print_error_and_exit("File %s already exists."%path)



def get_statements(args):
    """ given the arguments already validated, it returns the list of statements to be executed.

        args: a dictionary containing arguments and values.

        The statements can be defined in 'query' or in 'script' keys of args.

        In case, there are no statements it displays an error and stops execution.

        Note: this method doesn't check for sintactically nor semantically valid SQL statements. It
        will accept as a "valid" statement any string starting with a non whitespace and ended by ';' 
    """
    if 'query' in args:
        statements = get_sql_statements_from_contents(args['query'])
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


def get_sql_statements_from_file(path):
    """ returns the last SELECT statement from the specified file in path.
        In case there's not such a statement, it returns None
        It is assumed the file does exist """
    contents = pathlib.Path(path).read_text()
    statements = get_sql_statements_from_contents(contents)
    return statements[-1] if statements else None

def get_db(args):
    """ given the arguments already validated, it returns the db connection containing all the data """
    if 'use' in args:
         return open_db(args['use'])
    db = open_db(args.get('db', None))
    csvsql.import_csv_list(db, args['input'])
    return db

def write_output(results, filename=None):
    """ Writes results to output file.

        results: is a list of csv rows
        filename: is the path to a file where the results will be stored.

        It is assumed the file doesn't exist.
        If filename is not specified, the standard output is assumed.
    """
    if filename:
        with open(filename, 'wb') as fp:
            csvout = csv.writer(fp, quoting=csv.QUOTE_NONNUMERIC)
            csvout.writerows(results)
    else:
        pretty_print(results, sys.stdout)


def pretty_format(rows, fs=None):
    """ Composes a stream with the information in rows and writes it out to fs.
        In case fs is not provided, it creates one
        Finally it returns the stream
    """
    fs = fs if fs else io.StringIO()
    fs.write('jo')
    return fs

def pretty_print(rows, fp):
    """ This method writes the csv results to the standard output """
    # XXX TODO: consider generating a string to ease testing
    headers = rows[0]
    rows = [[unicode(col) for col in row] for row in rows[1:]]

    rcols = range(len(headers))

    colwidth = [max(0, len(headers[i])) for i in xrange(len(headers))]
    for y in xrange(len(rows)):
        for x in xrange(len(headers)):
            colwidth[x] = max(colwidth[x], len(rows[y][x]))

    # Header
    fp.write(' ' + ' | '.join([unicode(headers[i]).ljust(colwidth[i])
                               for i in rcols]) + '\n')

    # Seperator
    num_dashes = sum(colwidth) + 3 * len(headers) - 1
    fp.write('=' * num_dashes + '\n')

    # Rows
    for row in rows:
        fp.write(' ' + ' | '.join([row[i].ljust(colwidth[i])
                                   for i in rcols]) + '\n')

    if len(rows) == 0:
        fp.write('No results\n')


def print_error_and_exit(msg):
    """ prints msg to the standard error output and exists """
    print(msg, file=sys.stderr)
    sys.exit(1)

if __name__ == '__main__':
    csvsql_process_cml_args(sys.argv)


