"""Application service for project deployment analysis."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from Src.analyzers.component_dependencies import (
    ComponentDependencyUnit,
    build_component_dependency_graph,
)
from Src.analyzers.deployment import (
    merge_topologies,
    parse_compose,
    parse_dockerfile,
    parse_kubernetes,
    topology_from_component_graph,
)
from Src.analyzers.package_dependencies import ModuleDependencyUnit
from Src.data.files import read_text, write_text
from Src.data.project_files import discover_deployment_files, discover_supported_files
from Src.generators.deployment_diagram import build_deployment_diagram_bundle
from Src.languages.python_project import PythonProjectLanguageAdapter
from Src.renderers.mermaid_deployment_diagram import render_deployment_diagram


@dataclass(frozen=True, slots=True)
class DeploymentAnalysisRequest:
    root: Path
    mode: str = "full"


@dataclass(frozen=True, slots=True)
class DeploymentOutput:
    name: str
    content: str
    format: str = "mermaid"


@dataclass(frozen=True, slots=True)
class DeploymentSetResult:
    outputs: tuple[DeploymentOutput, ...]
    statistics: dict[str, int | tuple[int, ...]]


class DeploymentService:
    """Orchestrate deployment analysis without UI or renderer-specific discovery logic."""

    def generate(
        self,
        request: DeploymentAnalysisRequest,
        *,
        fan_in_threshold: int = 3,
    ) -> DeploymentSetResult:
        mode = request.mode.lower()
        if mode not in {"simple", "full"}:
            raise ValueError("Deployment mode must be 'simple' or 'full'.")
        if not request.root.is_dir():
            raise ValueError("Deployment analysis expects a project folder.")

        fragments = []
        component_graph = self._python_component_graph(request.root)
        if component_graph.nodes:
            fragments.append(topology_from_component_graph(component_graph))

        if mode == "full":
            for path in discover_deployment_files(request.root):
                relative = str(path.relative_to(request.root)).replace("\\", "/")
                name = path.name.lower()
                source = read_text(path)
                if name.startswith("dockerfile"):
                    fragments.append(parse_dockerfile(source, source_name=relative))
                elif name in {
                    "compose.yml",
                    "compose.yaml",
                    "docker-compose.yml",
                    "docker-compose.yaml",
                }:
                    fragments.append(parse_compose(source, source_name=relative))
                else:
                    fragments.append(parse_kubernetes(source, source_name=relative))

        topology = merge_topologies(*fragments)
        bundle = build_deployment_diagram_bundle(
            topology,
            fan_in_threshold=fan_in_threshold,
        )
        outputs = tuple(
            DeploymentOutput(diagram.name, render_deployment_diagram(diagram))
            for diagram in bundle.diagrams
        )
        statistics = dict(bundle.statistics)
        statistics["mode"] = 1 if mode == "full" else 0
        return DeploymentSetResult(outputs, statistics)

    @staticmethod
    def save(
        output_root: Path,
        result: DeploymentSetResult,
    ) -> tuple[Path, ...]:
        target = output_root / "deployment_diagrams"
        paths: list[Path] = []
        seen: set[Path] = set()
        for output in result.outputs:
            path = target / f"{output.name}.mmd"
            if path in seen:
                raise ValueError(f"Duplicate deployment output path: {path}")
            seen.add(path)
            write_text(path, output.content)
            paths.append(path)
        return tuple(paths)

    @classmethod
    def _python_component_graph(cls, root: Path):
        adapter = PythonProjectLanguageAdapter()
        units: list[ComponentDependencyUnit] = []
        for path in discover_supported_files(root):
            if path.suffix.lower() != ".py":
                continue
            module = adapter.parse(read_text(path))
            unit = ModuleDependencyUnit(
                cls._python_module_name(root, path),
                module.imports,
                path.name == "__init__.py",
            )
            units.append(
                ComponentDependencyUnit(
                    unit,
                    cls._python_component_name(root, path),
                )
            )
        return build_component_dependency_graph(units)

    @staticmethod
    def _python_module_name(root: Path, path: Path) -> str:
        relative = path.relative_to(root)
        parts = list(relative.parts)
        stem = Path(parts[-1]).stem
        if stem == "__init__":
            parts = parts[:-1]
        else:
            parts[-1] = stem
        return ".".join(parts) or root.name

    @staticmethod
    def _python_component_name(root: Path, path: Path) -> str:
        relative = path.relative_to(root)
        if len(relative.parts) == 1:
            return root.name if path.name == "__init__.py" else path.stem
        return ".".join(relative.parts[:-1])
