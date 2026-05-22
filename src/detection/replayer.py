# Example of running a transaction with Cast
# cast run -v -q 0xc5215eb1d9c63373a02a013105b9f6745df1c935bb5c25817423b947be8d3aea --rpc-url mainnet > trace_example.log

# Example of running a scripted transaction with Forge
# forge test --contracts ./src/test/2024-10/MorphoBlue_exp.sol -vvvv --evm-version shanghai > test_trace_example.log

# run all the tests and save the output to ../traces/<test_name>.log

import subprocess
import json
import os
from pipeline.runner import parse_trace_lines
from pipeline.parser import preorder_traversal_ignore_static_call_children, separate_content_lines, separate_attack_vector
from core.function_cluster import read_data, classify_new_function_names
from core.loop import simplify_sequence_with_loops
from core.similarity import edit_similarity, load_data
import pandas as pd
import multiprocessing
from glob import glob
import logging
import csv
from tqdm import tqdm
import ast
import argparse
import config


class Replayer:

    def __init__(self, network='mainnet'):
        self.network = network
        # with open('/home/bowen/Github/GenDetect/dune_tx/signature.json', 'r') as f:
        #     signature_data = json.load(f)
        # self.hash_to_signature = {item["hash"]: item["signature"] for item in signature_data}
        self.no_loop_rule_file = str(config.NOLOOP_ENCODED_TRACE)
        self.clusters, self.remaining_non_cluster, self.unique_non_cluster, self.model, self.centroids = read_data(str(config.FINAL_CLASSIFIED_FUNCTIONS))
        self.trace_rules_df = load_data(self.no_loop_rule_file)
        self.logger = None
        self._setup_logging()

    def _setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[
                logging.FileHandler(str(config.ERROR_LOG)),  # 将日志写入文件
                logging.StreamHandler()           # 同时输出到控制台
            ]
        )
        self.logger = logging.getLogger(__name__)

    def multi_process_es_data_matcher_start(self):
        os.environ["OMP_NUM_THREADS"] = "3"
        multiprocessing.set_start_method("spawn", force=True)
        with multiprocessing.Pool(processes=60) as pool:
            pool.starmap(
                self.offline_match_tx_trace,
                [(file, ) for file in self.es_files]
            )
        print("All files processed.")

    def multi_process_replayer_start(self):
        os.environ["OMP_NUM_THREADS"] = "1"
        multiprocessing.set_start_method("spawn", force=True)
        with multiprocessing.Pool(processes=40) as pool:
            pool.starmap(
                self.process_file,
                [(file, ) for file in self.files]
            )
        print("All files processed.")

    def replay_tx(self, hash):
        # Run the transaction with Forge
        tx_hash = hash
        # forge_cmd = f"cast run -v -q {tx_hash} --rpc-url {self.network} > tx_replay_example.log"
        forge_cmd = f"cast run -vvvv --quick {tx_hash} --rpc-url {self.network} -j 1"

        try:
            result = subprocess.run(forge_cmd, shell=True, check=True, capture_output=True, text=True)
            return result.stdout
        except Exception as e:
            print(f"Error running forge command: {e}")
            return result.stderr

    def deLoop(self, address_list, encoded_sequence):
        merged_sequence = [(single_address, *entry) for single_address, entry in zip(address_list, encoded_sequence)]
        no_loop_sequence = simplify_sequence_with_loops(merged_sequence)
        extracted_values = [(entry[1], entry[2]) for entry in no_loop_sequence]
        return extracted_values

    def vectorize_tx(self, tx_hash):
        result = self.replay_tx(tx_hash)
        lines = [line[2:] if line.startswith('  ') else line for line in result.splitlines()][1:-5]
        json_trace = parse_trace_lines(lines)
        contents = preorder_traversal_ignore_static_call_children(json_trace)
        attack_vector = separate_content_lines(contents)
        (address_vector, function_name_vector, function_params_vector) = separate_attack_vector(attack_vector)
        return address_vector, function_name_vector, function_params_vector

    @staticmethod
    def eliminate_static_calls(type_vector, address_vector, function_name_vector, function_params_vector):
        new_address_vector = []
        new_function_name_vector = []
        new_function_params_vector = []
        for i in range(len(type_vector)):
            if type_vector[i] != 250:
                new_address_vector.append(address_vector[i])
                new_function_name_vector.append(function_name_vector[i])
                new_function_params_vector.append(function_params_vector[i])
        return new_address_vector, new_function_name_vector, new_function_params_vector

    def most_similar_rule(self, tx_hash, address_vector, function_name_vector, function_params_vector):
        encoded_function_sequence = []
        for i in range(len(function_name_vector)):
            encoded_function_name = classify_new_function_names(function_name_vector[i], self.clusters, self.remaining_non_cluster, self.unique_non_cluster, self.model, self.centroids)
            encoded_function_sequence.append(encoded_function_name)
        no_loop_sequence = self.deLoop(address_vector, encoded_function_sequence)
        similarity_list = []
        for i in range(len(self.trace_rules_df)):
            known_sequence = self.trace_rules_df['encoded_trace'][i]
            similarity = edit_similarity(no_loop_sequence, known_sequence)
            similarity_list.append((i, similarity))
        similarity_list.sort(key=lambda x: x[1])
        new_row = pd.DataFrame([{'tx_hash': tx_hash, 'rule_id_1': similarity_list[-1][0],
                                                                'similarity_1': similarity_list[-1][1], 'rule_name_1': self.trace_rules_df['id'][similarity_list[-1][0]],
                                                            'rule_id_2': similarity_list[-2][0],
                                                                'similarity_2': similarity_list[-2][1], 'rule_name_2': self.trace_rules_df['id'][similarity_list[-2][0]]}])
        return new_row

    def offline_match_tx_trace(self, es_data_file):
        # read the data from the es_data_file
        new_rows = []
        es_data = pd.read_csv(es_data_file)
        columns_to_convert = ['CallTypes', 'FunctionNames', 'ContractAddresses', 'ContractParams']
        for column in columns_to_convert:
            es_data[column] = es_data[column].apply(ast.literal_eval)

        tx_hashes = es_data['TransactionHash'].tolist()
        for i in tqdm(range(len(tx_hashes)), desc=f"Processing {es_data_file}"):
            type_vector, function_name_vector, address_vector, function_params_vector = es_data['CallTypes'][i], es_data['FunctionNames'][i], es_data['ContractAddresses'][i], es_data['ContractParams'][i]
            new_address_vector, new_function_name_vector, new_function_params_vector = Replayer.eliminate_static_calls(type_vector, address_vector, function_name_vector, function_params_vector)
            new_row = self.most_similar_rule(tx_hashes[i], new_address_vector, new_function_name_vector, new_function_params_vector)
            new_rows.append(new_row)

        output_file = f"{self.output_dir}processed_{os.path.basename(es_data_file)}"
        pd.concat(new_rows, ignore_index=True).to_csv(output_file, index=False)
        print(f"Processed {es_data_file} and saved to {output_file}")

    def match_tx_trace(self, tx_hash):
        (address_vector, function_name_vector, function_params_vector) = self.vectorize_tx(tx_hash)

        encoded_function_sequence = []
        for i in range(len(function_name_vector)):
            encoded_function_name = classify_new_function_names(function_name_vector[i], self.clusters, self.remaining_non_cluster, self.unique_non_cluster, self.model, self.centroids)
            encoded_function_sequence.append(encoded_function_name)
        no_loop_sequence = self.deLoop(address_vector, encoded_function_sequence)
        similarity_list = []
        for i in range(len(self.trace_rules_df)):
            known_sequence = self.trace_rules_df['encoded_trace'][i]
            similarity = edit_similarity(no_loop_sequence, known_sequence)
            similarity_list.append((i, similarity))
        similarity_list.sort(key=lambda x: x[1])
        new_row = pd.DataFrame([{'tx_hash': tx_hash, 'rule_id_1': similarity_list[-1][0],
                                                                'similarity_1': similarity_list[-1][1], 'rule_name_1': self.trace_rules_df['id'][similarity_list[-1][0]],
                                                            'rule_id_2': similarity_list[-2][0],
                                                                'similarity_2': similarity_list[-2][1], 'rule_name_2': self.trace_rules_df['id'][similarity_list[-2][0]]}])

        return new_row

    def add_new_rule(self, tx_hash, rule_name):
        print(f"Adding new rule for tx {tx_hash} trace...")
        (address_vector, function_name_vector, function_params_vector) = self.vectorize_tx(tx_hash)

        encoded_function_sequence = []
        for i in range(len(function_name_vector)):
            encoded_function_name = classify_new_function_names(function_name_vector[i], self.clusters, self.remaining_non_cluster, self.unique_non_cluster, self.model, self.centroids)
            encoded_function_sequence.append(encoded_function_name)
        extracted_values = self.deLoop(address_vector, encoded_function_sequence)

        with open(self.no_loop_rule_file, mode='a', newline='') as attack_vectors_file:
            attack_vectors_writer = csv.writer(attack_vectors_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            attack_vectors_writer.writerow([rule_name, extracted_values])


def main():
    parser = argparse.ArgumentParser(description='Transaction Replayer - Match transaction traces or add new rules')

    # Global options with example values
    parser.add_argument('--network', default='mainnet',
                       help='Network name - options: mainnet, polygon, bsc, etc. (default: mainnet)')

    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Match command - for matching transaction traces against existing rules
    match_parser = subparsers.add_parser('match', help='Match transaction trace against existing rules')
    match_parser.add_argument('tx_hash', help='Transaction hash to match (e.g., 0x1106418384414ed56cd7cbb9fedc66a02d39b663d580abc618f2d387348354ab)')

    # Add-rule command - for adding new attack pattern rules
    add_rule_parser = subparsers.add_parser('add-rule', help='Add new attack pattern rule')
    add_rule_parser.add_argument('tx_hash', help='Transaction hash (e.g., 0xabc123...)')
    add_rule_parser.add_argument('rule_name', help='Rule name (e.g., "FlashLoan_Attack", "Reentrancy_Exploit")')

    args = parser.parse_args()

    # Initialize data and model
    # IMPORTANT: Connect to ES database SSH tunnel before running this script!!!
    replayer = Replayer(
        network=args.network,      # e.g., 'mainnet', 'polygon', 'bsc'
    )

    if args.command == 'match':
        print(f"Matching transaction trace: {args.tx_hash}")
        result = replayer.match_tx_trace(args.tx_hash)
        print(result)
    elif args.command == 'add-rule':
        print(f"Adding new rule - TX Hash: {args.tx_hash}, Rule Name: {args.rule_name}")
        replayer.add_new_rule(args.tx_hash, args.rule_name)
        print(f"Successfully added rule: {args.rule_name}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
