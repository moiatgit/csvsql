Currently
=========

- adding -u (--unheadded) functionality that allows specifying inputs
  without header and --header that allows to specify a replacement header
  for the previous input

  - (done) store input files in tuples (path, hasHeader)
  - add -u option and store unheaded files in tuples (path, unheaded)
  - store input/unheaded files in tuples (path, hasHeader|unheaded, newHeader)
    for newHeader the one specified with the --header option

ToDo
====


- test csvsqlcli

  - (done) test expanded options. For example --statement and --file, so it is
    possible that the way their values are stored doesn't work properly
    with the option_string

  - (done) case csv is not sound (e.g. some rows have extra or fewer columns),

  - (done) resque test cases from csvquery


- define package

  following https://packaging.python.org/tutorials/packaging-projects/

  $ python3 setup.py sdist bdist_wheel
  $ pip install -e .

- test packaging

- edit readme.md

- push csvsql to github

  Don't forget to thank original author!



Enhancements
============

- allow ignoring block statements /* */

- allow specifying the headers of an input file. That is, consider that
  the file doesn't contain headers.

- some optimizations:

  - db.commit() only when non SELECT statement is present

  - perform only the last SELECT statement.

  - allow the execution of CREATE TABLE statements to generate the corresponding .csv

  - allow the specification of tables in FROM clausules to infer the .csv files even if not present
    in the --input args. That would make sense specially when definining some set of folders
    containing .csv that compose the .csv database. Something like a CSVSQLPATH env var.

    Alternativelly, a new option --folder could be added to specify
    multiple folders containing .csv files. These files shoudln't be
    loaded unleast they appear in a FROM clausule


  - if you keep the results of each statement just to show the last one, you might be keeping a lot
    of data in memory for nothing! In fact, just the last statement could simply be too much for big
    csv! Find a way to keep so much data from memory

- add options to clean up the csv data:
  - check for robustness: e.g. what happens when the statements are not valid sql statements, or the
    db or csv are not actually the expected type of files.
  - headed columns only
  - non headed columns named as COLn
  - define column id (by pos or head name) and filter any row without value there
  - filter rows (not) in a set
  - filter dup rows (by id) and cols (by header)
  - keep only rows until the first empty id
  - keep only rows with id in a set
  - allow specification of dialect particularities (by default csv.excel) and for encoding (by
    default utf-8)
  - allow specifying the default name of missing headed columns (by default '__COLn')
  - it could evolve to a full db with any amount of tables (csv files) distributed in the fs and
    synced with a central sqlite3 (or another dbms) so it keeps track of any change within files and 
    db
  - currently, csvsql is not performing transactions on execute_statements() but it could! It is
    probably easier to allow it as part of the list of statements but, by now I'm not sure it is
    possible to rollback 

  - (done) Currently csvsqlcli is using a lot of memory. One of the places is to
    check for consistent csv input. It reads the whole input file twice to
    get the maximum number of columns
    For small files as input, it is not a problem: just process the whole
    contents and get the max columns. BUT for streams and for huge files,
    such approach could be inappropiate. Instead, you can process row by
    row and, in case you find:
    - less columns than expected, you can fill the gaps with empty values
    - mode columns than expected, you can alter table and add further
      columns. Have into account that existing rows should expand
      accordingly

