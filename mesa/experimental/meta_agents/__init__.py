"""Meta agents - Agents that are composed of other agents.

A meta agent is an agent that contains and manages other agents, while being an agent itself.
It leverages Mesa's AgentSet functionality to manage its components efficiently.

Example uses:
    - Organizations made up of individual agents
    - Complex entities like vehicles made up of component agents
    - Hierarchical structures where groups of agents act as a unit

Basic usage:
    ```python
    class Robot(MetaAgent):
        def __init__(self, model, components=None):
            super().__init__(model, components)
            # Compute robot properties from components
            self.power = self.components.agg("power", sum)

    # Create robot from components
    robot = Robot(model, components={engine, wheel1, wheel2})

    # Add/remove components
    robot.add_component(sensor)
    robot.remove_component(wheel1)

    # Use AgentSet methods on components
    powerful_components = robot.components.select(lambda a: a.power > 10)
    robot.components.do("activate")
    ```
"""

from mesa.experimental.meta_agents.meta_agents import MetaAgent

__all__ = ["MetaAgent"]
