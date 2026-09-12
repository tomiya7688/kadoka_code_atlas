"""Deterministic class responsibility table generation from Common IR."""
from __future__ import annotations
import csv
import io
from dataclasses import dataclass
from Src.analyzers.ir import CodeEntity, ModuleIR
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
    classes=module.classes(); result=[]
    for cls in classes:
        methods=[e for e in module.entities if e.parent==cls.qualified_name and e.kind.value=="method"]
        result.append(ResponsibilityRow(cls.qualified_name,_describe(cls,methods)))
    return result

def to_markdown(rows_: list[ResponsibilityRow]) -> str:
    lines=["| Class | Responsibility |","| --- | --- |"]
    lines.extend(f"| {r.class_name} | {r.responsibility} |" for r in rows_)
    return "\n".join(lines)+"\n"

def to_csv(rows_: list[ResponsibilityRow]) -> str:
    output=io.StringIO(); writer=csv.writer(output,lineterminator="\n"); writer.writerow(["Class","Responsibility"])
    writer.writerows((r.class_name,r.responsibility) for r in rows_)
    return output.getvalue()