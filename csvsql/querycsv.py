#!/usr/bin/env python
"""
Executes SQL on a delimited text file.

This project is a fork of R. Dreas Nielsen's querycsv

Licensed under the GNU General Public License version 3.

Syntax:
    querycsv -i <csv file>... [-o <fname>] [-f <sqlite file>]
        (-s <fname>|<SELECT stmt>)
    querycsv -u <sqlite file> [-o <fname>] (-s <fname>|<SELECT stmt>)
    querycsv (-h|-V)

Options:
   -i <fname> Input CSV file name.
              Multiple -i options can be used to specify more than one input
              file.
   -u <fname> Use the specified sqlite file for input.
              Options -i and -f, are ignored if -u is specified
   -o <fname> Send output to the named CSV file.
   -s <fname> Execute a SQL script from the file given as the argument.
              Output will be displayed from the last SQL command in
              the script.
   -f <fname> Use a sqlite file instead of memory for intermediate storage.
   -h         Print this help and exit.
   -V         Print the version number.

Notes:
   1. Table names used in the SQL should match the input CSV file names,
      without the ".csv" extension.
   2. When multiple input files or an existing sqlite file are used,
      the SQL can contain JOIN expressions.
   3. When a SQL script file is used instead of a single SQL command on
      the command line, only the output of the last command will be
      displayed.

Main changes in this version:

- addapted to python3
- replaced getopt by argparse
- non tested for platforms other than gnu/linux
- non encoding aware: encoding is by default utf-8.
  XXX In future enhancements it will be possible to specify the encoding of the input files
- non csv dialect aware: csv dialect is by csv.excel
  XXX In future enhancements it will be possible to specify dialect variants


Improvements:
- test on non utf-8 files

"""

#from __future__ import print_function
#from __future__ import unicode_literals
#from __future__ import division

import sys
import os.path
import argparse
import csv
import sqlite3
import pathlib
import csvsql

from contextlib import contextmanager

VERSION = "5.0.0"


def print_error_and_exit(msg):
    """ prints msg to the standard error output and exists """
    print(msg, file=sys.stderr)
    sys.exit(1)


# Source: Aaron Watters posted to gadfly-rdbms@egroups.com 1999-01-18
# Modified version taken from sqliteplus.py by Florent Xicluna


def pretty_print(rows, fp):
    headers = rows.pop(0)
    rows = [[unicode(col) for col in row] for row in rows]

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


def read_sqlfile(filename):
    """
    Open the text file with the specified name, read it, and return a list of
    the SQL statements it contains.
    """
    # Currently (11/11/2007) this routine knows only two things about SQL:
    #    1. Lines that start with "--" are comments.
    #    2. Lines that end with ";" terminate a SQL statement.
    sqlfile = open(filename, "rt")
    sqlcmds = []
    currcmd = ''
    for line in sqlfile:
        line = line.strip()
        if len(line) > 0 and not (len(line) > 1 and line[:2] == "--"):
            currcmd = "%s %s" % (currcmd, line)
            if line[-1] == ';':
                sqlcmds.append(currcmd.strip())
                currcmd = ''
    return sqlcmds


def as_list(item):
    """Wrap `item` in a list if it isn't already one."""
    if isinstance(item, (str, unicode)):
        return [item]
    return item


@contextmanager
def as_connection(db):
    if isinstance(db, (str, unicode)):
        with sqlite3.connect(db) as conn:
            yield conn
    else:
        yield db


def table_exists(conn, table_name):
    # TODO: replace by conn.execute('select name from sqlite_master where type='table' and name='{table_name}';')
    try:
        conn.execute('select 1 from {0}'.format(table_name))
        return True
    except sqlite3.OperationalError:
        return False


def execute_sql(conn, sqlcmds):
    """
    Parameters
    ----------
    conn: Database connection that conforms to the Python DB API.
    sqlcmds: List of SQL statements, to be executed in order.
    """
    curs = conn.cursor()
    for cmd in sqlcmds:
        curs.execute(cmd)
    headers = tuple([item[0] for item in curs.description])
    return [headers] + curs.fetchall()


def query_sqlite(sqlcmd, sqlfilename=None):
    """
    Run a SQL command on a sqlite database in the specified file
    (or in memory if sqlfilename is None).
    """
    database = sqlfilename if sqlfilename else ':memory:'
    with as_connection(database) as conn:
        return execute_sql(conn, as_list(sqlcmd))


def query_sqlite_file(scriptfile, *args, **kwargs):
    """
    Run a script of SQL commands on a sqlite database in the specified
    file (or in memory if sqlfilename is None).
    """
    cmds = read_sqlfile(scriptfile)
    return query_sqlite(cmds, *args, **kwargs)


