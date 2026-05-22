import json
import os
import re
import csv

def read_structured_trace(file_path):
    # read json file
    with open(file_path, 'r') as f:
        structured_trace = json.load(f)
    return structured_trace

def read_structured_traces(directory, start_file=None, end_file=None):
    # read all json files in the directory
    structured_traces = []
    files = os.listdir(directory)
    files = [f for f in files if f.endswith('.json')]
    if start_file:
        files = files[files.index(start_file):]
    if end_file:
        files = files[:files.index(end_file)+1]
    for file in files:
        structured_trace = read_structured_trace(directory + file)
        structured_traces.append(structured_trace)
    return structured_traces

# Preorder traversal (root -> children recursively)
def preorder_traversal(json_obj):
    result = []
    if "content" in json_obj:
        result.append(json_obj["content"])  # Visit the root
    if "children" in json_obj:
        for child in json_obj["children"]:
            result.extend(preorder_traversal(child))  # Recursively traverse children
    return result

def preorder_traversal_ignore_static_call_children(json_obj):
    result = []
    if "content" in json_obj:
        if '[staticcall]' in json_obj["content"]:
            return result
        result.append(json_obj["content"])  # Visit the root
    if "children" in json_obj:
        for child in json_obj["children"]:
            result.extend(preorder_traversal_ignore_static_call_children(child))  # Recursively traverse children
    return result

def separate_content(line):
    # Split the line through the spaces
    parts = re.split(r"(\{|\(|\s)", line)
    parts = [part for part in parts if part.strip()]
    # find the part with '::', and separate the content before and after '::'
    for i, part in enumerate(parts):
        if '::' in part:
            address = part.split('::')[0]
            function_name = part.split('::')[1].split('(')[0]


            function_params = ''

            for j in range(i+1, len(parts)):
                function_params = function_params+parts[j]

            return (address, function_name, function_params)

    return (None, None, None)


def separate_content_lines(lines):
    # Separate the content of each line
    separated_lines = []
    for line in lines:
        separated_lines.append(separate_content(line))
    return separated_lines

def create_csv_file():
    # create a csv file with 4 columns: attack_id(contract name), address_vector, function_name_vector, function_params_vector
    with open('attack_vectors.csv', mode='w') as attack_vectors_file:
        attack_vectors_writer = csv.writer(attack_vectors_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        attack_vectors_writer.writerow(['id', 'address', 'function_name', 'function_params'])

def write_csv_file(id, address_vector, function_name_vector, function_params_vector):
    with open('attack_vectors.csv', mode='a') as attack_vectors_file:
        attack_vectors_writer = csv.writer(attack_vectors_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        # for i in range(len(address_vector)):
        attack_vectors_writer.writerow([id, address_vector, function_name_vector, function_params_vector])

def separate_attack_vector(attack_vector):
        address_vector = []
        function_name_vector = []
        function_params_vector = []
        for variable in attack_vector:
            if variable[0] is not None:
                address_vector.append(variable[0])
                function_name_vector.append(variable[1])
                function_params_vector.append(variable[2])
        return address_vector, function_name_vector, function_params_vector

def extract_path_id(file_path):
    # Extract the id from the file path
    if '_' in file_path:
        id = file_path.split('/')[-1].split('_')[0]
        return id
    else:
        id = file_path.split('/')[-1].split('.')[0]
        return id

def pipeline_parse_json_trace():
    directory = './structured_traces/'
    files = os.listdir(directory)
    files = [f for f in files if f.endswith('.json')]
    create_csv_file()

    for path in files:
        json_trace = read_structured_trace(directory+path)
        contents = preorder_traversal_ignore_static_call_children(json_trace)
        attack_vector = separate_content_lines(contents)
        (address_vector, function_name_vector, function_params_vector) = separate_attack_vector(attack_vector)
        write_csv_file(extract_path_id(path), address_vector, function_name_vector, function_params_vector)


if __name__ == '__main__':
    pipeline_parse_json_trace()
