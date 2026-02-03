import sys
import os

# --- 插入【路径配置代码块】 ---
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(src_dir)
processing_dir = os.path.join(src_dir, 'processing')
sys.path.append(processing_dir)
analysis_dir = os.path.join(src_dir, 'analysis')       # <--- 新增
sys.path.append(analysis_dir)
DATA_DIR = os.path.join(project_root, 'data_rules_related')
from dtw_similarity import embed_sequence, calculate_dtw_distance, load_data
import timeit
import pandas as pd
    
def test_dtw_benchmark_timeit():
    csv_path = os.path.join(DATA_DIR, 'encoded_trace.csv')
    df = load_data(csv_path)
    results = []

    encoded_traces = df['encoded_trace'].tolist()

    seen_pairs = set()

    for i in range(len(encoded_traces)):
        for j in range(i + 1, len(encoded_traces)):
            seq1 = encoded_traces[i]
            seq2 = encoded_traces[j]

            len1 = len(seq1)
            len2 = len(seq2)

            # 用 (min, max) 去重组合
            length_pair = (min(len1, len2), max(len1, len2))
            if length_pair in seen_pairs or max(len1, len2) > 1000:
                continue
            seen_pairs.add(length_pair)

            # 运行 DTW
            stmt = lambda: calculate_dtw_distance(seq1, seq2)
            duration = timeit.timeit(stmt, number=1)

            results.append({
                'trace1_length': len1,
                'trace2_length': len2,
                'avg_time_seconds': duration
            })
            print(f"trace1_length: {len1}, trace2_length: {len2}, avg_time_seconds: {duration}")
            print("seq1:", i, "seq2:", j)

        #     # 可选：限制数量
        #     if len(results) >= 200:
        #         break
        # if len(results) >= 200:
        #     break

    # 保存结果
    output_path = os.path.join(current_dir, 'dtw_timeit_result_2.csv') 
    df_result = pd.DataFrame(results)
    df_result.to_csv(output_path, index=False)
    print(f"✅ 已保存为 {output_path}")

if __name__ == "__main__":
    test_dtw_benchmark_timeit()
