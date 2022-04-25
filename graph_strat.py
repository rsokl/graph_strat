import functools
from numbers import Integral
from typing import Generator, Optional, Tuple, Type, TypeVar, Union

import hypothesis.strategies as st
import networkx as nx
from hypothesis_networkx import graph_builder

__all__ = ["graphs"]

T = TypeVar("T")
OptionalStrategy = Union[T, st.SearchStrategy[T]]


@st.composite
def graphs(
    draw,
    min_nodes: int,
    max_nodes: Optional[int] = None,
    min_num_components: Optional[int] = None,
    max_num_components: Optional[int] = None,
    min_component_size: int = 1,
    max_component_size: Optional[int] = None,
) -> st.SearchStrategy[nx.Graph]:
    """Draws graphs whose number of nodes, number of connected components, and
    size of connected components are constrained.

    Parameters
    ----------
    min_nodes : int
        The minimum number of nodes permitted in a graph.

    max_nodes : Optional[int]
        The largest number of nodes permitted in a graph. Defaults to
        ``10 + min_nodes``.

    min_num_components : Optional[int]
        The minimum number of connected components permitted in a graph.
        Defaults to the smallest permissible number based on ``max_component_size``,
        if such a constraint is specified, and the number of nodes that were drawn.
        Otherwise this defaults to 1.

    max_num_components : Optional[int]
        The maximum number of connected components permitted in a graph.
        Defaults to the largest permissible number based on ``min_component_size``
        and the number of nodes that were drawn.

    min_component_size : int
        The smallest permissible size for a connected component in the a graph. The
        default value is one node.

    max_component_size : Optional[int]
        The largest permissible size for a connected component in the a graph. The
        default value adapts according to the constraints of other parameters to permit
        the largest possible connected component.

    Returns
    -------
    st.SearchStrategy[nx.Graph]

    Notes
    -----
    The parameters provided here have the potential of over-constraining the graphs.

    It is recommended that you either constrain the number of connected components or
    their size, not both.

    Values drawn from this strategy shrink towards a graph with:
        - fewer nodes
        - fewer connected components
        - an even distribution of nodes among its connected components

    Also note that the partition-generation process scales harshly with number of nodes:
    it is inadvisable to draw graphs with more then tens of nodes."""
    if not isinstance(min_nodes, Integral):
        raise InvalidArgument("`min_nodes` must be an integer value")

    if not isinstance(min_component_size, Integral):
        raise InvalidArgument("`min_component_size` must be an integer value")

    if (
        min_num_components is not None
        and min_nodes < min_num_components * min_component_size
    ):
        raise InvalidArgument(
            "The relationship:"
            "\n\tmin_num_components * min_component_size <= min_nodes"
            "\nmust hold."
        )

    if max_nodes is None:
        max_nodes = min_nodes + 10

    num_nodes = draw(st.integers(min_nodes, max_nodes))

    if min_num_components is None:
        if max_component_size is None:
            min_num_components = 1
        else:
            min_num_components = max(num_nodes // max_component_size, 1)

    if max_num_components is None:
        max_num_components = num_nodes // min_component_size

    num_components = draw(st.integers(min_num_components, max_num_components))

    partitions = st.sampled_from(
        restricted_partitions(
            num_items=num_nodes,
            num_partitions=num_components,
            min_partition_size=min_component_size,
            max_partition_size=max_component_size,
        )
    )
    graph = nx.Graph()

    for n_nodes in draw(partitions):
        graph = nx.disjoint_union(
            draw(
                graph_builder(
                    graph_type=nx.Graph,
                    min_nodes=n_nodes,
                    max_nodes=n_nodes,
                    connected=True,
                )
            ),
            graph,
        )
    return graph


class InvalidArgument(ValueError):
    pass


def _memoize(obj):
    cache = obj.cache = {}

    @functools.wraps(obj)
    def memoizer(*args, **kwargs):
        key = str(args) + str(kwargs)
        if key not in cache:
            cache[key] = obj(*args, **kwargs)
        return cache[key]

    return memoizer


def _generate_partitions(
    num_items: int, num_bins: int, min_partition_size: int = 1
) -> Generator[Tuple[int, ...], None, None]:
    if num_bins < 1:
        return

    if num_bins == 1:
        if num_items >= min_partition_size:
            yield (num_items,)
        return

    for i in range(min_partition_size, num_items + 1):
        for result in _generate_partitions(num_items - i, num_bins - 1, i):
            yield (i,) + result


@_memoize
def restricted_partitions(
    *,
    num_items: int,
    num_partitions: int,
    min_partition_size: int = 1,
    max_partition_size: Optional[int] = None,
) -> Tuple[Tuple[int, ...], ...]:
    """Returns all of the ways in which N can be partitioned K ways given a minimum
    partition size.

    Order is disregarded and the results are returned in descending order of
    partition-size

    Examples
    --------
    >>> restricted_partitions(num_items=10, num_partitions=3, min_partition_size=2)
    ((3, 3, 4), (2, 4, 4), (2, 3, 5), (2, 2, 6))

    >>> restricted_partitions(num_items=10, num_partitions=3, min_partition_size=2, max_partition_size=5)
    ((3, 3, 4), (2, 4, 4), (2, 3, 5))
    """
    if not isinstance(num_items, Integral) or num_items < 1:
        raise InvalidArgument(
            f"`num_items` must be an integer greater than 1, got {num_items}"
        )

    if not isinstance(num_partitions, Integral) or num_partitions < 1:
        raise InvalidArgument(
            f"`num_partitions` must be an integer greater than 0, got {num_partitions}"
        )

    if not isinstance(min_partition_size, Integral) or min_partition_size < 1:
        raise InvalidArgument(
            f"`min_partition_size` must be an integer greater than 0, got {min_partition_size}"
        )

    if num_items < num_partitions * min_partition_size:
        raise InvalidArgument(
            f"There are too few items to be partitioned."
            f"\nGot {num_items} items to be divided among {num_partitions} partitions, with a "
            f"minimum partition size of {min_partition_size}."
        )

    if max_partition_size is None:
        max_partition_size = num_items - (num_partitions - 1) * min_partition_size

    if (
        not isinstance(max_partition_size, Integral)
        or max_partition_size < min_partition_size
    ):
        raise InvalidArgument(
            f"`max_partition_size` must be an integer that is not exceeded by `min_partition_size`. "
            f"\nGot: {max_partition_size} (with min_partition_size={min_partition_size}."
        )

    if max_partition_size < num_items // num_partitions + bool(
        num_items % num_partitions
    ):
        raise InvalidArgument(
            f"`max_partition_size` is too small. There are no partitions that satisfy:"
            f"\n\tnum_items: {num_items}"
            f"\n\tnum_partitions: {num_partitions}"
            f"\n\tmin_partition_size: {min_partition_size}"
            f"\n\tmax_partition_size: {max_partition_size}"
            f"\nThe smallest permissible value for `max_partition_size` is: "
            f"{num_items // num_partitions + bool(num_items % num_partitions)}"
        )

    partitions = tuple(
        x
        for x in _generate_partitions(num_items, num_partitions, min_partition_size)
        if max(x) <= max_partition_size
    )
    if not partitions:
        raise AssertionError(
            f"There are no partitions that satisfy:"
            f"\nnum_items: {num_items}"
            f"\nnum_partitions: {num_partitions}"
            f"\nmin_partition_size: {min_partition_size}"
            f"\nmax_partition_size: {max_partition_size}"
        )
    else:
        return partitions[::-1]
