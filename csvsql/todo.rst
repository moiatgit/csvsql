Currently:

- now import_csv() basic is done, it's time to check import_csv_list() and then bak to main()

  (done) Current problem: check table contents (see assert False on test_csvsql.py)

Enhancements

- add options to clean up the csv data:
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
