"""
@Author: Alex Yu
@Created: 7/12/22
@Last Modified: 7/22/22

Contains helper functions for managing dataframes and running static analysis
"""

import pandas as pd
import os
import ast


def create_dataframe(survey, experiment_id, language):
    """Creates a dataframe from a csv file of the given path.

    Creates a dataframe from a csv file and initializes
    some headers with the given parameters.

    Args:
        survey:
            Source path of the task survey data to read.
        experiment_id:
            Experiment id for data frame.
        language:
            Programming language for the data frame.

    Returns:
        The data frame generated from the csv file.
    """

    df = pd.read_csv(survey)

    # filters the participants with complete survey
    new_df = df[df.Progress == "100"].copy()

    new_df["experiment_id"] = experiment_id
    new_df["proj_id"] = new_df["Project Number"].astype(int)
    new_df["proj_name"] = new_df["Q5"]
    new_df["gender"] = new_df["Gender"]
    new_df["race"] = new_df["Race"]
    new_df["language"] = language

    if experiment_id != "Hamilton_Fall20":
        new_df["lab_completed"] = new_df["Q28"]

    return new_df


def get_files(code_dir, extension):
    """
    Extracts Python or java files from the given code directory.

    Reference:
        TLX-preprocessing.ipynb

    Args:
        code_dir:
            Code directory containing the source codes.
        extension:
            File extension to distinguish between Python and Java.

    Returns:
        Python or Java source codes.
    """

    code_files = []

    # checks extension to determine proper index for slicing
    start = -3
    if extension == '.java':
        start = -5

    for root, dirs, files in os.walk(code_dir):
        for file in files:
            if file[start:] == extension and file[0] != '.':

                # checks for authority files to skip
                if extension == '.py' and 'authority' in file:
                    continue

                rel_dir = os.path.relpath(root, code_dir)

                # checks if file is in a subdirectory
                if rel_dir != '.':
                    code_files.append(os.path.join(rel_dir, file))
                else:
                    code_files.append(file)

    return code_files


def create_csv(df, headers, path, name):
    """ Creates a csv from the given data frame and stores the csv in the given
        path with the given name.

    Args:
        df:
            Dataframe to read in and convert into a csv file.
        headers:
            Dataframe headers to convert into a csv file.
        path:
            Path to store the csv file.
        name:
            Name for the csv file.

    Returns:
        None.
    """

    # sets the current directory to the specified path
    os.chdir(path)

    # converts the data frame to csv file with the given name
    df[headers].to_csv(name, index=False)


def get_source_codes(code_dir, code_files):
    """Extracts source codes from the given source code directory and stores the
       source codes, the corresponding paths, and the number of source codes
       that can't be compiled due to syntax error.

    Args:
        code_dir:
            Code directory of the source code.
        code_files:
            List of the code files containing source codes.

    Returns:
        List containing the list of source codes, paths, and the number of
        skipped source codes.
    """

    # initializes the variables to return
    source_codes = []
    paths = []
    skipped = 0

    for code_file in code_files:

        # reads in the source code
        code = open(code_dir + code_file, encoding="utf-8")
        source_code = code.read()

        # checks if source code can be compiled
        try:
            ast.parse(source_code)
        except SyntaxError:
            skipped += 1
            continue

        # stores the source codes and paths
        source_codes.append(source_code)
        paths.append(code_dir+code_file)

    return [source_codes, paths, skipped]


def delete_files(dir, extension, exception=None):
    """ Deletes all files that do not have the given extension from the given
        directory.

    Args:
        dir:
            Directory to search and delete files.
        extension:
            File extension to keep in the directory.
        exception:
            Files to exclude from deleting.
    Returns:
        None.
    """

    for root, dirs, files in os.walk(dir):
        for file in files:
            if exception:
                if file != 'submit-time' and not file.endswith(extension):
                    rel_dir = os.path.relpath(root, dir)

                    if rel_dir != '.':
                        os.remove(os.path.join(dir+rel_dir, file))
                    else:
                        os.remove(os.path.join(dir, file))

            else:
                if not file.endswith(extension):
                    rel_dir = os.path.relpath(root, dir)

                    if rel_dir != '.':
                        os.remove(os.path.join(dir+rel_dir, file))
                    else:
                        os.remove(os.path.join(dir, file))


def generate_id(df, header1, header2):
    """ Generates participant ids from the header column in the given dataframe.

    Args:
        df:
            Dataframe to generate participant ids for.
        header1:
            Header to store participant ids.
        header2:
            Header to extract usernames to generate participant ids.

    Returns:
        None.
    """
    d = {}
    count = 0

    for name in df[header2]:
        if name not in d:
            count += 1
            d[name] = count

    print('Total number of students: ', count)
    df[header1] = [d[name] for name in df[header2]]