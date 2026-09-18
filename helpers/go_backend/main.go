package main

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"go/ast"
	"go/format"
	"go/parser"
	"go/token"
	"go/types"
	"io"
	"os"
	"path/filepath"
	"strconv"
	"strings"
)

const (
	contractVersion = "1"
	backendID       = "go-stdlib-types-helper"
)

type request struct {
	ContractVersion string          `json:"contract_version"`
	RequestID       string          `json:"request_id"`
	Operation       string          `json:"operation"`
	Language        string          `json:"language"`
	Source          string          `json:"source"`
	Path            string          `json:"path,omitempty"`
	ProjectSources  []projectSource `json:"project_sources,omitempty"`
}

type projectSource struct {
	ImportPath string `json:"import_path"`
	Path       string `json:"path"`
	Source     string `json:"source"`
}

type response struct {
	ContractVersion string       `json:"contract_version"`
	RequestID       string       `json:"request_id"`
	OK              bool         `json:"ok"`
	IR              *moduleIR    `json:"ir,omitempty"`
	Error           *wireFailure `json:"error,omitempty"`
}

type wireFailure struct {
	Kind      string `json:"kind"`
	Message   string `json:"message"`
	BackendID string `json:"backend_id"`
	Retryable bool   `json:"retryable"`
}

type moduleIR struct {
	Language     string              `json:"language"`
	Entities     []codeEntity        `json:"entities,omitempty"`
	Diagnostics  []diagnosticIR      `json:"diagnostics,omitempty"`
	Dependencies []dependencyIR      `json:"dependencies,omitempty"`
	References   []symbolReferenceIR `json:"references,omitempty"`
	Imports      []string            `json:"imports,omitempty"`
}

type codeEntity struct {
	Kind           string   `json:"kind"`
	Name           string   `json:"name"`
	Line           int      `json:"line"`
	EndLine        int      `json:"end_line"`
	Indent         int      `json:"indent,omitempty"`
	Parent         *string  `json:"parent,omitempty"`
	Parameters     []string `json:"parameters,omitempty"`
	Calls          []string `json:"calls,omitempty"`
	CallSequence   []string `json:"call_sequence,omitempty"`
	Visibility     string   `json:"visibility"`
	Bases          []string `json:"bases,omitempty"`
	TypeParameters []string `json:"type_parameters,omitempty"`
	Interfaces     []string `json:"interfaces,omitempty"`
}

type diagnosticIR struct {
	Kind    string `json:"kind"`
	Message string `json:"message"`
	Line    *int   `json:"line,omitempty"`
}

type dependencyIR struct {
	Reference string  `json:"reference"`
	Kind      string  `json:"kind"`
	Line      *int    `json:"line,omitempty"`
	Resolved  bool    `json:"resolved"`
	Target    *string `json:"target,omitempty"`
}

type symbolReferenceIR struct {
	Kind     string  `json:"kind"`
	Name     string  `json:"name"`
	Line     int     `json:"line"`
	Owner    *string `json:"owner,omitempty"`
	Resolved bool    `json:"resolved"`
	Target   *string `json:"target,omitempty"`
}

type sourcePackage struct {
	importPath string
	files      []projectSource
}

type sourceImporter struct {
	packages map[string]sourcePackage
	cache    map[string]*types.Package
	loading  map[string]bool
	resolved map[string]bool
}

func newSourceImporter(sources []projectSource) *sourceImporter {
	packages := map[string]sourcePackage{}
	for _, src := range sources {
		pkg := packages[src.ImportPath]
		pkg.importPath = src.ImportPath
		pkg.files = append(pkg.files, src)
		packages[src.ImportPath] = pkg
	}
	return &sourceImporter{
		packages: packages,
		cache:    map[string]*types.Package{},
		loading:  map[string]bool{},
		resolved: map[string]bool{},
	}
}

