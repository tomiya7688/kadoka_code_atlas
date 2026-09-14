from Src.generators.sequence_diagram import SequenceDiagramOptions, build_sequence_diagram_bundle
from Src.languages.python import PythonLanguageAdapter
from Src.renderers.mermaid_sequence_diagram import render_sequence_diagram


def _bundle(source: str, **kwargs):
    module = PythonLanguageAdapter().parse(source)
    return build_sequence_diagram_bundle(module, **kwargs)


def test_python_ir_preserves_ordered_duplicate_calls():
    module = PythonLanguageAdapter().parse(
        """
def main():
    first()
    second()
    first()
"""
    )
    main = next(entity for entity in module.entities if entity.name == "main")

    assert main.calls == ("first", "second")
    assert main.call_sequence == ("first", "second", "first")


def test_sequence_expands_calls_in_order():
    bundle = _bundle(
        """
def main():
    helper()
    tail()

def helper():
    leaf()

def leaf():
    pass

def tail():
    pass
"""
    )
    diagram = next(item for item in bundle.diagrams if item.name.endswith("main"))

    assert [(item.caller, item.callee) for item in diagram.messages] == [
        ("main", "helper"),
        ("helper", "leaf"),
        ("main", "tail"),
    ]


def test_duplicate_calls_can_be_hidden():
    bundle = _bundle(
        """
def main():
    helper()
    helper()
    tail()

def helper(): pass
def tail(): pass
""",
        options=SequenceDiagramOptions(show_duplicate_calls=False),
    )
    diagram = next(item for item in bundle.diagrams if item.name.endswith("main"))

    assert [(item.caller, item.callee) for item in diagram.messages] == [
        ("main", "helper"),
        ("main", "tail"),
    ]


def test_duplicate_calls_are_shown_by_default():
    bundle = _bundle(
        """
def main():
    helper()
    helper()

def helper(): pass
"""
    )
    diagram = next(item for item in bundle.diagrams if item.name.endswith("main"))

    assert [(item.caller, item.callee) for item in diagram.messages] == [
        ("main", "helper"),
        ("main", "helper"),
    ]


def test_sequence_resolves_self_method_calls():
    bundle = _bundle(
        """
class Service:
    def run(self):
        self.load()

    def load(self):
        pass
"""
    )
    diagram = next(item for item in bundle.diagrams if item.name.endswith("Service_run"))

    assert [(item.caller, item.callee) for item in diagram.messages] == [
        ("Service.run", "Service.load"),
    ]


def test_sequence_excludes_cycle_edges_from_diagram():
    bundle = _bundle(
        """
def a(): b()
def b(): a()
"""
    )
    diagram = bundle.diagrams[0]

    assert diagram.messages == ()
    assert bundle.statistics["cycle_count"] == 1


def test_sequence_respects_depth_limit():
    bundle = _bundle(
        """
def a(): b()
def b(): c()
def c(): d()
def d(): pass
""",
        max_depth=2,
    )
    diagram = next(item for item in bundle.diagrams if item.name.endswith("a"))

    assert [(item.caller, item.callee) for item in diagram.messages] == [
        ("a", "b"),
        ("b", "c"),
    ]


def test_returns_can_be_enabled():
    bundle = _bundle(
        """
def main(): helper()
def helper(): leaf()
def leaf(): pass
""",
        options=SequenceDiagramOptions(show_returns=True),
    )
    diagram = next(item for item in bundle.diagrams if item.name.endswith("main"))

    assert [(item.caller, item.callee, item.kind) for item in diagram.messages] == [
        ("main", "helper", "call"),
        ("helper", "leaf", "call"),
        ("leaf", "helper", "return"),
        ("helper", "main", "return"),
    ]


def test_returns_are_hidden_by_default():
    bundle = _bundle(
        """
def main(): helper()
def helper(): pass
"""
    )
    diagram = next(item for item in bundle.diagrams if item.name.endswith("main"))

    assert all(item.kind == "call" for item in diagram.messages)


def test_high_fan_in_callable_gets_shared_sequence():
    bundle = _bundle(
        """
def first(): shared()
def second(): shared()
def shared(): sink()
def sink(): pass
""",
        fan_in_threshold=2,
    )

    shared = next(item for item in bundle.diagrams if item.name == "shared_shared")
    assert {(item.caller, item.callee) for item in shared.messages[:2]} == {
        ("first", "shared"),
        ("second", "shared"),
    }
    assert (shared.messages[-1].caller, shared.messages[-1].callee) == ("shared", "sink")
    assert bundle.statistics["shared_node_count"] == 1


def test_sequence_options_validate_boolean_values():
    try:
        SequenceDiagramOptions.from_mapping({"show_returns": "yes"})
    except ValueError as error:
        assert "show_returns" in str(error)
    else:
        raise AssertionError("invalid sequence option should be rejected")


def test_mermaid_sequence_renderer_uses_dashed_return_arrow():
    bundle = _bundle(
        """
def main(): helper()
def helper(): pass
""",
        options=SequenceDiagramOptions(show_returns=True),
    )
    rendered = render_sequence_diagram(bundle.diagrams[0])

    assert rendered.startswith("sequenceDiagram\n")
    assert "participant p0 as main" in rendered
    assert "->>" in rendered
    assert "-->>" in rendered
    assert ": return" in rendered
