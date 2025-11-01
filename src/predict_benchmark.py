import pandas as pd
from tx_replayer import Replayer
from dtw_similarity import edit_similarity, load_data
import numpy as np
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.metrics import make_scorer, accuracy_score
import ast

# Load the benign transactions
def add_benign_rules():
    classified_df = pd.read_csv('dune_tx/classified_tx_filtered.csv')

    benign_txs = classified_df['tx_hash']
    benign_names = classified_df['rule_name_1'] + (classified_df['similarity_1'] * 100).astype(int).astype(str) + '_benign' + classified_df['ID'].astype(str)

    replayer = Replayer(es_files='dune_tx/2023/new_dune_results_*_100k_*.csv', output_dir='dune_tx/results/2023/')
    for tx_hash, rule_name in zip(benign_txs, benign_names):
        replayer.add_new_rule(tx_hash, rule_name)
    
def run_benchmark():
    replayer = Replayer(es_files='dune_tx/2023/new_dune_results_*_100k_*.csv', output_dir='dune_tx/results/2023/')
    benchmark_data = pd.read_csv('dune_tx/benchmark-data.csv')
    
    # create a dataframe to store the test results
    test_results = pd.DataFrame(columns=['tx_hash', 'attack', 'rule_name_1', 'rule_name_2', 'match'])
    for tx_hash, label in zip(benchmark_data['tx_hash'], benchmark_data['attack']):
        similarity = replayer.match_tx_trace(tx_hash)
        
        if 'benign' in similarity['rule_name_1'].iloc[0] and 'benign' in similarity['rule_name_2'].iloc[0]:
            result = 0
        else:
            result = 1
        
        if label == result:
            match = 1
        else:
            match = 0
        
        new_row = pd.DataFrame([{
            'tx_hash': tx_hash,
            'attack': label,
            'rule_name_1': similarity['rule_name_1'].iloc[0],
            'rule_name_2': similarity['rule_name_2'].iloc[0],
            'match': match
        }])

        # Use pd.concat() to append data
        test_results = pd.concat([test_results, new_row], ignore_index=True)
        
    test_results.to_csv('dune_tx/benchmark-results.csv', index=False)

# Load data
def load_data(file_path):
    df = pd.read_csv(file_path)

    # Ensure `encoded_trace` is in the correct Python list format
    def safe_eval(x):
        if isinstance(x, str):
            try:
                return ast.literal_eval(x)
            except:
                return x  # Return original value directly (already a list)
        return x  # Return original value directly (already a list)

    df['encoded_trace'] = df['encoded_trace'].apply(safe_eval)
    return df

# Custom classifier
class SimilarityBasedClassifier(BaseEstimator, ClassifierMixin):
    def __init__(self):
        self.train_rules = None  # Training set rule data
        self.classes_ = None  # Add classes_ attribute

    def fit(self, X, y):
        """Store training data and initialize classes_"""
        self.train_rules = pd.DataFrame({'encoded_trace': X, 'label': y})
        
        if len(y) == 0:
            raise ValueError("Error: `y` in fit() is empty!")

        self.classes_ = np.unique(y)
        return self

    def predict(self, X):
        """Make predictions based on similarity matching"""
        predictions = []
        for no_loop_sequence in X:
            similarity_list = []
            for i in range(len(self.train_rules)):
                known_sequence = self.train_rules['encoded_trace'].iloc[i]
                similarity = edit_similarity(no_loop_sequence, known_sequence)
                similarity_list.append((i, similarity))

            similarity_list.sort(key=lambda x: x[1])
            rule_name_1 = self.train_rules['label'].iloc[similarity_list[-1][0]]
            rule_name_2 = self.train_rules['label'].iloc[similarity_list[-2][0]]

            if rule_name_1 == 0 and rule_name_2 == 0:
                predictions.append(0)
            else:
                predictions.append(1)

        if len(predictions) == 0:
            raise ValueError("Error: predict() produced an empty array!")

        return np.array(predictions)

# Cross-validation process
def cross_validation():
    trace_rules_df = load_data('./data_rules_related/noloop_encoded_trace.csv')
    # Data split (first 534 rows are attacks, rest are benign)
    attack_data = trace_rules_df.iloc[:534].copy()
    benign_data = trace_rules_df.iloc[534:].copy()

    # Add labels
    attack_data['label'] = 1
    benign_data['label'] = 0
    # Merge data
    df = pd.concat([attack_data, benign_data]).reset_index(drop=True)
    # Separate features and labels
    X = df['encoded_trace']
    y = df['label'].values

    # Cross-validation
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    # Use make_scorer to calculate accuracy
    scorer = make_scorer(accuracy_score)
    # Run cross_val_score
    model = SimilarityBasedClassifier()
    scores = cross_val_score(model, X, y, cv=skf, scoring=scorer)
    # Output results
    print(f"K-Fold Cross-Validation Accuracy: {scores.mean():.4f} ± {scores.std():.4f}")

    

if __name__ == '__main__':
    # run_benchmark()
    cross_validation()