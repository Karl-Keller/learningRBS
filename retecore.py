from collections import defaultdict, deque
import random
import copy

class WME:
    """Working Memory Element"""
    def __init__(self, identifier, attribute, value):
        self.identifier = identifier
        self.attribute = attribute
        self.value = value
        self.tokens = []  # Tokens this WME is part of
        self.alpha_memories = []  # Alpha memories this WME is in
    
    def __eq__(self, other):
        return (self.identifier == other.identifier and
                self.attribute == other.attribute and
                self.value == other.value)
    
    def __hash__(self):
        return hash((self.identifier, self.attribute, self.value))
    
    def __repr__(self):
        return f"WME({self.identifier}, {self.attribute}, {self.value})"

class AlphaMemory:
    """Alpha memory in the discrimination network"""
    def __init__(self):
        self.items = []  # WMEs that match this condition
        self.successors = []  # Join nodes that use this alpha memory
    
    def activate_with(self, wme):
        if wme not in self.items:
            self.items.append(wme)
            wme.alpha_memories.append(self)
            for successor in self.successors:
                successor.right_activation(wme)

class Token:
    """Token representing a partial match"""
    def __init__(self, parent=None, wme=None):
        self.parent = parent
        self.wme = wme
        self.children = []  # Tokens that extend this token
        self.join_results = []  # Join node results using this token
        
        if parent:
            parent.children.append(self)
    
    def __eq__(self, other):
        if not other or not isinstance(other, Token):
            return False
        if self.wme != other.wme:
            return False
        return self.parent == other.parent
    
    def get_wmes(self):
        """Return all WMEs in this token's path"""
        if not self.parent:
            return []
        return self.parent.get_wmes() + [self.wme]
    
    def __repr__(self):
        return f"Token({self.wme}, {self.parent})"

class JoinNode:
    """Join node in the discrimination network"""
    def __init__(self, parent=None, alpha_memory=None, tests=None):
        self.parent = parent  # Parent join node (None for root)
        self.alpha_memory = alpha_memory  # Alpha memory for right side
        self.tests = tests or []  # Tests to perform
        self.children = []  # Children beta nodes
        self.beta_memory = None  # Successor beta memory
        
        if alpha_memory:
            alpha_memory.successors.append(self)
    
    def right_activation(self, wme):
        """Called when a new WME enters the alpha memory"""
        if not self.parent:
            # This is a root node, create a new token
            token = Token(None, wme)
            for child in self.children:
                child.left_activation(token, wme)
            return
        
        # Get tokens from parent beta memory and perform join tests
        for token in self.parent.beta_memory.items:
            if self.perform_join_tests(token, wme):
                for child in self.children:
                    child.left_activation(token, wme)
    
    def left_activation(self, token, wme):
        """Called when a new token arrives"""
        # Store the match in beta memory
        new_token = Token(token, wme)
        self.beta_memory.items.append(new_token)
        
        # Perform right activation with existing items in alpha memory
        for item in self.alpha_memory.items:
            if self.perform_join_tests(new_token, item):
                for child in self.children:
                    child.left_activation(new_token, item)
    
    def perform_join_tests(self, token, wme):
        """Perform the join tests"""
        for test in self.tests:
            if not test(token, wme):
                return False
        return True

class BetaMemory:
    """Beta memory in the discrimination network"""
    def __init__(self, parent=None):
        self.items = []  # Tokens
        self.parent = parent  # Parent join node
        self.children = []  # Child join nodes
    
    def left_activation(self, token, wme):
        """Called when a new token should be added to this memory"""
        new_token = Token(token, wme)
        self.items.append(new_token)
        
        # Activate child join nodes
        for child in self.children:
            child.left_activation(new_token)

class ProductionNode:
    """Production node (terminal node) in the network"""
    def __init__(self, parent=None, production=None):
        self.parent = parent  # Parent beta memory
        self.production = production  # The production rule
        self.items = []  # Tokens that match the production
    
    def left_activation(self, token, wme=None):
        """Called when a new token satisfies the production"""
        new_token = Token(token, wme) if wme else token
        self.items.append(new_token)

class Condition:
    """A condition in a production rule"""
    def __init__(self, identifier, attribute, value):
        self.identifier = identifier
        self.attribute = attribute
        self.value = value
        
    def __repr__(self):
        return f"Condition({self.identifier}, {self.attribute}, {self.value})"

