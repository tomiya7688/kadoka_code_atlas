from Src.generators import CommentGenerator
from Src.models import CommentTarget

def test_cpp_candidates():
    source = """class ReportStore {
public:
    std::string cached_name;
    Report load_report(std::string name) { return Report(name); }
};
"""
    got = CommentGenerator().candidates(source, "cpp")
    assert [(x.target, x.name) for x in got] == [(CommentTarget.CLASS, "ReportStore"), (CommentTarget.FIELD, "cached_name"), (CommentTarget.METHOD, "load_report")]

def test_cpp_idempotent():
    g=CommentGenerator(); s="class Ready { public: bool is_ready(); };\n"; once=g.generate(s,"cxx"); assert g.generate(once,"cpp")==once