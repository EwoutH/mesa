"""
The model class for Mesa framework.

Core Objects: Model
"""
# Mypy; for the `|` operator purpose
# Remove this __future__ import once the oldest supported Python is 3.10
from __future__ import annotations

import random

# mypy
from typing import Any

from mesa.datacollection import DataCollector


class Model:
    """Base class for models."""

    def __new__(cls, *args: Any, **kwargs: Any) -> Any:
        """Create a new model object and instantiate its RNG automatically."""
        obj = object.__new__(cls)
        obj._seed = kwargs.get("seed")
        if obj._seed is None:
            # We explicitly specify the seed here so that we know its value in
            # advance.
            obj._seed = random.random()  # noqa: S311
        obj.random = random.Random(obj._seed)
        return obj

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Create a new model. Overload this method with the actual code to
        start the model.

        Attributes:
            schedule: schedule object
            running: a bool indicating if the model should continue running
        """

        self.running = True
        self.schedule = None
        self.current_id = 0
        self.agents_by_type = {}

    def create_agent(self, agent_type, *args, **kwargs):
        """
        Creates an agent of the given type with a unique ID and adds it to the agents_by_type dictionary.

        Parameters:
        agent_type (class): The class of the agent to be created.
        *args, **kwargs: Additional arguments passed to the agent's constructor.

        Returns:
        An instance of the specified agent_type.
        """
        # Create a new agent instance with a unique ID
        agent = agent_type(self.next_id(), self, *args, **kwargs)

        # Add the agent to the agents_by_type dictionary
        agent_class = agent.__class__
        if agent_class not in self.agents_by_type:
            self.agents_by_type[agent_class] = []
        self.agents_by_type[agent_class].append(agent)

        return agent

    def run_model(self) -> None:
        """Run the model until the end condition is reached. Overload as
        needed.
        """
        while self.running:
            self.step()

    def step(self) -> None:
        """A single step. Fill in here."""

    def next_id(self) -> int:
        """Return the next unique ID for agents, increment current_id"""
        self.current_id += 1
        return self.current_id

    def reset_randomizer(self, seed: int | None = None) -> None:
        """Reset the model random number generator.

        Args:
            seed: A new seed for the RNG; if None, reset using the current seed
        """

        if seed is None:
            seed = self._seed
        self.random.seed(seed)
        self._seed = seed

    def initialize_data_collector(
        self,
        model_reporters=None,
        agent_reporters=None,
        tables=None,
    ) -> None:
        if not hasattr(self, "schedule") or self.schedule is None:
            raise RuntimeError(
                "You must initialize the scheduler (self.schedule) before initializing the data collector."
            )
        if self.schedule.get_agent_count() == 0:
            raise RuntimeError(
                "You must add agents to the scheduler before initializing the data collector."
            )
        self.datacollector = DataCollector(
            model_reporters=model_reporters,
            agent_reporters=agent_reporters,
            tables=tables,
        )
        # Collect data for the first time during initialization.
        self.datacollector.collect(self)
