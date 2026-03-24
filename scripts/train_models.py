#!/usr/bin/env python3
"""
Standalone script to train and register ML models for MHRAS.

This script:
1. Generates synthetic training data based on realistic mental health distributions
2. Trains logistic regression and LightGBM models
3. Registers models in the ModelRegistry
"""

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from src.ml.baseline_models import BaselineModelTrainer
from src.ml.model_registry import ModelRegistry
from src.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


def generate_synthetic_data(n_samples: int = 5000, random_state: int = 42) -> pd.DataFrame:
    """
    Generate synthetic mental health screening data.

    The data is generated to reflect realistic distributions of PHQ-9 and GAD-7 scores
    in the general population, with correlations that would be clinically meaningful.

    Args:
        n_samples: Number of samples to generate
        random_state: Random seed for reproducibility

    Returns:
        DataFrame with synthetic features and binary risk label
    """
    np.random.seed(random_state)

    # PHQ-9 scores: skewed towards lower values (general population distribution)
    # Mild-moderate depression is relatively common, severe is rarer
    phq9_base = np.random.gamma(2, 2.5, n_samples)  # Skewed distribution
    phq9_base = np.clip(phq9_base, 0, 27).astype(int)

    # GAD-7 scores: similar distribution pattern
    gad7_base = np.random.gamma(2, 2, n_samples)
    gad7_base = np.clip(gad7_base, 0, 21).astype(int)

    # Sleep hours: normal distribution centered around 7 hours
    sleep_hours = np.random.normal(7, 1.5, n_samples)
    sleep_hours = np.clip(sleep_hours, 3, 12)

    # Heart rate: normal distribution
    heart_rate = np.random.normal(72, 10, n_samples)
    heart_rate = np.clip(heart_rate, 50, 110).astype(int)

    # Activity level (days per week with 30+ min activity)
    activity_days = np.random.poisson(3.5, n_samples)
    activity_days = np.clip(activity_days, 0, 7)

    # Social support score (1-5 scale)
    social_support = np.random.choice([1, 2, 3, 4, 5], n_samples, p=[0.05, 0.1, 0.35, 0.35, 0.15])

    # History of mental health treatment (binary)
    has_history = np.random.choice([0, 1], n_samples, p=[0.7, 0.3])

    # Age group (encoded as numeric for model)
    age_groups = np.random.choice([0, 1, 2, 3, 4], n_samples, p=[0.1, 0.25, 0.35, 0.2, 0.1])

    # Life stressors score (0-10)
    stressors = np.random.exponential(2.5, n_samples)
    stressors = np.clip(stressors, 0, 10).astype(int)

    # Combine features into DataFrame
    data = pd.DataFrame({
        'phq9_score': phq9_base,
        'gad7_score': gad7_base,
        'sleep_hours': sleep_hours,
        'avg_heart_rate': heart_rate,
        'activity_days': activity_days,
        'social_support': social_support,
        'has_mental_health_history': has_history,
        'age_group': age_groups,
        'life_stressors': stressors
    })

    # Create correlated risk indicator based on clinically meaningful combinations
    # High PHQ-9 + High GAD-7 + Poor sleep + High stressors = Higher risk
    risk_score = (
        data['phq9_score'] * 1.5 +
        data['gad7_score'] * 1.2 +
        (10 - data['sleep_hours']) * 0.8 +
        data['life_stressors'] * 0.6 +
        (5 - data['social_support']) * 0.5 -
        data['activity_days'] * 0.3 -
        data['has_mental_health_history'] * 2  # Prior treatment = already managing
    )

    # Normalize and create binary label
    # Higher risk threshold
    risk_score_normalized = (risk_score - risk_score.min()) / (risk_score.max() - risk_score.min())
    data['risk_label'] = (risk_score_normalized > 0.55).astype(int)

    logger.info(f"Generated {n_samples} samples with {data['risk_label'].sum()} positive cases ({data['risk_label'].mean()*100:.1f}%)")

    return data


