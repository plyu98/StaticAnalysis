# StaticAnalysis

Automate running various static code analysis tools on Python and Java source code

## Purpose
This project tries to automate the process of running the following static code analysis tools on Python and Java source code.

- Python
  - [Radon](https://github.com/rubik/radon)
  - [Pycodestyle](https://github.com/PyCQA/pycodestyle)
- Java
  - [Multimetric](https://github.com/priv-kweihmann/multimetric)
  - [PMD](https://github.com/pmd)

While Pycodestyle and PMD were used for analyzing code style errors, Radon and Multimetric were used to compute various metrics, such as Halstead metrics, Cyclomatic complexity, etc.

The ultimate goal of this project is to automate the running of these tools programmatically rather than using CLI, store the analysis results on Pandas dataframe, and create a csv file for further statistical analysis on the relationship between Python/Java source code and corresponding [NASA-TLX](https://humansystems.arc.nasa.gov/groups/tlx/) score, which is a subjective workload assessment index.
