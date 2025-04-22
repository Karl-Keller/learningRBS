from collections import defaultdict, deque
import random
import copy

from conflictResolution import DefaultStrategy, GamblersBucketBrigade

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
        """Add a WME to this alpha memory and notify successors"""
        print(f"  Alpha memory activate_with called with WME: {wme}")
        if wme not in self.items:
            print(f"    Adding WME to alpha memory: {wme}")
            self.items.append(wme)
            wme.alpha_memories.append(self)
            for successor in self.successors:
                print(f"    Notifying successor: {successor}")
                successor.right_activation(wme)
        else:
            print(f"    WME already in alpha memory: {wme}")

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
        print(f"Right activation with WME: {wme}")
        if not self.parent:
            # This is a root node, create a new token
            token = Token(None, wme)
            for child in self.children:
                child.left_activation(token, wme)
            return
        
        # Get tokens from parent beta memory and perform join tests
        # Fix here: self.parent is already the beta memory
        for token in self.parent.items:  # Changed from self.parent.beta_memory.items
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
        print(f"Testing token {token} with WME {wme}")
        for test in self.tests:
            result = test(token, wme)
            print(f"  Test result: {result}")
            if not result:
                return False
        return True

class BetaMemory:
    """Beta memory in the discrimination network"""
    def __init__(self, parent=None):
        self.items = []  # Tokens
        self.parent = parent  # Parent join node
        self.children = []  # Child join nodes
    
    def left_activation(self, token, wme=None):
        """Called when a new token should be added to this memory
        
        We've added a default wme=None parameter to match how it's called
        """
        if wme is not None:
            # If wme is provided, create a new token with it
            new_token = Token(token, wme)
        else:
            # If no wme, just use the token as is (already a Token object)
            new_token = token
            
        self.items.append(new_token)
        
        # Activate child join nodes
        for child in self.children:
            if hasattr(child, 'left_activation'):
                child.left_activation(new_token)

class ProductionNode:
    """Production node (terminal node) in the network"""
    def __init__(self, parent=None, production=None):
        self.parent = parent  # Parent beta memory
        self.production = production  # The production rule
        self.items = []  # Tokens that match the production
    
    def left_activation(self, token, wme=None):
        """Called when a new token satisfies the production
        Add debug logging here!
        """
        print(f"Production {self.production.name} activated with token: {token}")
        new_token = Token(token, wme) if wme else token
        self.items.append(new_token)
        
        # Add this line to print token details
        print(f"Token WMEs: {[wme for wme in new_token.get_wmes()]}")

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
        if variable_bindings is None:
            print(f"Skipping execution of {self.name} due to missing variable bindings")
            return
            
        for action in self.actions:
            action(variable_bindings, engine)
    
    # def _get_variable_bindings(self, token):
    #     """Get variable bindings from the token"""
    #     bindings = {}
    #     wmes = token.get_wmes()
        
    #     print(f"Getting bindings from token with WMEs: {wmes}")
    #     print(f"Conditions: {self.conditions}")
        
    #     # The token might not have WMEs in the same order as conditions
    #     # So we need a more robust approach to extract bindings
        
    #     # First collect all values from the WMEs
    #     wme_values = {}
    #     for wme in wmes:
    #         # Store each WME's identifier, attribute, and value
    #         if isinstance(wme.identifier, str):
    #             wme_values[wme.identifier] = wme.identifier
    #         if isinstance(wme.attribute, str):
    #             wme_values[wme.attribute] = wme.attribute
    #         if isinstance(wme.value, str) or isinstance(wme.value, (int, float)):
    #             wme_values[wme.value] = wme.value
        
    #     # Then extract variable bindings
    #     for condition in self.conditions:
    #         # Check if identifier is a variable
    #         if isinstance(condition.identifier, str) and condition.identifier.startswith('?'):
    #             # For variables like ?person, we need to find the actual value
    #             # This is more complex and depends on your join tests
    #             # For now, we'll use a simple approach based on the WMEs
    #             for wme in wmes:
    #                 if condition.attribute == wme.attribute:
    #                     bindings[condition.identifier] = wme.identifier
            
    #         # Check if attribute is a variable
    #         if isinstance(condition.attribute, str) and condition.attribute.startswith('?'):
    #             for wme in wmes:
    #                 bindings[condition.attribute] = wme.attribute
            
    #         # Check if value is a variable
    #         if isinstance(condition.value, str) and condition.value.startswith('?'):
    #             for wme in wmes:
    #                 if condition.attribute == wme.attribute:
    #                     bindings[condition.value] = wme.value
        
    #     print(f"Extracted bindings: {bindings}")
    #     return bindings
    
    def _get_variable_bindings(self, token):
        """Get variable bindings from the token"""
        bindings = {}
        wmes = token.get_wmes()
        
        print(f"Getting bindings from token with WMEs: {wmes}")
        
        # Extract all possible variable bindings
        for wme in wmes:
            if wme.attribute == 'name':
                bindings['?name'] = wme.value
            elif wme.attribute == 'age':
                bindings['?age'] = wme.value
            elif wme.attribute == 'min-age':
                bindings['?min_age'] = wme.value
            
            # Also bind ?person variable
            if wme.attribute in ('name', 'age'):
                bindings['?person'] = wme.identifier
        
        # Check if we have all required bindings
        required_vars = ['?name', '?age', '?min_age']
        missing_vars = [var for var in required_vars if var not in bindings]
        if missing_vars:
            print(f"Warning: Missing variable bindings: {missing_vars}")
            # Add dummy values or skip execution
            return None
        
        print(f"Extracted bindings: {bindings}")
        return bindings

