"""
@Author: Alex Yu
@Created: 7/19/22
@Last Modified: 7/22/22

Contains static code analysis functions for merged_dataframe.ipynb.

"""

import statistics
import metrics as mt
import re
import utils
import os


def compute_tlx(df, df_headers):
    """Calculates TLX scores from raw metrics of the given data frame.

    Computes TLX scores and adjusted mental, physical, temporal,
    performance, effort, and frustration scores from the given
    data frame.

    Credit:
        Naser Al Madi (TLX-preprocessing.ipynb)

    Args:
        df:
            The data frame to read in and compute TLX scores.
        df_headers:
            Data frame headers.
    Returns:
      None.
    """

    # initializes the score values
    tlx_index = df_headers.index("TLX")
    for i in range(tlx_index, tlx_index+8):
        df[df_headers[i]] = 0

    for row in df.index:

        # counts "Performance, Temporal Demand, Frustration, Mental Demand,
        # Effort, Physical Demand
        aspect = ["Mental", "Physical", "Temporal", "Performance", "Effort",
                  "Frustration"]
        weight = [0, 0, 0, 0, 0, 0]

        for col in ['Q12', 'Q13', 'Q14', 'Q15', 'Q16', 'Q17', 'Q18', 'Q19',
                    'Q20', 'Q21', 'Q22', 'Q23','Q24', 'Q25', 'Q26']:

            aspect_index = aspect.index(df[col][row].split()[0])
            weight[aspect_index] += 1

        # error checking
        if sum(weight) != 15:
            print("ERROR weights are not equal to 15")

        # TLX subscales headers
        subscales = ["Q2_1", "Q8_1", "Q7_1", "Q9_1", "Q10_1", "Q11_1"]

        # multiply counts by ratings (Q2_1	Q8_1 Q7_1 Q9_1 Q10_1 Q11_1)
        adjusted_rating = [0, 0, 0, 0, 0, 0]
        for i in range(6):
            adjusted_rating[i] = weight[i] * int(df[subscales[i]][row])

        # stores TLX scores and adjusted rates on the data frame
        df.loc[row, 'TLX'] = round((sum(adjusted_rating)/15), 2)
        for i in range(6):
            df.loc[row, df_headers[i+tlx_index+1]] = adjusted_rating[i]


def run_python_analysis(source_codes, paths):
    """
    Runs static analysis on the Python source codes.
    Returns the analysis results as a list.

    Args:
        source_codes:
            Source codes to analyze.
        paths:
            Paths containing the source codes.

    Returns:
        The analysis results.
    """

    style_errors = mt.check_style_error(paths)
    raw_metrics = mt.compute_raw_metrics(source_codes)
    cc = mt.compute_cyclomatic_complexity(source_codes)
    mi = mt.compute_maintainability(source_codes)
    halstead = mt.compute_halstead(source_codes)
    cognitive = mt.compute_cognitive_complexity(source_codes)

    return [style_errors, raw_metrics, cc, mi, halstead, cognitive]


def run_java_analysis(files):
    """
    Runs static analysis on the Java source codes.  Stores the number of
    violations and cognitive complexities from PMD analysis; stores multimetric
    results for static code metrics.  Finally, returns the analysis results.

    Args:
        files:
            Java file directories containing the Java source codes.

    Returns:
        The static analysis results.
    """

    violations, complexities = mt.run_pmd()
    multimetric = mt.run_multimetric(files)

    return [violations, multimetric, complexities]


def parse_python_analysis(results, analysis):
    """
    Parses the Python static analysis results in the order of headers list.
    Then, stores the parsed results in the given list of results.
    Finally, returns the list of parsed results.

    Args:
        results:
            List to store the analysis results for the data frame.
        analysis:
            Analysis results.

    Returns:
        Parsed analysis results.
    """

    results[0] = analysis[1][0]  # loc
    results[1] = analysis[1][4]  # comments ratio
    results[2] = analysis[0]  # code style errors
    results[3] = round(results[2]/results[0], 2)  # style errors per loc

    # parses cyclomatic/cognitive, maintainability, and Halstead metrics
    metrics = [*analysis[2], *analysis[3], *analysis[4], *analysis[5]]
    for i in range(len(metrics)):
        results[i+4] = metrics[i]

    # parses the remaining results: lloc, sloc, etc
    for i in range(3):
        results[25+i] = analysis[1][i+1]

    for i in range(4):
        results[28+i] = analysis[1][i+5]

    return results


