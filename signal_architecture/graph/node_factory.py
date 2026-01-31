"""
Organisational Graph - Node Factory

Creates typed graph nodes from signal extraction data and
submission inputs. Maps signal outputs to the appropriate
node types defined in schemas/organisational_graph.yaml.
"""

import logging
import uuid
from typing import Any, Dict, List, Optional

from .types import (
    Node,
    NodeType,
    ProxyTier,
    SignalAttachment,
)

logger = logging.getLogger("dsi.graph.node_factory")


class NodeFactory:
    """
    Creates graph nodes from signal data and submission inputs.

    Nodes are created from:
    1. Submission data (entity name, domain, TIV, etc.)
    2. Signal extraction outputs (discovered assets, partners, etc.)
    3. External data sources (regulatory filings, certifications, etc.)
    """

    def _make_id(self, prefix: str, name: str) -> str:
        """Generate a deterministic node ID."""
        safe = name.lower().replace(" ", "_").replace(".", "_")[:60]
        return f"{prefix}:{safe}"

    def create_organisation(
        self,
        entity_id: str,
        legal_name: str,
        primary_domain: Optional[str] = None,
        industry: Optional[str] = None,
        jurisdiction: Optional[str] = None,
    ) -> Node:
        """Create the root organisation node (the insured entity)."""
        attrs = {
            "entity_id": entity_id,
            "legal_name": legal_name,
        }
        if primary_domain:
            attrs["primary_domain"] = primary_domain
        if industry:
            attrs["industry_classification"] = industry
        if jurisdiction:
            attrs["incorporation_jurisdiction"] = jurisdiction

        return Node(
            id=self._make_id("org", entity_id),
            node_type=NodeType.ORGANISATION,
            attributes=attrs,
        )

    def create_asset(
        self,
        asset_name: str,
        subtype: str,
        status: str = "active",
        signals: Optional[List[SignalAttachment]] = None,
    ) -> Node:
        """Create an asset node (domain, IP, certificate, etc.)."""
        node = Node(
            id=self._make_id("asset", asset_name),
            node_type=NodeType.ASSET,
            subtype=subtype,
            attributes={
                "asset_id": asset_name,
                "asset_subtype": subtype,
                "status": status,
            },
        )
        if signals:
            node.signals = signals
        return node

    def create_partner(
        self,
        partner_name: str,
        subtype: str,
        tier: str = "unknown",
        signals: Optional[List[SignalAttachment]] = None,
    ) -> Node:
        """Create a partner node (vendor, customer, certifier, etc.)."""
        node = Node(
            id=self._make_id("partner", partner_name),
            node_type=NodeType.PARTNER,
            subtype=subtype,
            attributes={
                "partner_id": partner_name,
                "partner_subtype": subtype,
                "partner_name": partner_name,
                "tier": tier,
            },
        )
        if signals:
            node.signals = signals
        return node

    def create_person(
        self,
        name: str,
        role_type: str,
        role_title: Optional[str] = None,
        public_visibility: bool = False,
    ) -> Node:
        """Create a person node (leadership, security team, board)."""
        attrs = {
            "person_id": name,
            "role_type": role_type,
            "public_visibility": public_visibility,
        }
        if role_title:
            attrs["role_title"] = role_title

        return Node(
            id=self._make_id("person", name),
            node_type=NodeType.PERSON,
            subtype=role_type,
            attributes=attrs,
        )

    def create_process(
        self,
        process_name: str,
        process_type: str,
        observable_indicators: Optional[List[str]] = None,
    ) -> Node:
        """Create a process node (hiring, security ops, compliance, etc.)."""
        attrs = {
            "process_id": process_name,
            "process_type": process_type,
        }
        if observable_indicators:
            attrs["observable_indicators"] = observable_indicators

        return Node(
            id=self._make_id("process", process_name),
            node_type=NodeType.PROCESS,
            subtype=process_type,
            attributes=attrs,
        )

    def create_jurisdiction(
        self,
        name: str,
        jurisdiction_type: str,
        complexity_weight: float = 1.0,
    ) -> Node:
        """Create a jurisdiction node (geographic or regulatory)."""
        return Node(
            id=self._make_id("jurisdiction", name),
            node_type=NodeType.JURISDICTION,
            subtype=jurisdiction_type,
            attributes={
                "jurisdiction_id": name,
                "jurisdiction_type": jurisdiction_type,
                "name": name,
                "complexity_weight": complexity_weight,
            },
        )

    def create_nodes_from_submission(
        self, submission: Dict[str, Any]
    ) -> List[Node]:
        """
        Create initial graph nodes from submission data.

        Extracts the root organisation and any directly stated
        assets, jurisdictions, or partners from the submission.
        """
        nodes = []

        # Root organisation (always present)
        entity_id = submission.get("entity_id", submission.get("company_name", "unknown"))
        org = self.create_organisation(
            entity_id=entity_id,
            legal_name=submission.get("company_name", entity_id),
            primary_domain=submission.get("domain", submission.get("domain_hint")),
            industry=submission.get("industry"),
            jurisdiction=submission.get("country"),
        )
        nodes.append(org)

        # Primary domain as asset
        domain = submission.get("domain", submission.get("domain_hint"))
        if domain:
            nodes.append(self.create_asset(domain, "domain"))

        # Country as jurisdiction
        country = submission.get("country")
        if country:
            nodes.append(self.create_jurisdiction(country, "geographic"))

        logger.debug(
            f"Created {len(nodes)} nodes from submission for '{entity_id}'"
        )
        return nodes

    def create_nodes_from_signals(
        self,
        signal_outputs: Dict[str, Any],
        org_node_id: str,
    ) -> List[Node]:
        """
        Create additional graph nodes from signal extraction outputs.

        Signal outputs may reveal:
        - Additional domains/assets (subdomain discovery, certificate transparency)
        - Partners (vendor relationships, certification bodies)
        - Key personnel (leadership team, board members)
        - Business processes (hiring activity, security operations)
        - Jurisdictions (operational presence)
        """
        nodes = []

        # Extract assets from technical signals
        for key, value in signal_outputs.items():
            if not isinstance(value, dict):
                continue

            raw = value.get("raw_data", {})
            if not isinstance(raw, dict):
                continue

            # Subdomain/asset discovery
            subdomains = raw.get("subdomains", [])
            for sub in subdomains[:20]:  # Cap to prevent graph explosion
                if isinstance(sub, str):
                    nodes.append(self.create_asset(sub, "domain"))

            # Certificate discovery
            certs = raw.get("certificates", [])
            for cert in certs[:10]:
                if isinstance(cert, dict):
                    name = cert.get("subject", cert.get("id", ""))
                    if name:
                        nodes.append(self.create_asset(name, "certificate"))

            # Partner/vendor discovery
            vendors = raw.get("vendors", raw.get("partners", []))
            for v in vendors[:15]:
                if isinstance(v, str):
                    nodes.append(self.create_partner(v, "vendor"))
                elif isinstance(v, dict):
                    name = v.get("name", "")
                    if name:
                        subtype = v.get("type", "vendor")
                        nodes.append(self.create_partner(name, subtype))

            # Certification bodies
            certifiers = raw.get("certifications", raw.get("certification_bodies", []))
            for c in certifiers[:10]:
                if isinstance(c, str):
                    nodes.append(self.create_partner(c, "certification_body"))
                elif isinstance(c, dict):
                    name = c.get("body", c.get("name", ""))
                    if name:
                        nodes.append(self.create_partner(
                            name, "certification_body", tier="tier_1"
                        ))

            # Key personnel
            leadership = raw.get("leadership", raw.get("executives", []))
            for person in leadership[:10]:
                if isinstance(person, str):
                    nodes.append(self.create_person(person, "leadership"))
                elif isinstance(person, dict):
                    name = person.get("name", "")
                    if name:
                        role = person.get("role_type", "leadership")
                        title = person.get("title")
                        nodes.append(self.create_person(name, role, title))

            # Jurisdictions from operational presence
            locations = raw.get("locations", raw.get("jurisdictions", []))
            for loc in locations[:10]:
                if isinstance(loc, str):
                    nodes.append(self.create_jurisdiction(loc, "geographic"))

        logger.debug(
            f"Created {len(nodes)} additional nodes from signal outputs"
        )
        return nodes
