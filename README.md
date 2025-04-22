# Pattern-Matched Inference Engine with Rete Algorithm

## Overview
This project implements a pattern-matched inference engine based on the Rete algorithm, originally developed by Charles Forgy. The implementation includes a discrimination network (dnet) for efficient pattern matching and rule execution, making it suitable for complex rule-based systems.

The engine is enhanced with customizable conflict resolution strategies, including the "Gambler's Bucket Brigade" approach for adaptive rule selection based on past performance through a reinforcement learning approach.

## Features
- Complete Python implementation of the Rete algorithm
- Efficient discrimination network for pattern matching
- Working memory element (WME) management
- Production rule compilation and execution
- Variable binding and pattern matching
- Pluggable conflict resolution strategies
- Visualization capabilities (optional)

## How It Works

### Rete Algorithm
The Rete algorithm creates a network of nodes that efficiently match patterns against a working memory:

1. **Alpha Network**: Tests individual conditions and filters WMEs
   - Each alpha node tests one feature (identifier, attribute, or value)
   - Alpha memories store WMEs that pass all tests for a condition

2. **Beta Network**: Joins consistent partial matches
   - Join nodes connect alpha memories with beta memories
   - Tests for consistent variable bindings across conditions
   - Beta memories store tokens (partial matches)

3. **Production Nodes**: Represent fully matched rules ready for execution
   - Connected to the final beta memory in a rule's condition network
   - Activated when all conditions for a rule are satisfied

The discrimination network structure allows for sharing of common pattern-matching operations across rules, resulting in significant performance improvements compared to naive approaches.

### Match-Select-Execute Cycle
The engine operates in a continuous cycle:

1. **Match**: Working memory elements are propagated through the network, activating appropriate production nodes
2. **Select**: A conflict resolution strategy selects one production from those that match (the agenda)
3. **Execute**: The selected production's actions are executed, potentially modifying working memory
4. **Repeat**: The cycle continues until no more productions match or a termination condition is met

### Conflict Resolution Strategies
The engine supports multiple conflict resolution strategies:

1. **DefaultStrategy**: Selects the production with the most complete match (most WMEs)
2. **LEXStrategy**: Prioritizes based on recency of working memory elements
3. **GamblersBucketBrigade**: Uses a reinforcement learning approach to adapt rule selection
4. **MEAStrategy**: Selects rules that minimize distance to a goal state

### Gambler's Bucket Brigade
The Gambler's Bucket Brigade strategy:

1. Assigns weights (or "credit") to rules based on their usefulness
2. Selects rules probabilistically based on their weights (roulette wheel selection)
3. Adjusts weights based on feedback after rule execution
4. Enables the system to learn which rules are most effective over time

This approach allows the system to adapt its behavior based on the success of previous rule executions.

## Components

### Core Classes

The system consists of the following core components, as shown in the class diagram:

1. **WME**: Working Memory Element - represents a fact in the knowledge base
   - Consists of (identifier, attribute, value) triples
   - Can be part of multiple alpha memories and tokens

2. **AlphaMemory**: Stores WMEs that match specific patterns
   - Maintains a list of successors (join nodes)
   - Activates join nodes when new WMEs are added

3. **Token**: Represents partial matches in the network
   - Links to parent token and a WME
   - Forms a chain representing a complete match

4. **JoinNode**: Connects alpha and beta memories, performing tests
   - Performs right activation when new WMEs enter alpha memory
   - Performs left activation when new tokens enter beta memory
   - Tests consistency of variable bindings

5. **BetaMemory**: Stores tokens (partial matches)
   - Maintains a list of child nodes
   - Activates children when new tokens are added

6. **ProductionNode**: Represents a fully matched rule
   - Activated when all conditions are satisfied
   - Stores tokens that match the rule

7. **Condition**: Represents a pattern to match in working memory
   - Consists of (identifier, attribute, value) where any can be a variable

8. **Production**: Represents a rule in the system
   - Contains conditions and actions
   - Extracts variable bindings for rule execution

9. **ReteNetwork**: The discrimination network implementation
   - Builds and maintains the network structure
   - Manages alpha and beta memories
   - Handles WME propagation

10. **InferenceEngine**: The main engine driving execution
    - Manages working memory
    - Implements the recognize-act cycle
    - Uses a conflict resolution strategy to select rules

11. **ConflictResolutionStrategy**: Abstract base class for rule selection
    - Selects which rule to fire when multiple rules match
    - Can be extended with custom strategies

## Usage

### Basic Usage

```python
from rete_engine import InferenceEngine, Condition

# Create the engine
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
        lambda bindings, engine: print(f"{bindings['?name']} is "
                                       f"{'old enough' if bindings['?age'] >= bindings['?min_age'] else 'too young'}")
    ]
)

# Add facts
engine.add_wme("person1", "name", "Alice")
engine.add_wme("person1", "age", 25)
engine.add_wme("legal", "min-age", 18)

# Run the engine
engine.run()
# Output: Alice is old enough
```

### Using Different Conflict Resolution Strategies

```python
from rete_engine import InferenceEngine, GamblersBucketBrigade

# Create engine with GBB strategy
engine = InferenceEngine(GamblersBucketBrigade(learning_rate=0.2))

# Add rules and facts
# ...

# Run the engine
engine.run()

# Provide feedback on rule execution
engine.provide_feedback(fired_rule, 0.8)  # Positive feedback
```

## Visualization

The engine includes visualization capabilities to help understand the Rete network structure and execution flow.

```python
# After setting up the engine and adding rules/facts
engine.dump_state()
```

This will print detailed information about the current state of the engine, including:
- Working memory elements
- Alpha and beta memories
- Production nodes
- The agenda (conflict set)

## Installation

1. Clone this repository:
```
git clone https://github.com/yourusername/rete-engine.git
cd rete-engine
```

2. Install:
```
pip install -e .
```

## Future Improvements

- Add support for negated conditions (NOT)
- Implement more advanced join conditions
- Support for rule retraction (removing facts)
- Enhanced variable binding mechanisms
- Optimize network construction for complex rule sets
- Add visualization tools for network exploration
- Support for rule priorities (salience)

## License

[Add your license information here]

## Acknowledgments

- Original Rete algorithm developed by Charles Forgy
- Gambler's Bucket Brigade concept invented by Karl Keller in the late 1980's as a credit assignment algorithm for conflict resolution 
- Jim Antonisse for leading the ML project that yielded the original research and development
- Implementation assistance provided by Claude AI (Anthropic)
- Based on concepts from production systems like OPS5 and CLIPS
