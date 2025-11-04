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
    def __init__(self, verbose=False):
        self.train_rules = None  # Training set rule data
        self.classes_ = None  # Add classes_ attribute
        self.verbose = verbose
        self.fold_count = 0  # Track current fold

    def fit(self, X, y):
        """Store training data and initialize classes_"""
        self.train_rules = pd.DataFrame({'encoded_trace': X, 'label': y})
        
        if len(y) == 0:
            raise ValueError("Error: `y` in fit() is empty!")

        self.classes_ = np.unique(y)
        
        if self.verbose:
            self.fold_count += 1
            attack_count = sum(y == 1)
            benign_count = sum(y == 0)
            print(f"  Fold {self.fold_count} Training: {len(y)} samples (Attack: {attack_count}, Benign: {benign_count})")
        
        return self

    def predict(self, X):
        """Make predictions based on similarity matching"""
        if self.verbose:
            print(f"  Fold {self.fold_count} Predicting: {len(X)} test samples...")
        
        predictions = []
        total_samples = len(X)
        
        for i, no_loop_sequence in enumerate(X):
            # Show progress for every 20% or every 50 samples (whichever is smaller)
            if self.verbose and total_samples > 5:
                progress_step = min(max(1, total_samples // 5), 50)
                if (i + 1) % progress_step == 0 or i == total_samples - 1:
                    print(f"    Progress: {i+1}/{total_samples} ({(i+1)*100//total_samples}%)")
            
            similarity_list = []
            for j in range(len(self.train_rules)):
                known_sequence = self.train_rules['encoded_trace'].iloc[j]
                similarity = edit_similarity(no_loop_sequence, known_sequence)
                similarity_list.append((j, similarity))

            similarity_list.sort(key=lambda x: x[1])
            rule_name_1 = self.train_rules['label'].iloc[similarity_list[-1][0]]
            rule_name_2 = self.train_rules['label'].iloc[similarity_list[-2][0]]

            if rule_name_1 == 0 and rule_name_2 == 0:
                predictions.append(0)
            else:
                predictions.append(1)

        if len(predictions) == 0:
            raise ValueError("Error: predict() produced an empty array!")

        if self.verbose:
            attack_pred = sum(predictions)
            benign_pred = len(predictions) - attack_pred
            print(f"  Fold {self.fold_count} Complete - Predictions: Attack: {attack_pred}, Benign: {benign_pred}")

        return np.array(predictions)

# Custom scorer with verbose output
def verbose_accuracy_scorer(fold_num=[0]):  # Use mutable default to maintain state
    def scorer_func(estimator, X, y):
        fold_num[0] += 1
        y_pred = estimator.predict(X)
        accuracy = accuracy_score(y, y_pred)
        
        # Calculate detailed metrics
        from sklearn.metrics import confusion_matrix
        cm = confusion_matrix(y, y_pred)
        
        print(f"\nFold {fold_num[0]} Results: Accuracy = {accuracy:.4f} ({accuracy*100:.1f}%)")
        print(f"   Confusion Matrix: TN={cm[0,0]}, FP={cm[0,1]}, FN={cm[1,0]}, TP={cm[1,1]}")
        
        if cm[1,1] + cm[1,0] > 0:  # Avoid division by zero
            precision = cm[1,1] / (cm[1,1] + cm[0,1]) if (cm[1,1] + cm[0,1]) > 0 else 0
            recall = cm[1,1] / (cm[1,1] + cm[1,0])
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            print(f"   Metrics: Precision={precision:.3f}, Recall={recall:.3f}, F1={f1:.3f}")
        
        return accuracy
    
    return scorer_func

# Cross-validation process
def cross_validation(verbose=True, sample_size=None):
    """
    Run cross-validation with optional verbose output and sampling
    
    Args:
        verbose: Whether to show detailed progress
        sample_size: If specified, randomly sample this many rows for faster testing
    """
    print("Starting K-Fold Cross-Validation...")
    trace_rules_df = load_data('./data_rules_related/noloop_encoded_trace.csv')
    
    print(f"Loaded {len(trace_rules_df)} total rules")
    
    # Data split (first 534 rows are attacks, rest are benign)
    attack_data = trace_rules_df.iloc[:534].copy()
    benign_data = trace_rules_df.iloc[534:].copy()

    # Optional sampling for faster testing
    if sample_size and sample_size < len(trace_rules_df):
        print(f"Sampling {sample_size} rows for faster testing...")
        attack_sample_size = int(sample_size * len(attack_data) / len(trace_rules_df))
        benign_sample_size = sample_size - attack_sample_size
        
        attack_data = attack_data.sample(n=min(attack_sample_size, len(attack_data)), random_state=42)
        benign_data = benign_data.sample(n=min(benign_sample_size, len(benign_data)), random_state=42)

    print(f"Data composition: {len(attack_data)} attacks, {len(benign_data)} benign")

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
    print(f"Using 5-fold stratified cross-validation...")
    
    if verbose:
        # Use custom scorer with verbose output
        scorer = make_scorer(verbose_accuracy_scorer())
        model = SimilarityBasedClassifier(verbose=True)
        scores = cross_val_score(model, X, y, cv=skf, scoring=scorer, verbose=1)
    else:
        # Use simple scorer for faster execution
        scorer = make_scorer(accuracy_score)
        model = SimilarityBasedClassifier(verbose=False)
        scores = cross_val_score(model, X, y, cv=skf, scoring=scorer)
        print("Cross-validation in progress (no detailed output)...")
    
    # Output final results
    print(f"\nFinal Results:")
    print(f"   Mean Accuracy: {scores.mean():.4f} ± {scores.std():.4f}")
    print(f"   Individual Fold Scores: {[f'{score:.4f}' for score in scores]}")
    print(f"   Best Fold: {scores.max():.4f}")
    print(f"   Worst Fold: {scores.min():.4f}")

# Quick test function for development
def quick_test():
    """Run a quick test with sampled data"""
    print("Running quick test with 100 samples...")
    cross_validation(verbose=True, sample_size=100)

    

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'quick':
            quick_test()
        elif sys.argv[1] == 'silent':
            cross_validation(verbose=False)
        elif sys.argv[1] == 'sample' and len(sys.argv) > 2:
            sample_size = int(sys.argv[2])
            cross_validation(verbose=True, sample_size=sample_size)
        else:
            print("Usage:")
            print("  python predict_benchmark.py          # Full verbose cross-validation")
            print("  python predict_benchmark.py quick    # Quick test with 100 samples")  
            print("  python predict_benchmark.py silent   # Full cross-validation without verbose output")
            print("  python predict_benchmark.py sample N # Cross-validation with N samples")
    else:
        # Default: full verbose cross-validation
        cross_validation()