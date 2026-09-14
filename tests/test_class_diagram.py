from Src.analyzers.class_relations import build_class_relation_graph
from Src.analyzers.ir import Visibility
from Src.analyzers.ir_queries import classes, qualified_name
from Src.generators.class_diagram import ClassDiagramOptions, build_class_diagram_bundle
from Src.languages.python import PythonLanguageAdapter
from Src.renderers.mermaid_class_diagram import render_class_diagram


def _module(source: str):
    return PythonLanguageAdapter().parse(source)


def test_python_adapter_normalizes_bases_and_visibility():
    module = _module(
        """
class Base: pass
class _Child(Base):
    def public(self): pass
    def _protected(self): pass
    def __private(self): pass
"""
    )
    by_name = {qualified_name(entity): entity for entity in module.entities}

    assert by_name["_Child"].bases == ("Base",)
    assert by_name["_Child"].visibility is Visibility.PROTECTED
    assert by_name["_Child.public"].visibility is Visibility.PUBLIC
    assert by_name["_Child._protected"].visibility is Visibility.PROTECTED
    assert by_name["_Child.__private"].visibility is Visibility.PRIVATE


def test_class_relation_graph_collects_inheritance_and_class_use():
    graph = build_class_relation_graph(
        _module(
            """
class Base: pass
class Helper: pass
class Service(Base):
    def run(self):
        Helper()
"""
        )
    )

    assert {(edge.caller, edge.callee, edge.relation) for edge in graph.edges} == {
        ("Service", "Base", "inheritance"),
        ("Service", "Helper", "uses"),
    }


def test_class_diagram_uses_shared_partition_for_high_fan_in_class():
    bundle = build_class_diagram_bundle(
        _module(
            """
class Shared: pass
class First:
    def run(self): Shared()
class Second:
    def run(self): Shared()
"""
        ),
        fan_in_threshold=2,
    )

    assert bundle.statistics["shared_node_count"] == 1
    shared = next(diagram for diagram in bundle.diagrams if diagram.name == "shared_Shared")
    assert {node.name for node in shared.nodes} == {"First", "Second", "Shared"}
    assert {(relation.source, relation.target) for relation in shared.relations} == {
        ("First", "Shared"),
        ("Second", "Shared"),
    }


def test_visibility_options_filter_members_before_rendering():
    bundle = build_class_diagram_bundle(
        _module(
            """
class Service:
    def public(self): pass
    def _protected(self): pass
    def __private(self): pass
"""
        ),
        options=ClassDiagramOptions(
            include_public=True,
            include_protected=False,
            include_private=False,
        ),
    )
    rendered = render_class_diagram(bundle.diagrams[0])

    assert "+public(self)" in rendered
    assert "_protected" not in rendered
    assert "__private" not in rendered


def test_mermaid_renderer_draws_inheritance_without_owning_partition_logic():
    bundle = build_class_diagram_bundle(
        _module(
            """
class Base: pass
class Child(Base): pass
"""
        )
    )

    rendered = render_class_diagram(bundle.diagrams[0])
    assert rendered.startswith("classDiagram\n")
    assert "<|--" in rendered
    assert '"Base"' in rendered
    assert '"Child"' in rendered