def train_and_register_models(
    n_samples: int = 5000,
    model_dir: str = "models",
    registry_dir: str = "models/registry",
    random_state: int = 42
) -> dict:
    """
    Train models and register them in the ModelRegistry.

    Args:
        n_samples: Number of training samples
        model_dir: Directory for saving models
        registry_dir: Directory for model registry
        random_state: Random seed

    Returns:
        Dictionary with training results
    """
    logger.info("=" * 60)
    logger.info("Starting model training pipeline")
    logger.info("=" * 60)

    # Generate synthetic data
    logger.info("\n[1/4] Generating synthetic training data...")
    data = generate_synthetic_data(n_samples=n_samples, random_state=random_state)

    # Prepare features and target
    feature_columns = [
        'phq9_score', 'gad7_score', 'sleep_hours', 'avg_heart_rate',
        'activity_days', 'social_support', 'has_mental_health_history',
        'age_group', 'life_stressors'
    ]

    X = data[feature_columns]
    y = data['risk_label']

    # Split data
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=random_state, stratify=y
    )

    logger.info(f"Training set: {len(X_train)} samples")
    logger.info(f"Validation set: {len(X_val)} samples")

    # Initialize trainer and registry
    trainer = BaselineModelTrainer(model_dir=model_dir, random_state=random_state)
    registry = ModelRegistry(registry_dir=registry_dir)

    results = {}

    # Train Logistic Regression
    logger.info("\n[2/4] Training Logistic Regression model...")
    try:
        lr_model, lr_metadata = trainer.train_logistic_regression(
            X_train, y_train, X_val, y_val,
            cv=5,
            search_method='random'
        )

        # Register model
        lr_model_id = registry.register_model(
            model=lr_model,
            model_type='logistic_regression',
            metadata={
                'name': 'Logistic Regression Risk Classifier',
                'version': '1.0.0',
                'description': 'Baseline logistic regression model for mental health risk assessment',
                'performance_metrics': {
                    'cv_auroc': lr_metadata.get('cv_score'),
                    'val_auroc': lr_metadata.get('val_score')
                },
                'training_samples': len(X_train),
                'validation_samples': len(X_val)
            },
            artifacts={'scaler': trainer._get_lr_scaler() if hasattr(trainer, '_get_lr_scaler') else None},
            set_active=True
        )

        results['logistic_regression'] = {
            'model_id': lr_model_id,
            'metadata': lr_metadata
        }
        logger.info(f"✓ Logistic Regression registered as {lr_model_id}")

    except Exception as e:
        logger.error(f"Failed to train Logistic Regression: {e}")

    # Train LightGBM
    logger.info("\n[3/4] Training LightGBM model...")
    try:
        lgbm_model, lgbm_metadata = trainer.train_lgbm(
            X_train, y_train, X_val, y_val,
            early_stopping_rounds=50,
            cv=5
        )

        # Register model
        lgbm_model_id = registry.register_model(
            model=lgbm_model,
            model_type='lightgbm',
            metadata={
                'name': 'LightGBM Risk Classifier',
                'version': '1.0.0',
                'description': 'Gradient boosting model for mental health risk assessment',
                'performance_metrics': {
                    'cv_auroc': lgbm_metadata.get('cv_score'),
                    'val_auroc': lgbm_metadata.get('val_score')
                },
                'training_samples': len(X_train),
                'validation_samples': len(X_val)
            },
            set_active=True
        )

        results['lightgbm'] = {
            'model_id': lgbm_model_id,
            'metadata': lgbm_metadata
        }
        logger.info(f"✓ LightGBM registered as {lgbm_model_id}")

    except Exception as e:
        logger.error(f"Failed to train LightGBM: {e}")

    # Summary
    logger.info("\n[4/4] Training complete!")
    logger.info("=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)

    active_models = registry.get_active_models()
    logger.info(f"Total models registered: {len(registry.list_models())}")
    logger.info(f"Active models: {len(active_models)}")

    for model in active_models:
        logger.info(f"  - {model['model_id']} ({model['model_type']})")

    return results


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Train and register MHRAS models')
    parser.add_argument('--samples', type=int, default=5000, help='Number of training samples')
    parser.add_argument('--model-dir', default='models', help='Model directory')
    parser.add_argument('--registry-dir', default='models/registry', help='Registry directory')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')

    args = parser.parse_args()

    results = train_and_register_models(
        n_samples=args.samples,
        model_dir=args.model_dir,
        registry_dir=args.registry_dir,
        random_state=args.seed
    )

    if results:
        print("\n✓ Model training completed successfully!")
        return 0
    else:
        print("\n✗ Model training failed!")
        return 1


if __name__ == '__main__':
    sys.exit(main())