def parse_java_analysis(results, analysis):
    """
    Parses the Java static analysis results.
    Then, stores the parsed results in the given list of results.
    Finally, returns the list of parsed results.

    Args:
        results:
            List to store the analysis results for the data frame.
        analysis:
            Analysis results.

    Returns:
        Parsed analysis results.
    """

    results[0] = analysis[1][0]  # loc
    results[1] = analysis[1][1]  # comments ratio
    results[2] = analysis[0]  # code style errors
    results[3] = round(results[2]/results[0], 2)  # errors per loc

    # parses cyclomatic complexities
    for i in range(3):
        results[i+4] = analysis[1][i+5]

    # parses maintainability
    for i in range(3):
        results[i+7] = analysis[1][i+2]

    # parses the rest of the metrics
    for i in range(len(analysis[1])-8):
        results[i+10] = analysis[1][i+8]

    # parses the cognitive complexities
    results[22] = statistics.fmean(analysis[2])
    results[23] = min(analysis[2])
    results[24] = max(analysis[2])

    return results


def store_151_analysis(df, path, extension, headers, start):
    """Runs static code analysis on the source codes in the given paths.

    Loops through each file in the given paths and performs static code
    analysis, i.e. cyclomatic complexity, halstead metrics, raw metrics,
    and maintainability of the source codes. Then, stores the analysis results
    on the given data frame.  Finally, returns a csv file generated from
    the data frame.

    Args:
        df:
            The data frame for csv file.
        path:
            File paths of the source codes.
        extension:
            File extension of the source codes.
        headers:
            Data frame headers.
        start:
            Start index for looping.
            CS151 & CS231: 15
            Hamilton: 14
    Returns:
        Dataframe containing the analysis results values.
    """

    for i in range(start, len(headers)-2):
        df[headers[i]] = 0.0

    # extracts usernames
    emails = df["Q4"]
    df["username"] = [email.split('@')[0].lower() for email in emails]

    # perform analysis on each project's source codes
    for row in df.index:

        username = df["username"][row]
        proj_num = df["proj_id"][row]
        code_dir = path + username + "/project_" + str(proj_num) + "/"
        code_files = utils.get_files(code_dir, extension)
        results = [0 for _ in range(start, len(headers)-1)]

        # if source codes exist in the folder, then performs analysis
        if code_files:

            source_codes, paths, skipped = utils.get_source_codes(code_dir,
                                                            code_files)
            results[-1] = skipped
            static_analysis = run_python_analysis(source_codes, paths)
            analysis_results = parse_python_analysis(results, static_analysis)

            # stores analysis results on the data frame
            for i in range(len(headers)-start-1):
                df.loc[row, headers[i+start]] = analysis_results[i]

        # if source codes don't exist, skips to the next row
        else:
            continue

    # drops rows with no analysis results from the dataframe
    new_df = df[df["loc"] > 0].copy()

    return new_df


def store_231_analysis(df, path, extension, headers, start):
    """Runs static code analysis on the source codes in the given paths.

    Loops through each file in the given paths and performs static code
    analysis, i.e. cyclomatic complexity, halstead metrics, raw metrics,
    and maintainability of the source codes. Then, stores the analysis results
    on the given data frame.  Finally, returns a csv file generated from
    the data frame.

    Args:
        df:
            The data frame for csv file.
        path:
            File paths of the source codes.
        extension:
            File extension of the source codes.
        headers:
            Data frame headers.
        start:
            Start index for looping.

    Returns:
        Dataframe with analysis result values.
    """

    for i in range(start, len(headers)-1):
        df[headers[i]] = 0.0

    # extract usernames
    emails = df["Q4"]
    df["username"] = [email.split('@')[0].lower() for email in emails]

    # loops through each row on the data frame to extract the corresponding
    # source codes and perform static code analysis on them
    for row in df.index:

        username = df["username"][row]
        proj_num = df["proj_id"][row]
        code_dir = path + username + "/project_" + str(proj_num) + "/"
        code_files = utils.get_files(code_dir, extension)
        results = [0 for _ in range(start, len(headers)-1)]

        if code_files:

            files = []

            # writes the file path of each java source code for pmd analysis
            f = open('filepaths.txt', 'w')

            for code_file in code_files:
                f.write(code_dir+code_file+'\n')
                files.append(code_dir+code_file)

            f.close()

            java_analysis = run_java_analysis(files)
            analysis_results = parse_java_analysis(results, java_analysis)

            # stores the analysis results on the data frame
            for i in range(len(headers)-start-1):
                df.loc[row, headers[i+start]] = analysis_results[i]

        # if no source codes exist, skips to the next row
        else:
            continue

    # drops rows with no analysis results from the dataframe
    new_df = df[df["loc"] > 0].copy()
    return new_df


