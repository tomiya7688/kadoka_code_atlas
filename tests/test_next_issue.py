from tools.next_issue import priority


def test_priority_uses_label_before_title() -> None:
    issue = {
        "number": 10,
        "title": "[P0] title priority",
        "labels": [{"name": "p2"}],
    }

    assert priority(issue) == (2, 10)


def test_priority_falls_back_to_title_prefix() -> None:
    issue = {
        "number": 11,
        "title": "[P1] title priority",
        "labels": [],
    }

    assert priority(issue) == (1, 11)


def test_priority_title_prefix_is_case_insensitive() -> None:
    issue = {
        "number": 12,
        "title": "[p3] title priority",
        "labels": [],
    }

    assert priority(issue) == (3, 12)


def test_priority_without_label_or_prefix_is_unlabeled() -> None:
    issue = {
        "number": 13,
        "title": "No explicit priority",
        "labels": [],
    }

    assert priority(issue) == (50, 13)


def test_priority_uses_issue_number_as_stable_tiebreaker() -> None:
    older = {"number": 2, "title": "[P1] older", "labels": []}
    newer = {"number": 20, "title": "[P1] newer", "labels": []}

    assert min([newer, older], key=priority) is older
