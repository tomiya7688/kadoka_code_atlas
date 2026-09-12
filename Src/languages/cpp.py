"""Conservative C++ adapter for deterministic comment suggestions."""
from __future__ import annotations
import re
from Src.models import CommentCandidate, CommentTarget, ParsedSource
_TYPE=re.compile(r"^\s*(?:(?:public|private|protected|abstract|final|static|sealed|non-sealed)\s+)*(?:class|struct|enum)\s+(?P<name>[A-Za-z_]\w*)")
_METHOD=re.compile(r"^\s*(?!(?:return|throw|new|if|for|while|switch)\b)(?:(?:public|private|protected|static|final|abstract|synchronized|native|default)\s+)*(?:[\w<>, ?\[\].]+\s+)*(?P<name>[A-Za-z_]\w*)\s*\([^;{}]*\)\s*(?:throws\b|\{|;|$)")
_FIELD=re.compile(r"^\s*(?:(?:public|private|protected|static|final|volatile|transient)\s+)*(?:[\w<>,: ?\[\].]+\s+)(?P<name>[A-Za-z_]\w*)\s*(?:=|;)")
_WORDS=re.compile(r"(?<=[a-z0-9])(?=[A-Z])|_+")
def _words(name): return " ".join(x.lower() for x in _WORDS.split(name) if x)
def _comment(lines,line):
 i=line-2
 while i>=0 and not lines[i].strip(): i-=1
 return i>=0 and lines[i].lstrip().startswith("//")
class CppAdapter:
 language="cpp"
 def parse(self,source):
  lines=source.splitlines(); out=[]
  for n,line in enumerate(lines,1):
   if _comment(lines,n): continue
   indent=line[:len(line)-len(line.lstrip())]
   if m:=_TYPE.match(line): out.append(CommentCandidate(CommentTarget.CLASS,m.group("name"),n,indent,f"// Groups behavior related to {_words(m.group('name'))}."))
   elif m:=_FIELD.match(line): out.append(CommentCandidate(CommentTarget.FIELD,m.group("name"),n,indent,f"// Stores {_words(m.group('name'))} state."))
   elif m:=_METHOD.match(line):
    name=m.group("name"); out.append(CommentCandidate(CommentTarget.METHOD,name,n,indent,f"// Performs the {_words(name)} operation."))
  return ParsedSource(self.language,tuple(out))
