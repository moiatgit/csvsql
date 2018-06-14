Currently:

Currently checking querycsv.main()
- Moving any contents from querycsv to csvsqlcli. Mostly unchecked!


Enhancements

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