class Production:
    """A production rule with conditions and actions"""
    def __init__(self, name, conditions, actions):
        self.name = name
        self.conditions = conditions
        self.actions = actions
        self.matches = []  # Tokens that match this production
        
    def execute(self, token, engine):
        """Execute the rule actions"""
        variable_bindings = self._get_variable_bindings(token)
        for action in self.actions:
            action(variable_bindings, engine)
    
    def _get_variable_bindings(self, token):
        """Get variable bindings from the token"""
        bindings = {}
        conditions = self.conditions
        wmes = token.get_wmes()
        
        for i, condition in enumerate(conditions):
            # Bind the variables in the condition to WME values
            if isinstance(condition.identifier, str) and condition.identifier.startswith('?'):
                bindings[condition.identifier] = wmes[i].identifier
            if isinstance(condition.attribute, str) and condition.attribute.startswith('?'):
                bindings[condition.attribute] = wmes[i].attribute
            if isinstance(condition.value, str) and condition.value.startswith('?'):
                bindings[condition.value] = wmes[i].value
                
        return bindings

class ReteNetwork:
    """The discrimination network implementation"""
    def __init__(self):
        self.alpha_root = {}  # Maps test types to alpha nodes
        self.beta_root = None  # Root of the beta network
        self.productions = []  # Production nodes
        
    def add_production(self, production):
        """Add a production to the network"""
        self.productions.append(production)
        current_node = self.build_or_share_network_for_conditions(production.conditions)
        
        # Create a production node
        pnode = ProductionNode(current_node, production)
        current_node.children.append(pnode)
        
        return pnode
        
    def build_or_share_network_for_conditions(self, conditions):
        """Build or share the network for a set of conditions"""
        current_node = self.beta_root
        
        for condition in conditions:
            # Build or share alpha memory
            alpha_memory = self.build_or_share_alpha_memory(condition)
            
            # Build or share beta network
            current_node = self.build_or_share_beta_memory(current_node, alpha_memory, condition)
            
        return current_node
    
    def build_or_share_alpha_memory(self, condition):
        """Build or share an alpha memory for a condition"""
        tests = self._get_alpha_tests(condition)
        
        # Find or create the alpha memory
        current_node = self.alpha_root
        for test in tests:
            if test not in current_node:
                current_node[test] = {}
            current_node = current_node[test]
        
        if 'memory' not in current_node:
            current_node['memory'] = AlphaMemory()
            
        return current_node['memory']
    
    def build_or_share_beta_memory(self, parent, alpha_memory, condition):
        """Build or share a beta memory and join node"""
        # Create beta memory if needed
        if not parent:
            # Create a dummy top beta memory if none exists
            if not self.beta_root:
                self.beta_root = BetaMemory()
            beta_memory = self.beta_root
        else:
            # Check if an existing beta memory can be shared
            for child in parent.children:
                if (isinstance(child, JoinNode) and 
                    child.alpha_memory == alpha_memory and 
                    child.tests == self._get_join_tests(parent, alpha_memory, condition)):
                    return child.beta_memory
                    
            # Create a new beta memory
            beta_memory = BetaMemory(parent)
            parent.children.append(beta_memory)
        
        # Create join node
        join_node = JoinNode(
            parent=parent,
            alpha_memory=alpha_memory,
            tests=self._get_join_tests(parent, alpha_memory, condition)
        )
        
        # Link the nodes
        beta_memory.parent = join_node
        join_node.beta_memory = beta_memory
        join_node.children = [beta_memory]
        
        # Perform initial right activation
        for wme in alpha_memory.items:
            join_node.right_activation(wme)
            
        return beta_memory
    
    def _get_alpha_tests(self, condition):
        """Get the alpha network tests for a condition"""
        tests = []
        
        # Add tests for each field
        if not isinstance(condition.identifier, str) or not condition.identifier.startswith('?'):
            tests.append(('identifier', condition.identifier))
            
        if not isinstance(condition.attribute, str) or not condition.attribute.startswith('?'):
            tests.append(('attribute', condition.attribute))
            
        if not isinstance(condition.value, str) or not condition.value.startswith('?'):
            tests.append(('value', condition.value))
            
        return tests
    
    def _get_join_tests(self, parent, alpha_memory, condition):
        """Get join tests for a condition"""
        tests = []
        
        # No join tests for root node
        if not parent:
            return tests
            
        # Variable binding tests
        if isinstance(condition.identifier, str) and condition.identifier.startswith('?'):
            var = condition.identifier
            for i, earlier_cond in enumerate(parent.earlier_conditions):
                if (earlier_cond.identifier == var or
                    earlier_cond.attribute == var or
                    earlier_cond.value == var):
                    tests.append(self._make_test(i, 'identifier', var))
                    
        # Add similar tests for attribute and value
        # (code omitted for brevity)
        
        return tests
    
    def _make_test(self, condition_number, field, variable):
        """Create a join test function"""
        def test(token, wme):
            path = token.get_wmes()
            if len(path) <= condition_number:
                return False
                
            earlier_wme = path[condition_number]
            return getattr(earlier_wme, field) == getattr(wme, variable.lstrip('?'))
            
        return test
        
    def add_wme(self, wme):
        """Add a working memory element to the network"""
        # Activate alpha memories
        alpha_tests = [
            ('identifier', wme.identifier),
            ('attribute', wme.attribute),
            ('value', wme.value)
        ]
        
        self._activate_alpha_memories(self.alpha_root, wme, alpha_tests)
    
    def _activate_alpha_memories(self, node, wme, tests, test_idx=0):
        """Recursively activate alpha memories"""
        if test_idx >= len(tests):
            if 'memory' in node:
                node['memory'].activate_with(wme)
            return
            
        field, value = tests[test_idx]
        
        # Activate with exact match
        if value in node:
            self._activate_alpha_memories(node[value], wme, tests, test_idx + 1)
            
        # Activate with variable match
        if ('?', field) in node:
            self._activate_alpha_memories(node[('?', field)], wme, tests, test_idx + 1)

