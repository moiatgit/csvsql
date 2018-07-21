Introduction
============

This package allows the execution of SQL statements on csv files.

This project has been developed using R. Dreas Nielsen's `querycsv
<https://github.com/kdeloach/querycsv-redux>`_ as a base.

``csvsql`` offers a API to allow using SQL access to csv from Python3 programs.
As R. Dreas' ``querycsv``, ``csvsql`` also offers a CLI (command line interface)
to allow the execution of SQL statements from the command line: ``csvsqlcli``.

Installation
============

For testing purposes, I recommend you simply clone it, and in a ``virtualenv`` install the dependencies.

For example:

::

    $ git clone git@github.com:moiatgit/csvsql.git
    $ cd csvsql
    $ mkvirtualenv --python=/usr/bin/python3 csvsql
    $ workon moodleing
    $ pip install -r requirements.txt

**Note**: Actually, ``csvsql`` has no external dependencies to be used. The dependencies in
``requirements.txt`` are for development purposes only.

Once installed, you can just run tests with: ::

    $ make test

Until the documentation is properly developed, you can get some simple use cases from these tests.

Currently, this program is in `testpypi <https://test.pypi.org/project/csvsql/>`_. So it should be
possible to install it from there with: ::

    $ pip3 install --index-url https://test.pypi.org/simple/ csvsql

Unfortunately this option doesn't seem to work. See `Known bugs`_ for more details.


csvsqlcli
=========

The CLI is named as ``csvsqlcli.py`` and offers the following output with option ``-h`` ::

    usage: csvsql/csvsqlcli.py [-h] [-v] [-d DATABASE] [-i INPUT [INPUT ...]]
                               [-u INPUT [INPUT ...]] [-o OUTPUT]
                               [-O UNHEADEDOUTPUT] [--force]
                               [-f STATEMENTS [STATEMENTS ...]]
                               [-s STATEMENTS [STATEMENTS ...]]

    This program allows the execution of SQL statements on csv files.

    optional arguments:
      -h, --help            show this help message and exit
      -v, --version         show program's version number and exit
      -d DATABASE, --database DATABASE
                            Use the specified sqlite file as intermediate storage.
                            If the file does not exist, it will be created.
      -i INPUT [INPUT ...], --input INPUT [INPUT ...]
                            Input csv filename. The first row is assumed to be the
                            headers. Multiple -i options can be used to specify
                            more than one input file.Duplications will be ignored.
                            In case --database is specified, the contents of -i
                            files will be stored in the database, as tables named
                            after the file name. On pre-existing tables, the
                            previous contents will be overriden (not merged)
                            without warning.
      -u INPUT [INPUT ...], --unheaded INPUT [INPUT ...]
                            Input csv filename. The file doesn't contain headers.
                            Multiple -u options can be used to specify more than
                            one input file.Duplications will be ignored. In case
                            --database is specified, the contents of -u files will
                            be stored in the database, as tables named after the
                            file name. On pre-existing tables, the previous
                            contents will be overriden (not merged) without
                            warning.
      -o OUTPUT, --output OUTPUT
                            Send output to this csv file. The file must not exist
                            unleast --force is specified.
      -O UNHEADEDOUTPUT, --unheadedOutput UNHEADEDOUTPUT
                            Send output to this csv file. The file must not exist
                            unleast --force is specified.
      --force               Allows to override --output filename if already
                            present.
      -f STATEMENTS [STATEMENTS ...], --file STATEMENTS [STATEMENTS ...]
                            Execute SQL statements stored in the given file.
                            Multiple -f options can be used to specify more than
                            one statement sources. Each statement will be executed
                            sequentially in the specified order.
      -s STATEMENTS [STATEMENTS ...], --statement STATEMENTS [STATEMENTS ...]
                            Execute one or more SQL statements. Multiple -s
                            options can be used to specify more than one
                            statement. Each statement will be executed
                            sequentially in the specified order.

Some particularities:

* All the provided statements are executed as a transaction in the order they appear in the command
  line. That is, at the end of the execution of all the statements, a commit is issued.

* It is possible to extract both the headed and the *unheaded* version (with no headers) of the
  output with the same execution.

