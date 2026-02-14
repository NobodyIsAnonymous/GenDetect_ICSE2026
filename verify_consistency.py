import pandas as pd
import os
import ast

def verify_data_consistency_debug():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(current_dir, 'data_rules_related')
    
    new_file_path = os.path.join(data_dir, 'noloop_encoded_trace.csv')
    old_file_path = os.path.join(data_dir, 'noloop_encoded_trace_backup.csv')

    df_new = pd.read_csv(new_file_path, index_col='id')
    df_old = pd.read_csv(old_file_path, index_col='id')

    print("🚀 启动深度差异分析...")

    for tx_id, row in df_new.iterrows():
        if tx_id not in df_old.index: continue
        
        # 解析数据
        new_trace = ast.literal_eval(row['encoded_trace'])
        old_trace = ast.literal_eval(df_old.loc[tx_id, 'encoded_trace'])
        
        if new_trace == old_trace:
            print(f"✅ ID [{tx_id}]: 完全一致")
        else:
            print(f"❌ ID [{tx_id}]: 发现差异！")
            # 找出第一个不同的地方
            limit = min(len(new_trace), len(old_trace))
            diff_found = False
            for i in range(limit):
                if new_trace[i] != old_trace[i]:
                    print(f"   📍 差异位置: 第 {i+1} 个动作")
                    print(f"      🔴 新版: {new_trace[i]}")
                    print(f"      🔵 旧版: {old_trace[i]}")
                    diff_found = True
                    break # 只看第一个差异
            
            if not diff_found:
                print(f"   ⚠️ 长度不同！新版长度: {len(new_trace)}, 旧版长度: {len(old_trace)}")

if __name__ == "__main__":
    verify_data_consistency_debug()