class ReteNetwork:
    """The discrimination network implementation"""
    def __init__(self):
        self.alpha_root = {}  # Maps test types to alpha nodes
        self.beta_root = None  # Root of the beta network
        self.productions = []  # Production nodes
        
    def add_production(self, production):
        """Add a production to the network"""
        current_node = self.build_or_share_network_for_conditions(production.conditions)
        
        # Create a production node
        pnode = ProductionNode(current_node, production)
        current_node.children.append(pnode)
        
        # Add to the productions list (this is what was missing)
        self.productions.append(pnode)
        
        return pnode
        
    def build_or_share_network_for_conditions(self, conditions):
        """Build or share the network for a set of conditions"""
        current_node = self.beta_root
        earlier_conditions = []
        
        for condition in conditions:
            # Build or share alpha memory
            alpha_memory = self.build_or_share_alpha_memory(condition)
            
            # Store the condition in earlier_conditions
            earlier_conditions.append(condition)
            
            # Build or share beta network
            current_node = self.build_or_share_beta_memory(
                current_node, 
                alpha_memory, 
                condition,
                earlier_conditions[:-1]  # All conditions except the current one
            )
            
        return current_node
    
    def build_or_share_alpha_memory(self, condition):
        """Build or share an alpha memory for a condition"""
        print(f"Building alpha memory for condition: {condition}")
        tests = self._get_alpha_tests(condition)
        print(f"Alpha tests: {tests}")
        
        # Find or create the alpha memory
        current_node = self.alpha_root
        print(f"Alpha root: {current_node}")
        
        for test in tests:
            print(f"  Processing test: {test}")
            if test not in current_node:
                print(f"    Creating new node for test {test}")
                current_node[test] = {}
            current_node = current_node[test]
            print(f"    Current node after test: {current_node}")
        
        if 'memory' not in current_node:
            print(f"  Creating new alpha memory")
            current_node['memory'] = AlphaMemory()
        else:
            print(f"  Reusing existing alpha memory")
        
        print(f"  Final alpha memory: {current_node['memory']}")
        return current_node['memory']
    
    def build_or_share_beta_memory(self, parent, alpha_memory, condition, earlier_conditions):
        """Build or share a beta memory and join node"""
        # Create beta memory if needed
        if not parent:
            # Create a dummy top beta memory if none exists
            if not self.beta_root:
                self.beta_root = BetaMemory()
                # Store earlier conditions in the beta memory
                self.beta_root.earlier_conditions = earlier_conditions
            beta_memory = self.beta_root
        else:
            # Check if an existing beta memory can be shared
            for child in parent.children:
                if (isinstance(child, JoinNode) and 
                    child.alpha_memory == alpha_memory and 
                    child.tests == self._get_join_tests(parent, alpha_memory, condition, earlier_conditions)):
                    return child.beta_memory
                
            # Create a new beta memory
            beta_memory = BetaMemory(parent)
            # Store earlier conditions
            beta_memory.earlier_conditions = earlier_conditions
            parent.children.append(beta_memory)
        
        # Create join node
        join_node = JoinNode(
            parent=parent,
            alpha_memory=alpha_memory,
            tests=self._get_join_tests(parent, alpha_memory, condition, earlier_conditions)
        )
        print(f"Created join node with tests: {join_node.tests}")
        
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

        print(f"Alpha tests: {tests}")       
        return tests
    
    def _get_join_tests(self, parent, alpha_memory, condition, earlier_conditions):
        """Get join tests for a condition"""
        tests = []
        
        # No join tests for root node
        if not parent:
            return tests
            
        # If condition identifier is a variable
        if isinstance(condition.identifier, str) and condition.identifier.startswith('?'):
            var_name = condition.identifier
            
            # Check earlier conditions for the same variable
            for i, earlier_cond in enumerate(earlier_conditions):
                # If variable appears in identifier position
                if earlier_cond.identifier == var_name:
                    tests.append(self._make_test(i, 'identifier', 'identifier'))
                
                # If variable appears in attribute position
                if earlier_cond.attribute == var_name:
                    tests.append(self._make_test(i, 'attribute', 'identifier'))
                
                # If variable appears in value position
                if earlier_cond.value == var_name:
                    tests.append(self._make_test(i, 'value', 'identifier'))
        
        # Similar checks for attribute and value
        # Add similar code for attributes and values
        
        return tests
    
    def _make_test(self, condition_number, field_of_earlier_wme, field_of_this_wme):
        """Create a join test function that compares fields between WMEs"""
        def test(token, wme):
            path = token.get_wmes()
            if len(path) <= condition_number:
                return False
                
            earlier_wme = path[condition_number]
            
            # Get the value from the earlier WME
            earlier_value = getattr(earlier_wme, field_of_earlier_wme)
            
            # Get the value from the current WME
            this_value = getattr(wme, field_of_this_wme)
            
            # Compare the values
            return earlier_value == this_value
                
        return test
        
    def add_wme(self, wme):
        """Add a working memory element to the network"""
        # Activate alpha memories
        # alpha_tests = [
        #     ('identifier', wme.identifier),
        #     ('attribute', wme.attribute),
        #     ('value', wme.value)
        # ]
        self._activate_alpha_memories(self.alpha_root, wme)
    
    def _activate_alpha_memories(self, node, wme, test_idx=0):
        """Recursively activate alpha memories"""
        # If we've reached a memory node, activate it
        if 'memory' in node:
            node['memory'].activate_with(wme)
            
        # Check each possible path in the alpha network
        for key in node:
            if key == 'memory':
                continue
                
            # If this is a constant test
            if isinstance(key, tuple) and len(key) == 2:
                field_type, field_value = key
                
                # Get actual WME value for this field
                wme_value = None
                if field_type == 'identifier':
                    wme_value = wme.identifier
                elif field_type == 'attribute':
                    wme_value = wme.attribute
                elif field_type == 'value':
                    wme_value = wme.value
                    
                # If it matches, follow this path
                if wme_value == field_value:
                    self._activate_alpha_memories(node[key], wme)
                
            # For variable tests, always follow
            elif key == ('?', field_type):
                self._activate_alpha_memories(node[key], wme)

    def dump_network_state(self):
        """Print the current state of the network for debugging"""
        print("\n--- NETWORK STATE ---")
        print("Alpha memories:")
        for am in self._get_all_alpha_memories():
            print(f"  Items: {am.items}")
        
        print("\nBeta memories:")
        # Traverse beta network and print contents
        self._dump_beta_node(self.beta_root)
        
        print("\nProduction nodes:")
        for prod_node in self.productions:
            # Fix this line to access production.name instead of name directly
            print(f"  {prod_node.production.name}: {len(getattr(prod_node, 'items', []))} matches")
        print("--------------------\n")

    def _get_all_alpha_memories(self):
        """Get all alpha memories in the network"""
        memories = []
        self._collect_alpha_memories(self.alpha_root, memories)
        return memories

    def _collect_alpha_memories(self, node, memories):
        """Recursively collect alpha memories"""
        if 'memory' in node:
            memories.append(node['memory'])
        
        for key, child in node.items():
            if key != 'memory' and isinstance(child, dict):
                self._collect_alpha_memories(child, memories)
                
    def _dump_beta_node(self, node, level=0):
        """Recursively print beta network state"""
        if node is None:
            return
            
        indent = "  " * level
        if hasattr(node, 'items'):
            print(f"{indent}Beta memory: {len(node.items)} items")
            
        if hasattr(node, 'children'):
            for child in node.children:
                self._dump_beta_node(child, level + 1)

