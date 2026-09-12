from Src.generators import CommentGenerator

def test_all_primary_language_adapters_are_registered():
    assert CommentGenerator().supported_languages() == ("cpp", "cs", "csharp", "cxx", "gd", "gdscript", "go", "java", "py", "python")