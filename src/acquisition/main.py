import re
import subprocess
import os # <--- 引入 os

# ================= 路径配置 =================
# 1. 获取当前脚本所在目录 (src/acquisition)
current_dir = os.path.dirname(os.path.abspath(__file__))
# 2. 获取 src 目录
src_dir = os.path.dirname(current_dir)
# 3. 获取项目根目录 (ICSE2026Anonym-main)
project_root = os.path.dirname(src_dir)

# 定义文件绝对路径
COMMANDS_FILE = os.path.join(project_root, 'commands_set.txt')
ERROR_LOG_FILE = os.path.join(project_root, 'error.log')
TRACES_DIR = os.path.join(project_root, 'traces')

def read_commands(start_line):
    with open(COMMANDS_FILE, 'r') as file:
        commands = file.readlines()
    return commands[start_line:]

def extract_contract_name(command):
    # Extract the contract name from the command
    # forge test --contracts ./src/test/2021-04/Uranium_exp.sol -vvvv, only obtain Uranium_exp, the years might change, also the starting can be ./src or src
    match = re.search(r'--contracts\s+(?:\./|)src/test/\d{4}-\d{2}/([^/]+\.sol)', command)
    
    if match:
        # split the match with "/" and get the last element
        file_name = match.group().split("/")[-1]
        # remove the .sol extension
        contract = file_name.split(".")[0]
    else:
        # forge test --match-contract LavaLending_exp -vvvv, search for the format like this, excluding -vvvv
        match = re.search(r'(?<=--match-contract )(.*)', command)
        contract = match.group().split(" ")[0]
    return contract

def obtain_traces(command):
    # Run the transaction with Forge
    contract = extract_contract_name(command)
    log_file_path = os.path.join(TRACES_DIR, f"{contract}.log")
    forge_cmd = f"{command.strip()} --ignored-error-codes 5667 > {log_file_path}"
    
    # try running the forge command
    try:
        # 在项目根目录下运行指令，确保 forge 路径正确
        subprocess.run(forge_cmd, shell=True, check=True, cwd=project_root)
        print(f"Traces saved to: {log_file_path}")
        
        if os.path.getsize(log_file_path) == 0:
            with open(ERROR_LOG_FILE, "a") as f:
                f.write(f"Error: {contract} trace is empty\n")
    except Exception as e:
        print(f"Error running forge command: {e}")
        with open(ERROR_LOG_FILE, "a") as f:
            f.write(f"Error: {contract} failed to obtain trace with error {e}\n")

def read_error_log(end_line):
    with open(ERROR_LOG_FILE, "r") as f:
        errors = f.readlines()
    return errors[:end_line]

def check_if_command_failed(errors, command):
    contract = extract_contract_name(command)
    for error in errors:
        if contract in error:
            return True
    return False

if __name__ == '__main__':
    errors = read_error_log(34)
    commands = read_commands(0)
    for command in commands:
        if check_if_command_failed(errors, command):
            # retry the command
            print(f"ReObtaining traces for {command}")
            obtain_traces(command)
        else:
            continue
    
    print("All traces saved successfully!")
