"""Mesa Agent-Based Modeling Framework.

Core Objects: Model, and Agent.
"""

import datetime

import mesa.space as space
import mesa.time as time
from mesa.agent import Agent
from mesa.model import Model

__all__ = [
    "Model",
    "Agent",
    "time",
    "space",
]

__title__ = "mesa"
__version__ = "3.0.0a4"
__license__ = "Apache 2.0"
_this_year = datetime.datetime.now(tz=datetime.timezone.utc).date().year
__copyright__ = f"Copyright {_this_year} Project Mesa Team"
