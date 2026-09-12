"""Deterministic class responsibility table generation from Common IR."""
from __future__ import annotations
import csv
import io
from dataclasses import dataclass
from Src.analyzers.ir import CodeEntity, ModuleIR
from Src.analyzers.ir_queries import classes, functions, qualified_name
@dataclass(frozen=True)
class ResponsibilityRow:
    class_name: str
    responsibility: str

def _words(name: str) -> list[str]:
    import re
    normalized=re.sub(r"([a-z0-9])([A-Z])",r"\1_\2",name).strip("_")
    return [x.lower() for x in normalized.split("_") if x]

def _describe(entity: CodeEntity, methods: list[CodeEntity]) -> str:
    if entity.docstring:
        return entity.docstring.splitlines()[0].strip()
    words=" ".join(_words(entity.name))
    names={m.name.lower() for m in methods}
    if names & {"load","read","save","write"}: return f"Handles {words} data input and output."
    if names & {"update","process","run","execute"}: return f"Coordinates {words} processing."
    if names & {"validate","check","evaluate"}: return f"Validates or evaluates {words} state."
    return f"Manages {words} state and behavior."

def rows(module: ModuleIR) -> list[ResponsibilityRow]:
    class_entities=classes(module); result=[]
    for cls in class_entities:
        methods=[e for e in module.entities if e.parent==qualified_name(cls) and e.kind.value=="method"]
        result.append(ResponsibilityRow(qualified_name(cls),_describe(cls,methods)))
    return result

def to_markdown(rows_: list[ResponsibilityRow]) -> str:
    lines=["| Class | Responsibility |","| --- | --- |"]
    lines.extend(f"| {r.class_name} | {r.responsibility} |" for r in rows_)
    return "\n".join(lines)+"\n"

def to_csv(rows_: list[ResponsibilityRow]) -> str:
    output=io.StringIO(); writer=csv.writer(output,lineterminator="\n"); writer.writerow(["Class","Responsibility"])
    writer.writerows((r.class_name,r.responsibility) for r in rows_)
    return output.getvalue()
def partitions(module: ModuleIR) -> list[list[ResponsibilityRow]]:
    """Group responsibility rows by class-to-class call connectivity."""
    class_names = [qualified_name(entity) for entity in classes(module)]
    parent = {name: name for name in class_names}
    def find(name):
        while parent[name] != name:
            parent[name] = parent[parent[name]]
            name = parent[name]
        return name
    def union(left, right):
        left, right = find(left), find(right)
        if left != right:
            parent[right] = left
    for entity in functions(module):
        owner = entity.parent
        if owner not in parent:
            continue
        for call in entity.calls:
            target = next((name for name in class_names if call == name or call.startswith(name + ".")), None)
            if target:
                union(owner, target)
    grouped: dict[str, list[ResponsibilityRow]] = {}
    by_name = {row.class_name: row for row in rows(module)}
    for name in class_names:
        grouped.setdefault(find(name), []).append(by_name[name])
    return sorted((sorted(group, key=lambda row: row.class_name) for group in grouped.values()), key=lambda group: group[0].class_name)
