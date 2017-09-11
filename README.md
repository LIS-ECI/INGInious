### INGInious - IEAPIS fork. Innovación Educativa con Arenas de Programación para Ingeniería de Sistemas

<!--
TODO: update badges
![http://jenkins2.info.ucl.ac.be/job/INGInious/](http://jenkins2.info.ucl.ac.be/job/INGInious/badge/icon)
//![https://landscape.io/github/UCL-INGI/INGInious/master](https://landscape.io/github/UCL-INGI/INGInious/master/landscape.svg?style=flat)
#![https://landscape.io/github/UCL-INGI/INGInious/master](https://landscape.io/github/UCL-INGI/INGInious/master/landscape.svg?style=flat)
#![https://gitter.im/UCL-INGI/INGInious?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge](https://badges.gitter.im/Join%20Chat.svg)
#![https://readthedocs.org/projects/inginious/?badge=latest](https://readthedocs.org/projects/inginious/badge/?version=latest)
-->

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/7d783c7603454d45b5a9b267591c0a3e)](https://www.codacy.com/app/hcadavid/INGInious?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=LIS-ECI/INGInious&amp;utm_campaign=Badge_Grade)

[![CircleCI](https://circleci.com/gh/LIS-ECI/INGInious.svg?style=shield)](https://circleci.com/gh/LIS-ECI/INGInious)

INGInious is an intelligent grader that allows secured and automated testing of code made by students.

It is written in Python and uses Docker_ to run student's code inside a secured environment.

INGInious provides a backend which manages interaction with Docker and grade code, and a frontend which allows students to submit their code in a simple and beautiful interface. The frontend also includes a simple administration interface that allows teachers to check the progression of their students and to modify exercices in a simple way.

The backend is independent of the frontend and was made to be used as a library.


### Original Documentation

The documentation is available on Read the Docs: http://inginious.readthedocs.org/en/latest/index.html

On Linux, run ``make html`` in the directory ``/doc`` to create a html version of the documentation.


### Notes on security

Docker containers can be used securely with SELinux enabled. Please do not run untrusted code without activating SELinux.

### Mailing list


A mailing list for both usage and development discussion can be joined by registering [here](https://sympa-2.sipr.ucl.ac.be/sympa/info/inginious).