class InferenceEngine:
    def __init__(self, strategy=None):
        self.working_memory = []
        self.network = ReteNetwork()
        self.agenda = []
        self.strategy = strategy or DefaultStrategy()  # Use default if none provided
    
    # ... other methods ...
    
    def set_conflict_resolution_strategy(self, strategy):
        """Set the conflict resolution strategy"""
        self.strategy = strategy
    
    def _select_production(self):
        """Select a production to execute using the current strategy"""
        result = self.strategy.select(self.agenda)

        return result
    
    def provide_feedback(self, fired_rule, success_factor):
        """Provide feedback to the conflict resolution strategy"""
        if hasattr(self.strategy, 'update_weights'):
            self.strategy.update_weights(fired_rule, success_factor)
    
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
        print("Starting inference engine run")
        cycle = 0
        
        # This line is crucial - it builds the initial agenda
        self._build_conflict_set()
        
        while cycle < max_cycles:
            # If no rules to fire, we're done
            if not self.agenda:
                print(f"No more rules to fire after {cycle} cycles")
                break
                
            # Select a rule using conflict resolution
            print(f"Selecting production from {len(self.agenda)} items in agenda")
            selection = self._select_production()
            
            if selection is None:
                print("No production selected")
                break
                
            production, token = selection
            print(f"Selected {production.name}")
            
            # Execute the rule
            print(f"Executing {production.name}")
            production.execute(token, self)
            
            # Build new conflict set for next cycle
            self._build_conflict_set()
            
            cycle += 1
            
        return cycle
    
    def _build_conflict_set(self):
        """Build the conflict set of activations"""
        print("Building conflict set")
        self.agenda = []  # Clear the current agenda
        
        # Add matches from production nodes to agenda
        for prod_node in self.network.productions:
            print(f"Checking production node: {prod_node.production.name} with {len(prod_node.items)} matches")
            for token in prod_node.items:
                print(f"  Adding to agenda: {prod_node.production.name} with token {token}")
                self.agenda.append((prod_node.production, token))
        
        print(f"Built agenda with {len(self.agenda)} items")
    
    def dump_state(self):
        """Dump the current state of the engine"""
        print(f"\n=== ENGINE STATE ===")
        print(f"Working memory: {len(self.working_memory)} elements")
        print(f"Agenda: {len(self.agenda)} productions ready to fire")
        print("Productions in network:", [p.production.name for p in self.network.productions])
        self.network.dump_network_state()
        print(f"===================\n")

