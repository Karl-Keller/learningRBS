"""
Pattern-Matched Inference Engine with Discrimination Network (Rete Algorithm)

This package implements a rule-based inference engine using the Rete algorithm,
featuring a discrimination network for efficient pattern matching and various
conflict resolution strategies, including the Gambler's Bucket Brigade.
"""

from .retecore import (
    WME,
    AlphaMemory,
    Token,
    JoinNode,
    BetaMemory,
    ProductionNode,
    Condition, 
    Production,
    ReteNetwork,
    InferenceEngine
)

from .conflictResolution import (
    ConflictResolutionStrategy,
    DefaultStrategy,
    LEXStrategy,
    GamblersBucketBrigade
)

__all__ = [
    'WME',
    'AlphaMemory', 
    'Token',
    'JoinNode',
    'BetaMemory',
    'ProductionNode',
    'Condition',
    'Production',
    'ReteNetwork',
    'InferenceEngine',
    'ConflictResolutionStrategy',
    'DefaultStrategy',
    'LEXStrategy',
    'GamblersBucketBrigade'
]

__version__ = '0.1.0'