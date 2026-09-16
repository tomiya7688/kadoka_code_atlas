"""Deployment topology extraction from source dependencies and deployment config."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import yaml

from Src.analyzers.component_dependencies import ComponentDependencyGraph
from Src.models.deployment import DeploymentConnection, DeploymentNode, DeploymentTopology

_CONFIDENCE = {"unknown": 0, "inferred": 1, "confirmed": 2}


def merge_topologies(*topologies: DeploymentTopology) -> DeploymentTopology:
    """Merge topology fragments, preferring higher-confidence node descriptions."""

    nodes: dict[str, DeploymentNode] = {}
    connections: dict[tuple[str, str, str], DeploymentConnection] = {}
    for topology in topologies:
        for node in topology.nodes:
            current = nodes.get(node.id)
            if current is None or _CONFIDENCE.get(node.confidence, 0) > _CONFIDENCE.get(
                current.confidence, 0
            ):
                nodes[node.id] = node
        for connection in topology.connections:
            key = (connection.source, connection.target, connection.relation)
            current = connections.get(key)
            if current is None or _CONFIDENCE.get(
                connection.confidence, 0
            ) > _CONFIDENCE.get(current.confidence, 0):
                connections[key] = connection
    return DeploymentTopology(
        tuple(sorted(nodes.values(), key=lambda item: item.id)),
        tuple(
            sorted(
                connections.values(),
                key=lambda item: (item.source, item.target, item.relation),
            )
        ),
    )


def topology_from_component_graph(graph: ComponentDependencyGraph) -> DeploymentTopology:
    """Convert project component dependencies into inferred deployment relations."""

    nodes: list[DeploymentNode] = []
    for name in sorted(graph.nodes):
        if name in graph.external_nodes:
            label = name.removeprefix("external:")
            nodes.append(
                DeploymentNode(
                    name,
                    label,
                    "external-dependency",
                    "inferred",
                    source="source imports",
                )
            )
        else:
            nodes.append(
                DeploymentNode(
                    f"component:{name}",
                    name,
                    "application-component",
                    "inferred",
                    source="source imports",
                )
            )

    def node_id(value: str) -> str:
        return value if value in graph.external_nodes else f"component:{value}"

    connections = tuple(
        DeploymentConnection(
            node_id(edge.caller),
            node_id(edge.callee),
            "imports",
            "inferred",
        )
        for edge in graph.edges
    )
    return DeploymentTopology(tuple(nodes), connections)


def parse_dockerfile(source: str, *, source_name: str = "Dockerfile") -> DeploymentTopology:
    """Extract container/base-image placement facts from a Dockerfile."""

    bases: list[str] = []
    for raw_line in source.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) >= 2 and parts[0].upper() == "FROM":
            index = 1
            while index < len(parts) and parts[index].startswith("--"):
                index += 1
            if index < len(parts):
                bases.append(parts[index])

    if not bases:
        return DeploymentTopology()

    runtime_id = f"docker:{source_name}"
    runtime = DeploymentNode(
        runtime_id,
        source_name,
        "container-image",
        "confirmed",
        environment="container",
        source=source_name,
        metadata=(("base_images", ", ".join(bases)),),
    )
    image_nodes = tuple(
        DeploymentNode(
            f"image:{base}",
            base,
            "external-image",
            "confirmed",
            environment="registry",
            source=source_name,
        )
        for base in dict.fromkeys(bases)
    )
    connections = tuple(
        DeploymentConnection(runtime_id, f"image:{base}", "FROM", "confirmed")
        for base in dict.fromkeys(bases)
    )
    return DeploymentTopology((runtime, *image_nodes), connections)


def _load_yaml_documents(source: str, source_name: str) -> list[Mapping[str, Any]]:
    try:
        values = list(yaml.safe_load_all(source))
    except yaml.YAMLError as error:
        raise ValueError(f"Invalid YAML in {source_name}: {error}") from error
    return [value for value in values if isinstance(value, Mapping)]


def _as_string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, Mapping):
        return [str(item) for item in value]
    if value is None:
        return []
    return [str(value)]


def _classify_service(name: str, image: str) -> str:
    value = f"{name} {image}".lower()
    kinds = (
        ("database", ("postgres", "mysql", "mariadb", "mongo", "sqlite")),
        ("cache", ("redis", "memcached")),
        ("message-queue", ("rabbitmq", "kafka", "nats", "activemq")),
    )
    for kind, markers in kinds:
        if any(marker in value for marker in markers):
            return kind
    return "service"


def parse_compose(source: str, *, source_name: str = "compose.yaml") -> DeploymentTopology:
    """Extract confirmed services and declared service dependencies from Compose YAML."""

    documents = _load_yaml_documents(source, source_name)
    if not documents:
        return DeploymentTopology()
    services = documents[0].get("services")
    if not isinstance(services, Mapping):
        return DeploymentTopology()

    nodes: list[DeploymentNode] = []
    connections: list[DeploymentConnection] = []
    known = {str(name) for name in services}
    for raw_name, raw_spec in services.items():
        name = str(raw_name)
        spec = raw_spec if isinstance(raw_spec, Mapping) else {}
        image = str(spec.get("image", ""))
        build = spec.get("build")
        ports = ", ".join(_as_string_list(spec.get("ports")))
        metadata = tuple(
            (key, value)
            for key, value in (
                ("image", image),
                ("build", str(build) if build is not None else ""),
                ("ports", ports),
            )
            if value
        )
        nodes.append(
            DeploymentNode(
                f"compose:{name}",
                name,
                _classify_service(name, image),
                "confirmed",
                environment="compose",
                source=source_name,
                metadata=metadata,
            )
        )
        for dependency in _as_string_list(spec.get("depends_on")):
            if dependency in known:
                connections.append(
                    DeploymentConnection(
                        f"compose:{name}",
                        f"compose:{dependency}",
                        "depends_on",
                        "confirmed",
                    )
                )
        for link in _as_string_list(spec.get("links")):
            dependency = link.split(":", 1)[0]
            if dependency in known:
                connections.append(
                    DeploymentConnection(
                        f"compose:{name}",
                        f"compose:{dependency}",
                        "links",
                        "confirmed",
                    )
                )
    return DeploymentTopology(tuple(nodes), tuple(connections))


def _metadata_name(document: Mapping[str, Any]) -> str:
    metadata = document.get("metadata")
    if isinstance(metadata, Mapping):
        return str(metadata.get("name", ""))
    return ""


def _selector_matches(selector: Mapping[str, Any], labels: Mapping[str, Any]) -> bool:
    return bool(selector) and all(str(labels.get(key)) == str(value) for key, value in selector.items())


def parse_kubernetes(source: str, *, source_name: str = "manifest.yaml") -> DeploymentTopology:
    """Extract workloads, Services and Ingress routing from Kubernetes manifests."""

    documents = _load_yaml_documents(source, source_name)
    nodes: list[DeploymentNode] = []
    connections: list[DeploymentConnection] = []
    workload_labels: dict[str, Mapping[str, Any]] = {}
    service_names: set[str] = set()

    workload_kinds = {"Deployment", "StatefulSet", "DaemonSet", "Pod", "Job", "CronJob"}
    for document in documents:
        kind = str(document.get("kind", ""))
        name = _metadata_name(document)
        if not name:
            continue
        if kind in workload_kinds:
            spec = document.get("spec")
            spec = spec if isinstance(spec, Mapping) else {}
            template = spec.get("template")
            template = template if isinstance(template, Mapping) else document
            template_meta = template.get("metadata")
            template_meta = template_meta if isinstance(template_meta, Mapping) else {}
            labels = template_meta.get("labels")
            labels = labels if isinstance(labels, Mapping) else {}
            pod_spec = template.get("spec")
            pod_spec = pod_spec if isinstance(pod_spec, Mapping) else spec
            containers = pod_spec.get("containers")
            images: list[str] = []
            if isinstance(containers, list):
                for container in containers:
                    if isinstance(container, Mapping) and container.get("image"):
                        images.append(str(container["image"]))
            node_id = f"k8s:{kind.lower()}:{name}"
            workload_labels[node_id] = labels
            metadata = tuple(
                (key, value)
                for key, value in (
                    ("kind", kind),
                    ("images", ", ".join(images)),
                    ("replicas", str(spec.get("replicas", ""))),
                )
                if value
            )
            nodes.append(
                DeploymentNode(
                    node_id,
                    name,
                    "workload",
                    "confirmed",
                    environment="kubernetes",
                    source=source_name,
                    metadata=metadata,
                )
            )
        elif kind == "Service":
            service_names.add(name)
            nodes.append(
                DeploymentNode(
                    f"k8s:service:{name}",
                    name,
                    "service-endpoint",
                    "confirmed",
                    environment="kubernetes",
                    source=source_name,
                )
            )
        elif kind == "Ingress":
            nodes.append(
                DeploymentNode(
                    f"k8s:ingress:{name}",
                    name,
                    "ingress",
                    "confirmed",
                    environment="kubernetes",
                    source=source_name,
                )
            )

    for document in documents:
        kind = str(document.get("kind", ""))
        name = _metadata_name(document)
        spec = document.get("spec")
        spec = spec if isinstance(spec, Mapping) else {}
        if kind == "Service" and name:
            selector = spec.get("selector")
            selector = selector if isinstance(selector, Mapping) else {}
            for workload_id, labels in workload_labels.items():
                if _selector_matches(selector, labels):
                    connections.append(
                        DeploymentConnection(
                            f"k8s:service:{name}",
                            workload_id,
                            "routes_to",
                            "confirmed",
                        )
                    )
        elif kind == "Ingress" and name:
            targets: set[str] = set()
            default_backend = spec.get("defaultBackend")
            if isinstance(default_backend, Mapping):
                service = default_backend.get("service")
                if isinstance(service, Mapping) and service.get("name"):
                    targets.add(str(service["name"]))
            rules = spec.get("rules")
            if isinstance(rules, list):
                for rule in rules:
                    if not isinstance(rule, Mapping):
                        continue
                    http = rule.get("http")
                    http = http if isinstance(http, Mapping) else {}
                    paths = http.get("paths")
                    if not isinstance(paths, list):
                        continue
                    for path in paths:
                        if not isinstance(path, Mapping):
                            continue
                        backend = path.get("backend")
                        backend = backend if isinstance(backend, Mapping) else {}
                        service = backend.get("service")
                        if isinstance(service, Mapping) and service.get("name"):
                            targets.add(str(service["name"]))
            for target in sorted(targets & service_names):
                connections.append(
                    DeploymentConnection(
                        f"k8s:ingress:{name}",
                        f"k8s:service:{target}",
                        "routes_to",
                        "confirmed",
                    )
                )

    return DeploymentTopology(tuple(nodes), tuple(connections))
