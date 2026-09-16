from pathlib import Path

from Src.process.deployment_service import DeploymentAnalysisRequest, DeploymentService


def test_deployment_service_generates_and_saves_project_diagrams(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("import requests\n", encoding="utf-8")
    (tmp_path / "compose.yaml").write_text(
        """
services:
  app:
    build: .
    depends_on: [db]
  db:
    image: postgres:17
""",
        encoding="utf-8",
    )
    (tmp_path / "Dockerfile").write_text("FROM python:3.13-slim\n", encoding="utf-8")

    service = DeploymentService()
    result = service.generate(DeploymentAnalysisRequest(tmp_path, "full"))

    assert result.outputs
    combined = "\n".join(output.content for output in result.outputs)
    assert "requests" in combined
    assert "app" in combined
    assert "db" in combined
    assert "python:3.13-slim" in combined
    assert result.statistics["confirmed_node_count"] >= 3
    assert result.statistics["inferred_node_count"] >= 1

    output_root = tmp_path / "out"
    paths = service.save(output_root, result)
    assert paths
    assert all(path.parent.name == "deployment_diagrams" for path in paths)
    assert all(path.suffix == ".mmd" and path.exists() for path in paths)


def test_simple_mode_skips_deployment_config_but_keeps_source_inference(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("import requests\n", encoding="utf-8")
    (tmp_path / "compose.yaml").write_text(
        "services:\n  db:\n    image: postgres:17\n",
        encoding="utf-8",
    )

    result = DeploymentService().generate(DeploymentAnalysisRequest(tmp_path, "simple"))
    combined = "\n".join(output.content for output in result.outputs)
    assert "requests" in combined
    assert "postgres" not in combined
    assert result.statistics["mode"] == 0
