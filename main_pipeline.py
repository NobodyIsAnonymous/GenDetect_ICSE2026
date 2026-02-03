import os
import subprocess
import sys

# 获取项目根目录
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

def run_script(script_path, description):
    """通用脚本运行函数，自动配置环境变量"""
    full_path = os.path.join(PROJECT_ROOT, script_path)
    
    print(f"\n{'='*60}")
    print(f"▶️ 正在执行步骤: {description}")
    print(f"   脚本路径: {script_path}")
    print(f"{'='*60}")

    if not os.path.exists(full_path):
        print(f"❌ 错误: 找不到脚本 {full_path}")
        return False

    # ================= 核心修复点 START =================
    # 获取当前环境变量
    env = os.environ.copy()
    
    # 构造需要加入的路径列表
    # 我们不仅要加 src，还要把 src/analysis 和 src/processing 加入
    # 这样代码里直接写 "import new_function_name_cluster" 才能生效
    additional_paths = [
        os.path.join(PROJECT_ROOT, "src"),
        os.path.join(PROJECT_ROOT, "src", "analysis"),   # <--- 关键修复：让 Python 能看见 analysis 里的文件
        os.path.join(PROJECT_ROOT, "src", "processing"), # <--- 关键修复：让 Python 能看见 processing 里的文件
    ]
    
    # 将旧的 PYTHONPATH 和新路径拼接（兼容 Windows 和 Linux）
    current_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = os.pathsep.join(additional_paths + [current_pythonpath])
    # ================= 核心修复点 END ==================

    try:
        # 实时打印子进程输出
        process = subprocess.run(
            [sys.executable, full_path],
            cwd=PROJECT_ROOT, # 确保在根目录运行
            env=env,
            check=True
        )
        print(f"✅ {description} 完成。\n")
        return True
    except subprocess.CalledProcessError:
        print(f"❌ {description} 失败！流水线终止。")
        return False

# 下面的 if __name__ == "__main__": 部分保持不变...
if __name__ == "__main__":
    print("🚀 全自动攻击分析流水线启动...\n")

    # ==========================================
    # 第一阶段：Processing (提取素材)
    # ==========================================
    if not run_script("src/processing/read_trace_func.py", "1. 日志解析与向量提取"):
        sys.exit(1)

    # ==========================================
    # 第二阶段：Analysis (构建大脑)
    # ==========================================
    if not run_script("src/analysis/data_overview.py", "2. 数据清洗与统计"):
        sys.exit(1)
        
    if not run_script("src/analysis/function_name_cluster.py", "3. 函数名语义聚类"):
        sys.exit(1)

    # ==========================================
    # 第三阶段：Processing (特征加工)
    # ==========================================
    #simple_loop.py new_function_name_cluster.py
    if not run_script("src/processing/trace_encoder.py", "4. 语义编码与循环去重"):
        sys.exit(1)

    # ==========================================
    # 第四阶段：Analysis (评估产出)
    # ==========================================
    if not run_script("src/analysis/dtw_similarity.py", "5. 相似度计算与可视化"):
        sys.exit(1)

    print(f"{'='*60}")
    print("🎉🎉🎉 流水线全部执行完毕！所有结果已保存至 data_rules_related 文件夹。")
    print(f"{'='*60}")
