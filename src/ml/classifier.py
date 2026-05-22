import pandas as pd
import ast
import xgboost as xgb
from sklearn.model_selection import StratifiedKFold, cross_val_score, GridSearchCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import classification_report, confusion_matrix, precision_score, recall_score, f1_score
from sklearn.model_selection import cross_val_predict
from sklearn.metrics import accuracy_score, make_scorer
import joblib
from detection.replayer import Replayer
import config

def load_data(file_path):
    """ 解析 CSV 并转换 encoded_trace 格式 """
    df = pd.read_csv(file_path)

    def safe_eval(x):
        if isinstance(x, str):
            try:
                return ast.literal_eval(x)
            except:
                return x
        return x

    df['encoded_trace'] = df['encoded_trace'].apply(safe_eval)
    df['encoded_trace'] = df['encoded_trace'].apply(
        lambda x: ' '.join(["_".join(t).replace(" ", "_") for t in x])
    )

    return df

# 自定义 FPR scorer
def fpr_score(y_true, y_pred):
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    return fp / (fp + tn) if (fp + tn) > 0 else 0.0

# 自定义 FNR scorer
def fnr_score(y_true, y_pred):
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    return fn / (fn + tp) if (fn + tp) > 0 else 0.0

# 包装为 scorers
scorers = {
    'Accuracy': make_scorer(accuracy_score),
    'Precision': make_scorer(precision_score),
    'Recall': make_scorer(recall_score),
    'F1-score': make_scorer(f1_score),
    'FPR': make_scorer(fpr_score, greater_is_better=False),  # FPR 越小越好
    'FNR': make_scorer(fnr_score, greater_is_better=False),  # FNR 越小越好
}

def train():
    """ 训练 XGBoost 模型 """
    trace_rules_df = load_data(str(config.NOLOOP_ENCODED_TRACE))

    attack_data = trace_rules_df.iloc[:534].copy()
    benign_data = trace_rules_df.iloc[534:].copy()
    attack_data['label'] = 1
    benign_data['label'] = 0
    df = pd.concat([attack_data, benign_data]).reset_index(drop=True)

    vectorizer = TfidfVectorizer(ngram_range=(1,2), max_features=5000)
    X = vectorizer.fit_transform(df['encoded_trace'])
    y = df['label'].values
    joblib.dump(vectorizer, str(config.TFIDF_VECTORIZER))

    xgb_clf = xgb.XGBClassifier(objective='binary:logistic', eval_metric='logloss', random_state=42)
    param_grid = {
        'n_estimators': [100, 200, 300],
        'max_depth': [4, 6, 8],
        'learning_rate': [0.01, 0.1, 0.2],
        'subsample': [0.7, 0.8, 0.9],
        'colsample_bytree': [0.7, 0.8, 0.9]
    }
    grid_search = GridSearchCV(xgb_clf, param_grid, cv=3, scoring='accuracy', n_jobs=-1, verbose=2)
    grid_search.fit(X, y)

    best_xgb_clf = xgb.XGBClassifier(**grid_search.best_params_, objective='binary:logistic', eval_metric='logloss')
    best_xgb_clf.fit(X, y)

    best_xgb_clf.save_model(str(config.XGBOOST_MODEL_JSON))
    joblib.dump(best_xgb_clf, str(config.XGBOOST_MODEL_PKL))

    print(f"Training complete. Best params: {grid_search.best_params_}")

    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    for name, scorer in scorers.items():
        scores = cross_val_score(best_xgb_clf, X, y, cv=skf, scoring=scorer)
        sign = -1 if name in ['FPR', 'FNR'] else 1
        print(f"{name:<10}: {sign * scores.mean():.4f} ± {scores.std():.4f}")

    y_pred = cross_val_predict(best_xgb_clf, X, y, cv=skf)

    tn, fp, fn, tp = confusion_matrix(y, y_pred).ravel()
    print(f"Confusion Matrix:")
    print(f"TP: {tp}, FP: {fp}, TN: {tn}, FN: {fn}")

    report = classification_report(y, y_pred, digits=4)
    print("\nClassification Report:")
    print(report)

    acc = accuracy_score(y, y_pred)
    prec = precision_score(y, y_pred)
    rec = recall_score(y, y_pred)
    f1 = f1_score(y, y_pred)

    print(f"Accuracy:  {acc:.4f}")
    print(f"Precision: {prec:.4f}")
    print(f"Recall:    {rec:.4f}")
    print(f"F1-score:  {f1:.4f}")

class TransactionClassifier:
    """ 交易分类器 """
    def __init__(self, es_files, output_dir, model_dir=None):
        self.replayer = Replayer(es_files=es_files, output_dir=output_dir)
        if model_dir is None:
            model_dir = str(config.MODELS_DIR)
        self.vectorizer = joblib.load(f'{model_dir}/tfidf_vectorizer.pkl')
        self.model = xgb.XGBClassifier()
        self.model.load_model(f'{model_dir}/xgboost_model.json')

    def _convert_trace_to_string(self, trace):
        """ 处理 trace 使其符合 TF-IDF 格式 """
        return [' '.join(["_".join(t).replace(" ", "_") for t in trace])]

    def get_trace_from_tx(self, tx_hash):
        """ 获取交易的 trace 并转换 """
        trace = self.replayer.es_generate_trace(tx_hash)
        if not trace:
            print(f"Warning: No trace found for {tx_hash}")
            return [""]

        converted_trace = self._convert_trace_to_string(trace)
        print(f"Trace for {tx_hash}: {converted_trace}")
        return converted_trace

    def predict(self, tx_hash):
        """ 预测交易类型 """
        trace_str = self.get_trace_from_tx(tx_hash)

        # transfer trace_str to dataframe
        df = pd.DataFrame(trace_str, columns=['encoded_trace'])

        print(f"Encoded trace for {tx_hash}: {df['encoded_trace']}")

        X_new = self.vectorizer.transform(df['encoded_trace'])

        print(f"Transformed X_new shape: {X_new.shape}")

        prediction = self.model.predict(X_new)[0]
        print(f"Transaction {tx_hash} Prediction: {prediction}")
        return prediction

def run_benchmark():
    benchmark_data = pd.read_csv(str(config.BENCHMARK_DATA))
    classifier = TransactionClassifier(
        es_files=str(config.DATA_BENCHMARK_DIR / '2023' / 'new_dune_results_*_100k_*.csv'),
        output_dir=str(config.DATA_BENCHMARK_DIR / 'results' / '2023' / ''),
        model_dir=str(config.MODELS_DIR)
    )
    results = []
    correct = 0
    total = 0
    for tx_hash, label in zip(benchmark_data['tx_hash'], benchmark_data['attack']):
        print(f"Processing {tx_hash}...")
        result = classifier.predict(tx_hash)

        match = (label == result)
        if match:
            correct += 1
        total += 1
        results.append({'tx_hash': tx_hash, 'attack': label, 'result': result, 'match': match})
        accuracy = correct / total if total > 0 else 0
        print(f"Benchmark Accuracy: {accuracy:.4f} ({correct}/{total})")
    pd.DataFrame(results).to_csv(str(config.ML_BENCHMARK_RESULTS), index=False)
    print("Benchmark results saved.")

if __name__ == '__main__':
    train()