func (i *sourceImporter) Import(path string) (*types.Package, error) {
	if pkg, ok := i.cache[path]; ok {
		i.resolved[path] = true
		return pkg, nil
	}
	srcPkg, ok := i.packages[path]
	if !ok {
		i.resolved[path] = false
		return nil, fmt.Errorf("unresolved import %q", path)
	}
	if i.loading[path] {
		return nil, fmt.Errorf("import cycle involving %q", path)
	}
	i.loading[path] = true
	defer delete(i.loading, path)

	fset := token.NewFileSet()
	files := make([]*ast.File, 0, len(srcPkg.files))
	for _, src := range srcPkg.files {
		name := src.Path
		if name == "" {
			name = path + ".go"
		}
		file, err := parser.ParseFile(fset, name, src.Source, parser.AllErrors)
		if err != nil && file == nil {
			i.resolved[path] = false
			return nil, fmt.Errorf("parse project package %q: %w", path, err)
		}
		if file != nil {
			files = append(files, file)
		}
	}
	if len(files) == 0 {
		i.resolved[path] = false
		return nil, fmt.Errorf("project package %q has no parseable files", path)
	}

	var typeErrors []error
	conf := types.Config{
		Importer: i,
		Error: func(err error) {
			typeErrors = append(typeErrors, err)
		},
	}
	pkg, err := conf.Check(path, fset, files, nil)
	if pkg == nil {
		i.resolved[path] = false
		if err != nil {
			return nil, err
		}
		return nil, errors.New("type checker returned no package")
	}
	i.cache[path] = pkg
	i.resolved[path] = true
	_ = typeErrors
	return pkg, nil
}

func main() {
	raw, err := io.ReadAll(os.Stdin)
	if err != nil {
		writeFailure("", "failure", err.Error(), true)
		return
	}
	var req request
	if err := json.Unmarshal(raw, &req); err != nil {
		writeFailure("", "protocol_error", "invalid request JSON", false)
		return
	}
	if req.ContractVersion != contractVersion {
		writeFailure(req.RequestID, "protocol_error", "unsupported contract_version", false)
		return
	}
	if req.Operation != "parse" {
		writeFailure(req.RequestID, "protocol_error", "unsupported operation", false)
		return
	}
	if req.Language != "go" {
		writeFailure(req.RequestID, "unsupported_language", "backend only supports go", false)
		return
	}
	ir, err := analyze(req)
	if err != nil {
		writeFailure(req.RequestID, "failure", err.Error(), false)
		return
	}
	writeResponse(response{
		ContractVersion: contractVersion,
		RequestID:       req.RequestID,
		OK:              true,
		IR:              ir,
	})
}

func analyze(req request) (*moduleIR, error) {
	fset := token.NewFileSet()
	path := req.Path
	if path == "" {
		path = "source.go"
	}
	file, parseErr := parser.ParseFile(fset, path, req.Source, parser.AllErrors|parser.ParseComments)
	if file == nil {
		if parseErr == nil {
			parseErr = errors.New("Go parser returned no syntax tree")
		}
		return nil, parseErr
	}

	out := &moduleIR{Language: "go"}
	if parseErr != nil {
		out.Diagnostics = append(out.Diagnostics, diagnosticIR{
			Kind:    "syntax_error",
			Message: parseErr.Error(),
		})
	}

	importer := newSourceImporter(req.ProjectSources)
	info := &types.Info{
		Defs:       map[*ast.Ident]types.Object{},
		Uses:       map[*ast.Ident]types.Object{},
		Selections: map[*ast.SelectorExpr]*types.Selection{},
		Types:      map[ast.Expr]types.TypeAndValue{},
	}
	var typeErrors []error
	conf := types.Config{
		Importer: importer,
		Error: func(err error) {
			typeErrors = append(typeErrors, err)
		},
	}
	pkgPath := file.Name.Name
	checkedPkg, _ := conf.Check(pkgPath, fset, []*ast.File{file}, info)
	for _, err := range typeErrors {
		line := lineFromError(err)
		out.Diagnostics = append(out.Diagnostics, diagnosticIR{
			Kind:    "semantic_error",
			Message: err.Error(),
			Line:    line,
		})
	}

	importAliases := map[string]string{}
	for _, spec := range file.Imports {
		importPath, err := strconv.Unquote(spec.Path.Value)
		if err != nil {
			importPath = strings.Trim(spec.Path.Value, "\"")
		}
		out.Imports = append(out.Imports, importPath)
		alias := filepath.Base(importPath)
		if spec.Name != nil {
			alias = spec.Name.Name
		}
		importAliases[alias] = importPath
		resolved := importer.resolved[importPath]
		var target *string
		if resolved {
			value := importPath
			target = &value
		}
		line := fset.Position(spec.Pos()).Line
		out.Dependencies = append(out.Dependencies, dependencyIR{
			Reference: importPath,
			Kind:      "import",
			Line:      &line,
			Resolved:  resolved,
			Target:    target,
		})
	}

	typeEntities := map[string]int{}
	interfaceObjects := map[string]*types.Interface{}
	for _, decl := range file.Decls {
		gen, ok := decl.(*ast.GenDecl)
		if !ok || gen.Tok != token.TYPE {
			continue
		}
		for _, item := range gen.Specs {
			spec, ok := item.(*ast.TypeSpec)
			if !ok {
				continue
			}
			entity := typeEntity(fset, spec)
			typeEntities[spec.Name.Name] = len(out.Entities)
			out.Entities = append(out.Entities, entity)
			if checkedPkg != nil {
				if obj, ok := checkedPkg.Scope().Lookup(spec.Name.Name).(*types.TypeName); ok {
					if named, ok := obj.Type().(*types.Named); ok {
						if iface, ok := named.Underlying().(*types.Interface); ok {
							interfaceObjects[spec.Name.Name] = iface.Complete()
						}
					}
				}
			}
			if iface, ok := spec.Type.(*ast.InterfaceType); ok {
				out.Entities = append(out.Entities, interfaceMethodEntities(fset, spec.Name.Name, iface)...)
			}
		}
	}

	if checkedPkg != nil && len(interfaceObjects) > 0 {
		for typeName, index := range typeEntities {
			obj, ok := checkedPkg.Scope().Lookup(typeName).(*types.TypeName)
			if !ok {
				continue
			}
			named, ok := obj.Type().(*types.Named)
			if !ok {
				continue
			}
			var implemented []string
			for ifaceName, iface := range interfaceObjects {
				if ifaceName == typeName {
					continue
				}
				if types.Implements(named, iface) || types.Implements(types.NewPointer(named), iface) {
					implemented = append(implemented, ifaceName)
				}
			}
			out.Entities[index].Interfaces = implemented
		}
	}

	for _, decl := range file.Decls {
		fn, ok := decl.(*ast.FuncDecl)
		if !ok {
			continue
		}
		entity, refs := functionEntity(fset, fn, info, importAliases)
		out.Entities = append(out.Entities, entity)
		out.References = append(out.References, refs...)
	}

	return out, nil
}