* When a column name is not specified at the csv, ``csvsql`` assigns a default header name
  ``__COLn`` being ``n`` the number of column (one-based) This allows to refer to this column from a
  SQL statement.

* When a csv is not sound (e.g. rows with more or less columns than the header), ``csvsql``
  accommodates it by, for example, generating the missing headers.

Current status and expected future
==================================

At this moment, this project is under development.

The immediate future of this project depends on how well it suits my needs. In brief, I'm a teacher
and have students, assignments and scores. I use csv because it is just plain text (i.e. git
friendly).  Most of these scores are generated by automated (homemade) tools. Up to now, I expend a
lot of time preparing and using spreadsheets to compute relatively simple formulae that, finally,
must be converted back into csv to upload them to Moodle. My hunch here is that I can simplify my
workflow by defining these formulae directly in SQL.

In the `To Do List`_ section you can get some idea of my foreseen improvements.

To Do List
==========

The following list contains some of the pending tasks.

If you feel like trying some of them, please feel free to fork me and go ahead.
Any help will be highly appreciated!

Quality
-------

- review codestyle (e.g. with pycodestyle)

  Mostly done with ``csvsql.py``

- test it on other Operating Systems

  Currently it has been tested just in a GNU/Linux box. It could be interesting, but out of reach
  for me, to test it on other platforms like MS Windows or MAC OS.


Documentation
-------------

- All the user documentation currently available is in this file!

  A way to add more information of usage could be to include several
  use cases as examples.

New features
------------

- offer the inclusion of python expressions to the computation of fields

  sql formulae tend to get quite complex for very simple use cases. For example
  if you have the table (id, value01, value02, value03) and you want the output
  (id, result) where result is computed as
    result = 0 if value01 < 50 else min(value01, avg(value02, value03))

  The resulting sql statement is… well, I'm unable to find it out without some
  tries. The problem is that this kind of formula is quite common and varied,
  so this feature gets high priority if I want to use csvsql

  The syntax could be something like:

    select id, 
           !python("result",
                   "value01 as value,value02,value03",
                   "0 if value < 50 else min(value, avg(value02, value03))"),
           another_field
    from mytable

  That would imply the following
    - run query 'select id,value01 as value,value02,value03,another_field from mytable' on a temporary
      table named view_n (id,value01,value02,value03,another_field)
    - on the obtained result, generate a temporary table named view_n1 (id, result)
      with result col containing the resulting of running python's expression
      over the given variables
    - run query 'select id,result,another_field from view_n,view_n1 where view_n = view_n1'
      That would be the final result

  Notice: for simplification, the first version could limit to one the number
  of python expressions accepted in a statement. Otherwise, the 'other_field'
  column should be considered too as possibly containing python expressions.

  The !python() expression in this example has three args: the resulting column
  name, the list of required fields, and the python expression.
  The second arg should be replaced as is into the first query

  Notice: sqlite allows multiple appearances of the same col name in the
  results and 'select un,dos from (select 3 as un,dos,un from fefo)' is
  possible over a 'un,dos\n1,2' table fefo, resulting as 'un,dos\n,3,2'
  To avoid problems, at least document this! i.e. if the original statement
  does select a certain column, then the python expression doesn't need to
  specify it in the 2nd arg.

    select id, 
           value01,
           !python("result",
                   "value02,value03",
                   "0 if value01 < 50 else min(value01, avg(value02, value03))"),
           another_field
    from mytable

  This would require that the python expression would get all the selected values as context. Since
  it is possible for sqlite to select a col with the same name multiple times, it could represent a
  crash-name problem. 
  While a solution for this problem should be found, it should be remember that the csv module
  already has this problem when dealing with csv
  Consider:
  $ cat fefo.csv
  un,dos,un
  1,2,3
  $ cat trydict.py
  import csv
  with open('fefo.csv') as f:
      reader = csv.DictReader(f)
      for row in reader:
          print(row['un'], row['dos'])
  $ python3 trydict.py
  3 2

  That is, csv DictReader() is getting the last value it founds for the same column name
  Unfortunately, csvsql currently is crashing on this kind of inputs

  $ python3 csvsql/csvsqlcli.py -i /tmp/fefo.csv -s 'select un,dos from fefo'
  Traceback (most recent call last):
   File "csvsql/csvsqlcli.py", line 307, in <module>
     csvsql_process_cml_args(sys.argv)
   File "csvsql/csvsqlcli.py", line 104, in csvsql_process_cml_args
     load_input(db, args.input)
   File "csvsql/csvsqlcli.py", line 268, in load_input
     csvsql.import_csv_list(db, files)
   File "/home/moi/dev/csvsql/csvsql/csvsql.py", line 73, in import_csv_list
     import_csv(db, fo, table_name, header=header)
   File "/home/moi/dev/csvsql/csvsql/csvsql.py", line 47, in import_csv
     db.execute('create table %s (%s);' % (table_name, colstr))
  sqlite3.OperationalError: duplicate column name: un

  Also, to force python given expression as actual expressions, it could
  simply be implemented with a lambda formula encapsulated in a try statement


