from Src.generators.comments import RuleBasedCommentGenerator
from Src.languages.python import PythonLanguageAdapter
from Src.languages.python_comments import apply_python_comments


def test_python_adapter_extracts_classes_methods_and_calls():
    source = '''\
class Worker:
    def load_data(self, path):
        return open(path).read()
'''

    module = PythonLanguageAdapter().parse(source)

    assert [entity.qualified_name for entity in module.entities] == [
        "Worker",
        "Worker.load_data",
    ]
    method = module.functions()[0]
    assert method.parameters == ("self", "path")
    assert "open" in method.calls


def test_generator_skips_entities_with_docstrings():
    source = '''\
def load_config(path):
    """Load application configuration."""
    return path
'''

    module = PythonLanguageAdapter().parse(source)
    candidates = RuleBasedCommentGenerator().generate(module)

    assert candidates == []


def test_writer_inserts_role_comments_and_keeps_code_valid():
    source = '''\
class Worker:
    def load_data(self, path):
        return open(path).read()
'''

    module = PythonLanguageAdapter().parse(source)
    candidates = RuleBasedCommentGenerator().generate(module)
    rewritten = apply_python_comments(source, candidates)

    assert "# worker に関する状態と処理をまとめる。" in rewritten
    assert "    # dataを読み込む。" in rewritten
    compile(rewritten, "<generated>", "exec")


def test_writer_does_not_duplicate_existing_adjacent_comment():
    source = '''\
# 設定を読み込む。
def load_config(path):
    return path
'''

    module = PythonLanguageAdapter().parse(source)
    candidates = RuleBasedCommentGenerator().generate(module)
    rewritten = apply_python_comments(source, candidates)

    assert rewritten == source
