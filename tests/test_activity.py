from Src.languages.python_activity import analyze_python_activity
from Src.renderers import render_activity_flow


def test_python_activity_extracts_branch_loop_return_and_calls() -> None:
    flow = analyze_python_activity("""
def run(items):
    for item in items:
        if valid(item):
            save(item)
    return True
""", function="run")

    labels = {node.label for node in flow.nodes}
    assert "loop items" in labels
    assert "if valid(item)" in labels
    assert "call save" in labels
    assert "return True" in labels
    rendered = render_activity_flow(flow)
    assert rendered.startswith("flowchart TD\n")
    assert "Yes" in rendered
