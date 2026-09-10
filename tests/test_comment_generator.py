from __future__ import annotations

import ast

from Src.generators import CommentGenerator
from Src.models import CommentTarget


def test_python_candidates_describe_classes_and_functions() -> None:
    source = """class ReportBuilder:\n    def build_report(self):\n        return {}\n\ndef load_config():\n    return {}\n"""

    candidates = CommentGenerator().candidates(source, "python")

    assert [(item.target, item.name) for item in candidates] == [
        (CommentTarget.CLASS, "ReportBuilder"),
        (CommentTarget.METHOD, "build_report"),
        (CommentTarget.FUNCTION, "load_config"),
    ]
    assert candidates[2].text == "# Retrieves config."


def test_generation_preserves_valid_python_and_existing_documentation() -> None:
    source = '''class Documented:\n    """Keep this documentation."""\n\n    def save(self):\n        # Existing explanation.\n        return True\n\ndef is_ready():\n    return True\n'''

    result = CommentGenerator().generate(source, "py")

    ast.parse(result)
    assert '"""Keep this documentation."""' in result
    assert "# Existing explanation." in result
    assert result.count("# Checks whether ready.") == 1
    assert "# Groups behavior related to documented." not in result
    assert "# Performs the save operation." not in result


def test_generation_is_idempotent() -> None:
    source = "def calculate_total():\n    return 1\n"
    generator = CommentGenerator()

    once = generator.generate(source, "python")

    assert generator.generate(once, "python") == once
