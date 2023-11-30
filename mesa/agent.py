"""
The agent class for Mesa framework.

Core Objects: Agent
"""
# Mypy; for the `|` operator purpose
# Remove this __future__ import once the oldest supported Python is 3.10
from __future__ import annotations

from random import Random

# mypy
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # We ensure that these are not imported during runtime to prevent cyclic
    # dependency.
    from mesa.model import Model
    from mesa.space import Position


class Agent:
    """
    Base class for a model agent in Mesa.

    Attributes:
        unique_id (int): A unique identifier for this agent.
        agent_type (type): The class of the agent, used for type categorization.
        model (Model): A reference to the model instance.
        self.pos: Position | None = None
    """

    def __init__(self, unique_id: int, model: Model) -> None:
        """
        Create a new agent.

        Args:
            unique_id (int): A unique identifier for this agent.
            model (Model): The model instance in which the agent exists.
        """
        self.unique_id = unique_id
        self.agent_type = self.__class__
        self.model = model
        self.pos: Position | None = None

    def step(self) -> None:
        """A single step of the agent."""

    def advance(self) -> None:
        pass

    @property
    def random(self) -> Random:
        return self.model.random
