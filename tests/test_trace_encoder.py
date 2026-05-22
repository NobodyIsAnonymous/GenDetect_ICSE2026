from pipeline.encoder import read_data_frame, encode_trace
from core.function_cluster import read_data
from ast import literal_eval
import timeit
import csv
import pandas as pd
import config

def test_read_cleaned_frame():
    attack_ids, addresses, func_names, func_params = read_data_frame(str(config.DATA_RULES_DIR / 'cleaned_attack_vectors.csv'))
    addresses = [literal_eval(address) for address in addresses]
    func_names = [literal_eval(func_name) for func_name in func_names]
    func_params = [literal_eval(func_param) for func_param in func_params]
    assert attack_ids[0] == 'SellToken'
    assert addresses[1][0] =='ContractTest'
    assert func_names[2][1] == 'swap'
    assert func_params[10] == ['()']
    

def test_encode_trace():
    clusters, remaining_non_cluster, unique_non_cluster, model, centroids = read_data(str(config.FINAL_CLASSIFIED_FUNCTIONS))
    attack_ids, addresses, func_names, func_params = read_data_frame(str(config.DATA_RULES_DIR / 'cleaned_attack_vectors.csv'))
    addresses = [literal_eval(address) for address in addresses]
    func_names = [literal_eval(func_name) for func_name in func_names]
    func_params = [literal_eval(func_param) for func_param in func_params]
    
    encoded_trace = encode_trace(func_names[0], clusters, remaining_non_cluster, unique_non_cluster, model, centroids)

def test_encode_trace_time():
    # 加载数据
    clusters, remaining_non_cluster, unique_non_cluster, model, centroids = read_data(str(config.FINAL_CLASSIFIED_FUNCTIONS))
    attack_ids, addresses, func_names, func_params = read_data_frame(str(config.DATA_RULES_DIR / 'cleaned_attack_vectors.csv'))

    # 解析字符串为列表
    func_names = [literal_eval(func_name) for func_name in func_names]

    results = []

    for trace in func_names:
        trace_len = len(trace)

        # 用 lambda 封装 encode_trace 的调用
        stmt = lambda: encode_trace(trace, clusters, remaining_non_cluster, unique_non_cluster, model, centroids)

        # 使用 timeit 重复执行多次求平均
        duration = timeit.timeit(stmt, number=3)
        avg_duration = duration / 3

        results.append({
            'trace_length': trace_len,
            'avg_time_seconds': avg_duration
        })

    # 写入 CSV 文件
    df = pd.DataFrame(results)
    df.to_csv('encode_trace_runtime.csv', index=False)
    print("✅ 已保存为 encode_trace_runtime.csv")