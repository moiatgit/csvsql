# This module contains a bunch of usecases for the csvsqlcli program

import pathlib
import csvsqlcli

def test_uc_compute_scores_avg(tmpdir):
    """ Input:
            - students (id, name)
            - scores (student_id, score01, score02, score03)

        Output:
            - results (student_id, name, result)

        Where result = avg(score«i»)
    """
    students_contents = ('id,name\n'
                         'gerard.funny,"Funny, Gerard"\n'
                         'miriam.racket, "Racket Marlopint, Miriam"\n'
                         'jashid.ahmed, "Ahmed Gómez, Jashid"\n'
                         'moises.gomez, "Gómez Girón, Moisès"\n')       # missing in scores
    scores_contents = ('student_id,score01,score02,score03\n'
                       'cristina.cifuentes,34,45,51\n'                  # missing in students
                       'gerard.funny, 20,30,40\n'
                       'jashid.ahmed, 30,40,50\n'                       # different order in students
                       'miriam.racket, 50,60,70\n' )                    # different order in students
    sql_statement = ('select student_id, cast(((score01 + score02 + score03) / 3) as float) as result '
                     'from students, scores '
                     'where id = student_id '
                     'order by id')
    expected_results = ('student_id,result\n'
                        'gerard.funny,30.0\n'
                        'jashid.ahmed,40.0\n'
                        'miriam.racket,60.0\n')

    fin_students = tmpdir.join('students.csv')
    fin_students.write(students_contents)
    fin_scores = tmpdir.join('scores.csv')
    fin_scores.write(scores_contents)
    output_file_path = pathlib.Path(str(tmpdir.realpath())) / 'results.csv'
    clargs = ['csvsqlcli.py',
              '-i', str(fin_students.realpath()),
              '-i', str(fin_scores.realpath()),
              '-o', str(output_file_path),
              '-s', sql_statement]
    csvsqlcli.csvsql_process_cml_args(clargs)
    assert output_file_path.read_text() == expected_results


def test_uc_compute_scores_simple_formulae(tmpdir):
    """ Input:
            - students (id, name)
            - scores (student_id, score01, score02, score03)

        Output:
            - results (student_id, name, result)

        Where result = 20% score01 + 30% score02 + 50% score03
    """
    students_contents = ('id,name\n'
                         'gerard.funny,"Funny, Gerard"\n'
                         'miriam.racket, "Racket Marlopint, Miriam"\n'
                         'jashid.ahmed, "Ahmed Gómez, Jashid"\n'
                         'moises.gomez, "Gómez Girón, Moisès"\n')       # missing in scores
    scores_contents = ('student_id,score01,score02,score03\n'
                       'cristina.cifuentes,34,45,51\n'                  # missing in students
                       'gerard.funny, 20,30,40\n'
                       'jashid.ahmed, 30,40,50\n'                       # different order in students
                       'miriam.racket, 50,60,70\n' )                    # different order in students
    sql_statement = ('select student_id, cast((0.2 * score01 + 0.3 * score02 + 0.5 * score03) as float) as result '
                     'from students, scores '
                     'where id = student_id '
                     'order by id')
    expected_results = ('student_id,result\n'
                        'gerard.funny,33.0\n'
                        'jashid.ahmed,43.0\n'
                        'miriam.racket,63.0\n')

    fin_students = tmpdir.join('students.csv')
    fin_students.write(students_contents)
    fin_scores = tmpdir.join('scores.csv')
    fin_scores.write(scores_contents)
    output_file_path = pathlib.Path(str(tmpdir.realpath())) / 'results.csv'
    clargs = ['csvsqlcli.py',
              '-i', str(fin_students.realpath()),
              '-i', str(fin_scores.realpath()),
              '-o', str(output_file_path),
              '-s', sql_statement]
    csvsqlcli.csvsql_process_cml_args(clargs)
    assert output_file_path.read_text() == expected_results


#def test_uc_compute_scores_conditional(tmpdir):
#    """ Input:
#            - students (id, name)
#            - scores (student_id, score01, score02, score03)
#
#        Output:
#            - results (student_id, name, result)
#
#        Where result = 0 if score01 < 30 else avg(score02, score03)
#    """
#    students_contents = ('id,name\n'
#                         'gerard.funny,"Funny, Gerard"\n'
#                         'miriam.racket, "Racket Marlopint, Miriam"\n'
#                         'jashid.ahmed, "Ahmed Gómez, Jashid"\n')
#    scores_contents = ('student_id,score01,score02,score03\n'
#                       'gerard.funny, 10,30,40\n'
#                       'jashid.ahmed, 30,10,20\n'
#                       'miriam.racket, 50,60,70\n')
##    sql_statement = ('select student_id, '
##                     '       (case when score01 < 30 then 0.0 when score01 >= 30 then cast(((score02+score03)/2) as float) end) '
##                     '     as result '
#    sql_statement = ('select student_id, ('
#                     'case when score01 > 30 then score02 else score03 end'
#                     ') as result '
#                     'from students, scores '
#                     'where id = student_id '
#                     'order by id')
#    expected_results = ('student_id,result\n'
#                        'gerard.funny,0.0\n'
#                        'jashid.ahmed,15.0\n'
#                        'miriam.racket,65.0\n')
#
#    fin_students = tmpdir.join('students.csv')
#    fin_students.write(students_contents)
#    fin_scores = tmpdir.join('scores.csv')
#    fin_scores.write(scores_contents)
#    output_file_path = pathlib.Path(str(tmpdir.realpath())) / 'results.csv'
#    clargs = ['csvsqlcli.py',
#              '-i', str(fin_students.realpath()),
#              '-i', str(fin_scores.realpath()),
#              '-o', str(output_file_path),
#              '-s', sql_statement]
#    csvsqlcli.csvsql_process_cml_args(clargs)
#    assert output_file_path.read_text() == expected_results
#
#
#
