import pandas as pd
from detection.replayer import Replayer
from core.similarity import edit_similarity, load_data
import numpy as np
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.metrics import make_scorer, accuracy_score
import ast
import config

# Load the benign transactions
def add_benign_rules():
    classified_df = pd.read_csv(str(config.CLASSIFIED_TX_FILTERED))

    benign_txs = classified_df['tx_hash']
    benign_names = classified_df['rule_name_1'] + (classified_df['similarity_1'] * 100).astype(int).astype(str) + '_benign' + classified_df['ID'].astype(str)

    replayer = Replayer(es_files=str(config.DATA_BENCHMARK_DIR / '2023' / 'new_dune_results_*_100k_*.csv'), output_dir=str(config.DATA_BENCHMARK_DIR / 'results' / '2023' / ''))
    for tx_hash, rule_name in zip(benign_txs, benign_names):
        replayer.add_new_rule(tx_hash, rule_name)

def run_benchmark():
    replayer = Replayer(es_files=str(config.DATA_BENCHMARK_DIR / '2023' / 'new_dune_results_*_100k_*.csv'), output_dir=str(config.DATA_BENCHMARK_DIR / 'results' / '2023' / ''))
    benchmark_data = pd.read_csv(str(config.BENCHMARK_DATA))

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

    test_results.to_csv(str(config.BENCHMARK_RESULTS), index=False)

# Load data
def load_data_fixed(file_path):
    df = pd.read_csv(file_path)

    # Ensure `encoded_trace` is in the correct Python list format
    def safe_eval(x):
        if isinstance(x, str):
            try:
                return ast.literal_eval(x)
            except:
                return []  # Return empty list if parsing fails
        return x if isinstance(x, list) else []  # Return list or empty list

    df['encoded_trace'] = df['encoded_trace'].apply(safe_eval)

    # Filter out empty or invalid traces
    df = df[df['encoded_trace'].apply(lambda x: isinstance(x, list) and len(x) > 0)]

    return df

# Fixed similarity function
def edit_similarity_fixed(seq1, seq2):
    """
    计算编辑距离的相似度，值在 [0, 1] 之间。
    修复版本：处理边界情况和 NaN 问题
    """
    # Handle empty sequences
    if not seq1 or not seq2:
        return 0.0

    # Calculate edit distance using existing function
    from core.similarity import tuple_edit_distance
    try:
        raw_distance = tuple_edit_distance(seq1, seq2)
        max_length = max(len(seq1), len(seq2))

        if max_length == 0:
            return 1.0  # Both sequences are empty, perfect match

        similarity = 1 - (raw_distance / max_length)

        # Ensure similarity is in [0, 1] range and not NaN
        if np.isnan(similarity) or similarity < 0:
            return 0.0
        elif similarity > 1:
            return 1.0
        else:
            return float(similarity)

    except Exception as e:
        print(f"Error calculating similarity: {e}")
        return 0.0

# Custom classifier
class SimilarityBasedClassifier(BaseEstimator, ClassifierMixin):
    def __init__(self, verbose=False):
        self.train_rules = None  # Training set rule data
        self.classes_ = None  # Add classes_ attribute
        self.verbose = verbose
        self.fold_count = 0  # Track current fold

    def fit(self, X, y):
        """Store training data and initialize classes_"""
        # Filter out invalid traces
        valid_indices = []
        valid_X = []
        valid_y = []

        for i, trace in enumerate(X):
            if isinstance(trace, list) and len(trace) > 0:
                valid_indices.append(i)
                valid_X.append(trace)
                valid_y.append(y[i])

        if len(valid_y) == 0:
            raise ValueError("Error: No valid training data after filtering!")

        self.train_rules = pd.DataFrame({'encoded_trace': valid_X, 'label': valid_y})
        self.classes_ = np.unique(valid_y)

        if self.verbose:
            self.fold_count += 1
            attack_count = sum(np.array(valid_y) == 1)
            benign_count = sum(np.array(valid_y) == 0)
            print(f"  Fold {self.fold_count} Training: {len(valid_y)} valid samples (Attack: {attack_count}, Benign: {benign_count})")
            print(f"    Filtered out {len(X) - len(valid_X)} invalid traces")

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

            # Handle invalid test sequences
            if not isinstance(no_loop_sequence, list) or len(no_loop_sequence) == 0:
                predictions.append(0)  # Default to benign for invalid sequences
                continue

            similarity_list = []
            valid_similarities = []

            for j in range(len(self.train_rules)):
                known_sequence = self.train_rules['encoded_trace'].iloc[j]
                try:
                    similarity = edit_similarity_fixed(no_loop_sequence, known_sequence)
                    if not np.isnan(similarity):
                        similarity_list.append((j, similarity))
                        valid_similarities.append(similarity)
                except Exception as e:
                    if self.verbose:
                        print(f"    Warning: Similarity calculation failed for sample {j}: {e}")
                    continue

            if len(similarity_list) == 0:
                # No valid similarities computed, default to benign
                predictions.append(0)
                if self.verbose:
                    print(f"    Warning: No valid similarities for test sample {i}")
                continue

            # Sort by similarity (highest first)
            similarity_list.sort(key=lambda x: x[1], reverse=True)

            # Get top 2 matches
            if len(similarity_list) >= 2:
                rule_name_1 = self.train_rules['label'].iloc[similarity_list[0][0]]
                rule_name_2 = self.train_rules['label'].iloc[similarity_list[1][0]]
            elif len(similarity_list) == 1:
                rule_name_1 = self.train_rules['label'].iloc[similarity_list[0][0]]
                rule_name_2 = rule_name_1  # Use same rule for both
            else:
                # Should not happen due to check above, but just in case
                predictions.append(0)
                continue

            # Classification logic: if both top matches are benign (0), predict benign
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
class VerboseScorer:
    def __init__(self):
        self.fold_count = 0
        self.__name__ = 'verbose_accuracy_scorer'

    def __call__(self, y_true, y_pred):
        self.fold_count += 1
        try:
            accuracy = accuracy_score(y_true, y_pred)

            # Check for NaN
            if np.isnan(accuracy):
                print(f"\nFold {self.fold_count} ERROR: Accuracy is NaN!")
                return 0.0

            # Calculate detailed metrics
            from sklearn.metrics import confusion_matrix
            cm = confusion_matrix(y_true, y_pred)

            print(f"\nFold {self.fold_count} Results: Accuracy = {accuracy:.4f} ({accuracy*100:.1f}%)")
            print(f"   Confusion Matrix: TN={cm[0,0]}, FP={cm[0,1]}, FN={cm[1,0]}, TP={cm[1,1]}")

            if cm[1,1] + cm[1,0] > 0:  # Avoid division by zero
                precision = cm[1,1] / (cm[1,1] + cm[0,1]) if (cm[1,1] + cm[0,1]) > 0 else 0
                recall = cm[1,1] / (cm[1,1] + cm[1,0])
                f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
                print(f"   Metrics: Precision={precision:.3f}, Recall={recall:.3f}, F1={f1:.3f}")

            return accuracy
        except Exception as e:
            print(f"\nFold {self.fold_count} ERROR: {e}")
            return 0.0

