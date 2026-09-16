from Src.generators.use_case_diagram import build_use_case_diagram_bundle
from Src.languages.python import PythonLanguageAdapter
from Src.languages.python_usecase import PythonUseCaseLanguageAdapter
from Src.renderers.mermaid_use_case_diagram import render_use_case_diagram


def _combined(source: str):
    module = PythonLanguageAdapter().parse(source)
    module.input_events = PythonUseCaseLanguageAdapter().parse(source).input_events
    return module


def test_tkinter_command_and_bind_become_user_inputs_without_duplicate_widget_event() -> None:
    source = """
import tkinter as tk
from tkinter import ttk

class Window:
    def __init__(self):
        self.save_button = ttk.Button(text="Save", command=self.on_save_clicked)
        self.save_button.bind("<Return>", self.on_save_clicked)

    def on_save_clicked(self, event=None):
        self.validate()
        self.save_file()

    def validate(self):
        return True

    def save_file(self):
        pass

    def internal_maintenance(self):
        pass
"""
    event_module = PythonUseCaseLanguageAdapter().parse(source)

    assert [(item.component, item.event, item.handler, item.label) for item in event_module.input_events] == [
        ("self.save_button", "command", "self.on_save_clicked", "Save"),
        ("self.save_button", "<Return>", "self.on_save_clicked", None),
    ]

    bundle = build_use_case_diagram_bundle(_combined(source))
    assert bundle.statistics["use_case_count"] == 2
    assert len(bundle.diagrams) == 1
    use_case = bundle.diagrams[0].use_cases[0]
    assert use_case.name == "Save"
    assert use_case.handler == "Window.on_save_clicked"
    assert use_case.call_chain == ("Window.validate", "Window.save_file")
    assert all("internal_maintenance" not in item.call_chain for item in bundle.diagrams[0].use_cases)


def test_qt_signal_and_kivy_bind_are_detected() -> None:
    source = """
class Window:
    def wire(self):
        self.save_button.clicked.connect(self.on_save)
        self.cancel_button.bind(on_press=self.on_cancel)

    def on_save(self):
        persist()

    def on_cancel(self):
        close()
"""
    events = PythonUseCaseLanguageAdapter().parse(source).input_events
    assert [(item.component, item.event, item.handler) for item in events] == [
        ("self.save_button", "clicked", "self.on_save"),
        ("self.cancel_button", "on_press", "self.on_cancel"),
    ]


def test_use_case_name_falls_back_to_handler_and_call_chain_is_cycle_safe() -> None:
    source = """
class Window:
    def wire(self):
        self.login_button.clicked.connect(self.handle_login_clicked)

    def handle_login_clicked(self):
        self.authenticate()

    def authenticate(self):
        self.handle_login_clicked()
"""
    bundle = build_use_case_diagram_bundle(_combined(source), max_depth=5)
    use_case = bundle.diagrams[0].use_cases[0]
    assert use_case.name == "Login"
    assert use_case.call_chain == ("Window.authenticate",)


def test_mermaid_use_case_output_is_user_facing_and_keeps_handler_chain_as_comment() -> None:
    source = """
class Window:
    def __init__(self):
        self.save = Button(text="Save file", command=self.on_save)
    def on_save(self):
        self.persist()
    def persist(self):
        pass
"""
    diagram = build_use_case_diagram_bundle(_combined(source)).diagrams[0]
    rendered = render_use_case_diagram(diagram)

    assert rendered.startswith("flowchart LR\n")
    assert '["User"]' in rendered
    assert '(["Save file"])' in rendered
    assert 'self.save / command' in rendered
    assert "%% handler-chain: Window.on_save -> Window.persist" in rendered
    assert "persist([" not in rendered


def test_internal_functions_without_gui_registration_do_not_become_use_cases() -> None:
    module = _combined("""
def save_file():
    validate()
def validate():
    pass
""")
    bundle = build_use_case_diagram_bundle(module)
    assert bundle.diagrams == ()
    assert bundle.statistics["use_case_count"] == 0
