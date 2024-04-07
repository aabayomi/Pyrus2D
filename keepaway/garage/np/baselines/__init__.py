"""Baselines (value functions) which use NumPy as a numerical backend."""
from keepaway.garage.np.baselines.base import Baseline
from keepaway.garage.np.baselines.linear_feature_baseline import LinearFeatureBaseline
from keepaway.garage.np.baselines.zero_baseline import ZeroBaseline

__all__ = ['Baseline', 'LinearFeatureBaseline', 'ZeroBaseline']