class InferenceEngine:
    """Rule-based inference engine using a discrimination network"""
    def __init__(self):
        self.working_memory = []  # List of WMEs
        self.network = ReteNetwork()  # Discrimination network
        self.agenda = []  # Conflict set of production activations
    
    def add_production(self, name, conditions, actions):
        """Add a production rule to the engine"""
        production = Production(name, conditions, actions)
        self.network.add_production(production)
        return production
    
    def add_wme(self, identifier, attribute, value):
        """Add a working memory element to the engine"""
        wme = WME(identifier, attribute, value)
        self.working_memory.append(wme)
        self.network.add_wme(wme)
        return wme
    
    def remove_wme(self, wme):
        """Remove a working memory element from the engine"""
        if wme in self.working_memory:
            self.working_memory.remove(wme)
            # Remove from alpha memories
            for am in wme.alpha_memories:
                am.items.remove(wme)
            # Remove tokens
            for token in wme.tokens:
                self._remove_token(token)
    
    def _remove_token(self, token):
        """Remove a token and its descendants from the network"""
        for child in token.children:
            self._remove_token(child)
        for jr in token.join_results:
            jr.owner.items.remove(jr)
        if token.wme:
            token.wme.tokens.remove(token)
    
    def run(self, max_cycles=100):
        """Run the inference engine"""
        cycle = 0
        while cycle < max_cycles:
            # Build conflict set
            self._build_conflict_set()
            
            # If no rules to fire, we're done
            if not self.agenda:
                break
                
            # Select a rule using conflict resolution
            production, token = self._select_production()
            
            # Execute the rule
            production.execute(token, self)
            
            cycle += 1
            
        return cycle
    
    def _build_conflict_set(self):
        """Build the conflict set of activations"""
        self.agenda = []
        for prod_node in self.network.productions:
            for token in prod_node.items:
                self.agenda.append((prod_node.production, token))
    
    def _select_production(self):
        """Select a production to execute (conflict resolution)"""
        # Default strategy: select the first production
        # This is where you would implement your "gambler's bucket brigade"
        return self.agenda[0]

# Example usage
def main():
    engine = InferenceEngine()
    
    # Define a rule
    engine.add_production(
        "example-rule",
        [
            Condition("person", "name", "?name"),
            Condition("person", "age", "?age"),
            Condition("threshold", "min-age", "?min_age")
        ],
        [
            lambda bindings, engine: print(f"{bindings['?name']} is {'old enough' if bindings['?age'] >= bindings['?min_age'] else 'too young'}")
        ]
    )
    
    # Add facts
    engine.add_wme("person1", "name", "Alice")
    engine.add_wme("person1", "age", 25)
    engine.add_wme("threshold", "min-age", 18)
    
    # Run the engine
    engine.run()

if __name__ == "__main__":
    main()