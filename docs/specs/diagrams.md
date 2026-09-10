# Diagram Generators

## Shared policy
Diagram generators should consume shared, language-independent analysis results whenever possible. Mermaid is the default rendering format.

## Planned diagrams
- Class diagram
- Object diagram
- Sequence diagram
- Package diagram
- Use-case diagram
- Communication diagram
- Activity diagram
- Component diagram
- Deployment diagram
- State-machine diagram
- Timing diagram
- Call graph

## Static vs dynamic bias
Prefer static analysis when relationships can be inferred reliably from source. Features that depend on runtime/UI behavior may require optional dynamic or LLM-assisted analysis, but that must be isolated from deterministic analysis.

## Class diagrams
Group primarily by caller relationships. Classes referenced by only a narrow set of callers stay near those callers. Highly shared classes (for example logging, evaluation, error, or screen-related classes) should receive dedicated callee-centered diagrams.

Visibility such as public/private should be configurable in rendering rather than hard-coded into analysis.

## Sequence diagrams
Reuse call relationships extracted for class/call-graph analysis. Generate views around meaningful caller-driven flows rather than duplicating parser logic.

## Object diagrams
Reuse class-structure data where possible and represent concrete object/instance relationships when they can be inferred.

## Package diagrams
Infer package/module relationships from imports, namespaces, folders, and dependency edges when supported by the language.

## Communication diagrams
Emphasize object/class communication relationships and reuse call/dependency graph data.

## Component / deployment diagrams
Use module/package/dependency information for components. Deployment information may require configuration or runtime metadata beyond source alone.

## Activity / state-machine / timing / use-case diagrams
These may require control-flow, event-flow, GUI/input, configuration, or runtime hints. Keep speculative inference clearly distinguishable from deterministic facts.
