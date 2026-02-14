# Example of running a transaction with Cast
# cast run -v -q 0xc5215eb1d9c63373a02a013105b9f6745df1c935bb5c25817423b947be8d3aea --rpc-url mainnet > trace_example.log

# Example of running a scripted transaction with Forge
# forge test --contracts ./src/test/2024-10/MorphoBlue_exp.sol -vvvv --evm-version shanghai > test_trace_example.log

# run all the tests and save the output to ../traces/<test_name>.log

import subprocess
import re
import json
import os

# ================= 路径配置 =================
# 1. 获取当前脚本所在目录 (src/processing)
current_dir = os.path.dirname(os.path.abspath(__file__))
# 2. 获取项目根目录
project_root = os.path.dirname(os.path.dirname(current_dir))

# 3. 定义统一的文件夹路径
TRACES_DIR = os.path.join(project_root, 'traces')
STRUCTURED_DIR = os.path.join(project_root, 'structured_traces')

# 确保必要的目录存在
os.makedirs(TRACES_DIR, exist_ok=True)
os.makedirs(STRUCTURED_DIR, exist_ok=True)

def obtain_traces(contract):
    log_path = os.path.join(TRACES_DIR, f"{contract}.log")
    # 确保命令在项目根目录下执行，以便正确找到合约
    forge_cmd = f"forge test --contracts src/test/compilation/{contract}.sol -vvvv --evm-version shanghai > {log_path}"
    
    try:
        subprocess.run(forge_cmd, shell=True, check=True, cwd=project_root)
        print(f"Traces saved to: {log_path}")
    except Exception as e:
        print(f"Error running forge command: {e}")


def parse_trace_line(line):
    # 匹配缩进（每2或3个空格为一级）、框图符号（如 '├─' 或 '└─'）、调用信息
    match = re.match(r'(?P<indent>((  (│ |├─|└─)))*)(?P<content>.*)', line)
    if not match:
        return None
    
    indent = match.group('indent')
    indent_level = len(re.findall(r'  (│ |├─|└─)', indent))
    content = match.group('content').strip()
    
    return {
        'indent_level': indent_level,
        'content': content,
        'children': []
    }

def parse_trace_lines(trace_lines):
    root = {'content': 'root', 'children': []}
    node_stack = [root]

    for line in trace_lines:
        trace_info = parse_trace_line(line)
        if not trace_info:
            continue

        current_node = {
            'content': trace_info['content'],
            'children': []
        }

        # 确保缩进层级正确并将当前节点添加到其父节点的children中
        while len(node_stack) > trace_info['indent_level'] + 1:
            node_stack.pop()

        node_stack[-1]['children'].append(current_node)
        node_stack.append(current_node)

    return root

# 读取和处理第二个 Trace
def read_second_trace(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()

    trace_starts = [i for i, line in enumerate(lines) if line.startswith("Traces:")]
    if len(trace_starts) == 0:
        print(f"Error: 文件{file_path}中找不到 Trace")
        return
    if len(trace_starts) == 1:
        print(f"Warning: 文件{file_path}中只找到一个 Trace")
        start_index = trace_starts[0] + 1
    else:
        # 获取第二个 Trace 的内容，从 Traces: 开始到下一个空行之前
        start_index = trace_starts[1] + 1
        
    trace_lines = []
    for i in range(start_index, len(lines)):
        if lines[i].strip() == "":
            break
        trace_lines.append(lines[i][2:])
        
    return trace_lines

def pipeline(path):
    trace_lines = read_second_trace(path)
    if not trace_lines:
        return
    parsed_trace = parse_trace_lines(trace_lines)
    
    file_name = os.path.basename(path).replace('.log', '.json')
    output_path = os.path.join(STRUCTURED_DIR, file_name)
    # save as json
    with open(output_path, 'w') as f:
        f.write(json.dumps(parsed_trace, indent=4))
    print(f"Structured trace saved to: {output_path}")
    
if __name__ == '__main__':
    # 遍历原始日志目录
    if os.path.exists(TRACES_DIR):
        files = [f for f in os.listdir(TRACES_DIR) if f.endswith('.log')]
        for file in files:
            full_path = os.path.join(TRACES_DIR, file)
            pipeline(full_path)
        print("All traces processed successfully!")
    else:
        print(f"Directory not found: {TRACES_DIR}")
