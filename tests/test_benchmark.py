import pytest
import numpy as np
from core.similarity import embed_sequence, calculate_dtw_distance, load_data
import timeit
import pandas as pd

import config
df = load_data(str(config.ENCODED_TRACE))

@pytest.mark.benchmark
def test_load_data_benchmark(benchmark):
    data = benchmark(load_data, str(config.ENCODED_TRACE))

@pytest.mark.benchmark
def test_embed_sequence_benchmark(benchmark):
    sequence = df['encoded_trace'][0]
    result = benchmark(embed_sequence, sequence)

@pytest.mark.benchmark
def test_embed_sequence_batch_benchmark(benchmark):
    sequences = df['encoded_trace'][1]
    result = benchmark(embed_sequence, sequences)

@pytest.mark.benchmark
def test_calculate_dtw_distance_benchmark(benchmark):
    sequence1 = df['encoded_trace'][0]
    sequence2 = df['encoded_trace'][1]
    result = benchmark(calculate_dtw_distance, sequence1, sequence2)
    print(result)
    
def test_dtw_benchmark_timeit():
    results = []

    encoded_traces = df['encoded_trace'].tolist()

    for i in range(len(encoded_traces)):
        for j in range(i + 1, len(encoded_traces)):
            seq1 = encoded_traces[i]
            seq2 = encoded_traces[j]

            len1 = len(seq1)
            len2 = len(seq2)

            stmt = lambda: calculate_dtw_distance(seq1, seq2)
            duration = timeit.timeit(stmt, number=2)
            avg_time = duration / 2

            results.append({
                'trace1_length': len1,
                'trace2_length': len2,
                'avg_time_seconds': avg_time
            })

            # 可选：减少计算量，前100条
            if len(results) >= 100:
                break
        if len(results) >= 100:
            break

    # 保存结果
    df_result = pd.DataFrame(results)
    df_result.to_csv('dtw_timeit_result.csv', index=False)
    print("✅ 已保存为 dtw_timeit_result.csv")