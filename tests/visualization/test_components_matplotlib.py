"""tests for matplotlib components."""

import networkx as nx
from matplotlib.figure import Figure

from mesa import Agent, Model
from mesa.discrete_space import (
    CellAgent,
    HexGrid,
    Network,
    OrthogonalMooreGrid,
    VoronoiGrid,
)
from mesa.space import (
    ContinuousSpace,
    HexSingleGrid,
    NetworkGrid,
    PropertyLayer,
    SingleGrid,
)
from mesa.visualization.components import AgentPortrayalStyle, PropertyLayerStyle
from mesa.visualization.mpl_space_drawing import (
    draw_continuous_space,
    _get_hexmesh,
    _to_numpy_argument_array,
    collect_agent_data,
    draw_hex_grid,
    draw_network,
    draw_orthogonal_grid,
    draw_property_layers,
    draw_space,
    draw_voronoi_grid,
)


def agent_portrayal(agent):
    """Simple portrayal of an agent.

    Args:
        agent (Agent): The agent to portray

    """
    return AgentPortrayalStyle(
        size=10,
        color="tab:blue",
        marker="s" if (agent.unique_id % 2) == 0 else "o",
    )


def test_draw_space():
    """Test draw_space helper method."""

    def my_portrayal(agent):
        """Simple portrayal of an agent.

        Args:
            agent (Agent): The agent to portray

        """
        return AgentPortrayalStyle(
            size=10,
            color="tab:blue",
            marker="s" if (agent.unique_id % 2) == 0 else "o",
            alpha=0.5,
            linewidths=1,
            edgecolors="tab:orange",
        )

    # draw space for hexgrid
    model = Model(rng=42)
    grid = HexSingleGrid(10, 10, torus=True)
    for _ in range(10):
        agent = Agent(model)
        grid.move_to_empty(agent)

    fig = Figure()
    ax = fig.add_subplot()
    draw_space(grid, my_portrayal, ax=ax)

    # draw space for voroinoi
    model = Model(rng=42)
    coordinates = model.rng.random((100, 2)) * 10
    grid = VoronoiGrid(coordinates.tolist(), random=model.random, capacity=1)
    for _ in range(10):
        agent = CellAgent(model)
        agent.cell = grid.select_random_empty_cell()

    fig = Figure()
    ax = fig.add_subplot()
    draw_space(grid, my_portrayal, ax=ax)

    # draw orthogonal grid
    model = Model(rng=42)
    grid = OrthogonalMooreGrid((10, 10), torus=True, random=model.random, capacity=1)
    for _ in range(10):
        agent = CellAgent(model)
        agent.cell = grid.select_random_empty_cell()
    fig = Figure()
    ax = fig.add_subplot()
    draw_space(grid, my_portrayal, ax=ax)

    # draw network
    n = 10
    m = 20
    rng = 42
    graph = nx.gnm_random_graph(n, m, seed=rng)

    model = Model(rng=42)
    grid = NetworkGrid(graph)
    for _ in range(10):
        agent = Agent(model)
        pos = agent.random.randint(0, len(graph.nodes) - 1)
        grid.place_agent(agent, pos)
    fig = Figure()
    ax = fig.add_subplot()
    draw_space(grid, my_portrayal, ax=ax)

    # draw continuous space
    model = Model(rng=42)
    space = ContinuousSpace(10, 10, torus=True)
    for _ in range(10):
        x = model.random.random() * 10
        y = model.random.random() * 10
        agent = Agent(model)
        space.place_agent(agent, (x, y))

    fig = Figure()
    ax = fig.add_subplot()
    draw_space(space, my_portrayal, ax=ax)


@pytest.mark.parametrize(
    ("edgecolors", "expected"),
    [
        ([None, None], []),
        (["black", None], ["black", "none"]),
        ([(1.0, 0.0, 0.0, 1.0), None], [(1.0, 0.0, 0.0, 1.0), "none"]),
    ],
)
def test_to_numpy_argument_array_edgecolors(edgecolors, expected):
    """Edgecolors normalize None to "none", or drop entirely if unused by anyone."""
    result = _to_numpy_argument_array("edgecolors", edgecolors)
    assert result.tolist() == expected


def test_to_numpy_argument_array_preserves_tuple_markers():
    """Equal-length tuple marker specs must not collapse into a 2D array."""
    result = _to_numpy_argument_array("marker", [(3, 0, 0), (3, 0, 0)])
    assert result.shape == (2,)
    assert list(result) == [(3, 0, 0), (3, 0, 0)]


def test_draw_hex_grid():
    """Test drawing hexgrids."""
    model = Model(rng=42)
    grid = HexSingleGrid(10, 10, torus=True)
    for _ in range(10):
        agent = Agent(model)
        grid.move_to_empty(agent)

    fig = Figure()
    ax = fig.add_subplot()
    draw_hex_grid(grid, agent_portrayal, ax)

    model = Model(rng=42)
    grid = HexGrid((10, 10), torus=True, random=model.random, capacity=1)
    for _ in range(10):
        agent = CellAgent(model)
        agent.cell = grid.select_random_empty_cell()

    fig = Figure()
    ax = fig.add_subplot()
    draw_hex_grid(grid, agent_portrayal, ax)


def test_draw_voronoi_grid():
    """Test drawing voronoi grids."""
    model = Model(rng=42)

    coordinates = model.rng.random((100, 2)) * 10

    grid = VoronoiGrid(coordinates.tolist(), random=model.random, capacity=1)
    for _ in range(10):
        agent = CellAgent(model)
        agent.cell = grid.select_random_empty_cell()

    fig = Figure()
    ax = fig.add_subplot()
    draw_voronoi_grid(grid, agent_portrayal, ax)


