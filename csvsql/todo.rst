Currently:

- I'm reprogramming import_csv() method

  It should go to csvsql

  (done) The problem is that csv.reader() seems to be reluctant to split properly by lines



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
