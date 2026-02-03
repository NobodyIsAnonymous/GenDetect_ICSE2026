from tslearn.metrics import dtw
from sentence_transformers import SentenceTransformer
import pandas as pd
from ast import literal_eval
import numpy as np
import os
import sys
import Levenshtein as lev
from scipy.cluster.hierarchy import linkage, dendrogram, fcluster
import matplotlib.pyplot as plt

# 1. 获取当前脚本所在目录 (src/analysis)
current_dir = os.path.dirname(os.path.abspath(__file__))
# 2. 获取 src 目录
src_dir = os.path.dirname(current_dir)
# 3. 获取项目根目录 (ICSE2026Anonym-main)
project_root = os.path.dirname(src_dir)
# 4. 定义数据目录
DATA_DIR = os.path.join(project_root, 'data_rules_related')

# 初始化 SentenceTransformer 模型
model = SentenceTransformer('all-MiniLM-L6-v2')

def embed_sequence(sequence):
    """
    将序列 (tag, name) 转换为嵌入向量。
    """
    return [model.encode(f"{tag}:{name}") for tag, name in sequence]

def calculate_dtw_distance(seq1, seq2):
    """
    使用 tslearn.metrics.dtw 计算两嵌入序列之间的 DTW 距离。
    """
    vec_seq1 = np.array(embed_sequence(seq1))
    vec_seq2 = np.array(embed_sequence(seq2))
    
    # 使用 tslearn.metrics.dtw 计算多维嵌入序列的距离
    distance = dtw(vec_seq1, vec_seq2)
    return distance

# 加载数据
def load_data(file_path):
    df = pd.read_csv(file_path)
    df['encoded_trace'] = df['encoded_trace'].apply(literal_eval)  # 转换字符串为 Python 对象
    return df

def calculate_all_dtw(path, start_i, start_j):
    # 加载数据
    df = load_data(path)
    trace_id_list_1 = []
    trace_id_list_2 = []
    distance_list = []

    result_file = os.path.join(DATA_DIR, 'dtw_similarity.csv')
    if os.path.exists(result_file):
        existing_results = pd.read_csv(result_file)
    else:
        existing_results = pd.DataFrame(columns=['trace_id_1', 'trace_id_2', 'distance'])

    # 获取当前结果中最大的 i 和 j（如果需要，可以优化逻辑）
    try:
        for i in range(start_i, len(df)):
            for j in range(start_j if i == start_i else i, len(df)):
                trace1 = df['encoded_trace'][i]
                trace2 = df['encoded_trace'][j]
                distance = calculate_dtw_distance(trace1, trace2)
                trace_id_list_1.append(df['id'][i])
                trace_id_list_2.append(df['id'][j])
                distance_list.append(distance)
                print(f"Calculated distance for {i} and {j}")
    except KeyboardInterrupt:
        print("Saving current progress...")
    finally:
        new_results = pd.DataFrame({'trace_id_1': trace_id_list_1, 'trace_id_2': trace_id_list_2, 'distance': distance_list})
        combined_results = pd.concat([existing_results, new_results], ignore_index=True)
        combined_results.to_csv(result_file, index=False)

def calculate_edit_distance(seq1, seq2):
    """
    计算两序列之间的编辑距离
    """
    # 将元组序列转换为字符串表示，以便计算编辑距离
    str1 = " ".join([f"{x[0]}:{x[1]}" for x in seq1])
    print(str1)
    str2 = " ".join([f"{x[0]}:{x[1]}" for x in seq2])
    return lev.distance(str1, str2)

def tuple_edit_distance(seq1, seq2):
    """
    计算两元组序列之间的插入距离。
    
    Args:
        seq1 (list of tuple): 第一个元组序列。
        seq2 (list of tuple): 第二个元组序列。
    
    Returns:
        int: 两序列的插入距离。
    """
    m, n = len(seq1), len(seq2)
    
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    # 初始化DP表
    for i in range(m + 1):
        dp[i][0] = i  # seq1 的所有元素都删除
    for j in range(n + 1):
        dp[0][j] = j  # seq2 的所有元素都插入

    # 填充DP表
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if seq1[i - 1] == seq2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]  # 如果元组相同，不需要额外操作
            else:
                dp[i][j] = min(
                    dp[i - 1][j] + 1,  # 删除 seq1[i-1]
                    dp[i][j - 1] + 1,  # 插入 seq2[j-1]
                    dp[i - 1][j - 1] + 1  # 替换 seq1[i-1] 为 seq2[j-1]
                )

    return dp[m][n]

def edit_similarity(seq1, seq2):
    """
    计算编辑距离的相似度，值在 [0, 1] 之间。
    """
    raw_distance = tuple_edit_distance(seq1, seq2)
    max_length = max(len(seq1), len(seq2))
    min_length = min(len(seq1), len(seq2))
    if max_length <= 1:
        return 0  # 两个序列都为1时表示这个序列时无效的，所以相似度为0，直接剔除
    return 1 - (raw_distance / max_length)

