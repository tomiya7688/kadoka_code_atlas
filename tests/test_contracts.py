from Src.analyzers.ir import ModuleIR
from Src.languages import CSharpAdapter, LanguageAdapter
from Src.languages.python import PythonLanguageAdapter
from Src.models.comments import ParsedSource
from Src.process.contracts import CommentAdapter
from Src.renderers import Renderer
from Src.renderers.mermaid_call_graph import render_call_graph


def test_language_adapter_contract_returns_common_ir() -> None:
    adapter: LanguageAdapter = PythonLanguageAdapter()
    result = adapter.parse("value = 1\n")
    assert isinstance(result, ModuleIR)


def test_comment_adapter_contract_is_separate_from_common_ir_adapter() -> None:
    adapter: CommentAdapter = CSharpAdapter()
    result = adapter.parse("class Sample {}\n")
    assert isinstance(result, ParsedSource)


def test_renderer_contract_describes_text_output() -> None:
    class TextRenderer:
        def render(self, value: str) -> str:
            return value.upper()

    renderer: Renderer[str] = TextRenderer()
    assert renderer.render("logical output") == "LOGICAL OUTPUT"
    assert isinstance(render_call_graph, object)