def query_csv(sqlcmd, infilenames, file_db=None):
    """
    sqlcmd: list of sql commands
    infilenames: a path or a list of paths to csv filenames
    file_db: path to a sqlite3 filename

    Query the listed CSV files, optionally writing the output to a
    sqlite file on disk.
    If not file_db, the database will reside in RAM
    """
    # TODO: get file contents from a module that allows mocking
    database = file_db if file_db else ':memory:'
    with as_connection(database) as conn:
        for csvfile in as_list(infilenames):
            # import each csv with the name of it's file without overwriting
            import_csv(conn, csvfile)
        return execute_sql(conn, as_list(sqlcmd))


def get_table_name(csvfile):
    """ composes a table name from the csv filename (with no extension) """
    head, tail = os.path.split(csvfile)
    return os.path.splitext(tail)[0]


def query_csv_file(scriptfile, *args, **kwargs):
    """
    Query the listed CSV files, optionally writing the output to a sqlite
    file on disk.
    """
    cmds = read_sqlfile(scriptfile)
    return query_csv(cmds, *args, **kwargs)


def get_args(arguments):
    """ processes the arguments in args and returns a dictionary with the parsed arguments.

        args: a list of arguments. Usually sys.argv
    """

    p = argparse.ArgumentParser(prog=arguments[0], description="querycsv: executes SQL on csv files")
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
    p.add_argument('-V', '--version', action='version', version='%s %s'%(arguments[0], VERSION))
    args = p.parse_args(arguments[1:])
    return vars(args)


def assert_file_exists(path):
    """ Asserts path is an existing file. Otherwise, displays an error and stops execution """
    if not pathlib.Path(path).is_file():
        print_error_and_exit("File %s not found"%path)


def assert_file_does_not_exist(path):
    """ Asserts path is a non existing file. Otherwise, displays an error and stops execution """
    if pathlib.Path(path).is_file():
        print_error_and_exit("File %s already exists."%path)


def assert_valid_args(args):
    """ Asserts that the arguments are valid

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


def get_statements(args):
    """ given the arguments already validated, it returns the list of statements to be executed.

        If 'query' is directly specified in args. it uses it. Otherwise, it gets the last SELECT in the --script file
        If there's no such SELECT, it displays an error and stops execution.
    """
    if 'query' in args:
        statements = csvsql.get_sql_statements_from_contents(args['query'])
    else:
        statements = csvsql.get_sql_statements_from_file(args['script'])
    if statements:
        return statements
    print_error_and_exit("Not proper SQL statement has been specified")


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

def csvsql_process_cml_args(clargs):
    """ This method interprets the commandline arguments in clargs (typically the contents of sys.args) and
    executes the required statements on the required data.
    Finally, it writes out the results of the last statement to the required output destination.
    """
    args = get_args(clargs)
    assert_valid_args(args)
    statements = get_statements(args)
    db = get_db(args)
    results = csvsql.execute_statements(db, statements)
    write_output(results[-1], vars(args).get('output', None))


#def main():
    #csvsql_process_cml_args(sys.args)
    #args = get_args(sys.argv)
    #assert_valid_args(args)
    #statements = get_statements(args)
    #db = get_db(args)
    #results = csvsql.execute_statements(db, statements)
    ##optlist, arglist = getopt.getopt(sys.argv[1:], "i:u:o:f:Vhs")
    ##flags = dict(optlist)

    ##outfile = flags.get('-o', None)
    ##usefile = flags.get('-u', None)

    ##execscript = '-s' in flags
    ##sqlcmd = " ".join(arglist)

    ##if usefile:
    ##    if execscript:
    ##        # sqlcmd should be the script file name
    ##        results = query_sqlite_file(sqlcmd, usefile)
    ##    else:
    ##        results = query_sqlite(sqlcmd, usefile)
    ##else:
    ##    file_db = flags.get('-f', None)
    ##    csvfiles = [opt[1] for opt in optlist if opt[0] == '-i']
    ##    if len(csvfiles) > 0:
    ##        if execscript:
    ##            # sqlcmd should be the script file name
    ##            results = query_csv_file(sqlcmd, csvfiles, file_db)
    ##        else:
    ##            results = query_csv(sqlcmd, csvfiles, file_db)
    ##    else:
    ##        print_help()
    ##        sys.exit(1)
    #write_output(results, vars(args).get('output', None))


if __name__ == '__main__':
    csvsql_process_cml_args(sys.argv)
