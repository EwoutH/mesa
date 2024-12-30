"""Tests for Mesa's meta agents functionality."""
import pytest

from mesa import Agent, Model
from mesa.experimental.meta_agents import MetaAgent


class TestAgent(Agent):
    """A basic test agent with some attributes."""
    def __init__(self, model, power=10):
        super().__init__(model)
        self.power = power
        self.activated = False

    def activate(self):
        """Test method for component operations."""
        self.activated = True


class TestMetaAgent(MetaAgent):
    """A test meta agent that computes properties from components."""
    def __init__(self, model, components=None):
        super().__init__(model, components)
        # Set own power based on components
        self.power = self.components.agg("power", sum) if self.components else 0


@pytest.fixture
def model():
    """Create a basic model for testing."""
    return Model()


@pytest.fixture
def agents(model):
    """Create a set of basic agents for testing."""
    return [
        TestAgent(model, power=10),
        TestAgent(model, power=20),
        TestAgent(model, power=30),
    ]


def test_meta_agent_creation(model, agents):
    """Test basic meta agent creation and initialization."""
    # Create empty meta agent
    meta = MetaAgent(model)
    assert len(meta.components) == 0
    assert meta.model == model
    assert meta.unique_id is not None

    # Create meta agent with components
    meta = MetaAgent(model, components=agents)
    assert len(meta.components) == 3
    assert all(agent in meta.components for agent in agents)


def test_meta_agent_component_management(model, agents):
    """Test adding and removing components."""
    meta = MetaAgent(model)

    # Add components
    for agent in agents:
        meta.add_component(agent)
    assert len(meta.components) == 3
    assert all(agent in meta.components for agent in agents)

    # Remove component
    meta.remove_component(agents[0])
    assert len(meta.components) == 2
    assert agents[0] not in meta.components
    assert all(agent in meta.components for agent in agents[1:])

    # Add existing component (should not duplicate)
    meta.add_component(agents[1])
    assert len(meta.components) == 2


def test_meta_agent_properties(model, agents):
    """Test computing properties from components."""
    meta = TestMetaAgent(model, components=agents)

    # Test initial properties
    assert meta.power == 60  # 10 + 20 + 30

    # Test properties after removing component
    meta.remove_component(agents[0])
    meta.power = meta.components.agg("power", sum)  # Need to recompute
    assert meta.power == 50  # 20 + 30


def test_meta_agent_agentset_operations(model, agents):
    """Test using AgentSet operations on components."""
    meta = MetaAgent(model, components=agents)

    # Test selection
    powerful = meta.components.select(lambda a: a.power > 15)
    assert len(powerful) == 2
    assert all(a.power > 15 for a in powerful)

    # Test sorting
    sorted_agents = meta.components.sort(key="power", ascending=True)
    powers = [a.power for a in sorted_agents]
    assert powers == [10, 20, 30]

    # Test do
    meta.components.do("activate")
    assert all(a.activated for a in meta.components)

    # Test get
    powers = meta.components.get("power")
    assert sorted(powers) == [10, 20, 30]

    # Test agg
    total_power = meta.components.agg("power", sum)
    assert total_power == 60


def test_meta_agent_iteration(model, agents):
    """Test iteration and container operations."""
    meta = MetaAgent(model, components=agents)

    # Test len
    assert len(meta) == 3

    # Test iteration
    assert list(meta) == list(meta.components)

    # Test contains
    assert agents[0] in meta
    assert Agent(model) not in meta


def test_multiple_membership(model, agents):
    """Test agents can be part of multiple meta agents."""
    meta1 = MetaAgent(model, components=agents[:2])
    meta2 = MetaAgent(model, components=agents[1:])

    # Agent should be in both meta agents
    assert agents[1] in meta1
    assert agents[1] in meta2


def test_hierarchical_meta_agents(model, agents):
    """Test meta agents containing other meta agents."""
    # Create two meta agents
    meta1 = TestMetaAgent(model, components=agents[:2])
    meta2 = TestMetaAgent(model, components=agents[2:])

    # Verify first level meta agents
    assert meta1.power == 30  # 10 + 20
    assert meta2.power == 30  # 30

    # Create a meta-meta agent
    meta3 = TestMetaAgent(model, components=[meta1, meta2])
    assert len(meta3) == 2
    assert meta1 in meta3
    assert meta2 in meta3

    # Verify meta-meta agent properties work just like any other agents
    assert meta3.power == 60  # 30 + 30


def test_meta_agent_model_integration(model, agents):
    """Test meta agents are properly integrated with model."""
    meta = MetaAgent(model, components=agents)

    # Meta agent should be registered with model
    assert meta in model.agents

    # Meta agent should be in agents_by_type
    assert meta in model.agents_by_type[MetaAgent]

    # Components should still be registered independently
    for agent in agents:
        assert agent in model.agents
        assert agent in model.agents_by_type[TestAgent]


def test_empty_meta_agent_operations(model):
    """Test operations on meta agent with no components."""
    meta = TestMetaAgent(model)

    # Properties should handle empty case
    assert meta.power == 0

    # AgentSet operations should work
    assert len(meta.components.select(lambda a: True)) == 0
    assert len(meta.components.sort(key="power")) == 0
    meta.components.do("activate")  # Should not raise error