func typeEntity(fset *token.FileSet, spec *ast.TypeSpec) codeEntity {
	kind := "class"
	var bases []string
	switch value := spec.Type.(type) {
	case *ast.InterfaceType:
		kind = "interface"
	case *ast.StructType:
		for _, field := range value.Fields.List {
			if len(field.Names) == 0 {
				bases = append(bases, exprText(fset, field.Type))
			}
		}
	}
	return codeEntity{
		Kind:           kind,
		Name:           spec.Name.Name,
		Line:           fset.Position(spec.Pos()).Line,
		EndLine:        fset.Position(spec.End()).Line,
		Visibility:     visibility(spec.Name.Name),
		Bases:          bases,
		TypeParameters: fieldNames(spec.TypeParams),
	}
}

func interfaceMethodEntities(
	fset *token.FileSet,
	parent string,
	iface *ast.InterfaceType,
) []codeEntity {
	var result []codeEntity
	for _, field := range iface.Methods.List {
		fnType, ok := field.Type.(*ast.FuncType)
		if !ok || len(field.Names) == 0 {
			continue
		}
		for _, name := range field.Names {
			parentValue := parent
			result = append(result, codeEntity{
				Kind:       "method",
				Name:       name.Name,
				Line:       fset.Position(field.Pos()).Line,
				EndLine:    fset.Position(field.End()).Line,
				Parent:     &parentValue,
				Parameters: fieldNames(fnType.Params),
				Visibility: visibility(name.Name),
			})
		}
	}
	return result
}

func functionEntity(
	fset *token.FileSet,
	fn *ast.FuncDecl,
	info *types.Info,
	importAliases map[string]string,
) (codeEntity, []symbolReferenceIR) {
	var parent *string
	owner := fn.Name.Name
	if fn.Recv != nil && len(fn.Recv.List) > 0 {
		name := receiverName(fn.Recv.List[0].Type)
		if name != "" {
			parent = &name
			owner = name + "." + fn.Name.Name
		}
	}

	var sequence []string
	var refs []symbolReferenceIR
	if fn.Body != nil {
		ast.Inspect(fn.Body, func(node ast.Node) bool {
			if node == nil {
				return false
			}
			if lit, ok := node.(*ast.FuncLit); ok {
				_ = lit
				return false
			}
			call, ok := node.(*ast.CallExpr)
			if !ok {
				return true
			}
			name := callDisplayName(call.Fun, importAliases)
			if name == "" {
				return true
			}
			sequence = append(sequence, name)
			resolvedTarget := resolveCallTarget(call.Fun, info)
			ref := symbolReferenceIR{
				Kind:  "call",
				Name:  name,
				Line:  fset.Position(call.Pos()).Line,
				Owner: &owner,
			}
			if resolvedTarget != "" {
				ref.Resolved = true
				ref.Target = &resolvedTarget
			}
			refs = append(refs, ref)
			return true
		})
	}

	return codeEntity{
		Kind:         map[bool]string{true: "method", false: "function"}[parent != nil],
		Name:         fn.Name.Name,
		Line:         fset.Position(fn.Pos()).Line,
		EndLine:      fset.Position(fn.End()).Line,
		Parent:       parent,
		Parameters:   fieldNames(fn.Type.Params),
		Calls:        unique(sequence),
		CallSequence: sequence,
		Visibility:   visibility(fn.Name.Name),
		TypeParameters: fieldNames(fn.Type.TypeParams),
	}, refs
}

