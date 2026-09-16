from Src.analyzers.deployment import (
    merge_topologies,
    parse_compose,
    parse_dockerfile,
    parse_kubernetes,
)
from Src.generators.deployment_diagram import build_deployment_diagram_bundle
from Src.renderers.mermaid_deployment_diagram import render_deployment_diagram


def test_compose_extracts_services_and_confirmed_dependencies() -> None:
    topology = parse_compose(
        """
services:
  web:
    build: .
    ports: ["8000:8000"]
    depends_on:
      - db
      - cache
  db:
    image: postgres:17
  cache:
    image: redis:8
"""
    )
    nodes = {node.id: node for node in topology.nodes}
    assert nodes["compose:web"].kind == "service"
    assert nodes["compose:db"].kind == "database"
    assert nodes["compose:cache"].kind == "cache"
    assert all(node.confidence == "confirmed" for node in topology.nodes)
    assert {(edge.source, edge.target) for edge in topology.connections} == {
        ("compose:web", "compose:db"),
        ("compose:web", "compose:cache"),
    }


def test_dockerfile_extracts_runtime_and_base_images() -> None:
    topology = parse_dockerfile(
        "FROM python:3.13-slim AS build\nFROM gcr.io/distroless/python3\n",
        source_name="Dockerfile",
    )
    ids = {node.id for node in topology.nodes}
    assert "docker:Dockerfile" in ids
    assert "image:python:3.13-slim" in ids
    assert "image:gcr.io/distroless/python3" in ids
    assert len(topology.connections) == 2


def test_kubernetes_extracts_ingress_service_and_workload_routing() -> None:
    topology = parse_kubernetes(
        """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
spec:
  replicas: 2
  template:
    metadata:
      labels:
        app: api
    spec:
      containers:
        - name: api
          image: example/api:1
---
apiVersion: v1
kind: Service
metadata:
  name: api-service
spec:
  selector:
    app: api
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: public
spec:
  rules:
    - http:
        paths:
          - path: /
            backend:
              service:
                name: api-service
                port:
                  number: 80
"""
    )
    edges = {(edge.source, edge.target, edge.relation) for edge in topology.connections}
    assert (
        "k8s:service:api-service",
        "k8s:deployment:api",
        "routes_to",
    ) in edges
    assert (
        "k8s:ingress:public",
        "k8s:service:api-service",
        "routes_to",
    ) in edges


def test_deployment_bundle_preserves_confidence_in_mermaid() -> None:
    topology = merge_topologies(
        parse_compose(
            """
services:
  web:
    depends_on: [db]
  db:
    image: postgres:17
"""
        ),
        parse_dockerfile("FROM python:3.13-slim\n"),
    )
    bundle = build_deployment_diagram_bundle(topology)
    assert bundle.diagrams
    content = "\n".join(render_deployment_diagram(diagram) for diagram in bundle.diagrams)
    assert "flowchart LR" in content
    assert "depends_on [confirmed]" in content
    assert bundle.statistics["confirmed_node_count"] >= 3
