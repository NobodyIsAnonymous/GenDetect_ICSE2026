from sklearn.cluster import KMeans
from sklearn.preprocessing import normalize
from sentence_transformers import SentenceTransformer
import pandas as pd
import re

# Load your CSV file
file_path = 'function_count.csv'  # 替换为你的文件路径
data = pd.read_csv(file_path)

# Function to check if a name is non-meaningful
def is_non_meaningful(name):
    return bool(re.match(r'^[a-f0-9]{8,}$', name))

# Function to group by substrings
def group_by_substring(functions, substrings):
    groups = {}
    for func in functions:
        matched = False
        for substring in substrings:
            if substring.lower() in func.lower():
                if substring not in groups:
                    groups[substring] = []
                groups[substring].append(func)
                matched = True
                break
        if not matched:
            if 'Others' not in groups:
                groups['Others'] = []
            groups['Others'].append(func)
    return groups

# Function to perform clustering with Sentence-BERT
def perform_clustering(functions, num_clusters):
    model = SentenceTransformer('all-MiniLM-L6-v2')
    embeddings = model.encode(functions)
    normalized_embeddings = normalize(embeddings)
    kmeans = KMeans(n_clusters=num_clusters, random_state=42)
    kmeans.fit(normalized_embeddings)
    labels = kmeans.labels_
    clusters = {i: [] for i in range(num_clusters)}
    for func, label in zip(functions, labels):
        clusters[label].append(func)
    return clusters

def cluster_function_names():
    # Step 1: Separate non-meaningful functions
    non_meaningful_functions = data[data['Function'].apply(is_non_meaningful)]['Function'].tolist()

    # Step 2: Separate unique functions (Count = 1)
    unique_functions = data[(data['Count'] == 1) & (~data['Function'].apply(is_non_meaningful))]['Function'].tolist()

    # Step 3: Group unique functions by substrings
    substrings_to_check = ['test', 'reentrant', 'callback', 'call', 'back', 'price', 'checkpoint', 'get', 'fee', 'earn', 'invest' 'reserve', 'claim', 'reward', 'redeem', 'repay', 'stake', 'accrue', 'flash', 'exchange', 'swap', 'buy', 'sell', 'account', 'token', 'nft', 'collateral', 'interest', 'liquid', 'pool', 'pair', 'add', 'remove', 'receive', 'deposit', 'withdraw', 'borrow', 'allow', 'approve', 'balance', 'mint', 'burn', 'transfer', 'send', 'exec', 'operat', 'delegate', 'hand', 'implement', 'init', 'set', 'move', 'patch'] # 一个词蕴含的信息越丰富，越排在前面
    unique_grouped = group_by_substring(unique_functions, substrings_to_check)

    # Step 4: Cluster unique "Others" using Sentence-BERT
    unique_others = unique_grouped.get('Others', [])
    if unique_others:
        unique_others_clusters = perform_clustering(unique_others, num_clusters=16)
    else:
        unique_others_clusters = {}

    # Step 5: Group remaining non-unique functions by substrings
    remaining_functions = data[(data['Count'] > 1) & (~data['Function'].apply(is_non_meaningful))]['Function'].tolist()
    remaining_grouped = group_by_substring(remaining_functions, substrings_to_check)

    # Step 6: Cluster remaining "Others" using Sentence-BERT
    remaining_others = remaining_grouped.get('Others', [])
    if remaining_others:
        remaining_others_clusters = perform_clustering(remaining_others, num_clusters=12)
    else:
        remaining_others_clusters = {}

    # Combine all results into final groups
    final_groups = {
        'Non-Meaningful': non_meaningful_functions,
        **{f'Unique {group}': funcs for group, funcs in unique_grouped.items() if group != 'Others'},
        **{f'Unique Cluster {cluster}': funcs for cluster, funcs in unique_others_clusters.items()},
        **{f'Common {group}': funcs for group, funcs in remaining_grouped.items() if group != 'Others'},
        **{f'Common Cluster {cluster}': funcs for cluster, funcs in remaining_others_clusters.items()},
    }

    # Prepare DataFrame for output
    final_grouped_df = pd.DataFrame([(group, ', '.join(funcs)) for group, funcs in final_groups.items() if funcs],
                                    columns=['Group', 'Functions'])

    # Save results to CSV
    output_path = 'final_classified_functions.csv'
    final_grouped_df.to_csv(output_path, index=False)
    print(f"Results saved to {output_path}")

if __name__ == '__main__':
    cluster_function_names()
