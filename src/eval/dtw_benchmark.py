from core.similarity import embed_sequence, calculate_dtw_distance, load_data
import timeit
import pandas as pd
import config

def test_dtw_benchmark_timeit():
    df = load_data(str(config.ENCODED_TRACE))
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

    # 保存结果
    df_result = pd.DataFrame(results)
    df_result.to_csv('dtw_timeit_result_2.csv', index=False)
    print("Saved as dtw_timeit_result_2.csv")

if __name__ == "__main__":
    test_dtw_benchmark_timeit()
