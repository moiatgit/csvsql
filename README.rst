Introduction
============

This package allows the execution of SQL statements on csv files.

This project is based on R. Dreas Nielsen's ``querycsv`` 

``csvsql`` offers a API to allow using SQL access to csv from Python programs.
As R. Dreas' ``querycsv``, ``csvsql`` also offers a CLI (command line interface)
to allow the execution of SQL statements from the command line.

Installation
============

Currently, this program is in PyPiTest


csvsqlcli
=========

The CLI is named as ``csvsqlcli.py`` and offers the following output with
option ``-h``

::

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

* all the provided statements are executed as in a transaction. That is,
  at the end of the execution, a commit is issued.

* it is possible to extract both the headed and the unheaded version of
  the output with the same execution.


Current status
==============

At this moment, this project is under development.

While probably ``csvsqlcli.py`` api will just increase, ``csvsql.py`` will probably get some
important changes in some or all its functions. See 'known bugs' section for details.

To Do List
==========

The following list contains some of the pending tasks.

If you feel like trying some of them, please feel free to fork me and go ahead!

Quality
-------

- review codestyle (e.g. with pycodestyle) Mostly done with ``csvsql.py``

- test it on other Operating Systems

  Currently it has been tested just in a GNU/Linux box. It could be
  interesting, but out of reach for the author, to test it on other
  platforms like MS Windows or MAC OS


Documentation
-------------

- The current documentation is more a working sheet than a documentation.
  A way to add more information of usage could be to include several
  use cases as example

New features
------------

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

- ``csvsql`` module contains function ``import_csv_list()``. This function
  has to deal with option_string (-i, -u) It shouldn't since the module is
  intended to be used by other python programs not only the CLI. The
  function, whoever is required since it encapsulates a transaction.
