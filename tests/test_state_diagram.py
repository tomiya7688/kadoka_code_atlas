from Src.generators.state_diagram import build_state_diagram_bundle
from Src.languages.python import PythonLanguageAdapter
from Src.renderers.mermaid_state_diagram import render_state_diagram


SOURCE = '''
from enum import Enum

class State(Enum):
    IDLE = "idle"
    RUNNING = "running"
    ERROR = "error"
    DONE = "done"

class Worker:
    def __init__(self):
        self.state = State.IDLE

    def start(self):
        if self.state == State.IDLE:
            self.state = State.RUNNING

    def fail(self):
        match self.state:
            case State.RUNNING:
                self.state = State.ERROR

    def reset(self):
        self.state = State.IDLE

    def finish(self):
        if self.state is State.RUNNING:
            self.state = State.DONE
'''


def test_python_adapter_extracts_explicit_enum_state_machine():
    module = PythonLanguageAdapter().parse(SOURCE)

    assert len(module.state_machines) == 1
    machine = module.state_machines[0]
    assert machine.owner == "Worker"
    assert machine.state_type == "State"
    assert machine.state_variable == "state"
    assert machine.states == ("IDLE", "RUNNING", "ERROR", "DONE")
    assert machine.initial_state == "IDLE"
    assert machine.terminal_states == ("ERROR", "DONE")

    transitions = {
        (item.source, item.target, item.event, item.condition)
        for item in machine.transitions
    }
    assert ("IDLE", "RUNNING", "start", "self.state == State.IDLE") in transitions
    assert ("RUNNING", "ERROR", "fail", None) in transitions
    assert ("*", "IDLE", "reset", None) in transitions
    assert ("RUNNING", "DONE", "finish", "self.state is State.RUNNING") in transitions


def test_state_diagram_bundle_and_mermaid_renderer():
    module = PythonLanguageAdapter().parse(SOURCE)
    bundle = build_state_diagram_bundle(module)

    assert bundle.statistics == {
        "machine_count": 1,
        "state_count": 4,
        "transition_count": 4,
    }
    diagram = bundle.diagrams[0]
    rendered = render_state_diagram(diagram)
    assert diagram.name.startswith("state_")
    assert diagram.name.endswith("_Worker.state")
    assert rendered.startswith("stateDiagram-v2\n")
    assert "[*] --> IDLE" in rendered
    assert "IDLE --> RUNNING: start [self.state == State.IDLE]" in rendered
    assert 'state "Any current state" as __any' in rendered
    assert "__any --> IDLE: reset" in rendered
    assert "ERROR --> [*]" in rendered
    assert "DONE --> [*]" in rendered


def test_non_enum_state_values_are_not_inferred_as_state_machine():
    module = PythonLanguageAdapter().parse(
        '''
class Worker:
    def __init__(self):
        self.state = "idle"
    def start(self):
        self.state = "running"
'''
    )

    assert module.state_machines == []
