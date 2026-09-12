from Src.generators.responsibility import partitions
from Src.languages.python import PythonLanguageAdapter

def test_partitions_follow_class_calls():
    source="""class Writer:
    def write(self, state):
        State.save()
class State:
    def save(self):
        pass
class Isolated:
    def run(self):
        pass
"""
    groups=partitions(PythonLanguageAdapter().parse(source))
    assert [[row.class_name for row in group] for group in groups] == [["Isolated"],["State","Writer"]]