from pathlib import Path
from tempfile import TemporaryDirectory

from Src.process.application import ApplicationService, SourceAnalysisRequest


def test_application_service_generates_and_saves_state_diagrams():
    with TemporaryDirectory() as folder:
        root = Path(folder)
        source = root / "sample.py"
        source.write_text(
            '''from enum import Enum

class State(Enum):
    IDLE = "idle"
    RUNNING = "running"
    DONE = "done"

class Worker:
    def __init__(self):
        self.state = State.IDLE

    def start(self):
        if self.state == State.IDLE:
            self.state = State.RUNNING

    def finish(self):
        if self.state == State.RUNNING:
            self.state = State.DONE
''',
            encoding="utf-8",
        )
        service = ApplicationService()

        result = service.generate_state_diagrams(
            SourceAnalysisRequest(source, "python")
        )
        paths = service.save_diagram_set(
            root / "output",
            result,
            category="state_diagrams",
        )

        assert len(result.outputs) == 1
        assert result.outputs[0].format == "mermaid"
        assert result.statistics["machine_count"] == 1
        assert paths[0].parent.name == "state_diagrams"
        assert paths[0].suffix == ".mmd"
        content = paths[0].read_text(encoding="utf-8")
        assert "stateDiagram-v2" in content
        assert "[*] --> IDLE" in content
        assert "RUNNING --> DONE" in content
        assert "DONE --> [*]" in content