func fieldNames(fields *ast.FieldList) []string {
	if fields == nil {
		return nil
	}
	var result []string
	for _, field := range fields.List {
		for _, name := range field.Names {
			result = append(result, name.Name)
		}
	}
	return result
}

func receiverName(expr ast.Expr) string {
	switch value := expr.(type) {
	case *ast.Ident:
		return value.Name
	case *ast.IndexExpr:
		return receiverName(value.X)
	case *ast.IndexListExpr:
		return receiverName(value.X)
	case *ast.StarExpr:
		return receiverName(value.X)
	}
	return ""
}

func callDisplayName(expr ast.Expr, importAliases map[string]string) string {
	switch value := expr.(type) {
	case *ast.Ident:
		return value.Name
	case *ast.SelectorExpr:
		if ident, ok := value.X.(*ast.Ident); ok {
			if _, imported := importAliases[ident.Name]; imported {
				return ident.Name + "." + value.Sel.Name
			}
			return value.Sel.Name
		}
		return value.Sel.Name
	default:
		return exprText(token.NewFileSet(), expr)
	}
}

func resolveCallTarget(expr ast.Expr, info *types.Info) string {
	var obj types.Object
	switch value := expr.(type) {
	case *ast.Ident:
		obj = info.Uses[value]
	case *ast.SelectorExpr:
		if selection := info.Selections[value]; selection != nil {
			obj = selection.Obj()
		} else {
			obj = info.Uses[value.Sel]
		}
	}
	fn, ok := obj.(*types.Func)
	if !ok || fn == nil {
		return ""
	}
	pkgPath := ""
	if fn.Pkg() != nil {
		pkgPath = fn.Pkg().Path()
	}
	recvName := ""
	if sig, ok := fn.Type().(*types.Signature); ok && sig.Recv() != nil {
		recvName = namedTypeName(sig.Recv().Type())
	}
	parts := []string{}
	if pkgPath != "" {
		parts = append(parts, pkgPath)
	}
	if recvName != "" {
		parts = append(parts, recvName)
	}
	parts = append(parts, fn.Name())
	return strings.Join(parts, ".")
}

func namedTypeName(t types.Type) string {
	if ptr, ok := t.(*types.Pointer); ok {
		t = ptr.Elem()
	}
	if named, ok := t.(*types.Named); ok {
		return named.Obj().Name()
	}
	return ""
}

func exprText(fset *token.FileSet, expr ast.Expr) string {
	var buf bytes.Buffer
	if err := format.Node(&buf, fset, expr); err != nil {
		return ""
	}
	return buf.String()
}

func visibility(name string) string {
	if name != "" {
		first := rune(name[0])
		if first >= 'A' && first <= 'Z' {
			return "public"
		}
	}
	return "private"
}

func unique(values []string) []string {
	seen := map[string]bool{}
	result := make([]string, 0, len(values))
	for _, value := range values {
		if !seen[value] {
			seen[value] = true
			result = append(result, value)
		}
	}
	return result
}

func lineFromError(err error) *int {
	var typed types.Error
	if errors.As(err, &typed) && typed.Fset != nil {
		line := typed.Fset.Position(typed.Pos).Line
		if line > 0 {
			return &line
		}
	}
	return nil
}

func writeFailure(requestID, kind, message string, retryable bool) {
	writeResponse(response{
		ContractVersion: contractVersion,
		RequestID:       requestID,
		OK:              false,
		Error: &wireFailure{
			Kind:      kind,
			Message:   message,
			BackendID: backendID,
			Retryable: retryable,
		},
	})
}

func writeResponse(value response) {
	encoder := json.NewEncoder(os.Stdout)
	encoder.SetEscapeHTML(false)
	if err := encoder.Encode(value); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
