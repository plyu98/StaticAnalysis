"""
@Author: Alex Yu
@Created: 6/16/22
@Last Modified: 7/19/22

Contains functions for running static code analysis.
"""

from radon.complexity import cc_visit
from radon.raw import analyze
from radon.metrics import h_visit, mi_visit
import pycodestyle
import statistics
import ast
from cognitive_complexity.api import get_cognitive_complexity
import json
import re
import subprocess
import math


def compute_cyclomatic_complexity(source_codes):
    """Performs cyclomatic complexity on the given python source codes.

    Loops through each source code and computes its avg, min, max
    cyclomatic complexity.  Then, computes the total avg, min, max
    cyclomatic complexity of all source codes.

    Args:
      source_codes:
        Python source codes to analyze.

    Returns:
      The total avg, min, max cyclomatic complexity rounded to 2 decimals.
    """

    avg_cc = []
    min_cc = []
    max_cc = []

    for source_code in source_codes:

        blocks = cc_visit(source_code)
        complexities = [block.complexity for block in blocks]

        # checks if no function/class exists in cc blocks
        if not complexities:
            avg_cc.append(1.0)
            min_cc.append(1.0)
            max_cc.append(1.0)
        else:
            avg_cc.append(statistics.fmean(complexities))
            min_cc.append(min(complexities))
            max_cc.append(max(complexities))

    results = [statistics.fmean(avg_cc), min(min_cc), max(max_cc)]

    return round_results(results)


def check_style_error(paths):
    """Runs pycodestyle on the given file paths to check for style errors.

    Loops through each python source code in the given paths.
    Computes the number of coding style errors in the source code using
    pycodestyle.

    Args:
      paths:
        A list of paths containing the source codes.

    Returns:
      The total number of coding style errors in the paths.
    """

    errors = 0
    style = pycodestyle.StyleGuide(quiet=True)

    for path in paths:
        result = style.check_files([path])
        errors += result.total_errors

    return errors


def compute_raw_metrics(source_codes):
    """Obtains raw metrics of the source code.

    Loops through each source code and obtains the raw metrics: loc, lloc,
    sloc, comments, multi-string, single_comments.

    Args:
      source_codes:
        Python source codes to analyze.

    Returns:
      The total number of the raw metrics.
    """

    loc = 0
    lloc = 0
    sloc = 0
    comments = 0
    multi = 0
    single_comments = 0
    functions = 0
    classes = 0

    for source_code in source_codes:
        raw_metric = analyze(source_code)
        loc += raw_metric.loc
        lloc += raw_metric.lloc
        sloc += raw_metric.sloc
        comments += raw_metric.comments
        multi += raw_metric.multi
        single_comments += raw_metric.single_comments
        functions += source_code.count('def')
        classes += source_code.count('class')

    # comments/sloc: comments ratio
    return [loc, lloc, sloc, comments, comments/sloc, multi, single_comments,
            functions, classes]


def compute_maintainability(source_codes):
    """ Obtains the maintainability index of the source code

    Loops through each source code and computes its maintainability index.
    Then computes the avg, min, max maintainability of all source codes.

    Args:
      source_codes:
        Python source codes to analyze.

    Returns:
      The avg, min, max maintainability rounded to 2 decimals.
    """

    maintainability = []

    for source_code in source_codes:
        maintainability.append(mi_visit(source_code, True))

    results = [statistics.fmean(maintainability),
               min(maintainability), max(maintainability)]

    return round_results(results)


def compute_halstead(source_codes):
    """ Obtains the Halstead metrics of the source code.

    Loops through each source code to compute its halstead volume and
    difficulty.  Then computes the avg, min, max halstead volume/difficulty of
    all source codes.

    Args:
      source_codes:
        Python source codes to analyze.

    Returns:
      The avg, min, max halstead volume/difficulty rounded to 2 decimals.
    """

    halstead_volume = []
    halstead_difficulty = []
    halstead_time = []
    halstead_effort = []

    for source_code in source_codes:
        result = h_visit(source_code).total
        halstead_volume.append(result.volume)
        halstead_difficulty.append(result.difficulty)
        halstead_time.append(result.time)
        halstead_effort.append(result.effort)

    results = [statistics.fmean(halstead_volume), min(halstead_volume),
               max(halstead_volume), statistics.fmean(halstead_difficulty),
               min(halstead_difficulty), max(halstead_difficulty),
               statistics.fmean(halstead_time), min(halstead_time),
               max(halstead_time), statistics.fmean(halstead_effort),
               min(halstead_effort), max(halstead_effort)]

    return round_results(results)


