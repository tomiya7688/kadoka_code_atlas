from Src.analyzers.package_dependencies import (
    ModuleDependencyUnit,
    build_package_dependency_graph,
)
from Src.generators.package_diagram import build_package_diagram_bundle
from Src.languages.python_project import PythonProjectLanguageAdapter
from Src.renderers.mermaid_package_diagram import render_package_diagram


def test_python_project_adapter_normalizes_import_references():
    module = PythonProjectLanguageAdapter().parse(
        "import pkg.b\nfrom . import c\nfrom ..shared import value\n"
    )

    assert module.imports == ("pkg.b", ".c", "..shared")


def test_package_dependency_graph_resolves_relative_imports_cycles_and_isolates():
    graph = build_package_dependency_graph(
        [
            ModuleDependencyUnit("pkg", (), True),
            ModuleDependencyUnit("pkg.a", (".b",)),
            ModuleDependencyUnit("pkg.b", (".a",)),
            ModuleDependencyUnit("pkg.lone", ()),
        ]
    )

    assert {(item.caller, item.callee) for item in graph.edges} == {
        ("pkg.a", "pkg.b"),
        ("pkg.b", "pkg.a"),
    }
    assert graph.isolated_nodes() == ("pkg", "pkg.lone")
    assert graph.cycles()


def test_package_diagram_marks_cycles_and_isolated_modules():
    graph = build_package_dependency_graph(
        [
            ModuleDependencyUnit("pkg.a", ("pkg.b",)),
            ModuleDependencyUnit("pkg.b", ("pkg.a",)),
            ModuleDependencyUnit("pkg.lone", ()),
        ]
    )
    bundle = build_package_diagram_bundle(graph, fan_in_threshold=3)

    assert bundle.statistics["cycle_count"] >= 1
    assert bundle.statistics["isolated_node_count"] == 1
    cycle_diagram = next(item for item in bundle.diagrams if "pkg.a" in item.nodes)
    rendered_cycle = render_package_diagram(cycle_diagram)
    assert "flowchart LR" in rendered_cycle
    assert "pkg.a" in rendered_cycle and "pkg.b" in rendered_cycle
    assert "classDef cycle" in rendered_cycle

    isolated_diagram = next(item for item in bundle.diagrams if "pkg.lone" in item.nodes)
    rendered_isolated = render_package_diagram(isolated_diagram)
    assert "classDef isolated" in rendered_isolated