- allow ignoring block statements ``/* */``

- allow specification of dialect particularities (by default csv.excel)
  and for encoding (by default utf-8)

- allow specifying the default name of missing headed columns (by default '__COLn')

- allow synchronization of db with filesystem

  Currently input files are not modified once the execution of the
  statements is performed. However, some of the statements could modify
  one or more existing tables, create and even remove some of them.
  This functionality could allow the use of a bunch of files as an actual database

  Some steps:

  - allow the execution of CREATE TABLE statements to generate the
    corresponding .csv

  - allow the execution of UPDATE TABLE statements to update the
    corresponding .csv

  - allow the execution of DROP TABLE statements to remove the
    corresponding .csv

- add options to clean up the csv data:

  - check for robustness: e.g. what happens when the statements are not valid sql statements, or the
    db or csv are not actually the expected type of files.

  - filter headed columns only
    this requires ignoring those values in rows that correspond to an
    unheaded column

  - define column id (by pos or head name) and filter any row without value there, remove dups, etc.

  - add an strict option to halt on inconsistent csv (i.e. rows with more
    or less columns than the header)

Optimizations
-------------

- db.commit() only when non SELECT statement is present

- perform only the last SELECT statement.

  Currently it is keeping the results of each statement just to output the last one!

- get output as a stream

  Even keeping just the last statement could simply be too much for large csv!

- allow the specification of tables in FROM clauses to infer the .csv
  files even if not present in the --input args. That would make sense
  specially when defining some set of folders containing .csv that
  compose the .csv database. Something like a CSVSQLPATH env var.

  Alternatively, a new option --folder could be added to specify multiple
  folders containing .csv files. These files shouldn't be loaded unless
  they appear in a FROM clause

- once the previous optimization (interpreting the FROM clauses to decide
  which tables to use), import into sqlite3 just the csv actually required
  by the statements


Known bugs
==========

- some sql statements break sqlcsvcli. e.g

  $ cat fefo.csv
  un,dos,un
  1,2,3
  $ python3 csvsqlcli.py -i fefo.csv -s 'select un,dos from fefo'
  Traceback (most recent call last):
    File "csvsql/csvsqlcli.py", line 307, in <module>
      csvsql_process_cml_args(sys.argv)
    File "csvsql/csvsqlcli.py", line 104, in csvsql_process_cml_args
      load_input(db, args.input)
    File "csvsql/csvsqlcli.py", line 268, in load_input
      csvsql.import_csv_list(db, files)
    File "/home/moi/dev/csvsql/csvsql/csvsql.py", line 73, in import_csv_list
      import_csv(db, fo, table_name, header=header)
    File "/home/moi/dev/csvsql/csvsql/csvsql.py", line 47, in import_csv
      db.execute('create table %s (%s);' % (table_name, colstr))
  sqlite3.OperationalError: duplicate column name: un


- Installing from ``testpypi`` doesn't work properly

  I have most probably missed something when preparing the package.

  The ``csvsqlcli.py`` doesn't get executable when installing with: ::

    $ pip3 install --index-url https://test.pypi.org/simple/ csvsql

  It could also be nice to have it as ``csvsqlcli`` instead of ``csvsqlcli.py``.


- ``csvsql`` module contains function ``import_csv_list()``. This function has to deal with
  option_string (``-i``, ``-u``) It shouldn't since the module is intended to be used by other
  python programs not only the CLI. The function, whoever is required to be placed in the module,
  since it encapsulates a transaction.
