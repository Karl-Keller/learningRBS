"""
Conflict Resolution Strategies for Rete-based Inference Engine

This module implements various conflict resolution strategies for selecting
which rule to fire when multiple rules match the current working memory.
"""

import random


class ConflictResolutionStrategy:
    """Base class for conflict resolution strategies"""
    
    def select(self, agenda):
        """Select a production from the agenda
        
        Args:
            agenda: List of (production, token) pairs representing matched rules
            
        Returns:
            A (production, token) pair to execute, or None if agenda is empty
        """
        raise NotImplementedError("Subclasses must implement select()")
    
    def provide_feedback(self, fired_rule, success_factor):
        """Provide feedback about the success of a fired rule
        
        Args:
            fired_rule: The production rule that was fired
            success_factor: How successful the rule was (-1.0 to 1.0)
        """
        pass  # Optional method, only needed for learning strategies


class DefaultStrategy(ConflictResolutionStrategy):
    """Default strategy - selects the first production in the agenda"""
    
    def select(self, agenda):
        """Select the first rule in the agenda
        
        Args:
            agenda: List of (production, token) pairs
            
        Returns:
            First (production, token) pair, or None if agenda is empty
        """
        if agenda:
            return agenda[0]
        return None


class LEXStrategy(ConflictResolutionStrategy):
    """LEX strategy - prioritizes based on recency of working memory elements
    
    The LEX strategy (used in OPS5) prioritizes rules that match the most
    recently added working memory elements.
    """
    
    def select(self, agenda):
        """Select the rule matching the most recent working memory elements
        
        Args:
            agenda: List of (production, token) pairs
            
        Returns:
            (production, token) pair with highest recency, or None if agenda is empty
        """
        if not agenda:
            return None
            
        # Sort by recency of WMEs
        def recency_score(item):
            production, token = item
            # Calculate recency based on WME timestamps or IDs
            wmes = token.get_wmes()
            # Assuming newer WMEs have higher IDs or timestamps
            return sum(id(wme) for wme in wmes)
            
        return sorted(agenda, key=recency_score, reverse=True)[0]


class GamblersBucketBrigade(ConflictResolutionStrategy):
    """Gambler's Bucket Brigade strategy
    
    This strategy uses a form of reinforcement learning to adapt rule selection
    based on past performance. Rules that lead to successful outcomes get higher
    weights, increasing their chance of being selected in the future.
    """
    
    def __init__(self, learning_rate=0.1, initial_weight=1.0):
        """Initialize the Gambler's Bucket Brigade
        
        Args:
            learning_rate: Rate at which weights are adjusted (0.0-1.0)
            initial_weight: Initial weight for new rules
        """
        self.rule_weights = {}  # Maps rule names to weights
        self.learning_rate = learning_rate
        self.initial_weight = initial_weight
        self.last_fired_rule = None
        
    def select(self, agenda):
        """Select a rule probabilistically based on weights
        
        Args:
            agenda: List of (production, token) pairs
            
        Returns:
            Selected (production, token) pair, or None if agenda is empty
        """
        if not agenda:
            return None
            
        # Initialize weights for new rules
        for production, _ in agenda:
            if production.name not in self.rule_weights:
                self.rule_weights[production.name] = self.initial_weight
        
        # Calculate total weight
        total_weight = sum(self.rule_weights[prod.name] for prod, _ in agenda)
        
        # Special case: If all weights are zero, use uniform selection
        if total_weight <= 0:
            return random.choice(agenda)
        
        # Probabilistic selection (roulette wheel)
        selection = random.random() * total_weight
        current = 0
        
        for item in agenda:
            production, token = item
            current += self.rule_weights[production.name]
            if current >= selection:
                self.last_fired_rule = production
                return item
                
        # Fallback (should not reach here unless floating point issues)
        selected_item = agenda[0]
        self.last_fired_rule = selected_item[0]
        return selected_item
    
    def provide_feedback(self, fired_rule, success_factor):
        """Update rule weights based on success
        
        Args:
            fired_rule: The rule that was fired
            success_factor: How successful the rule was (-1.0 to 1.0)
        """
        if fired_rule.name in self.rule_weights:
            # Update weight - increase on success, decrease on failure
            adjustment = success_factor * self.learning_rate
            self.rule_weights[fired_rule.name] += adjustment
            
            # Ensure weight stays positive
            self.rule_weights[fired_rule.name] = max(0.1, self.rule_weights[fired_rule.name])
    
    def get_rule_weights(self):
        """Get the current rule weights
        
        Returns:
            Dictionary mapping rule names to weights
        """
        return self.rule_weights.copy()
    
    def set_rule_weights(self, weights):
        """Set rule weights explicitly
        
        Args:
            weights: Dictionary mapping rule names to weights
        """
        self.rule_weights.update(weights)


class MEAStrategy(ConflictResolutionStrategy):
    """MEA (Means-Ends Analysis) strategy
    
    Prioritizes rules based on how much they move the system toward a goal state.
    This is a simplified version that requires rules to have a 'goal_distance' attribute.
    """
    
    def select(self, agenda):
        """Select the rule that minimizes distance to goal
        
        Args:
            agenda: List of (production, token) pairs
            
        Returns:
            (production, token) pair with minimum goal distance
        """
        if not agenda:
            return None
            
        # Sort by goal distance (assuming productions have this attribute)
        def goal_distance(item):
            production, _ = item
            return getattr(production, 'goal_distance', float('inf'))
            
        return sorted(agenda, key=goal_distance)[0]