"""Tkinter GUI for the Python reference implementation."""

from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

from Src.process.application import (
    ApplicationService,
    CIRequest,
    CommentRequest,
    DiagramSetResult,
    SourceAnalysisRequest,
)

PROJECT_NAME = "Kadoka Code Atlas"

_OPERATION_COMMENTS = "Generate comments"
_OPERATION_CALL_GRAPH = "Call graph (Mermaid)"
_OPERATION_CLASS_DIAGRAM = "Class diagrams (Mermaid)"
_OPERATION_OBJECT_DIAGRAM = "Object diagrams (Mermaid)"
_OPERATION_SEQUENCE_DIAGRAM = "Sequence diagrams (Mermaid)"
_OPERATION_COMMUNICATION_DIAGRAM = "Communication diagrams (Mermaid)"
_OPERATION_STATE_DIAGRAM = "State diagrams (Mermaid)"
_OPERATION_RESPONSIBILITY = "Class responsibility tables"
_OPERATION_DESIGN_QUALITY = "Design quality report"
_OPERATION_CI = "GitHub Actions CI graph"
_OPERATIONS = (
    _OPERATION_COMMENTS,
    _OPERATION_CALL_GRAPH,
    _OPERATION_CLASS_DIAGRAM,
    _OPERATION_OBJECT_DIAGRAM,
    _OPERATION_SEQUENCE_DIAGRAM,
    _OPERATION_COMMUNICATION_DIAGRAM,
    _OPERATION_STATE_DIAGRAM,
    _OPERATION_RESPONSIBILITY,
    _OPERATION_DESIGN_QUALITY,
    _OPERATION_CI,
)


