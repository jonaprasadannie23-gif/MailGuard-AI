"""
Model Training Module for ProbMail.
Executes stratified splitting, non-leaking pipeline assembly (TF-IDF -> Chi-Square -> MultinomialNB),
evaluation on held-out test data, artifact serialization, and metadata persistence.
"""
import os
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_selection import SelectKBest, chi2
from sklearn.naive_bayes import MultinomialNB

from config import MODELS_DIR, DEFAULT_K_BEST, DEFAULT_MAX_FEATURES, DEFAULT_TEST_SIZE, RANDOM_STATE
from ml.evaluate import evaluate_pipeline
from ml.feature_selection import analyze_selected_features


class NumpyTypeEncoder(json.JSONEncoder):
    """Custom JSON encoder converting numpy data types to native Python types."""
    def default(self, obj):
        if isinstance(obj, (np.bool_, np.bool_)):
            return bool(obj)
        elif isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


# In-memory cache to avoid disk reads on every single inference request
_CACHED_PIPELINE: Optional[Pipeline] = None
_CACHED_METADATA: Optional[Dict[str, Any]] = None
_CACHED_MTIME: float = 0.0


def train_probmail_model(
    df: pd.DataFrame,
    text_col: str = "clean_text",
    label_col: str = "label",
    k_best: int = DEFAULT_K_BEST,
    max_features: int = DEFAULT_MAX_FEATURES,
    test_size: float = DEFAULT_TEST_SIZE,
    alpha: float = 1.0,
    random_state: int = RANDOM_STATE,
    dataset_info: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Trains the end-to-end ProbMail machine learning pipeline:
    1. Stratified train/test split.
    2. Constructs Pipeline([('tfidf', ...), ('chi2', ...), ('nb', MultinomialNB())]).
    3. Fits strictly on (X_train, y_train) to guarantee zero data leakage.
    4. Evaluates strictly on held-out (X_test, y_test).
    5. Saves serialized pipeline artifact and detailed training metadata.
    """
    global _CACHED_PIPELINE, _CACHED_METADATA, _CACHED_MTIME
    start_time = time.time()
    trained_at = datetime.now(timezone.utc).isoformat()

    if df.empty or len(df) < 10:
        raise ValueError("Dataset is too small to train a reliable model (minimum 10 samples required).")

    X = df[text_col].astype(str).tolist()
    y = df[label_col].astype(str).tolist()

    classes = sorted(list(set(y)))
    if len(classes) < 2:
        raise ValueError(f"Dataset must contain at least 2 distinct classes. Found: {classes}")

    # Check class counts for stratified splitting
    class_counts = pd.Series(y).value_counts()
    min_class_count = int(class_counts.min())

    can_stratify = bool(min_class_count >= 2)
    stratify_target = y if can_stratify else None

    # 1. Train / Test Split
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        stratify=stratify_target,
        random_state=random_state
    )

    # 2. Build Pipeline
    actual_k = max(5, int(k_best))

    vectorizer_step = TfidfVectorizer(
        max_features=max_features,
        ngram_range=(1, 2),
        stop_words="english",
        sublinear_tf=True,
        min_df=1
    )

    # Quick pre-check on train vocab to cap k safely
    pre_vocab_check = vectorizer_step.fit(X_train)
    vocab_len = len(pre_vocab_check.vocabulary_)
    actual_k = min(actual_k, vocab_len)

    selector_step = SelectKBest(score_func=chi2, k=actual_k)
    classifier_step = MultinomialNB(alpha=alpha)

    pipeline = Pipeline([
        ("tfidf", vectorizer_step),
        ("chi2", selector_step),
        ("nb", classifier_step)
    ])

    # 3. Fit Pipeline on Training Data ONLY
    pipeline.fit(X_train, y_train)

    # 4. Extract Chi-Square Analysis from Training Fit
    tfidf_fitted = pipeline.named_steps["tfidf"]
    chi2_fitted = pipeline.named_steps["chi2"]
    X_train_vec = tfidf_fitted.transform(X_train)

    chi2_analysis = analyze_selected_features(
        vectorizer=tfidf_fitted,
        selector=chi2_fitted,
        X_train_vec=X_train_vec,
        y_train=y_train,
        top_n=min(50, actual_k)
    )

    # 5. Evaluate on Held-out Test Data ONLY
    evaluation_results = evaluate_pipeline(
        pipeline=pipeline,
        X_test=X_test,
        y_test=y_test,
        classes=classes
    )

    duration_seconds = round(time.time() - start_time, 3)

    # 6. Save Pipeline and Metadata
    pipeline_filename = "model_pipeline.joblib"
    pipeline_path = os.path.join(MODELS_DIR, pipeline_filename)
    metadata_path = os.path.join(MODELS_DIR, "model_metadata.json")

    metadata = {
        "model_name": "ProbMail Multinomial Naive Bayes with Chi-Square Selection",
        "trained_at": trained_at,
        "duration_seconds": duration_seconds,
        "dataset_info": dataset_info or {},
        "dataset_statistics": {
            "total_samples": len(X),
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "split_ratio": f"{int((1 - test_size) * 100)}/{int(test_size * 100)}",
            "stratified": can_stratify,
            "classes": classes,
            "class_distribution_train": {str(k): int(v) for k, v in pd.Series(y_train).value_counts().items()},
            "class_distribution_test": {str(k): int(v) for k, v in pd.Series(y_test).value_counts().items()}
        },
        "hyperparameters": {
            "k_best_features": actual_k,
            "max_features": max_features,
            "ngram_range": [1, 2],
            "nb_alpha": alpha,
            "random_state": random_state
        },
        "evaluation": evaluation_results,
        "chi_square_summary": {
            "selected_k": int(chi2_analysis["selected_k"]),
            "significant_features_count": int(chi2_analysis["significant_features_count"]),
            "top_features": chi2_analysis["features"][:30]
        },
        "pipeline_path": pipeline_path,
        "status": "active"
    }

    try:
        joblib.dump(pipeline, pipeline_path)
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, cls=NumpyTypeEncoder)
    except (OSError, PermissionError):
        tmp_models = Path("/tmp/models")
        tmp_models.mkdir(parents=True, exist_ok=True)
        pipeline_path = str(tmp_models / pipeline_filename)
        metadata_path = str(tmp_models / "model_metadata.json")
        joblib.dump(pipeline, pipeline_path)
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, cls=NumpyTypeEncoder)
        metadata["pipeline_path"] = pipeline_path

    # Update in-memory cache
    _CACHED_PIPELINE = pipeline
    _CACHED_METADATA = metadata
    try:
        _CACHED_MTIME = os.path.getmtime(pipeline_path)
    except OSError:
        _CACHED_MTIME = time.time()

    return metadata


def load_trained_pipeline() -> Tuple[Optional[Pipeline], Optional[Dict[str, Any]]]:
    """Loads the active saved pipeline and metadata, with in-memory caching."""
    global _CACHED_PIPELINE, _CACHED_METADATA, _CACHED_MTIME

    tmp_pipe = Path("/tmp/models/model_pipeline.joblib")
    tmp_meta = Path("/tmp/models/model_metadata.json")
    if tmp_pipe.exists() and tmp_meta.exists():
        pipeline_path = str(tmp_pipe)
        metadata_path = str(tmp_meta)
    else:
        pipeline_path = os.path.join(MODELS_DIR, "model_pipeline.joblib")
        metadata_path = os.path.join(MODELS_DIR, "model_metadata.json")

    if not os.path.exists(pipeline_path) or not os.path.exists(metadata_path):
        _CACHED_PIPELINE = None
        _CACHED_METADATA = None
        return None, None

    try:
        current_mtime = os.path.getmtime(pipeline_path)
        if _CACHED_PIPELINE is not None and _CACHED_METADATA is not None and current_mtime == _CACHED_MTIME:
            return _CACHED_PIPELINE, _CACHED_METADATA

        pipeline = joblib.load(pipeline_path)
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        _CACHED_PIPELINE = pipeline
        _CACHED_METADATA = metadata
        _CACHED_MTIME = current_mtime
        return pipeline, metadata
    except Exception as e:
        print(f"Error loading trained pipeline: {e}")
        return None, None


def ensure_trained_model(force_retrain: bool = False) -> Optional[Dict[str, Any]]:
    """
    Checks if a trained model exists and matches the current usable dataset.
    If not, automatically trains the model in the background so the user never needs
    to manually configure or trigger training.
    """
    from services.dataset_service import dataset_service
    from services.db import log_training_run

    cleaned_df = dataset_service.get_cleaned_dataset()
    if cleaned_df is None or len(cleaned_df) < 10:
        return None

    pipeline, metadata = load_trained_pipeline()
    needs_training = force_retrain or (pipeline is None) or (metadata is None)

    if not needs_training and metadata:
        ds_stats = metadata.get("dataset_statistics", {})
        total_samples = ds_stats.get("total_samples", 0)
        # Check if sample count matches cleaned dataset (e.g. 1352 vs 16)
        if total_samples != len(cleaned_df):
            needs_training = True

    if needs_training:
        print(f"[ProbMail ML] Automatically training pipeline on {len(cleaned_df)} usable samples...")
        dataset_info = dataset_service.get_dataset_file_info()
        meta = train_probmail_model(
            df=cleaned_df,
            text_col="clean_text",
            label_col="label",
            k_best=50,
            max_features=1500,
            test_size=0.2,
            alpha=1.0,
            dataset_info=dataset_info
        )
        try:
            log_training_run(meta)
        except Exception as e:
            print(f"[ProbMail DB] Warning: could not log training run: {e}")
        return meta

    return metadata
