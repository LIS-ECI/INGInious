Tutorial
========

In this document we will describe how to create a simple problem, that checks that a code in Python returns "Hello World!".


Creating the problem description
--------------------------------

Using the webapp
````````````````

If you are using the webapp, this procedure can be done using the graphical interface:

#. Go to the *Course administration/Problems* page, enter ``helloworld`` as a new problem id and click on *Create new problem*.
#. In the *Basic settings* tab fill the required parameters. In the *Grading environment* field, please select **python3pylint**.
#. In the *Test cases* tab, upload every testcase that you need to test the problem. In this case you could create an empty helloworld.in, a helloworld.out with the expected "Hello world!" and an empty helloworld.fb.

Manually
````````
**Warning: This feature is not tested at all in ECINGInious**

This is only possible if the administrator has given access to the course directory to the course administrator.

The problem description is a YAML file describing everything that INGInious needs to know to verify the input of the student.
Here is a simple problem description. Put this file with the name ``task.yaml`` in a newly created ``helloworld`` folder in your course directory.

.. code-block:: yaml
    accessible: true
    authenticity_percentage: 100.0
    author: UVa
    category: Ad hoc
    code_analysis: true
    difficulty: 1
    environment: python3pylint
    limits:
        memory: '100'
        real_time: '5'
        output: '2'
        time: 30
    name: Relational operator
    network_grading: true
    problems:
        '1':
            allowed_exts:
                - .py
            header: ''
            type: code-file
    structure: Ninguna
    weight: 1.0

Most of the fields are self-explanatory. Some remarks:

- The field ``problems`` is a dictionary of problems in INGInious but in ECINGInious is mandatory to left this field as in the example.
- The field ``limits`` are the limits that the problem cannot exceed. The ``real_time`` is in seconds, and ``memory`` and  ``output`` are in MB. The ``time`` is the number of seconds that the grading container will wait until it kills the submission (avoiding a possible infinite loop, for example).
- The ``environment`` field is intended to change the environment where the problems run. The available environment in ECINGInious is **python3pylint**.
- If the ``code_analysis`` field is true, the python3pylint container will execute an static code analysis under the student submission.
- The ``authenticity_percentage`` field is a field associated with the plagiarism plugin, but it doesn't work by the moment.

In your problem folder, you will put every file needed to test the input of the student. So, in order to test the problem you must have to upload test files as following syntax: *<name_of_testcase>*.in, *<name_of_testcase>*.out, *<name_of_testcase>*.fb, *<name_of_testcase>*.name where *<name_of_testcase>*.in is the input file,  *<name_of_testcase>*.out is the expected output file, *<name_of_testcase>*.fb if the feedback given to students and *<name_of_testcase>*.desc is the description. You will put  the **run** file (located in *<storage folder defined during the installation>/run* folder) also. Finally, you could upload the problem file statement using the following syntax: *<problem_id>*.pdf where *<problem_id>* is the problem folder name.
