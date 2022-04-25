## Dependencies

- `networkx`
- `hypothesis-networkx`

## Usage

```python
from graph_strat import graphs
```

`graphs` is a search strategy that draws networkx graphs whose number of nodes, number of connected components, and size of connected components are constrained.

```python
>>> strat = graphs(min_nodes=6, min_num_components=3, min_component_size=2)

>>> list(nx.connected_components(strat.example()))  # note: first call to example draws 100 examples; is 100x slower than an actual draw from strat
[{0, 1, 2, 3, 4, 5, 6, 7, 8}, {9, 10, 11, 12, 13}, {14, 15}]

>>> list(nx.connected_components(strat.example()))
[{0, 1, 2}, {3, 4}, {5, 6}, {7, 8}, {9, 10}, {11, 12}]

>>> list(nx.connected_components(strat.example()))
[{0, 1, 2}, {3, 4}, {5, 6}]
```


Install pytest and run

```shell
pytest test_graph_strat.py test_partitions.py
```

## License

```
MIT License

Copyright (c) 2022 Ryan Soklaski

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
