# Call graph generator

The call graph pipeline reuses language adapters and `ModuleIR`.

```text
language adapter -> ModuleIR -> CallGraph -> generator -> Mermaid renderer
```

Initial Python support provides direct caller/callee edges, fan-in/fan-out metrics,
rooted depth-limited traversal, high fan-in detection, cycle detection, and Mermaid
flowchart output. Additional language adapters can feed the same `ModuleIR` without
changing the graph analysis or renderer.
