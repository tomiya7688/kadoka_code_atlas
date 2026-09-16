from Src.analyzers.component_dependencies import (
    ComponentDependencyUnit,
    build_component_dependency_graph,
)
from Src.analyzers.package_dependencies import ModuleDependencyUnit
from Src.generators.component_diagram import build_component_diagram_bundle
from Src.renderers.mermaid_component_diagram import render_component_diagram


def test_component_graph_aggregates_modules_and_keeps_external_dependencies():
    graph = build_component_dependency_graph(
        [
            ComponentDependencyUnit(
                ModuleDependencyUnit("ui.view", ("ui.controller", "data.repo", "requests")),
                "ui",
            ),
            ComponentDependencyUnit(
                ModuleDependencyUnit("ui.controller", ("data.repo",)),
                "ui",
            ),
            ComponentDependencyUnit(
                ModuleDependencyUnit("data.repo", ("ui.view", "requests")),
                "data",
            ),
        ]
    )

    assert graph.nodes == {"ui", "data", "external:requests"}
    assert graph.external_nodes == {"external:requests"}
    assert {(item.caller, item.callee) for item in graph.edges} == {
        ("ui", "data"),
        ("ui", "external:requests"),
        ("data", "ui"),
        ("data", "external:requests"),
    }
    assert all(item.caller != item.callee for item in graph.edges)
    assert graph.cycles()


def test_component_diagram_marks_cycles_and_external_nodes():
    graph = build_component_dependency_graph(
        [
            ComponentDependencyUnit(ModuleDependencyUnit("ui.view", ("data.repo", "requests")), "ui"),
            ComponentDependencyUnit(ModuleDependencyUnit("data.repo", ("ui.view",)), "data"),
        ]
    )
    bundle = build_component_diagram_bundle(graph, fan_in_threshold=3)

    assert bundle.statistics["cycle_count"] >= 1
    assert bundle.statistics["external_node_count"] == 1
    diagram = next(item for item in bundle.diagrams if "ui" in {node.name for node in item.nodes})
    rendered = render_component_diagram(diagram)
    assert "flowchart LR" in rendered
    assert '(["requests"])' in rendered
    assert "component_ui --> component_data" in rendered
    assert "component_data --> component_ui" in rendered
    assert "classDef cycle" in rendered