def calculate_all_edit(path, start_i, start_j):
    # 加载数据
    df = load_data(path)
    trace_id_list_1 = []
    trace_id_list_2 = []
    distance_list = []

    result_file = os.path.join(DATA_DIR, 'edit_similarity.csv')
    if os.path.exists(result_file):
        existing_results = pd.read_csv(result_file)
    else:
        existing_results = pd.DataFrame(columns=['trace_id_1', 'trace_id_2', 'distance'])

    # 获取当前结果中最大的 i 和 j（如果需要，可以优化逻辑）
    try:
        for i in range(start_i, len(df)):
            for j in range(start_j if i == start_i else i, len(df)):
                trace1 = df['encoded_trace'][i]
                trace2 = df['encoded_trace'][j]
                id1 = df['id'][i]
                id2 = df['id'][j]
                distance = edit_similarity(trace1, trace2)
                trace_id_list_1.append(id1)
                trace_id_list_2.append(id2)
                distance_list.append(distance)
                print(f"Calculated edit distance for {i}:{id1} and {j}:{id2}")
    except KeyboardInterrupt:
        print("Saving current progress...")
    finally:
        new_results = pd.DataFrame({'trace_id_1': trace_id_list_1, 'trace_id_2': trace_id_list_2, 'distance': distance_list})
        combined_results = pd.concat([existing_results, new_results], ignore_index=True)
        combined_results.to_csv(result_file, index=False)

def load_distance_matrix(file_path):
    """
    从 CSV 文件加载数据，并将其转换为距离矩阵。

    Args:
        file_path (str): 输入文件路径。

    Returns:
        pd.DataFrame: 距离矩阵的 DataFrame 格式。
    """
    # 加载数据
    df = pd.read_csv(file_path)
    
    # 获取唯一的 trace_id 列表
    trace_ids = sorted(set(df['trace_id_1']).union(set(df['trace_id_2'])))
    
    # 初始化矩阵
    distance_matrix = pd.DataFrame(
        np.full((len(trace_ids), len(trace_ids)), np.nan),
        index=trace_ids,
        columns=trace_ids
    )
    
    # 填充矩阵
    for _, row in df.iterrows():
        distance_matrix.at[row['trace_id_1'], row['trace_id_2']] = row['distance']
        distance_matrix.at[row['trace_id_2'], row['trace_id_1']] = row['distance']
    
    # 将对角线填充为 0（自距离）
    np.fill_diagonal(distance_matrix.values, 0)
    
    return distance_matrix

def hierarchical_clustering(distance_matrix, threshold=100):
    """
    基于距离矩阵执行层次聚类，并绘制树状图。

    Args:
        distance_matrix (pd.DataFrame): 序列间的距离矩阵。
        threshold (int): 聚类的距离阈值。

    Returns:
        pd.DataFrame: 包含聚类结果的 DataFrame。
    """
    # 转换为 NumPy 矩阵
    distances = distance_matrix.values

    # 层次聚类
    linked = linkage(distances, method='ward')
    
    # 绘制树状图
    plt.figure(figsize=(20, 10))
    dendrogram(
        linked,
        labels=distance_matrix.index.tolist(),
        orientation='top',
        distance_sort='ascending',
        leaf_rotation=90,
        leaf_font_size=2,  # 标签字体大小
    )
    plt.title('Hierarchical Clustering Dendrogram', fontsize=16)
    plt.xlabel('Trace ID', fontsize=12)
    plt.ylabel('Distance', fontsize=12)
    plot_path = os.path.join(DATA_DIR, 'hierarchical_clustering_high_res.png')
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    print(f"Saved clustering plot to {plot_path}")
    
    # 根据阈值生成聚类结果
    clusters = fcluster(linked, t=threshold, criterion='distance')
    cluster_df = pd.DataFrame({'trace_id': distance_matrix.index, 'cluster': clusters})
    
    return cluster_df, plt

if __name__ == '__main__':
    # calculate_all_dtw('noloop_encoded_trace.csv', 15, 107) # 上次跑到15，107
    noloop_path = os.path.join(DATA_DIR, 'noloop_encoded_trace.csv')
    edit_sim_path = os.path.join(DATA_DIR, 'edit_similarity.csv')
    cluster_output_path = os.path.join(DATA_DIR, 'hierarchical_clusters.csv')
    
    calculate_all_edit(noloop_path, 0, 0) # 上次跑到15，107
    distance_matrix = load_distance_matrix(edit_sim_path)
    cluster_df, plt = hierarchical_clustering(distance_matrix, threshold=100)
    cluster_df.to_csv(cluster_output_path, index=False)