def test_draw_orthogonal_grid():
    """Test drawing orthogonal grids."""
    model = Model(rng=42)
    grid = SingleGrid(10, 10, torus=True)
    for _ in range(10):
        agent = Agent(model)
        grid.move_to_empty(agent)

    fig = Figure()
    ax = fig.add_subplot()
    draw_orthogonal_grid(grid, agent_portrayal, ax)

    model = Model(rng=42)
    grid = OrthogonalMooreGrid((10, 10), torus=True, random=model.random, capacity=1)
    for _ in range(10):
        agent = CellAgent(model)
        agent.cell = grid.select_random_empty_cell()

    fig = Figure()
    ax = fig.add_subplot()
    draw_orthogonal_grid(grid, agent_portrayal, ax)


def test_draw_continuous_space():
    """Test drawing continuous space."""
    model = Model(rng=42)
    space = ContinuousSpace(10, 10, torus=True)
    for _ in range(10):
        x = model.random.random() * 10
        y = model.random.random() * 10
        agent = Agent(model)
        space.place_agent(agent, (x, y))

    fig = Figure()
    ax = fig.add_subplot()
    draw_continuous_space(space, agent_portrayal, ax)


def test_draw_network():
    """Test drawing network."""
    n = 10
    m = 20
    rng = 42
    graph = nx.gnm_random_graph(n, m, seed=rng)

    model = Model(rng=42)
    grid = NetworkGrid(graph)
    for _ in range(10):
        agent = Agent(model)
        pos = agent.random.randint(0, len(graph.nodes) - 1)
        grid.place_agent(agent, pos)

    fig = Figure()
    ax = fig.add_subplot()
    draw_network(grid, agent_portrayal, ax)

    model = Model(rng=42)
    grid = Network(graph, random=model.random, capacity=1)
    for _ in range(10):
        agent = CellAgent(model)
        agent.cell = grid.select_random_empty_cell()

    fig = Figure()
    ax = fig.add_subplot()
    draw_network(grid, agent_portrayal, ax)


@pytest.mark.parametrize("edgecolor", ["black", (1.0, 0.0, 0.0, 1.0)])
def test_draw_network_with_partial_edgecolors(edgecolor):
    """Network drawing handles edgecolors provided for only some agents.

    Regression test for #2691: a network with agent types that don't all
    return the same portrayal fields (here, only "kind 0" sets edgecolors)
    used to crash draw_network with a boolean-index length mismatch.
    """
    graph = nx.path_graph(2)
    model = Model(rng=42)
    grid = Network(graph, random=model.random, capacity=1, layout=nx.spring_layout)

    for index, cell in enumerate(grid.all_cells):
        agent = CellAgent(model)
        agent.cell = cell
        agent.kind = index

    def partial_edgecolor_portrayal(agent):
        """Only agents of kind 0 specify an edgecolor; kind 1 omits it entirely."""
        portrayal = {"size": 10, "color": "tab:blue", "marker": "o", "zorder": 1}
        if agent.kind == 0:
            portrayal["edgecolors"] = edgecolor
        return portrayal

    fig = Figure()
    ax = fig.add_subplot()
    with pytest.warns(FutureWarning):
        draw_network(grid, partial_edgecolor_portrayal, ax)


def test_draw_property_layers():
    """Test drawing property layers."""
    model = Model(rng=42)
    grid = SingleGrid(10, 10, torus=True)
    grid.add_property_layer(
        PropertyLayer("test", grid.width, grid.height, 0, dtype=int)
    )

    def propertylayer_portrayal(_):
        return PropertyLayerStyle(colormap="viridis", colorbar=True)

    fig = Figure()
    ax = fig.add_subplot()
    draw_property_layers(grid, propertylayer_portrayal, ax)

    model = Model(rng=42)
    grid = OrthogonalMooreGrid((10, 10), torus=True, random=model.random, capacity=1)
    grid.create_property_layer("test", 0.0)

    fig = Figure()
    ax = fig.add_subplot()
    draw_property_layers(grid, propertylayer_portrayal, ax)
    draw_property_layers(grid, property_layer_portrayal, ax)


def test_get_hexmesh_returns_immutable_shared_safe_mesh():
    """_get_hexmesh must return an immutable, non-poisonable cached mesh.

    Regression test: the function is decorated with ``lru_cache`` and returns
    the same object on repeated calls with identical arguments. If that object
    were a mutable list, a caller mutating it would corrupt the shared cache for
    every other same-sized grid. The result must therefore be nested tuples.
    """
    mesh = _get_hexmesh(3, 4)

    # One entry per cell, each a hexagon of six vertices, all immutable tuples.
    assert isinstance(mesh, tuple)
    assert len(mesh) == 3 * 4
    for hexagon in mesh:
        assert isinstance(hexagon, tuple)
        assert len(hexagon) == 6
        for vertex in hexagon:
            assert isinstance(vertex, tuple)
            assert len(vertex) == 2

    # Cached object is shared across calls but cannot be mutated in place.
    assert _get_hexmesh(3, 4) is mesh
    with pytest.raises(AttributeError):
        mesh.append(("x", "y"))  # tuples have no append
    with pytest.raises(TypeError):
        mesh[0][0] = (0.0, 0.0)  # nested tuples are immutable too
