from Src.generators import generate_flowchart
from Src.languages.python_activity import analyze_python_activity
from Src.renderers import render_flowchart


def test_python_flowchart_api_reuses_logical_control_flow() -> None:
    flow = generate_flowchart(analyze_python_activity(
        """
def login(user):
    if user:
        return open_screen()
    return False
""",
        function="login",
    ))
    assert any(node.kind == "decision" for node in flow.nodes)
    rendered = render_flowchart(flow)
    assert rendered.startswith("flowchart TD\n")
    assert "return False" in rendered


def test_python_flowchart_supports_loops_and_exceptions() -> None:
    flow = generate_flowchart(analyze_python_activity(
        """
def work(items):
    for item in items:
        try:
            await_item(item)
        except TimeoutError:
            continue
""",
        function="work",
    ))
    labels = {node.label for node in flow.nodes}
    assert "loop items" in labels
    assert "except TimeoutError" in render_flowchart(flow)
    assert "continue" in labels
