from __future__ import annotations

from Src.generators import CommentGenerator
from Src.models import CommentTarget


def test_csharp_extracts_dotnet_class_method_and_property_candidates() -> None:
    source = """namespace Reports;
public sealed class ReportStore
{
    public string Name { get; set; }

    public Report LoadReport(string path)
    {
        return new Report();
    }
}
"""

    candidates = CommentGenerator().candidates(source, "cs")

    assert [(item.target, item.name) for item in candidates] == [
        (CommentTarget.CLASS, "ReportStore"),
        (CommentTarget.PROPERTY, "Name"),
        (CommentTarget.METHOD, "LoadReport"),
    ]
    assert candidates[2].text == "// Retrieves report."


def test_csharp_handles_unity_components_serialized_fields_and_lifecycle_methods() -> None:
    source = """public sealed class PlayerController : MonoBehaviour
{
    [SerializeField]
    private float moveSpeed;

    private void Awake()
    {
    }

    private void Update()
    {
    }
}
"""

    candidates = CommentGenerator().candidates(source, "csharp")

    assert [(item.target, item.name) for item in candidates] == [
        (CommentTarget.CLASS, "PlayerController"),
        (CommentTarget.FIELD, "moveSpeed"),
        (CommentTarget.METHOD, "Awake"),
        (CommentTarget.METHOD, "Update"),
    ]
    assert candidates[0].text == "// Coordinates this Unity player controller component."
    assert candidates[1].text == "// Stores the serialized move speed setting."
    assert candidates[2].text == "// Initializes Unity component state."


def test_csharp_generation_preserves_existing_comments_and_is_idempotent() -> None:
    source = """// Existing class description.
public class Documented
{
    // Existing method description.
    public bool IsReady() => true;
}
"""
    generator = CommentGenerator()

    once = generator.generate(source, "csharp")

    assert "// Existing class description." in once
    assert "// Existing method description." in once
    assert "// Groups behavior related to documented." not in once
    assert "// Checks whether ready." not in once
    assert generator.generate(once, "cs") == once
