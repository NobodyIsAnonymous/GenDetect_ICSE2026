import pandas as pd
import numpy as np
from sklearn.preprocessing import normalize
from sentence_transformers import SentenceTransformer
import os  # <--- 【新增】引入 os 模块

# ================= 路径配置 =================
# 1. 获取当前脚本所在目录 (src/analysis)
current_dir = os.path.dirname(os.path.abspath(__file__))
# 2. 获取 src 目录
src_dir = os.path.dirname(current_dir)
# 3. 获取项目根目录 (ICSE2026Anonym-main)
project_root = os.path.dirname(src_dir)
# 4. 定义数据目录
DATA_DIR = os.path.join(project_root, 'data_rules_related')

def calculate_centroids(clusters, model):
    centroids = {}
    for cluster_name, words in clusters.items():
        embeddings = model.encode(words)
        centroid = np.mean(embeddings, axis=0)
        centroids[cluster_name] = centroid
    return centroids


def classify_new_word(word, centroids, model, threshold=1.5):
    word_embedding = model.encode([word])[0]
    word_embedding = normalize([word_embedding])[0]
    
    # Calculate distances to each centroid
    distances = {}
    for cluster_name, centroid in centroids.items():
        centroid = normalize([centroid])[0]
        distance = np.linalg.norm(word_embedding - centroid)  # Euclidean distance
        distances[cluster_name] = distance
    
    # Find the closest cluster
    closest_cluster = min(distances, key=distances.get)
    closest_distance = distances[closest_cluster]
    
    if closest_distance < threshold:
        return closest_cluster, closest_distance
    else:
        return "Others", closest_distance

def read_data(file_path):
    data = pd.read_csv(file_path)
    # Parse clusters and non-cluster lists
    clusters = {}
    remaining_non_cluster = {}
    unique_non_cluster = {}
    
    for _, row in data.iterrows():
        group_name = row['Group']
        functions = row['Functions'].split(', ')
        if "Common" in group_name and "Cluster" not in group_name:
            # Extract group type (e.g., "Remaining group1")
            group_type = group_name.split(' ', 1)[-1].lower()
            remaining_non_cluster[group_type] = functions
        elif "Unique" in group_name and "Cluster" not in group_name:
            # Extract root from the group name (e.g., "Unique call" -> "call")
            root = group_name.split(' ', 1)[-1].lower()
            unique_non_cluster[root] = functions
        else:
            clusters[group_name] = functions

    model = SentenceTransformer('all-MiniLM-L6-v2')
    centroids = calculate_centroids(clusters, model)
    return clusters, remaining_non_cluster, unique_non_cluster, model, centroids

def classify_new_function_names(new_word, clusters, remaining_non_cluster, unique_non_cluster, model, centroids):
    # Step 1: Check in remaining_non_cluster
    for group_type, functions in remaining_non_cluster.items():
        if new_word in functions:
            # print(f"新词 '{new_word}' 被归类到 'Common Non-Cluster ({group_type})'")
            return 'Common', group_type

    # Step 2: Check in unique_non_cluster by matching roots
    for root, functions in unique_non_cluster.items():
        if root.lower() in new_word.lower():  # Case-insensitive substring match
            # print(f"新词 '{new_word}' 被归类到 'Unique Non-Cluster ({root})'")
            return 'Unique', root

    # Step 3: Use clusters for distance-based classification
    cluster, distance = classify_new_word(new_word, centroids, model)
    
    if cluster == "Others":
        # print(f"新词 '{new_word}' 未能匹配现有类别，被归类到 'Others'")
        return 'Cluster', 'Others'
    else:
        # print(f"新词 '{new_word}' 被归类到 '{cluster}'，距离为 {distance:.4f}")
        return 'Cluster', cluster


if __name__ == '__main__':
    csv_path = os.path.join(DATA_DIR, 'final_classified_functions.csv')
    clusters, remaining_non_cluster, unique_non_cluster, model, centroids = read_data(csv_path)
    classify_new_function_names("transfer", clusters, remaining_non_cluster, unique_non_cluster, model, centroids)
