"""
Organisational Graph - Edge Inferencer

Infers edges (relationships) between nodes based on signal data,
submission context, and structural rules from the schema.

Edge types: dependency, trust, data_flow, ownership, operates_in, employment
"""

import logging
import uuid
from typing import Any, Dict, List, Optional

from .types import (
    Edge,
    EdgeType,
    Graph,
    Node,
    NodeType,
)

logger = logging.getLogger("dsi.graph.edge_inferencer")


class EdgeInferencer:
    """
    Infers edges between graph nodes based on relationships
    discoverable from signal data and submission context.

    Inference rules:
    1. Organisation → Asset (ownership): All discovered assets
    2. Organisation → Partner (trust): Certification, vendor relationships
    3. Organisation → Person (employment): Key personnel
    4. Organisation → Process (dependency): Observable processes
    5. Organisation → Jurisdiction (operates_in): Operational presence
    6. Asset → Partner (dependency): Vendor-hosted assets
    7. Process → Asset (dependency): Process dependencies on assets
    """

    def _make_edge_id(self, edge_type: str, source_id: str, target_id: str) -> str:
        safe_src = source_id.split(":")[-1][:30]
        safe_tgt = target_id.split(":")[-1][:30]
        return f"edge:{edge_type}:{safe_src}:{safe_tgt}"

    def infer_edges(self, graph: Graph) -> List[Edge]:
        """
        Infer all edges for the graph based on node types and attributes.

        Returns list of new edges to add to the graph.
        """
        edges = []

        org = graph.get_root_organisation()
        if org is None:
            logger.warning("No root organisation node found")
            return edges

        # Organisation → Asset (ownership)
        edges.extend(self._infer_ownership_edges(org, graph))

        # Organisation → Partner (trust)
        edges.extend(self._infer_trust_edges(org, graph))

        # Organisation → Person (employment)
        edges.extend(self._infer_employment_edges(org, graph))

        # Organisation → Process (dependency)
        edges.extend(self._infer_process_dependency_edges(org, graph))

        # Organisation → Jurisdiction (operates_in)
        edges.extend(self._infer_operates_in_edges(org, graph))

        # Asset → Partner (dependency) for vendor-hosted assets
        edges.extend(self._infer_asset_dependencies(graph))

        # Process → Asset (dependency)
        edges.extend(self._infer_process_asset_dependencies(graph))

        # Data flow edges from signal context
        edges.extend(self._infer_data_flow_edges(graph))

        logger.debug(f"Inferred {len(edges)} edges for entity '{org.id}'")
        return edges

    def _infer_ownership_edges(self, org: Node, graph: Graph) -> List[Edge]:
        """Organisation owns all discovered assets."""
        edges = []
        for asset in graph.get_nodes_by_type(NodeType.ASSET):
            edge = Edge(
                id=self._make_edge_id("ownership", org.id, asset.id),
                edge_type=EdgeType.OWNERSHIP,
                source_id=org.id,
                target_id=asset.id,
                properties={
                    "ownership_percentage": 100.0,
                    "control_type": "full",
                },
            )
            edges.append(edge)
        return edges

    def _infer_trust_edges(self, org: Node, graph: Graph) -> List[Edge]:
        """
        Organisation has trust relationships with partners.

        Trust type depends on partner subtype:
        - certification_body → certification trust
        - vendor/technology_partner → partnership trust
        - customer → customer trust
        - financial_institution → endorsement trust
        """
        trust_type_map = {
            "certification_body": "certification",
            "vendor": "partnership",
            "technology_partner": "partnership",
            "customer": "customer",
            "financial_institution": "endorsement",
        }

        edges = []
        for partner in graph.get_nodes_by_type(NodeType.PARTNER):
            subtype = partner.attributes.get("partner_subtype", "vendor")
            trust_type = trust_type_map.get(subtype, "partnership")

            # Higher weight for certification trust (strong authority signal)
            weight = 0.85
            if trust_type == "certification":
                weight = 0.95
            elif trust_type == "endorsement":
                weight = 0.90

            edge = Edge(
                id=self._make_edge_id("trust", org.id, partner.id),
                edge_type=EdgeType.TRUST,
                source_id=org.id,
                target_id=partner.id,
                weight=weight,
                properties={
                    "trust_type": trust_type,
                    "public_evidence": True,
                },
            )
            edges.append(edge)
        return edges

    def _infer_employment_edges(self, org: Node, graph: Graph) -> List[Edge]:
        """Organisation employs all discovered persons."""
        edges = []
        for person in graph.get_nodes_by_type(NodeType.PERSON):
            emp_type = "employee"
            role_type = person.attributes.get("role_type", "")
            if role_type == "board_member":
                emp_type = "board"

            edge = Edge(
                id=self._make_edge_id("employment", org.id, person.id),
                edge_type=EdgeType.EMPLOYMENT,
                source_id=org.id,
                target_id=person.id,
                properties={
                    "employment_type": emp_type,
                },
            )
            edges.append(edge)
        return edges

    def _infer_process_dependency_edges(
        self, org: Node, graph: Graph
    ) -> List[Edge]:
        """Organisation depends on all observable processes."""
        edges = []
        for process in graph.get_nodes_by_type(NodeType.PROCESS):
            # Criticality based on process type
            process_type = process.attributes.get("process_type", "")
            criticality = "medium"
            if process_type in ("security_operations", "incident_response"):
                criticality = "critical"
            elif process_type == "compliance":
                criticality = "high"

            edge = Edge(
                id=self._make_edge_id("dependency", org.id, process.id),
                edge_type=EdgeType.DEPENDENCY,
                source_id=org.id,
                target_id=process.id,
                properties={
                    "criticality": criticality,
                    "redundancy": False,
                },
            )
            edges.append(edge)
        return edges

    def _infer_operates_in_edges(self, org: Node, graph: Graph) -> List[Edge]:
        """Organisation operates in discovered jurisdictions."""
        edges = []
        for jurisdiction in graph.get_nodes_by_type(NodeType.JURISDICTION):
            # Determine presence type from context
            inc_jurisdiction = org.attributes.get("incorporation_jurisdiction", "")
            jur_name = jurisdiction.attributes.get("name", "")

            presence_type = "branch"
            if inc_jurisdiction and inc_jurisdiction.lower() == jur_name.lower():
                presence_type = "headquarters"

            edge = Edge(
                id=self._make_edge_id("operates_in", org.id, jurisdiction.id),
                edge_type=EdgeType.OPERATES_IN,
                source_id=org.id,
                target_id=jurisdiction.id,
                properties={
                    "presence_type": presence_type,
                },
            )
            edges.append(edge)
        return edges

    def _infer_asset_dependencies(self, graph: Graph) -> List[Edge]:
        """
        Infer dependency edges from assets to vendor partners.

        If an asset is cloud-hosted (cloud_resource subtype), it depends
        on a technology partner.
        """
        edges = []
        tech_partners = [
            p for p in graph.get_nodes_by_type(NodeType.PARTNER)
            if p.attributes.get("partner_subtype") in ("vendor", "technology_partner")
        ]

        for asset in graph.get_nodes_by_type(NodeType.ASSET):
            subtype = asset.attributes.get("asset_subtype", "")
            if subtype in ("cloud_resource", "application"):
                # Link to first matching technology partner
                for partner in tech_partners:
                    edge = Edge(
                        id=self._make_edge_id("dependency", asset.id, partner.id),
                        edge_type=EdgeType.DEPENDENCY,
                        source_id=asset.id,
                        target_id=partner.id,
                        properties={
                            "criticality": "high",
                            "redundancy": False,
                        },
                    )
                    edges.append(edge)
                    break  # One dependency per asset for now
        return edges

    def _infer_process_asset_dependencies(self, graph: Graph) -> List[Edge]:
        """Processes depend on assets (e.g., security_operations depends on domains)."""
        edges = []
        assets = graph.get_nodes_by_type(NodeType.ASSET)
        if not assets:
            return edges

        for process in graph.get_nodes_by_type(NodeType.PROCESS):
            # Security operations depend on technical assets
            process_type = process.attributes.get("process_type", "")
            if process_type in ("security_operations", "incident_response"):
                for asset in assets[:5]:  # Link to first few assets
                    if asset.attributes.get("asset_subtype") in (
                        "domain", "application", "cloud_resource"
                    ):
                        edge = Edge(
                            id=self._make_edge_id("dependency", process.id, asset.id),
                            edge_type=EdgeType.DEPENDENCY,
                            source_id=process.id,
                            target_id=asset.id,
                            properties={
                                "criticality": "medium",
                                "redundancy": True,
                            },
                        )
                        edges.append(edge)
        return edges

    def _infer_data_flow_edges(self, graph: Graph) -> List[Edge]:
        """
        Infer data flow edges between assets and jurisdictions.

        Data flows to jurisdictions where the organisation operates.
        """
        edges = []
        jurisdictions = graph.get_nodes_by_type(NodeType.JURISDICTION)
        if not jurisdictions:
            return edges

        data_assets = [
            a for a in graph.get_nodes_by_type(NodeType.ASSET)
            if a.attributes.get("asset_subtype") in ("data_store", "application")
        ]

        for asset in data_assets:
            for jurisdiction in jurisdictions:
                edge = Edge(
                    id=self._make_edge_id("data_flow", asset.id, jurisdiction.id),
                    edge_type=EdgeType.DATA_FLOW,
                    source_id=asset.id,
                    target_id=jurisdiction.id,
                    properties={
                        "data_classification": "internal",
                        "volume": "medium",
                    },
                )
                edges.append(edge)
        return edges