def store_hamilton_analysis(df, path, extension, headers, start, sub_num):
    """Runs static code analysis on the source codes in the given paths.

    Loops through each file in the given paths and performs static code
    analysis, i.e. cyclomatic complexity, halstead metrics, raw metrics,
    and maintainability of the source codes. Then, stores the analysis results
    on the given data frame.  Finally, returns a csv file generated from
    the data frame.

    Args:
        df:
            The data frame for csv file.
        path:
            File paths of the source codes.
        extension:
            File extension of the source codes.
        headers:
            Data frame headers.
        start:
            Start index for looping.
        sub_num:
            Submit folder number to analyze the source codes within.
            1: first, -1: last

    Returns:
        Dataframe with analysis result values.
    """

    # initializes the analysis result values
    for i in range(start, len(headers)-2):
        df[headers[i]] = 0.0

    # extracts student folder names to match with usernames
    usernames = [name for name in
                 os.listdir('/Users/alexyu/'
                            'Downloads/Hamilton/hogwarts/students')]

    # performs analysis on each project's source codes
    for row in df.index:

        name = str(df["Q4"][row]).lower()

        # skips the missing names in survey data
        if name == 'nan':
            continue

        username = name.split()[0][0] + name.split()[-1]
        df.loc[row, "username"] = username
        proj_name = df["proj_name"][row].replace(" ", "").lower()
        code_dir = path + proj_name + "/students/"

        # checks if first and last name combinations matches the folder name
        if username in usernames:
            code_dir += username

        # if not, checks again with regular expression
        else:
            r = re.compile(".*"+username[1:]+"*")
            matched = list(filter(r.match, usernames))

            # if no corresponding source code folder found, skips the analysis
            if len(matched) == 0:
                continue
            elif len(matched) == 1:
                code_dir += matched[0]

            # only one case for angelo li
            else:
                code_dir += 'amli'

        # if source code directory exists, counts the number of submissions
        if os.path.isdir(code_dir):

            num_submits = 1  # by default

            # checks which submit folder to analyze
            if sub_num == 1:
                code_dir += "/submit/"

            else:
                num_submits = sum(1 for line in open(code_dir+'/submit-time'))

                if "last-submit" in os.listdir(code_dir):
                    code_dir += "/last-submit/"
                else:
                    code_dir += "/submit-" + str(num_submits-1) + "/"

            df.loc[row, "submit_num"] = num_submits
            code_files = utils.get_files(code_dir, extension)

            # initializes analysis result values
            results = [0 for _ in range(start, len(headers)-1)]

            # checks if code files exist
            if len(code_files) > 0:
                # gets source codes from the given code directory and files
                source_codes, paths, skipped = utils.get_source_codes(code_dir,
                                                                code_files)

            # if source codes don't exist, continues to the next row
            else:
                continue

            # stores the number of skipped files
            results[-1] = skipped

            # checks again if source codes exist after successfully compiling
            if source_codes:

                # runs static analysis and parses the results
                static_analysis = run_python_analysis(source_codes, paths)
                analysis_results = parse_python_analysis(results, static_analysis)

                # store analysis results on the data frame
                for i in range(len(headers)-start-1):
                    df.loc[row, headers[i+start]] = analysis_results[i]

            # if no source codes have been successfully compiled,
            # just stores the initialized result values
            else:
                for i in range(len(headers)-start-1):
                    df.loc[row, headers[i+start]] = results[i]

                continue

        # if source code directory does not exist, skips the analysis
        else:
            continue

    # drops rows with no analysis results from the dataframe
    new_df = df[df["loc"] > 0].copy()

    return new_df
