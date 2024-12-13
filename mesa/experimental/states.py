"""State management system for Mesa agents with signals integration.

This module extends the basic state management system to integrate with Mesa's
signals/observables functionality, enabling automatic notifications and updates
when states change.

Core Classes:
   State: Base class defining the state interface with signal support
   DiscreteState: States with explicit value changes that emit signals
   ContinuousState: States that change over time with signal emission
   CompositeState: States computed from other states with signal propagation
   StateAgent: Mesa Agent subclass with state management and signal support
"""

from collections.abc import Callable
from typing import Any

from mesa import Agent
from mesa.experimental.mesa_signals.signals import HasObservables, Observable
from mesa.experimental.mesa_signals.signals_util import AttributeDict


class State(Observable):
    """Base class for all states with signal support."""

    def __init__(self, initial_value: Any):
        """Create a new state with signal support."""
        super().__init__(fallback_value=initial_value)
        self._value = initial_value
        self._last_update_time = 0
        self.model = None  # Set when state is added to agent

        # Add state-specific signals
        self.signal_types.update({"update", "initialize"})

    @property
    def value(self) -> Any:
        """Get current state value."""
        raise NotImplementedError

    def update(self, time: float) -> None:
        """Update state to current time."""
        raise NotImplementedError


class DiscreteState(State):
    """A state with discrete values that change explicitly."""

    @property
    def value(self) -> Any:
        """Get the current state value."""
        return self._value

    @value.setter
    def value(self, new_value: Any) -> None:
        """Set the state value and emit change signal."""
        if new_value != self._value:
            old_value = self._value
            self._value = new_value
            # Emit change signal through owner
            if hasattr(self, 'owner'):
                self.owner.notify(
                    self.public_name,
                    old_value,
                    new_value,
                    "change"
                )

    def update(self, time: float) -> None:
        """DiscreteStates only update when value is explicitly changed."""
        if hasattr(self, 'owner'):
            self.owner.notify(
                self.public_name,
                self._value,
                self._value,
                "update",
                time=time
            )


class ContinuousState(State):
    """A state that changes continuously over time."""

    def __init__(
        self,
        initial_value: float,
        rate_function: Callable[[float, float], float],
    ):
        """Create a new continuous state."""
        super().__init__(initial_value)
        self.rate_function = rate_function

    @property
    def value(self) -> float:
        """Calculate and return current value based on elapsed time."""
        if self.model:
            current_time = self.model.time
            if current_time > self._last_update_time:
                self.update(current_time)
        return self._value

    def update(self, time: float) -> None:
        """Update state value based on elapsed time and emit signals."""
        old_value = self._value
        elapsed = time - self._last_update_time
        new_value = self._value + self.rate_function(self._value, elapsed)

        if new_value != old_value:
            self._value = new_value
            if hasattr(self, 'owner'):
                self.owner.notify(
                    self.public_name,
                    old_value,
                    new_value,
                    "change",
                    time=time
                )

        self._last_update_time = time


class CompositeState(State):
    """A state derived from other states with signal propagation."""

    def __init__(
        self,
        dependent_states: list[State],
        computation_function: Callable[..., Any],
    ):
        """Create a new composite state."""
        super().__init__(None)  # Value computed on first access
        self.dependent_states = dependent_states
        self.computation_function = computation_function

        # Subscribe to changes in dependent states
        def on_dependent_change(signal: AttributeDict):
            self._recompute()

        for state in dependent_states:
            if hasattr(state, 'owner'):
                state.owner.observe(state.public_name, "change", on_dependent_change)

    def _recompute(self):
        """Recompute value and emit change if needed."""
        old_value = self._value
        new_value = self.computation_function(*[state.value for state in self.dependent_states])

        if new_value != old_value:
            self._value = new_value
            if hasattr(self, 'owner'):
                self.owner.notify(
                    self.public_name,
                    old_value,
                    new_value,
                    "change"
                )

    @property
    def value(self) -> Any:
        """Compute value based on dependent states."""
        if self._value is None:
            self._recompute()
        return self._value

    def update(self, time: float) -> None:
        """Update all dependent states."""
        for state in self.dependent_states:
            state.update(time)
        self._recompute()


class StateAgent(Agent, HasObservables):
    """An agent with integrated state management and signal support."""

    def __init__(self, model):
        """Create a new agent with state management."""
        super().__init__(model)
        self.states = {}

    def update_states(self) -> None:
        """Update all states to current time."""
        current_time = self.model.time
        for state in self.states.values():
            state.update(current_time)

    def __getattribute__(self, name: str) -> Any:
        """Get an attribute, routing state access to its value."""
        states = object.__getattribute__(self, "states")
        if name in states:
            state = states[name]
            return state.value
        return object.__getattribute__(self, name)

    def __setattr__(self, name: str, value: Any) -> None:
        """Set an attribute, handling state assignment and signals."""
        if isinstance(value, State):
            # Initialize new state
            self.states[name] = value
            value.model = self.model
            value.owner = self
            value.public_name = name
            # Emit initialization signal
            self.notify(
                name,
                None,
                value.value,
                "initialize"
            )
        elif name in self.states:
            if isinstance(self.states[name], DiscreteState):
                self.states[name].value = value
            else:
                raise ValueError("Cannot directly set value of non-discrete state")
        else:
            object.__setattr__(self, name, value)
