"""Conservative Go adapter for deterministic comment suggestions."""
from __future__ import annotations
import re
from Src.models import CommentCandidate, CommentTarget, ParsedSource
_TYPE=re.compile(r"^\s*type\s+(?P<name>[A-Za-z_]\w*)\s+(?:struct|interface)\b")
_FUNC=re.compile(r"^\s*func\s+(?:\([^)]*\)\s*)?(?P<name>[A-Za-z_]\w*)\s*\(")
_FIELD=re.compile(r"^\s*(?P<name>[A-Za-z_]\w*)\s+[A-Za-z_]\w*(?:\s+`[^`]*`)?\s*$")
_WORDS=re.compile(r"(?<=[a-z0-9])(?=[A-Z])|_+")
def _words(name): return " ".join(x.lower() for x in _WORDS.split(name) if x)
def _comment(lines,line):
 i=line-2
 while i>=0 and not lines[i].strip(): i-=1
 return i>=0 and lines[i].lstrip().startswith("//")
class GoAdapter:
 language="go"
 def parse(self,source):
  lines=source.splitlines();out=[]
  for n,line in enumerate(lines,1):
   if _comment(lines,n): continue
   indent=line[:len(line)-len(line.lstrip())]
   if m:=_TYPE.match(line): out.append(CommentCandidate(CommentTarget.CLASS,m.group("name"),n,indent,f"// Groups behavior related to {_words(m.group('name'))}."))
   elif m:=_FUNC.match(line): out.append(CommentCandidate(CommentTarget.METHOD if line.lstrip().startswith('func (') else CommentTarget.FUNCTION,m.group("name"),n,indent,f"// Performs the {_words(m.group('name'))} operation."))
   elif (m:=_FIELD.match(line)) and m.group("name") not in {"package", "import"}: out.append(CommentCandidate(CommentTarget.FIELD,m.group("name"),n,indent,f"// Stores {_words(m.group('name'))} state."))
  return ParsedSource(self.language,tuple(out))