# Cross-validation process
def cross_validation(verbose=True, sample_size=None):
    """
    Run cross-validation with optional verbose output and sampling

    Args:
        verbose: Whether to show detailed progress
        sample_size: If specified, randomly sample this many rows for faster testing
    """
    print("Starting K-Fold Cross-Validation...")
    trace_rules_df = load_data_fixed(str(config.NOLOOP_ENCODED_TRACE))

    print(f"Loaded {len(trace_rules_df)} total valid rules")

    # Check actual data distribution
    print(f"Total data rows: {len(trace_rules_df)}")
    print(f"First 5 IDs: {list(trace_rules_df['id'].head())}")
    print(f"Last 5 IDs: {list(trace_rules_df['id'].tail())}")

    # Adjust data split based on actual data
    # Assuming first ~50% are attacks, rest are benign (adjust as needed)
    split_point = min(534, len(trace_rules_df) // 2)  # Use 534 or half, whichever is smaller

    attack_data = trace_rules_df.iloc[:split_point].copy()
    benign_data = trace_rules_df.iloc[split_point:].copy()

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
    X = df['encoded_trace'].tolist()  # Convert to list
    y = df['label'].values

    print(f"Final dataset: {len(X)} samples, {sum(y)} attacks, {len(y)-sum(y)} benign")

    # Cross-validation
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    print(f"Using 5-fold stratified cross-validation...")

    if verbose:
        # Use custom scorer with verbose output
        scorer = make_scorer(VerboseScorer())
        model = SimilarityBasedClassifier(verbose=True)
        scores = cross_val_score(model, X, y, cv=skf, scoring=scorer, verbose=1)
    else:
        # Use simple scorer for faster execution
        scorer = make_scorer(accuracy_score)
        model = SimilarityBasedClassifier(verbose=False)
        scores = cross_val_score(model, X, y, cv=skf, scoring=scorer)
        print("Cross-validation in progress (no detailed output)...")

    # Check for NaN in scores
    if np.any(np.isnan(scores)):
        print(f"WARNING: Some scores are NaN: {scores}")
        # Filter out NaN values
        valid_scores = scores[~np.isnan(scores)]
        if len(valid_scores) == 0:
            print("ERROR: All scores are NaN!")
            return
        scores = valid_scores

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

# Debug function to check data
def debug_data():
    """Debug function to examine data structure"""
    print("=== Data Debug Information ===")
    df = load_data_fixed(str(config.NOLOOP_ENCODED_TRACE))
    print(f"Total rows: {len(df)}")
    print(f"Columns: {df.columns.tolist()}")
    print(f"First few rows:")
    for i in range(min(5, len(df))):
        trace = df['encoded_trace'].iloc[i]
        print(f"  Row {i}: ID={df['id'].iloc[i]}, Trace length={len(trace) if isinstance(trace, list) else 'Invalid'}")
        if isinstance(trace, list) and len(trace) > 0:
            print(f"    First element: {trace[0]}")

    # Test similarity calculation
    if len(df) >= 2:
        trace1 = df['encoded_trace'].iloc[0]
        trace2 = df['encoded_trace'].iloc[1]
        if isinstance(trace1, list) and isinstance(trace2, list):
            try:
                sim = edit_similarity_fixed(trace1, trace2)
                print(f"\nTest similarity between first two traces: {sim}")
            except Exception as e:
                print(f"\nError calculating test similarity: {e}")

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
        elif sys.argv[1] == 'debug':
            debug_data()
        else:
            print("Usage:")
            print("  python eval/benchmark.py                  # Full verbose cross-validation")
            print("  python eval/benchmark.py quick            # Quick test with 100 samples")
            print("  python eval/benchmark.py silent           # Full cross-validation without verbose output")
            print("  python eval/benchmark.py sample N         # Cross-validation with N samples")
            print("  python eval/benchmark.py debug            # Debug data loading and similarity calculation")
    else:
        # Default: full verbose cross-validation
        cross_validation()
