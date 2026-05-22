import pandas as pd
import numpy as np
from collections import Counter
import ast

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

def save_cleaned_data(df):
    # Save the DataFrame to a new CSV file
    df.to_csv('cleaned_attack_vectors.csv', index=False)

if __name__ == '__main__':
    df = pd.read_csv('attack_vectors.csv')
    df = clean_data(df)
    save_cleaned_data(df)
    df = pd.read_csv('cleaned_attack_vectors.csv')

    function_count_df_sorted = sort_functions(df)
    function_count_df_sorted.to_csv('function_count.csv', index=False)

    address_count_df_sorted = sort_addresses(df)
    address_count_df_sorted.to_csv('address_count.csv', index=False)
