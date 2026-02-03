def simplify_sequence_with_loops(sequence):
    """
    找到序列中的所有循环，并将其简化为《loop start，single loop，loop stop》。

    Args:
        sequence (list): 要分析的序列，元素可以是任何可比较的类型。

    Returns:
        list: 简化后的序列，循环部分替换为《loop start，single loop，loop stop》。
    """
    n = len(sequence)
    loops = []

    # 找到所有循环
    for window_size in range(1, n // 2 + 1):
        visited_patterns = set()
        for start in range(n - window_size * 2 + 1):
            window1 = tuple(sequence[start:start + window_size])
            window2 = tuple(sequence[start + window_size:start + window_size * 2])

            if window1 == window2 and window1 not in visited_patterns:
                # 检测连续重复的次数
                times = 2
                while (
                    start + window_size * times <= n and
                    tuple(sequence[start + window_size * (times - 1):start + window_size * times]) == window1
                ):
                    times += 1
                
                # 限制仅记录严格连续的循环
                visited_patterns.add(window1)
                loops.append((window1, start, start + window_size * (times - 1), times))
    # 根据找到的循环简化序列
    simplified_sequence = []
    i = 0
    while i < n:
        # 检查当前索引是否在某个循环的起始位置
        loop_found = False
        for loop, start, end, times in loops:
            if i == start:
                # 添加循环标记
                simplified_sequence.append(('', 'Common', 'loop start'))
                simplified_sequence.extend(loop)  # 添加循环内容
                simplified_sequence.append(('', 'Common', 'loop stop'))
                i = end  # 跳过整个循环
                loop_found = True
                break
        if not loop_found:
            # 非循环部分，直接添加到结果中
            simplified_sequence.append(sequence[i])
            i += 1

    return simplified_sequence


# 测试示例
# sequence = [
#     ('0x01','Common', 'test'), ('0x01','Common', 'swap'), ('0x01','Common', 'transfer'),
#     ('0x02','Common', 'call'), ('0x01','Common', 'swap'), ('0x01','Common', 'transfer'),
#     ('0x01','Common', 'call'), ('0x01','Common', 'withdraw'), ('0x01','Common', 'receive'),
#     ('0x01','Common', 'test'), ('0x01','Common', 'swap'), ('0x01','Common', 'transfer'),
#     ('0x01','Common', 'call'), ('0x01','Common', 'swap'), ('0x01','Common', 'transfer'),
#     ('0x01','Common', 'call'), ('0x01','Common', 'swap'), ('0x01','Common', 'transfer'),
#     ('0x01','Common', 'call')
# ]

# # # 简化序列
# simplified_sequence = simplify_sequence_with_loops(sequence)

# # # 打印结果
# print("Simplified sequence:")
# for item in simplified_sequence:
#     print(item)