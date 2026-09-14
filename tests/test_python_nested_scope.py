from Src.analyzers.ir import EntityKind
from Src.analyzers.ir_queries import qualified_name
from Src.languages.python import PythonLanguageAdapter


def _entities(source: str):
    module = PythonLanguageAdapter().parse(source)
    return {qualified_name(entity): entity for entity in module.entities}


def test_nested_function_owns_its_calls_and_remains_function():
    entities = _entities(
        """
def outer():
    first()

    def inner():
        second()
"""
    )

    assert entities["outer"].calls == ("first",)
    assert entities["outer.inner"].calls == ("second",)
    assert entities["outer.inner"].kind is EntityKind.FUNCTION


def test_class_method_is_method_but_nested_function_is_not():
    entities = _entities(
        """
class Service:
    def run(self):
        direct()

        def helper():
            nested()
"""
    )

    assert entities["Service.run"].kind is EntityKind.METHOD
    assert entities["Service.run"].calls == ("direct",)
    assert entities["Service.run.helper"].kind is EntityKind.FUNCTION
    assert entities["Service.run.helper"].calls == ("nested",)


def test_nested_class_and_lambda_calls_do_not_leak_to_outer_function():
    entities = _entities(
        """
def outer():
    direct()

    class Local:
        def method(self):
            class_call()

    callback = lambda: lambda_call()
"""
    )

    assert entities["outer"].calls == ("direct",)
    assert entities["outer.Local.method"].kind is EntityKind.METHOD
    assert entities["outer.Local.method"].calls == ("class_call",)


def test_async_nested_function_uses_same_scope_rules():
    entities = _entities(
        """
async def outer():
    before()

    async def inner():
        after()
"""
    )

    assert entities["outer"].calls == ("before",)
    assert entities["outer.inner"].kind is EntityKind.FUNCTION
    assert entities["outer.inner"].calls == ("after",)
