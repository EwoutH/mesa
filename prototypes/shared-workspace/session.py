"""Local pathfinding session for Mesa's existing Schelling example.

This is deliberately outside Mesa's public API. UI clients only read snapshots
and send commands; one session owns the model and serializes all access.
"""

from __future__ import annotations

import importlib
import inspect
import threading
import traceback
import uuid
from pathlib import Path

from mesa.examples.basic.schelling import agents as agents_module
from mesa.examples.basic.schelling import model as model_module

DEFAULTS = {"seed": 42, "density": 0.8, "homophily": 0.55}
MAX_STEPS = 500


class Session:
    """Own one shared simulation, independent of browser and editor hosts."""

    def __init__(self):
        """Create a paused, seeded model."""
        self.lock = threading.RLock()
        self.playing = False
        self.interval = 0.15
        self.error = None
        self.revision = 0
        self._reset(DEFAULTS)

    def _reset(self, parameters, reload_code=False):
        values = DEFAULTS | parameters
        if set(values) != set(DEFAULTS):
            raise ValueError("Unknown model parameter")
        seed = values["seed"]
        if (
            isinstance(seed, bool)
            or not isinstance(seed, int)
            or not 0 <= seed <= 2**32 - 1
        ):
            raise ValueError("Seed must be an integer between 0 and 4294967295")
        for name, low, high in (("density", 0.1, 0.95), ("homophily", 0.1, 0.9)):
            value = values[name]
            if (
                isinstance(value, bool)
                or not isinstance(value, int | float)
                or not low <= value <= high
            ):
                raise ValueError(f"{name} must be between {low} and {high}")
        if reload_code:
            importlib.invalidate_caches()
            importlib.reload(agents_module)
            importlib.reload(model_module)
        scenario = model_module.SchellingScenario(
            rng=seed,
            width=28,
            height=28,
            density=values["density"],
            homophily=values["homophily"],
        )
        candidate = model_module.Schelling(scenario)
        self.model = candidate
        self.parameters = values
        self.run_id = uuid.uuid4().hex[:8]
        self.playing = False
        self.error = None
        self.history = []
        self._observe()
        self.revision += 1

    def _observe(self):
        self.history.append(
            {
                "time": self.model.time,
                "happy": 100 * self.model.happy / max(1, len(self.model.agents)),
            }
        )

    def _advance(self):
        if self.model.running and self.model.time < MAX_STEPS:
            self.model.step()
            self._observe()
            self.revision += 1
        if not self.model.running or self.model.time >= MAX_STEPS:
            self.playing = False

    def tick(self):
        """Advance from the server clock; polling never advances the model."""
        with self.lock:
            if self.playing:
                try:
                    self._advance()
                except Exception:
                    self.playing = False
                    self.error = traceback.format_exc()
                    self.revision += 1

    def command(self, action, parameters=None, speed=None):
        """Apply a serialized command, retaining the current run on bad input."""
        with self.lock:
            if action in {"reset", "reload"}:
                self.playing = False
                try:
                    self._reset(
                        parameters or self.parameters, reload_code=action == "reload"
                    )
                except ValueError:
                    raise
                except Exception:
                    self.error = traceback.format_exc()
            elif action == "play":
                self.playing = (
                    not self.error
                    and self.model.running
                    and self.model.time < MAX_STEPS
                )
            elif action == "pause":
                self.playing = False
            elif action == "step":
                self.playing = False
                if not self.error:
                    try:
                        self._advance()
                    except Exception:
                        self.error = traceback.format_exc()
            elif action == "speed":
                if (
                    isinstance(speed, bool)
                    or not isinstance(speed, int | float)
                    or not 1 <= speed <= 20
                ):
                    raise ValueError("Speed must be between 1 and 20 steps per second")
                self.interval = 1 / speed
            else:
                raise ValueError(f"Unknown action: {action}")
            self.revision += 1
            return self.snapshot()

    def snapshot(self):
        """Return detached JSON data; rendering consumes no model randomness."""
        with self.lock:
            status = "running" if self.playing else "paused"
            if self.error:
                status = "error"
            elif not self.model.running:
                status = "complete"
            elif self.model.time >= MAX_STEPS:
                status = "limit"
            return {
                "protocol": 1,
                "revision": self.revision,
                "run_id": self.run_id,
                "time": self.model.time,
                "status": status,
                "parameters": dict(self.parameters),
                "speed": 1 / self.interval,
                "width": 28,
                "height": 28,
                "limit": MAX_STEPS,
                "agents": [
                    {
                        "id": a.unique_id,
                        "x": a.cell.coordinate[0],
                        "y": a.cell.coordinate[1],
                        "group": a.type,
                        "happy": a.happy,
                    }
                    for a in self.model.agents
                ],
                "history": [dict(point) for point in self.history],
                "error": self.error,
            }

    def sources(self):
        """Expose only the two known example files and their source locations."""
        with self.lock:
            result = {}
            for name, cls in (
                ("model", model_module.Schelling),
                ("agents", agents_module.SchellingAgent),
            ):
                path = Path(inspect.getfile(cls)).resolve()
                result[name] = {
                    "name": path.name,
                    "path": str(path),
                    "line": inspect.getsourcelines(cls)[1],
                    "text": path.read_text(encoding="utf-8"),
                }
            return result
