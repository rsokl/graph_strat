import math
from typing import Any, Dict, Tuple, Type, Union

import hypothesis.strategies as st
import pytest
from hypothesis import given, settings

import graph_strat as cst


def everything_except(
    excluded_types: Union[Type, Tuple[Type, ...]]
) -> st.SearchStrategy[Any]:
    return (
        st.from_type(type)
        .flatmap(st.from_type)
        .filter(lambda x: not isinstance(x, excluded_types))
    )



def partitions(n, k=1):
    """Yields all ways in which n can be partitioned (ordered by ascending partition-size)"""
    yield (n,)
    for i in range(k, n // 2 + 1):
        for p in partitions(n - i, i):
            yield (i,) + p


@given(num_items=st.integers(1, 20), data=st.data())
def test_restricted_partition(num_items: int, data: st.DataObject):
    """Compare restricted partitions against exhaustive partitions that were filtered."""
    num_partitions = data.draw(st.integers(1, num_items), label="num_partitions")
    min_partition_size = data.draw(
        st.integers(1, num_items // num_partitions), label="min_partition_size"
    )
    smallest_max = num_items // num_partitions + bool(num_items % num_partitions)
    max_partition_size = data.draw(
        st.none() | st.integers(min_value=smallest_max), label="max_partition_size"
    )
    actual = cst.restricted_partitions(
        num_items=num_items,
        num_partitions=num_partitions,
        min_partition_size=min_partition_size,
        max_partition_size=max_partition_size,
    )
    assert len(actual) == len(set(actual))

    cap = max_partition_size if max_partition_size is not None else math.inf
    desired = [
        x
        for x in partitions(num_items)
        if len(x) == num_partitions and min_partition_size <= min(x) and max(x) <= cap
    ]
    assert set(actual) == set(desired)


@pytest.mark.parametrize(
    "kwargs",
    [
        dict(num_items=6, num_partitions=3, min_partition_size=2, max_partition_size=2),
        dict(num_items=6, num_partitions=3, min_partition_size=2),
        dict(num_items=4, num_partitions=3, min_partition_size=1),
        dict(num_items=4, num_partitions=3),
    ],
)
def test_partition_cache(kwargs: Dict[str, int]):
    cst.restricted_partitions.cache.clear()
    assert not cst.restricted_partitions.cache

    result = cst.restricted_partitions(**kwargs)
    assert cst.restricted_partitions.cache[f"(){repr(kwargs)}"] == result


@pytest.mark.parametrize(
    ("n", "k", "l"),
    [
        (0, 1, 1),
        (1, 0, 1),
        (1, 1, 0),
        (1, 1, 2),
        (1, 2, 1),  # unsatisfiable
        (3, 3, 2),  # unsatisfiable
    ],
)
def test_validate_input_values(n, k, l):
    with pytest.raises(ValueError):
        cst.restricted_partitions(num_items=n, num_partitions=k, min_partition_size=l)


@settings(max_examples=5000)
@given(
    num_items=st.integers(-1, 20),
    num_partitions=st.integers(-1, 5),
    min_partition_size=st.integers(-1, 5),
    max_partition_size=(st.none() | st.integers(-1, 20)),
)
def test_fuzz_partitions(
    num_items: int,
    num_partitions: int,
    min_partition_size: int,
    max_partition_size: int,
):
    try:
        out = cst.restricted_partitions(
            num_items=num_items,
            num_partitions=num_partitions,
            min_partition_size=min_partition_size,
            max_partition_size=max_partition_size,
        )
    except ValueError:
        return

    assert all(sum(part) == num_items for part in out), out
    assert all(len(part) == num_partitions for part in out), out

    if max_partition_size is None:
        max_partition_size = math.inf  # type: ignore
    assert all(
        min_partition_size <= s <= max_partition_size for part in out for s in part
    ), out
    assert out == tuple(sorted(out)[::-1]), "partitions are not in descending order"


@pytest.mark.parametrize(
    "field_name",
    ["num_items", "num_partitions", "min_partition_size", "max_partition_size"],
)
@given(bad_value=everything_except((int, type(None))))
def test_validate_input_types(field_name: str, bad_value: Any):
    inputs = {
        k: 1 if k != field_name else bad_value
        for k in [
            "num_items",
            "num_partitions",
            "min_partition_size",
            "max_partition_size",
        ]
    }

    with pytest.raises(cst.InvalidArgument):
        cst.restricted_partitions(**inputs)