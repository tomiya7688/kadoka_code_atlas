"""Kadoka Code Atlas launch point."""

from __future__ import annotations


PROJECT_NAME = "Kadoka Code Atlas"


def main() -> int:
    """Launch Kadoka Code Atlas.

    The application layer is intentionally minimal while the analyzer and
    generator architecture is being implemented. GUI/CLI startup can be
    connected here without changing the external launch point.
    """
    print(f"{PROJECT_NAME}")
    print("Project scaffold is ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