def round_results(results):
    """Rounds the values in the list to 2 decimals and returns them."""

    return [round(result, 2) for result in results]


def run_multimetric(files):
    """Runs and parses the multimetric analysis results accordingly.

    Args:
        List of java files to analyze using multimetric.

    Returns:
        Parsed analysis results.
    """

    analysis_results = []
    mi_indices = []

    # runs multimetric, stores the results in json, then converts into dict
    result = subprocess.run(['multimetric', *files],
                            capture_output=True)
    result_d = json.loads(result.stdout.decode('utf-8'))

    for metric in ['loc', 'comment_ratio']:
        analysis_results.append(result_d['overall'][metric])

    for file in result_d['files']:

        # skips empty files
        if result_d['files'][file] != {}:
            loc = result_d['files'][file]['loc']
            comment_ratio = result_d['files'][file]['comment_ratio']
            cc = result_d['files'][file]['cyclomatic_complexity']
            halstead_volume = result_d['files'][file]['halstead_volume']

            # computes maintainability index according to radon's formula
            mi = max(0, (171 - 5.2*math.log(halstead_volume) - 0.23*cc -
                         16.2*math.log(loc) + 50*math.sin(math.sqrt(
                         2.4*math.radians(comment_ratio)))) * 100/171)
            mi_indices.append(mi)

    analysis_results.extend([statistics.fmean(mi_indices), min(mi_indices),
                             max(0, max(mi_indices))])

    for metric in ['cyclomatic_complexity', 'halstead_volume',
                   'halstead_difficulty', 'halstead_timerequired',
                   'halstead_effort']:
        for calc in ['mean', 'min', 'max']:
            analysis_results.append(result_d['stats'][calc][metric])

    return round_results(analysis_results)


def compute_cognitive_complexity(source_codes):
    """Computes cognitive complexity of functions in the source codes.

    Args:
        source_codes:
            Python source codes to analyze for cognitive complexity.

    Returns:
        Avg, min, max cognitive complexities of functions from the given
        source codes.
    """

    complexities = []

    # loops through each source code and parses its abstract syntax tree to
    # extract all the functions from it and computes each function's cognitive
    # complexity
    for source_code in source_codes:
        body = ast.parse(source_code).body
        for node in body:
            if isinstance(node, ast.FunctionDef):
                complexities.append(get_cognitive_complexity(node))

    results = [statistics.fmean(complexities), min(complexities),
               max(complexities)]

    return round_results(results)


def run_pmd():
    """ Runs PMD on the 'filepaths.txt', which contains all java files
        to analyze.  Stores the number of violations according to 'all-java'
        ruleset and cognitive complexity.

    Args:
        None.

    Returns:
        A list that contains the number of violations according to PMD and
        a list of cognitive complexities.
    """

    # runs pmd on all java files in filepaths.txt
    result = subprocess.run(
        ['/Users/alexyu/Downloads/pmd-bin-6.47.0/bin/run.sh',
         'pmd', '--file-list', 'filepaths.txt', '-f', 'json',
         '-R',
         '/Users/alexyu/Downloads/pmd-src-6.47'
         '.0/pmd-core/src/main/resources/rulesets/internal'
         '/all-java.xml'], capture_output=True)

    # reads in analysis results (json format) into a dictionary
    result_d = json.loads(result.stdout)

    # loops through each file analysis results to sum the number of violations
    violations = 0
    complexities = []
    for file in result_d['files']:

        # counts the number of cognitive complexity reports
        count = 0

        # extracts cognitive complexity of every method
        for violation in file['violations']:
            if violation['rule'] == 'CognitiveComplexity':
                count += 1
                text = violation['description'].split('of ')[1]
                complexities.append(int(re.findall("\d+", text)[0]))

        # subtracts cognitive complexity violation
        violations += len(file['violations'])-count

    return [violations, complexities]


# main method for testing purpose
def main(path):
    code = open(path, encoding="utf8")
    source_code = code.read()
    source_codes = [source_code]
    output = []
    output.append(compute_cyclomatic_complexity(source_codes))
    # output.append(checkStyleError(path))
    # output.append(computeRaw(source_code))
    # output.append(computeMI(source_code))
    # output.append(computeHalstead(source_code))
    return output


# test the methods
if __name__ == "__main__":
    path = "/Volumes/GoogleDrive/My Drive/Summer Research/python files/lab2.py"
    print(main(path))
