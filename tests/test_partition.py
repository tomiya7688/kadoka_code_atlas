from Src.analyzers.call_graph import CallEdge, CallGraph
from Src.analyzers.partition import partition_graph


def _graph(*edges: tuple[str, str], extra_nodes: tuple[str, ...] = ()) -> CallGraph:
    graph = CallGraph([CallEdge(source, target) for source, target in edges])
    if extra_nodes:
        # CallGraph derives nodes from edges; isolated-node coverage uses a tiny adapter below.
        return _GraphWithNodes(graph, set(graph.nodes) | set(extra_nodes))
    return graph


class _GraphWithNodes:
    def __init__(self, graph: CallGraph, nodes: set[str]) -> None:
        self._graph = graph
        self.nodes = nodes
        self.edges = graph.edges

    def fan_in(self) -> dict[str, int]:
        values = self._graph.fan_in()
        return {node: values.get(node, 0) for node in self.nodes}

    def fan_out(self) -> dict[str, int]:
        values = self._graph.fan_out()
        return {node: values.get(node, 0) for node in self.nodes}

    def cycles(self) -> list[tuple[str, ...]]:
        return self._graph.cycles()


def test_partition_keeps_simple_chain_stable() -> None:
    partition = partition_graph(
        _graph(("a", "b"), ("b", "c"), ("c", "d")),
        fan_in_threshold=4,
    )

    assert partition.series == (("a", "b", "c", "d"),)
    assert partition.series_roots == ("a",)
    assert partition.series_depths == (0,)
    assert partition.cross_series_edge_count == 0


def test_partition_recursively_extracts_closed_branch_series() -> None:
    partition = partition_graph(
        _graph(
            ("A", "B"),
            ("A", "X"),
            ("B", "C"),
            ("B", "D"),
            ("C", "E"),
            ("C", "F"),
        ),
        fan_in_threshold=4,
    )

    assert partition.series == (
        ("A", "X"),
        ("B", "D"),
        ("C", "E", "F"),
    )
    assert partition.series_roots == ("A", "B", "C")
    assert partition.series_depths == (0, 1, 2)
    assert partition.series_parents == (None, "A", "B")
    assert partition.max_partition_depth == 2
    assert partition.cross_series_edge_count == 2
    assert partition.cross_series_edge_ratio == 2 / 6


def test_partition_does_not_extract_branch_with_external_reference() -> None:
    partition = partition_graph(
        _graph(
            ("A", "B"),
            ("A", "X"),
            ("B", "C"),
            ("B", "D"),
            ("X", "C"),
        ),
        fan_in_threshold=4,
    )

    assert partition.series == (("A", "B", "C", "D", "X"),)
    assert partition.max_partition_depth == 0


def test_partition_extracts_high_fan_in_shared_node() -> None:
    partition = partition_graph(
        _graph(
            ("first", "shared"),
            ("second", "shared"),
            ("shared", "sink"),
        ),
        fan_in_threshold=2,
    )

    assert partition.shared == ("shared",)
    assert partition.shared_node_count == 1
    assert partition.shared_node_ratio == 1 / 4
    assert set(partition.series) == {("first",), ("second",), ("sink",)}


def test_partition_cycle_is_stable_and_not_recursively_split() -> None:
    partition = partition_graph(
        _graph(
            ("A", "B"),
            ("A", "X"),
            ("B", "C"),
            ("C", "B"),
        ),
        fan_in_threshold=4,
    )

    assert partition.series == (("A", "B", "C", "X"),)
    assert partition.cycle_count == 1
    assert partition.max_partition_depth == 0


def test_partition_statistics_include_recursive_locality_metrics() -> None:
    partition = partition_graph(
        _graph(
            ("A", "B"),
            ("A", "X"),
            ("B", "C"),
            ("B", "D"),
            ("C", "E"),
            ("C", "F"),
        ),
        fan_in_threshold=4,
    )

    assert partition.statistics["series_count"] == 3
    assert partition.statistics["max_partition_depth"] == 2
    assert partition.statistics["avg_nodes_per_series"] == 7 / 3
    assert partition.statistics["cross_series_edge_ratio"] == 2 / 6
    assert partition.statistics["shared_node_ratio"] == 0.0


def test_partition_supports_isolated_nodes_via_generic_graph_protocol() -> None:
    partition = partition_graph(
        _graph(("a", "b"), extra_nodes=("isolated",)),
        fan_in_threshold=3,
    )

    assert set(partition.series) == {("a", "b"), ("isolated",)}
