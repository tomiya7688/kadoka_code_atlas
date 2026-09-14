from app import main


def test_version_does_not_require_gui(capsys):
    assert main(["--version"]) == 0
    assert "Kadoka Code Atlas 0.1.0" in capsys.readouterr().out
