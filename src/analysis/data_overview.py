import pandas as pd
import numpy as np
from collections import Counter
import ast
import os

def clean_data(df):
    exclude_keywords = {'roll', 'deal'}  # 无效数据关键词

    df['function_name'] = df['function_name'].apply(ast.literal_eval)
    df['address'] = df['address'].apply(ast.literal_eval)
    df['function_params'] = df['function_params'].apply(ast.literal_eval)

    # 清理数据
    for i in range(len(df['id'])):
        # 获取当前行的 function_name、address 和 function_params
        function_name = df['function_name'][i]
        address = df['address'][i]
        function_params = df['function_params'][i]

        # 筛选出非排除关键词的索引
        valid_indices = [j for j in range(len(function_name)) if function_name[j] not in exclude_keywords and address[j] != 'vm' and  address[j] != 'VM']

        # 根据有效索引重写 function_name、address 和 function_params
        df.at[i, 'function_name'] = [function_name[j] for j in valid_indices]
        df.at[i, 'address'] = [address[j] for j in valid_indices]
        df.at[i, 'function_params'] = [function_params[j] for j in valid_indices]

    return df

def sort_addresses(df):
    # Flatten the 'address' column and count occurrences
    # literal_eval(df["address"][0])
    # Update the logic to count each address only once per sublist
    unique_address_list = [address for sublist in df["address"] for address in set(ast.literal_eval(sublist))]
    address_count_unique = Counter(unique_address_list)

    # Convert the counter to a DataFrame
    address_count_unique_df = pd.DataFrame(address_count_unique.items(), columns=["Address", "Count"])

    # Sort the DataFrame by the "Count" column in descending order
    address_count_unique_df_sorted = address_count_unique_df.sort_values(by="Count", ascending=False)
    return address_count_unique_df_sorted

def sort_functions(df):
    # Flatten the 'function_name' column and count occurrences
    function_list = [function for sublist in df["function_name"] for function in set(ast.literal_eval(sublist))]
    function_count = Counter(function_list)
    
    # Convert the counter to a DataFrame
    function_count_df = pd.DataFrame(function_count.items(), columns=["Function", "Count"])
    
    # Sort the DataFrame by the "Count" column in descending order
    function_count_df_sorted = function_count_df.sort_values(by="Count", ascending=False)
    return function_count_df_sorted
    
def save_cleaned_data(df, path):
    # 使用传入的 path 变量，而不是写死的文件名
    df.to_csv(path, index=False)

if __name__ == '__main__':
    
    # 1. 获取当前脚本位置 (src/processing)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 2. 获取项目根目录 (往上跳两级: processing -> src -> ICSE2026Anonym-main)
    project_root = os.path.dirname(os.path.dirname(current_dir))
    
    # 3. 【关键】定义数据文件夹路径
    data_dir = os.path.join(project_root, 'data_rules_related')
    
    # 2. 定义所有文件的完整路径
    input_csv_path = os.path.join(data_dir, 'attack_vectors.csv')
    cleaned_csv_path = os.path.join(data_dir, 'cleaned_attack_vectors.csv')
    # 【修改点2】这两个输出文件也要定义路径
    func_count_path = os.path.join(data_dir, 'function_count.csv')
    addr_count_path = os.path.join(data_dir, 'address_count.csv')
    
    if os.path.exists(input_csv_path):
        df = pd.read_csv(input_csv_path) 
        
        df = clean_data(df)
        
        # 【修改点4】把计算好的路径传给函数
        save_cleaned_data(df, cleaned_csv_path) 
        print(f"已保存清理数据至: {cleaned_csv_path}")

        # 重新读取 (直接用路径变量)
        df = pd.read_csv(cleaned_csv_path)
        
        function_count_df_sorted = sort_functions(df)
        # 【修改点5】使用完整路径保存
        function_count_df_sorted.to_csv(func_count_path, index=False)
        print(f"已生成: {func_count_path}")
        
        address_count_df_sorted = sort_addresses(df)
        # 【修改点6】使用完整路径保存
        address_count_df_sorted.to_csv(addr_count_path, index=False)
        print(f"已生成: {addr_count_path}")
    else:
        print(f"错误: 找不到输入文件 {input_csv_path}")
