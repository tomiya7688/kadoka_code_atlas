from Src.generators.responsibility import rows, to_csv, to_markdown
from Src.languages.python import PythonLanguageAdapter

def test_responsibility_outputs_markdown_and_csv():
    module=PythonLanguageAdapter().parse('''class BoardState:\n    def update(self):\n        pass\n''')
    result=rows(module)
    assert result[0].responsibility == 'Coordinates board state processing.'
    assert '| BoardState | Coordinates board state processing. |' in to_markdown(result)
    assert to_csv(result).splitlines()[0] == 'Class,Responsibility'