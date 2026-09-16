from Src.generators.object_diagram import build_object_diagram_bundle
from Src.languages.python import PythonLanguageAdapter
from Src.renderers.mermaid_object_diagram import render_object_diagram


def _module(source: str):
    return PythonLanguageAdapter().parse(source)


def test_python_adapter_extracts_static_objects_values_and_references():
    module = _module(
        """
class Repository: pass
class Service: pass

def build():
    repo = Repository(path='db.sqlite')
    service = Service()
    service.timeout = 30
    service.repo = repo
"""
    )

    objects = {item.name: item for item in module.objects if item.scope == "build"}
    assert objects["repo"].type_name == "Repository"
    assert objects["repo"].values == (("path", "'db.sqlite'"),)
    assert objects["service"].values == (("timeout", "30"),)
    assert objects["service"].references == (("repo", "repo"),)


def test_object_diagram_preserves_cycle_without_recursive_expansion():
    module = _module(
        """
class Node: pass

def build():
    left = Node()
    right = Node()
    left.other = right
    right.other = left
"""
    )
    bundle = build_object_diagram_bundle(module)

    assert bundle.statistics["cycle_count"] == 1
    diagram = bundle.diagrams[0]
    assert len(diagram.nodes) == 2
    assert len(diagram.references) == 2


def test_high_fan_in_object_gets_shared_diagram():
    module = _module(
        """
class Config: pass
class Consumer: pass

def build():
    config = Config()
    first = Consumer()
    second = Consumer()
    first.config = config
    second.config = config
"""
    )
    bundle = build_object_diagram_bundle(module, fan_in_threshold=2)

    shared = next(item for item in bundle.diagrams if item.name.startswith("shared_"))
    assert len(shared.nodes) == 3
    assert len(shared.references) == 2
    assert bundle.statistics["shared_node_count"] == 1


def test_mermaid_object_renderer_shows_type_values_and_reference_label():
    module = _module(
        """
class Repository: pass
class Service: pass

def build():
    repo = Repository()
    service = Service(name='api')
    service.repo = repo
"""
    )
    bundle = build_object_diagram_bundle(module)
    rendered = render_object_diagram(bundle.diagrams[0])

    assert rendered.startswith("flowchart LR\n")
    assert "service : Service" in rendered
    assert "name = 'api'" in rendered
    assert "-->|repo|" in rendered
