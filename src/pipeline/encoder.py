import pandas as pd
from ast import literal_eval
from core.function_cluster import read_data, classify_new_function_names
import csv
from core.loop import simplify_sequence_with_loops
from core.similarity import load_data
import config

def read_data_frame(path):
    df = pd.read_csv(path)
    return df['id'], df['address'], df['function_name'], df['function_params']


def encode_trace(function_name_vector, clusters, remaining_non_cluster, unique_non_cluster, model, centroids):
    encoded_function_sequence = []
    for i in range(len(function_name_vector)):
        encoded_function_name = classify_new_function_names(function_name_vector[i], clusters, remaining_non_cluster, unique_non_cluster, model, centroids)
        encoded_function_sequence.append(encoded_function_name)
    return encoded_function_sequence

if __name__ == '__main__':
    attack_id, address, function_name, function_params = read_data_frame('cleaned_attack_vectors.csv')
    clusters, remaining_non_cluster, unique_non_cluster, model, centroids = read_data(str(config.FINAL_CLASSIFIED_FUNCTIONS))
    with open(str(config.NOLOOP_ENCODED_TRACE), mode='a') as attack_vectors_file:
        attack_vectors_writer = csv.writer(attack_vectors_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        encoded_df = load_data(str(config.ENCODED_TRACE))
        for i in range(484, len(function_name)):
            # encoded_sequence = encode_trace(literal_eval(function_name[i]), clusters, remaining_non_cluster, unique_non_cluster, model, centroids)
            encoded_sequence = encoded_df['encoded_trace'][i]
            address_list = literal_eval(address[i])
            merged_sequence = [(single_address, *entry) for single_address, entry in zip(address_list, encoded_sequence)]
            no_loop_sequence = simplify_sequence_with_loops(merged_sequence)
            extracted_values = [(entry[1], entry[2]) for entry in no_loop_sequence]

            # attack_vectors_writer.writerow([attack_id[i], extracted_values])
            print(str(i) + ' done')
