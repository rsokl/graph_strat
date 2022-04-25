import math
from typing import Dict, Union

import hypothesis.strategies as st
import networkx as nx
import pytest
from hypothesis import given

import graph_strat as cst


@pytest.mark.parametrize(
    "input_description",
    [  # vary number of nodes
        dict(min_nodes=st.integers(1, 20)),
        dict(min_nodes=st.integers(1, 30), max_nodes="min_nodes"),
        # vary component size
        dict(min_nodes=st.integers(1, 20), min_component_size="min_nodes"),
        dict(
            min_nodes=st.integers(1, 20),
            max_nodes="min_nodes",
            min_component_size="min_nodes",
        ),
        dict(
            min_nodes=st.integers(1, 20),
            max_nodes="min_nodes",
            max_component_size="min_nodes",
        ),
        dict(
            min_nodes=st.integers(1, 20),
            max_nodes="min_nodes",
            min_component_size="min_nodes",
            max_component_size="min_nodes",
        ),
        # vary number of components
        dict(min_nodes=st.integers(1, 20), min_num_components="min_nodes"),
        dict(min_nodes=st.integers(1, 20), min_num_components=1, max_num_components=1),
        dict(
            min_nodes=st.integers(1, 20),
            max_nodes="min_nodes",
            max_num_components="min_nodes",
        ),
        dict(
            min_nodes=st.integers(1, 20),
            max_nodes="min_nodes",
            min_num_components="min_nodes",
            max_num_components="min_nodes",
        ),
        dict(min_nodes=1, max_nodes=st.integers(1, 10)),
    ],
)
@given(data=st.data())
def test_fuzzing_with_default_args_for_graphs(
    data: st.DataObject,
    input_description: Dict[str, Union[int, float, st.SearchStrategy[int]]],
):
    """
    `input_description` is a dictionary whose values can be:
        -An integer
        -A hypothesis strategy
           + the argument's value will be drawn during the test
        -The name of another input argument
           + the argument's value will be mirrored to match that of the indicated argument
    Ensures that drawn graph always satisfies the specified constraints.
    """
    mirrored_kwargs = {k: v for k, v in input_description.items() if isinstance(v, str)}
    input_description = {
        k: v for k, v in input_description.items() if k not in mirrored_kwargs
    }

    kwargs = {
        k: data.draw(v, label=k) if isinstance(v, st.SearchStrategy) else v
        for k, v in input_description.items()
    }
    kwargs.update({k: kwargs[v] for k, v in mirrored_kwargs.items()})
    graph = data.draw(cst.graphs(**kwargs))

    min_nodes = kwargs.get("min_nodes", 1)
    max_nodes = kwargs.get("max_nodes", math.inf)
    min_num_components = kwargs.get("min_num_components", 1)
    max_num_components = kwargs.get("max_num_components", math.inf)
    min_component_size = kwargs.get("min_component_size", 1)
    max_component_size = kwargs.get("max_component_size", math.inf)

    comps = nx.connected_components(graph)
    sizes = tuple(len(c) for c in comps)

    assert min_nodes <= sum(sizes)
    assert sum(sizes) <= max_nodes
    assert min_num_components <= len(sizes)
    assert len(sizes) <= max_num_components
    assert min_component_size <= min(sizes)
    assert max(sizes) <= max_component_size
