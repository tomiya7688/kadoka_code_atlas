from Src.generators import CommentGenerator
from Src.models import CommentTarget

def test_go_candidates():
    source="""package reports
type Report struct { Name string }
type Store struct {
    CachedName string
}
func (s *Store) LoadReport(name string) Report { return Report{Name: name} }
func BuildReport() Report { return Report{} }
"""
    got=CommentGenerator().candidates(source,"go")
    assert [(x.target,x.name) for x in got]==[(CommentTarget.CLASS,"Report"),(CommentTarget.CLASS,"Store"),(CommentTarget.FIELD,"CachedName"),(CommentTarget.METHOD,"LoadReport"),(CommentTarget.FUNCTION,"BuildReport")]

def test_go_idempotent():
    g=CommentGenerator();s="type Ready struct {}\n";once=g.generate(s,"go");assert g.generate(once,"go")==once