# Example usage
# def main():
#     engine = InferenceEngine()
    
#     # Define a rule
#     engine.add_production(
#         "example-rule",
#         [
#             Condition("?person", "name", "?name"),
#             Condition("?person", "age", "?age"),
#             Condition("legal", "min-age", "?min_age")
#         ],
#         [
#             lambda bindings, engine: print(f"{bindings['?name']} is {'old enough' if bindings['?age'] >= bindings['?min_age'] else 'too young'}")
#         ]
#     )
    
#     # Add facts
#     engine.add_wme("person1", "name", "Alice")
#     engine.add_wme("person1", "age", 25)
#     engine.add_wme("legal", "min-age", 18)

#     # Check the network state
#     engine.dump_state()
    
#     # Build the conflict set first
#     print("Building conflict set...")
#     engine._build_conflict_set()
    
#     # Run and provide feedback
#     result = engine._select_production()
#     if result is not None:
#         production, token = result
#         print(f"Executing production: {production.name}")
#         production.execute(token, engine)
#         engine.provide_feedback(production, 0.5)  # Positive feedback
#     else:
#         print("No rules matched - agenda is empty.")

def main():
    engine = InferenceEngine()
    
    # Define a rule
    engine.add_production(
        "example-rule",
        [
            Condition("?person", "name", "?name"),
            Condition("?person", "age", "?age"),
            Condition("legal", "min-age", "?min_age")
        ],
        [
            lambda bindings, engine: print(f"{bindings['?name']} is {'old enough' if bindings['?age'] >= bindings['?min_age'] else 'too young'}")
        ]
    )
    
    # Add facts
    engine.add_wme("person1", "name", "Alice")
    engine.add_wme("person1", "age", 25)
    engine.add_wme("legal", "min-age", 18)
    
    # Check the network state
    engine.dump_state()
    
    # Run the engine for one cycle
    print("Running inference engine...")
    engine.run(max_cycles=1)


if __name__ == "__main__":
    main()