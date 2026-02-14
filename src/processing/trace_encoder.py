import pandas as pd
from ast import literal_eval
from new_function_name_cluster import read_data, classify_new_function_names
import csv
import os
from simple_loop import simplify_sequence_with_loops
from dtw_similarity import load_data

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

    # 1. 动态计算路径
    # 获取 src/processing 目录
    current_dir = os.path.dirname(os.path.abspath(__file__)) 
    # 获取根目录
    project_root = os.path.dirname(os.path.dirname(current_dir)) 
    # 获取数据目录 data_rules_related
    data_dir = os.path.join(project_root, 'data_rules_related')

    # 2. 定义所有文件的完整绝对路径
    # 输入文件
    cleaned_vectors_path = os.path.join(data_dir, 'cleaned_attack_vectors.csv')
    clusters_path = os.path.join(data_dir, 'final_classified_functions.csv')
    encoded_trace_path = os.path.join(data_dir, 'encoded_trace.csv')
    
    # 输出文件
    output_csv_path = os.path.join(data_dir, 'noloop_encoded_trace.csv')

    attack_id, address, function_name, function_params = read_data_frame(cleaned_vectors_path)
    clusters, remaining_non_cluster, unique_non_cluster, model, centroids = read_data(clusters_path)
    with open(output_csv_path, mode='a') as attack_vectors_file:
        attack_vectors_writer = csv.writer(attack_vectors_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        attack_vectors_writer.writerow(['id', 'encoded_trace'])
        #encoded_df = load_data(encoded_trace_path)
        for i in range(484, len(function_name)):
            encoded_sequence = encode_trace(literal_eval(function_name[i]), clusters, remaining_non_cluster, unique_non_cluster, model, centroids)
            #encoded_sequence = encoded_df['encoded_trace'][i]
            address_list = literal_eval(address[i])
            merged_sequence = [(single_address, *entry) for single_address, entry in zip(address_list, encoded_sequence)]
            no_loop_sequence = simplify_sequence_with_loops(merged_sequence)
            extracted_values = [(entry[1], entry[2]) for entry in no_loop_sequence]
            
            attack_vectors_writer.writerow([attack_id[i], extracted_values])
            print(str(i) + ' done')
            
            # ================= 🛑 这里的修改 🛑 =================
            # 当 i 等于 488 时，强制退出循环
            if i == 488:
                print("🎉 已到达 488，测试结束，停止运行。")
                break
            # ===================================================
