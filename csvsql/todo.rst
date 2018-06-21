Currently
=========

Currently checking querycsv.main()
- (done) current problem: test_csvsql_process_cml_args_when_non_existing_output_file
  The output is different when writen to stdout than on a file. \r\n
- (done) test_csvsql_process_cml_args_when_output_already_exists_and_not_forced 
  Problem: it seems pathlib is unable to find the existing file


ToDo
====

- consider if it has sense to use options 'use' and 'db'. Maybe it is enough with 'db' since both
  allow the use of a single sqlite db and it can be modified by the statements to execute
  Then, the validations would change: if 'db' doesn't already exist, at least one --input should be
  defined.
  That also could be reconsidered, since there could be statements not requiring data!
  So, --db could be replaced by --use and none --use nor --input should be required. Just the
  statements. Statements will fail when accessing to unnexisting tables, just as it does when that
  happens with tables not included in the --use or --input!

  Then, --db could be used to define the path of a folder containing a bunch of csv. BUT, it can be
  implemented by --input allowing multiple filenames (e.g. --input \*.csv ) and in a future, by
  allowing specification of the data by a .json-like file

- test csvsqlcli

  - case intermediate storage '-f' o '--db'

  - case more than one 'input'¡

  - case 'use' and ('input' or 'db')

  - case 'use'

  - case 'db'

- test packaging

- create a new repo at github and push this

  Don't forget to thank original author!



Enhancements
============

- some optimizations:

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
