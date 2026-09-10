from __future__ import annotations

from Src.generators import CommentGenerator
from Src.models import CommentTarget


def test_gdscript_extracts_godot_specific_candidates() -> None:
    source = """extends CharacterBody2D
signal health_changed(value: int)
@export var move_speed: float = 180.0
@onready var animation_player: AnimationPlayer = $AnimationPlayer

func _ready() -> void:
    pass

func _physics_process(delta: float) -> void:
    pass
"""
    candidates = CommentGenerator().candidates(source, "gd")
    assert [(item.target, item.name) for item in candidates] == [
        (CommentTarget.MODULE, "CharacterBody2D"), (CommentTarget.SIGNAL, "health_changed"),
        (CommentTarget.FIELD, "move_speed"), (CommentTarget.FIELD, "animation_player"),
        (CommentTarget.FUNCTION, "_ready"), (CommentTarget.FUNCTION, "_physics_process"),
    ]
    assert candidates[3].text == "# Caches the ready animation player node reference."
    assert candidates[5].text == "# Updates physics-related behavior on Godot's fixed timestep."


def test_gdscript_preserves_existing_comments_and_is_idempotent() -> None:
    source = """# Existing script description.
extends Node

# Existing lifecycle explanation.
func _ready() -> void:
    pass
"""
    generator = CommentGenerator()
    once = generator.generate(source, "gdscript")
    assert "# Defines behavior for a Node node." not in once
    assert "# Initializes node state after it enters the scene tree." not in once
    assert generator.generate(once, "gd") == once
