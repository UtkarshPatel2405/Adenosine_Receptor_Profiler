import logging

import numpy as np
from mapie.regression import CrossConformalRegressor

from src.config import MAPIE_CV_FOLDS, MAPIE_CONFIDENCE

logger = logging.getLogger(__name__)


def train_conformal_model(base_model, X_train, y_train, cv=MAPIE_CV_FOLDS):
    """
    Train a CrossConformalRegressor wrapper around a base estimator.

    Uses Jackknife+ (method="plus") for mathematically guaranteed
    conformal prediction intervals at the specified confidence level.
    """
    mapie = CrossConformalRegressor(
        estimator=base_model,
        cv=cv,
        confidence_level=MAPIE_CONFIDENCE,
        method="plus",
        n_jobs=1,
    )
    mapie.fit_conformalize(X_train, y_train)
    logger.info("Conformal model trained: cv=%d, confidence=%.2f", cv, MAPIE_CONFIDENCE)
    return mapie


