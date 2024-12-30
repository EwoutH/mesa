"""Implementation of Mesa's meta agent capability."""

from mesa.agent import Agent, AgentSet


class MetaAgent(Agent):
    """An agent that is composed of other agents and can act as a unit.

    A meta agent manages a collection of component agents using Mesa's AgentSet,
    providing all AgentSet functionality plus the ability to act as an agent itself.

    Meta agents can:
        - Add and remove component agents
        - Access components through AgentSet interface
        - Aggregate properties from components
        - Perform actions on all components
        - Act as an agent in their own right

    Attributes:
        components (AgentSet): Read-only access to component agents
        model (Model): The model instance
        unique_id (int): Unique identifier

    Notes:
        - Components are stored in an AgentSet using weak references
        - Components inherit the model's random number generator
        - The meta agent is automatically registered with the model
    """

    def __init__(self, model, components=None):
        """Initialize a meta agent.

        Args:
            model (Model): The model instance
            components (Iterable[Agent], optional): Initial component agents
        """
        super().__init__(model)
        self._components = AgentSet(components or [], random=model.random)

    @property
    def components(self):
        """Read-only access to components as an AgentSet."""
        return self._components

    def add_component(self, agent):
        """Add an agent as a component.

        Args:
            agent (Agent): The agent to add
        """
        self._components.add(agent)

    def remove_component(self, agent):
        """Remove an agent component.

        Args:
            agent (Agent): The agent to remove
        """
        self._components.discard(agent)

    def step(self):
        """Perform the agent's step.

        Override this method to define the meta agent's behavior.
        By default, does nothing.
        """
        pass

    def __len__(self):
        """Return the number of components."""
        return len(self._components)

    def __iter__(self):
        """Iterate over components."""
        return iter(self._components)

    def __contains__(self, agent):
        """Check if an agent is a component."""
        return agent in self._components