class AtlasTkApp:
    """Thin Tkinter front end over :class:`ApplicationService`."""

    def __init__(self, root: tk.Tk, service: ApplicationService | None = None) -> None:
        self.root = root
        self.service = service or ApplicationService()
        self.base_path: Path | None = None
        self.files: list[Path] = []
        self.current_file: Path | None = None
        self.last_result = ""
        self.last_format = "text"
        self.last_diagram_set: DiagramSetResult | None = None
        self.last_diagram_category: str | None = None

        sequence_settings = self.service.sequence_diagram_settings()
        self.path_var = tk.StringVar(value="No file or folder selected")
        self.language_var = tk.StringVar(value="Language: -")
        self.operation_var = tk.StringVar(value=_OPERATION_COMMENTS)
        self.status_var = tk.StringVar(value="Select a source file or project folder.")
        self.sequence_duplicate_var = tk.BooleanVar(
            value=sequence_settings["show_duplicate_calls"]
        )
        self.sequence_returns_var = tk.BooleanVar(value=sequence_settings["show_returns"])

        self._build_window()

    def _build_window(self) -> None:
        self.root.title(PROJECT_NAME)
        self.root.geometry("1100x740")
        self.root.minsize(820, 560)

        outer = ttk.Frame(self.root, padding=10)
        outer.pack(fill=tk.BOTH, expand=True)

        chooser = ttk.Frame(outer)
        chooser.pack(fill=tk.X)
        ttk.Label(chooser, textvariable=self.path_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(chooser, text="Open File", command=self.open_file).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(chooser, text="Open Folder", command=self.open_folder).pack(side=tk.LEFT, padx=(8, 0))

        controls = ttk.Frame(outer)
        controls.pack(fill=tk.X, pady=(10, 6))
        ttk.Label(controls, textvariable=self.language_var).pack(side=tk.LEFT)
        ttk.Label(controls, text="Operation:").pack(side=tk.LEFT, padx=(18, 6))
        operation = ttk.Combobox(
            controls,
            textvariable=self.operation_var,
            values=_OPERATIONS,
            state="readonly",
            width=36,
        )
        operation.pack(side=tk.LEFT)
        ttk.Button(controls, text="Run", command=self.run_selected).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(controls, text="Save Result", command=self.save_result).pack(side=tk.LEFT, padx=(8, 0))

        sequence_settings = ttk.Labelframe(outer, text="Sequence diagram settings", padding=6)
        sequence_settings.pack(fill=tk.X, pady=(0, 8))
        ttk.Checkbutton(
            sequence_settings,
            text="Show duplicate calls",
            variable=self.sequence_duplicate_var,
        ).pack(side=tk.LEFT)
        ttk.Checkbutton(
            sequence_settings,
            text="Show return messages",
            variable=self.sequence_returns_var,
        ).pack(side=tk.LEFT, padx=(18, 0))
        ttk.Label(
            sequence_settings,
            text="Cycles are always excluded from sequence diagrams.",
        ).pack(side=tk.LEFT, padx=(18, 0))

        pane = ttk.Panedwindow(outer, orient=tk.HORIZONTAL)
        pane.pack(fill=tk.BOTH, expand=True)

        files_frame = ttk.Labelframe(pane, text="Project files", padding=6)
        result_frame = ttk.Labelframe(pane, text="Result / Mermaid source", padding=6)
        pane.add(files_frame, weight=1)
        pane.add(result_frame, weight=3)

        self.file_list = tk.Listbox(files_frame, exportselection=False)
        file_scroll = ttk.Scrollbar(files_frame, orient=tk.VERTICAL, command=self.file_list.yview)
        self.file_list.configure(yscrollcommand=file_scroll.set)
        self.file_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        file_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_list.bind("<<ListboxSelect>>", self._on_file_selected)

        self.result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.NONE, undo=False)
        self.result_text.pack(fill=tk.BOTH, expand=True)
        self.result_text.configure(state=tk.DISABLED)

        ttk.Label(outer, textvariable=self.status_var, anchor=tk.W).pack(fill=tk.X, pady=(8, 0))

    def open_file(self) -> None:
        selected = filedialog.askopenfilename(
            title="Select source file",
            filetypes=[
                ("Supported files", "*.py *.gd *.cs *.cpp *.cc *.cxx *.hpp *.java *.go *.yml *.yaml"),
                ("All files", "*.*"),
            ],
        )
        if not selected:
            return
        path = Path(selected)
        if self.service.detect_language(path) == "unknown":
            messagebox.showwarning(PROJECT_NAME, "The selected file type is not supported yet.")
            return
        self._load_paths(path, [path])

    def open_folder(self) -> None:
        selected = filedialog.askdirectory(title="Select project folder")
        if not selected:
            return
        root = Path(selected)
        files = self.service.discover_supported_files(root)
        self._load_paths(root, files)
        if not files:
            self.status_var.set("No supported source files were found in the selected folder.")

    def _load_paths(self, base_path: Path, files: list[Path]) -> None:
        self.base_path = base_path
        self.files = files
        self.current_file = None
        self.path_var.set(str(base_path))
        self.file_list.delete(0, tk.END)
        for path in files:
            display = str(path.relative_to(base_path)) if base_path.is_dir() else path.name
            self.file_list.insert(tk.END, display)
        if files:
            self.file_list.selection_set(0)
            self.file_list.activate(0)
            self._select_file(0)
            self.status_var.set(f"{len(files)} supported file(s) available.")

    def _on_file_selected(self, _event: object) -> None:
        selection = self.file_list.curselection()
        if selection:
            self._select_file(selection[0])

    def _select_file(self, index: int) -> None:
        self.current_file = self.files[index]
        language = self.service.detect_language(self.current_file)
        self.language_var.set(f"Language: {language}")
        if language == "yaml":
            self.operation_var.set(_OPERATION_CI)
        elif language != "python" and self.operation_var.get() in {
            _OPERATION_CALL_GRAPH,
            _OPERATION_CLASS_DIAGRAM,
            _OPERATION_OBJECT_DIAGRAM,
            _OPERATION_SEQUENCE_DIAGRAM,
            _OPERATION_COMMUNICATION_DIAGRAM,
            _OPERATION_STATE_DIAGRAM,
            _OPERATION_RESPONSIBILITY,
            _OPERATION_DESIGN_QUALITY,
        }:
            self.operation_var.set(_OPERATION_COMMENTS)

    def run_selected(self) -> None:
        if self.current_file is None:
            messagebox.showinfo(PROJECT_NAME, "Select a source file first.")
            return

        path = self.current_file
        language = self.service.detect_language(path)
        operation = self.operation_var.get()
        self.status_var.set(f"Running {operation} for {path.name}...")
        self.root.update_idletasks()
        self.last_diagram_set = None
        self.last_diagram_category = None

        try:
            if operation == _OPERATION_COMMENTS:
                if language == "yaml":
                    raise ValueError("Comment generation is not available for YAML files.")
                result = self.service.generate_comments(CommentRequest(path, language))
                content = result.content
                result_format = "source"
            elif operation == _OPERATION_CALL_GRAPH:
                result = self.service.generate_call_graph(SourceAnalysisRequest(path, language))
                content = result.content
                result_format = result.format
            elif operation == _OPERATION_CLASS_DIAGRAM:
                outputs = self.service.generate_class_diagrams(SourceAnalysisRequest(path, language))
                self.last_diagram_set = outputs
                self.last_diagram_category = "class_diagrams"
                content = self._output_set_text(outputs)
                result_format = "mermaid-bundle"
            elif operation == _OPERATION_OBJECT_DIAGRAM:
                outputs = self.service.generate_object_diagrams(SourceAnalysisRequest(path, language))
                self.last_diagram_set = outputs
                self.last_diagram_category = "object_diagrams"
                content = self._output_set_text(outputs)
                result_format = "mermaid-bundle"
            elif operation == _OPERATION_SEQUENCE_DIAGRAM:
                outputs = self.service.generate_sequence_diagrams(
                    SourceAnalysisRequest(path, language),
                    show_duplicate_calls=self.sequence_duplicate_var.get(),
                    show_returns=self.sequence_returns_var.get(),
                )
                self.last_diagram_set = outputs
                self.last_diagram_category = "sequence_diagrams"
                content = self._output_set_text(outputs)
                result_format = "mermaid-bundle"
            elif operation == _OPERATION_COMMUNICATION_DIAGRAM:
                outputs = self.service.generate_communication_diagrams(
                    SourceAnalysisRequest(path, language),
                    show_duplicate_calls=self.sequence_duplicate_var.get(),
                )
                self.last_diagram_set = outputs
                self.last_diagram_category = "communication_diagrams"
                content = self._output_set_text(outputs)
                result_format = "mermaid-bundle"
            elif operation == _OPERATION_STATE_DIAGRAM:
                outputs = self.service.generate_state_diagrams(
                    SourceAnalysisRequest(path, language)
                )
                self.last_diagram_set = outputs
                self.last_diagram_category = "state_diagrams"
                content = self._output_set_text(outputs)
                result_format = "mermaid-bundle"
            elif operation == _OPERATION_RESPONSIBILITY:
                outputs = self.service.generate_responsibility_tables(
                    SourceAnalysisRequest(path, language),
                    output_format="markdown",
                )
                self.last_diagram_set = outputs
                self.last_diagram_category = "responsibility_tables"
                content = self._output_set_text(outputs)
                result_format = "markdown-bundle"
            elif operation == _OPERATION_DESIGN_QUALITY:
                result = self.service.evaluate_design_quality(
                    SourceAnalysisRequest(path, language)
                )
                content = result.content
                result_format = result.format
            elif operation == _OPERATION_CI:
                if path.suffix.lower() not in {".yml", ".yaml"}:
                    raise ValueError("CI analysis expects a GitHub Actions YAML file.")
                result = self.service.analyze_ci(CIRequest(path))
                content = result.content
                result_format = "mermaid"
            else:
                raise ValueError(f"Unknown operation: {operation}")
        except Exception as exc:
            self.status_var.set("Analysis failed.")
            messagebox.showerror(PROJECT_NAME, str(exc))
            return

        self.last_result = content
        self.last_format = result_format
        self._show_result(content)
        self.status_var.set(f"Completed: {operation} ({result_format}).")

    @staticmethod
    def _output_set_text(result: DiagramSetResult) -> str:
        if not result.outputs:
            return "No outputs were generated.\n"
        sections = []
        for output in result.outputs:
            if output.format == "mermaid":
                header = f"%% {output.name}"
            elif output.format == "markdown":
                header = f"## {output.name}"
            else:
                header = f"# {output.name}"
            sections.append(f"{header}\n{output.content.rstrip()}")
        return "\n\n".join(sections) + "\n"

    def _show_result(self, content: str) -> None:
        self.result_text.configure(state=tk.NORMAL)
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert("1.0", content)
        self.result_text.configure(state=tk.DISABLED)

    def save_result(self) -> None:
        if not self.last_result:
            messagebox.showinfo(PROJECT_NAME, "Run an analysis before saving a result.")
            return

        if self.last_diagram_set is not None and self.last_diagram_category is not None:
            selected = filedialog.askdirectory(title="Select output folder")
            if not selected:
                return
            paths = self.service.save_diagram_set(
                Path(selected),
                self.last_diagram_set,
                category=self.last_diagram_category,
            )
            self.status_var.set(f"Saved {len(paths)} output file(s) under {selected}")
            return

        extension = {
            "mermaid": ".mmd",
            "markdown": ".md",
            "csv": ".csv",
            "source": self.current_file.suffix if self.current_file else ".txt",
        }.get(self.last_format, ".txt")
        selected = filedialog.asksaveasfilename(
            title="Save result",
            defaultextension=extension,
            filetypes=[("Result file", f"*{extension}"), ("All files", "*.*")],
        )
        if not selected:
            return
        self.service.save_text(Path(selected), self.last_result)
        self.status_var.set(f"Saved result to {selected}")


def launch_gui(service: ApplicationService | None = None) -> None:
    """Start the Tkinter desktop application."""
    root = tk.Tk()
    AtlasTkApp(root, service)
    root.mainloop()
