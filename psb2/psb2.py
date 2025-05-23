"""
PSB2 - The Second Program Synthesis Benchmark Suite
"""

import os
import json
import random
import requests
import itertools
import sys
from pathlib import Path

def objects2lines(objects):
    lines = []
    for object in objects:
        if isinstance(object, list):
            lines.append(str(len(object)))
            lines.append(' '.join(map(str, object)))
        else:
            lines.append(str(object))
    return lines

def disnumerate_prefix(data, prefix):
    lines = []
    for line_number in itertools.count(start=1):
        try:
            lines.append(data[f'{prefix}{line_number}'])
        except KeyError:
            break
    return lines

def format_test_case(test_case, format):
    """
    Represents a test case in one of 3 formats: 'psb2', 'lists' or 'competitive'

    'psb2' format is a dictionary with keys 'input{i}' and 'output{i}'
        indicating ith input and output, respectively.
        Ex: {'input1': 1, 'input2': 2, 'output1': 'output'}
    'lists' format is a list of tuple of the form (input, output)
        where input and output are lists of objects.
        Ex: [(1, 2), ('output')]
    'competitive' format is the defacto standard format in competitive programming.
        It has the same structure as 'lists', but all inputs and outputs are strings
        corresponding to input and output lines
        Besides, every array/list input/output is represented with 2 lines:
        array length and array elements
    """

    if format == 'psb2':
        return test_case
    else:
        input_objs, output_objs = (disnumerate_prefix(test_case, prefix) 
                                   for prefix in ('input', 'output'))

        if format == 'lists':
            return (input_objs, output_objs)
        elif format == 'competitive':
            return (objects2lines(input_objs), objects2lines(output_objs))

    raise ValueError(f'Unknown format: {format}')

PROBLEMS = ["basement",
            "bouncing-balls",
            "bowling",
            "camel-case",
            "coin-sums",
            "cut-vector",
            "dice-game",
            "find-pair",
            "fizz-buzz",
            "fuel-cost",
            "gcd",
            "indices-of-substring",
            "leaders",
            "luhn",
            "mastermind",
            "middle-character",
            "paired-digits",
            "shopping-list",
            "snow-day",
            "solve-boolean",
            "spin-words",
            "square-digits",
            "substitution-cipher",
            "twitter",
            "vector-distance"]

def load_json_lines(filename):
    """Load edn from a filename. Expects file to have multiple lines of JSON."""

    data = []
    with open(filename) as f:
        for line in f:
            example = json.loads(line)
            data.append(example)

    return data

def fetch_and_possibly_cache_data(datasets_directory, problem_name, edge_or_random):
    """Helper function for fetch_examples that does the following for edge or
    random dataset:
    1. Checks if JSON file for dataset is already downloaded.
    2. If not, downloads the dataset file to the specified location.
    3. Loads and returns list of the data from the dataset file.
    """

    # Make directory path and file path
    directory_path = os.path.join(datasets_directory, "datasets", problem_name)
    file_path = os.path.join(directory_path, "{}-{}.json".format(problem_name, edge_or_random))

    # Make directories if necessary
    if not os.path.isdir(directory_path):
        os.makedirs(directory_path)

    # 1. Check if JSON file already exists
    if not os.path.isfile(file_path):
        # Make URL
        problem_url = "{}/{}-{}.json".format(problem_name, problem_name, edge_or_random)
        s3_url = "https://psb2-datasets.s3.amazonaws.com/PSB2/datasets/{}".format(problem_url)

        # 2. Download dataset file
        fetched_data = requests.get(s3_url)
        with open(file_path, 'wb') as data_file:
            data_file.write(fetched_data.content)

    # 3. Load and return dataset
    dataset = load_json_lines(file_path)
    return dataset


def fetch_examples(datasets_directory, problem_name, n_train, n_test, format='psb2', seed=None):
    """Downloads, fetches, and returns training and test data from a PSB2 problem.
    Caches downloaded datasets in `datasets_directory` to avoid multiple downloads.
    Returns a tuple of the form (training_examples testing_examples)
    where training-examples and testing-examples are lists of training and test
    data. The elements of these lists are dictionaries of the form:
    {'input1': first_input, 'input2': second_input, ..., "output1": first_output, ...}
    The training examples will include all hard-coded edge cases included in the suite,
    along with enough random cases to include `n-train` cases. The test examples
    will including a random sample of the random cases.
    Note that this function downloads and loads large datasets and can
    be slow, up to 1 minute.
    Parameters:
        `datasets_directory` - Location to download the PSB2 datasets.
        `problem_name` - Name of the PSB2 problem, lowercase and seperated by dashes.
            - Ex: indices-of-substring
        `n_train` - Number of training cases to return
        `n_test` - Number of test cases to return
        `format` - 'psb2', 'lists' or 'competitive'
        `seed` - Seed for random. Uses default random.seed behavior if no value is provided"""

    # Cannot sample more than 1 million examples for train or test
    assert n_train < 1000000, "Cannot sample more than 1 million examples"
    assert n_test < 1000000, "Cannot sample more than 1 million examples"

    # Load data
    edge_data = fetch_and_possibly_cache_data(datasets_directory, problem_name, "edge")
    random_data = fetch_and_possibly_cache_data(datasets_directory, problem_name, "random")

    # Seed RNG source
    random.seed(seed)

    # Make training and test sets
    if n_train < len(edge_data):
        train = random.sample(edge_data, n_train)
    else:
        train = edge_data
        train.extend(random.sample(random_data, n_train - len(edge_data)))

    test = random.sample(random_data, n_test)

    train = [format_test_case(test_case, format) for test_case in train]
    test = [format_test_case(test_case, format) for test_case in test]

    return (train, test)

def get_problem_names():
    """Returns a list of strings of the problem names in PSB2."""
    return PROBLEMS

if __name__ == "__main__":
    if Path.cwd().name != "rush":
        print("This script is not ran in the root folder of rush, do you want to continue with the download process? (y/n): ")
        user_input = input()
        if user_input != "y":
            sys.exit()

    for problem in PROBLEMS:
        temp_path = Path("psb2/")
        print(f"downloading {problem}")
        fetch_examples(str(temp_path), problem, 200, 2000)
