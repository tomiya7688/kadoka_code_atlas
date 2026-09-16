"""Format-specific rendering for class responsibility tables."""

from __future__ import annotations

import csv
import io
from collections.abc import Sequence

from Src.generators.responsibility import ResponsibilityRow


def render_responsibility_markdown(rows: Sequence[ResponsibilityRow]) -> str:
    lines = ["| Class | Responsibility |", "| --- | --- |"]
    lines.extend(f"| {row.class_name} | {row.responsibility} |" for row in rows)
    return "\n".join(lines) + "\n"


def render_responsibility_csv(rows: Sequence[ResponsibilityRow]) -> str:
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(["Class", "Responsibility"])
    writer.writerows((row.class_name, row.responsibility) for row in rows)
    return output.getvalue()
