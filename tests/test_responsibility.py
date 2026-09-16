from Src.generators.responsibility import build_responsibility_table_bundle, rows
from Src.languages.python import PythonLanguageAdapter
from Src.renderers.responsibility_table import (
    render_responsibility_csv,
    render_responsibility_markdown,
)


def test_responsibility_outputs_markdown_and_csv():
    module = PythonLanguageAdapter().parse(
        """class BoardState:
    def update(self):
        pass
"""
    )
    result = rows(module)
    assert result[0].responsibility == "Coordinates board state processing."
    assert "| BoardState | Coordinates board state processing. |" in render_responsibility_markdown(result)
    assert render_responsibility_csv(result).splitlines()[0] == "Class,Responsibility"


def test_responsibility_tables_partition_related_classes_and_isolated_classes():
    module = PythonLanguageAdapter().parse(
        """
class Repository: pass
class Service:
    def run(self): Repository()
class Unrelated: pass
"""
    )
    bundle = build_responsibility_table_bundle(module)
    groups = [{row.class_name for row in table.rows} for table in bundle.tables]

    assert {"Repository", "Service"} in groups
    assert {"Unrelated"} in groups
    assert bundle.statistics["series_count"] == 2


def test_high_fan_in_class_gets_shared_responsibility_table():
    module = PythonLanguageAdapter().parse(
        """
class Shared: pass
class First:
    def run(self): Shared()
class Second:
    def run(self): Shared()
"""
    )
    bundle = build_responsibility_table_bundle(module, fan_in_threshold=2)

    shared = next(table for table in bundle.tables if table.name.startswith("shared_"))
    assert [row.class_name for row in shared.rows] == ["Shared"]
    assert bundle.statistics["shared_node_count"] == 1
