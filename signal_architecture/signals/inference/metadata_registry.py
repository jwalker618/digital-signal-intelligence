"""
DSI Signal Metadata Registry

Provides a centralized registry of metadata for all inference signals across
all coverage domains. Each signal's metadata describes its identity, category,
proxy tier, TTL, required extractors, output characteristics, and coverage
applicability.

This registry enables:
    - Signal discovery and introspection at runtime
    - Validation that YAML configs reference known signals
    - Cross-coverage signal reuse identification
    - Consistent documentation of signal characteristics

Usage:
    from signals.inference.metadata_registry import SIGNAL_METADATA_REGISTRY

    # Lookup by signal ID
    meta = SIGNAL_METADATA_REGISTRY.get("tls_configuration")

    # Lookup by category
    security_signals = SIGNAL_METADATA_REGISTRY.get_by_category("security")

    # Lookup by coverage
    cyber_signals = SIGNAL_METADATA_REGISTRY.get_by_coverage("cyber")

    # Validate a config dict
    issues = SIGNAL_METADATA_REGISTRY.validate_config(parsed_config)
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple


# ---------------------------------------------------------------------------
# Proxy tier constants
# ---------------------------------------------------------------------------
DIRECT_OBSERVABLE = "DIRECT_OBSERVABLE"
INFERRED_PROXY = "INFERRED_PROXY"
COHORT_INFERENCE = "COHORT_INFERENCE"

VALID_PROXY_TIERS = {DIRECT_OBSERVABLE, INFERRED_PROXY, COHORT_INFERENCE}

# ---------------------------------------------------------------------------
# Output type constants
# ---------------------------------------------------------------------------
OUTPUT_SCORE = "score"
OUTPUT_CATEGORY = "category"
OUTPUT_BOOLEAN = "boolean"
OUTPUT_NUMERIC = "numeric"

VALID_OUTPUT_TYPES = {OUTPUT_SCORE, OUTPUT_CATEGORY, OUTPUT_BOOLEAN, OUTPUT_NUMERIC}

# ---------------------------------------------------------------------------
# Coverage domain constants
# ---------------------------------------------------------------------------
COVERAGE_AEROSPACE = "aerospace"
COVERAGE_CYBER = "cyber"
COVERAGE_FI = "fi"
COVERAGE_ENERGY = "energy"
COVERAGE_DO = "do"
COVERAGE_MARINE = "marine"
COVERAGE_PI = "pi"
COVERAGE_PROPERTY = "property"
COVERAGE_CASUALTY = "casualty"
COVERAGE_FPR = "fpr"

ALL_COVERAGES = [
    COVERAGE_AEROSPACE,
    COVERAGE_CYBER,
    COVERAGE_FI,
    COVERAGE_ENERGY,
    COVERAGE_DO,
    COVERAGE_MARINE,
    COVERAGE_PI,
    COVERAGE_PROPERTY,
    COVERAGE_CASUALTY,
    COVERAGE_FPR,
]


# ---------------------------------------------------------------------------
# SignalMetadata dataclass
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class SignalMetadata:
    """
    Immutable metadata descriptor for a single DSI inference signal.

    Attributes:
        signal_id: Unique identifier matching the YAML config ``id`` field
            and the ``inference_utility_function`` name (without the
            ``_basefunction`` suffix where applicable).
        signal_name: Human-readable display name.
        category: Logical category grouping, e.g. ``"security"``,
            ``"governance"``, ``"financial"``, ``"safety"``,
            ``"environmental"``, ``"operational"``, ``"sanctions"``,
            ``"regulatory"``, ``"corporate_footprint"``,
            ``"structured_data"``, ``"network_authority"``.
        proxy_tier: One of ``DIRECT_OBSERVABLE``, ``INFERRED_PROXY``,
            or ``COHORT_INFERENCE``.
        ttl_seconds: Default time-to-live for cached extraction results.
        required_extractors: Ordered list of extractor class names
            that feed this signal's inference function.
        output_type: The kind of value produced -- ``"score"`` (0-100),
            ``"category"`` (discrete string), ``"boolean"``, or
            ``"numeric"`` (unbounded number).
        value_range: For score / numeric outputs, the inclusive
            ``(min, max)`` bounds.  ``None`` for category / boolean.
        coverage_applicability: Coverage domains where this signal
            is referenced (e.g. ``["cyber", "fi"]``).
        description: Free-text description of what the signal measures.
    """

    signal_id: str
    signal_name: str
    category: str
    proxy_tier: str
    ttl_seconds: int
    required_extractors: List[str]
    output_type: str
    value_range: Optional[Tuple[float, float]]
    coverage_applicability: List[str]
    description: str

    def __post_init__(self):
        if self.proxy_tier not in VALID_PROXY_TIERS:
            raise ValueError(
                f"Invalid proxy_tier '{self.proxy_tier}' for signal "
                f"'{self.signal_id}'. Must be one of {VALID_PROXY_TIERS}"
            )
        if self.output_type not in VALID_OUTPUT_TYPES:
            raise ValueError(
                f"Invalid output_type '{self.output_type}' for signal "
                f"'{self.signal_id}'. Must be one of {VALID_OUTPUT_TYPES}"
            )


# ---------------------------------------------------------------------------
# Validation result
# ---------------------------------------------------------------------------
@dataclass
class ValidationResult:
    """
    Result of validating a coverage config against the metadata registry.

    Attributes:
        is_valid: ``True`` when no errors were found.
        missing_metadata: Signal IDs referenced in config but absent
            from the registry.
        invalid_references: Signal IDs in the registry that claim
            applicability to the coverage but are missing from the config.
        warnings: Non-fatal observations (e.g. deprecated signals).
    """

    is_valid: bool = True
    missing_metadata: List[str] = field(default_factory=list)
    invalid_references: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# MetadataRegistry class
# ---------------------------------------------------------------------------
class MetadataRegistry:
    """
    Central store for signal metadata across all DSI coverage domains.

    Provides registration, lookup, and config-validation capabilities.
    """

    def __init__(self) -> None:
        self._by_id: Dict[str, SignalMetadata] = {}
        self._by_category: Dict[str, List[SignalMetadata]] = {}
        self._by_coverage: Dict[str, List[SignalMetadata]] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, metadata: SignalMetadata) -> None:
        """
        Register a ``SignalMetadata`` entry.

        Args:
            metadata: The metadata to register.

        Raises:
            ValueError: If a signal with the same ``signal_id`` is
                already registered.
        """
        if metadata.signal_id in self._by_id:
            raise ValueError(
                f"Signal '{metadata.signal_id}' is already registered."
            )

        self._by_id[metadata.signal_id] = metadata

        # Index by category
        self._by_category.setdefault(metadata.category, []).append(metadata)

        # Index by each applicable coverage
        for cov in metadata.coverage_applicability:
            self._by_coverage.setdefault(cov, []).append(metadata)

    def register_many(self, entries: List[SignalMetadata]) -> None:
        """Convenience: register a list of metadata entries."""
        for entry in entries:
            self.register(entry)

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def get(self, signal_id: str) -> Optional[SignalMetadata]:
        """
        Look up metadata by signal ID.

        Args:
            signal_id: The unique signal identifier.

        Returns:
            The ``SignalMetadata`` if found, else ``None``.
        """
        return self._by_id.get(signal_id)

    def get_by_category(self, category: str) -> List[SignalMetadata]:
        """
        Return all signals in the given category.

        Args:
            category: Category name (e.g. ``"security"``).

        Returns:
            List of matching ``SignalMetadata`` (may be empty).
        """
        return list(self._by_category.get(category, []))

    def get_by_coverage(self, coverage: str) -> List[SignalMetadata]:
        """
        Return all signals applicable to the given coverage domain.

        Args:
            coverage: Coverage identifier (e.g. ``"cyber"``).

        Returns:
            List of matching ``SignalMetadata`` (may be empty).
        """
        return list(self._by_coverage.get(coverage, []))

    def get_by_proxy_tier(self, proxy_tier: str) -> List[SignalMetadata]:
        """
        Return all signals with the given proxy tier.

        Args:
            proxy_tier: One of the ``VALID_PROXY_TIERS`` constants.

        Returns:
            List of matching ``SignalMetadata``.
        """
        return [m for m in self._by_id.values() if m.proxy_tier == proxy_tier]

    def list_signal_ids(self) -> List[str]:
        """Return a sorted list of all registered signal IDs."""
        return sorted(self._by_id.keys())

    def list_categories(self) -> List[str]:
        """Return a sorted list of all categories."""
        return sorted(self._by_category.keys())

    def list_coverages(self) -> List[str]:
        """Return a sorted list of coverages that have registered signals."""
        return sorted(self._by_coverage.keys())

    @property
    def size(self) -> int:
        """Total number of registered signals."""
        return len(self._by_id)

    def contains(self, signal_id: str) -> bool:
        """Check whether a signal ID is registered."""
        return signal_id in self._by_id

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate_config(
        self, config: Dict[str, Any], coverage: Optional[str] = None
    ) -> ValidationResult:
        """
        Validate a parsed coverage configuration against this registry.

        Checks performed:
            1. Every ``inference_utility_function`` referenced in the
               config's ``signal_features``, ``categorical_groups``, and
               ``signal_registry`` has a corresponding metadata entry.
            2. If ``coverage`` is supplied, every registry entry that
               claims applicability to that coverage is present in the
               config.

        The method walks through multiple config shapes:
            - Legacy layout: ``signal_features`` dict of groups, each
              containing lists of signal dicts with
              ``inference_utility_function``.
            - Legacy categorical: ``categorical_groups`` list with
              ``inference_utility_function``.
            - New layout: ``signal_registry`` list with ``id`` and
              ``inference_utility_function``.

        Args:
            config: The inner configuration dict (e.g. the value under
                ``cyber_general`` or ``aerospace_general``).
            coverage: Optional coverage domain name for reverse-check.

        Returns:
            ``ValidationResult`` with details of any issues.
        """
        result = ValidationResult()
        config_signal_ids: Set[str] = set()

        # --- Extract signal IDs from signal_features (legacy layout) ---
        signal_features = config.get("signal_features", {})
        if isinstance(signal_features, dict):
            for group_signals in signal_features.values():
                if isinstance(group_signals, list):
                    for sig in group_signals:
                        if isinstance(sig, dict):
                            sid = sig.get("id")
                            if sid:
                                config_signal_ids.add(sid)
                                func_name = sig.get(
                                    "inference_utility_function", ""
                                )
                                if func_name and not self._has_signal_for_function(
                                    func_name
                                ):
                                    result.missing_metadata.append(sid)

        # --- Extract signal IDs from categorical_groups ---
        cat_groups = config.get("categorical_groups", [])
        if isinstance(cat_groups, list):
            for cg in cat_groups:
                if isinstance(cg, dict):
                    sid = cg.get("id")
                    if sid:
                        config_signal_ids.add(sid)
                        func_name = cg.get("inference_utility_function", "")
                        if func_name and not self._has_signal_for_function(
                            func_name
                        ):
                            result.missing_metadata.append(sid)

        # --- Extract signal IDs from signal_registry (new layout) ---
        signal_registry = config.get("signal_registry", [])
        if isinstance(signal_registry, list):
            for entry in signal_registry:
                if isinstance(entry, dict):
                    sid = entry.get("id")
                    if sid:
                        config_signal_ids.add(sid)
                        if not self.contains(sid):
                            func_name = entry.get(
                                "inference_utility_function", ""
                            )
                            if func_name and not self._has_signal_for_function(
                                func_name
                            ):
                                result.missing_metadata.append(sid)

        # --- Reverse check: registry entries claiming this coverage ---
        if coverage:
            registry_signals = self.get_by_coverage(coverage)
            for meta in registry_signals:
                if meta.signal_id not in config_signal_ids:
                    result.invalid_references.append(meta.signal_id)

        # --- Determine overall validity ---
        if result.missing_metadata or result.invalid_references:
            result.is_valid = False

        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _has_signal_for_function(self, function_name: str) -> bool:
        """
        Check if any registered signal matches the given inference
        utility function name.

        Handles the convention where function names end with
        ``_basefunction``: the signal ID is typically the function name
        without that suffix, or may match directly.
        """
        # Direct match by signal_id
        if function_name in self._by_id:
            return True

        # Strip _basefunction suffix and try
        stripped = function_name
        if stripped.endswith("_basefunction"):
            stripped = stripped[: -len("_basefunction")]
        if stripped in self._by_id:
            return True

        # Brute-force check against all registered IDs
        for sid in self._by_id:
            if sid == function_name or function_name.startswith(sid):
                return True

        return False

    def __repr__(self) -> str:
        return (
            f"MetadataRegistry(signals={self.size}, "
            f"categories={len(self._by_category)}, "
            f"coverages={len(self._by_coverage)})"
        )


# ==========================================================================
# Pre-populated global registry
# ==========================================================================

SIGNAL_METADATA_REGISTRY = MetadataRegistry()

# ---------------------------------------------------------------------------
# Helper for concise registration
# ---------------------------------------------------------------------------
_SCORE_RANGE = (0.0, 100.0)

_TTL_REALTIME = 60
_TTL_FREQUENT = 300
_TTL_HOURLY = 3600
_TTL_DAILY = 86400
_TTL_WEEKLY = 604800
_TTL_MONTHLY = 2592000


def _sm(
    signal_id: str,
    signal_name: str,
    category: str,
    proxy_tier: str,
    ttl_seconds: int,
    required_extractors: List[str],
    output_type: str,
    value_range: Optional[Tuple[float, float]],
    coverage_applicability: List[str],
    description: str,
) -> SignalMetadata:
    """Shorthand factory for ``SignalMetadata``."""
    return SignalMetadata(
        signal_id=signal_id,
        signal_name=signal_name,
        category=category,
        proxy_tier=proxy_tier,
        ttl_seconds=ttl_seconds,
        required_extractors=required_extractors,
        output_type=output_type,
        value_range=value_range,
        coverage_applicability=coverage_applicability,
        description=description,
    )


# =========================================================================
# AEROSPACE SIGNALS
# =========================================================================

_AEROSPACE_SIGNALS: List[SignalMetadata] = [
    # -- Network Authority --
    _sm(
        "alliance_membership", "Airline Alliance Membership", "network_authority",
        INFERRED_PROXY, _TTL_DAILY, ["AllianceMembershipExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_AEROSPACE],
        "Membership in Star Alliance, oneworld, SkyTeam",
    ),
    _sm(
        "codeshare_quality", "Codeshare Partner Quality", "network_authority",
        INFERRED_PROXY, _TTL_DAILY, ["CodesharePartnerExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_AEROSPACE],
        "Average safety rating of codeshare partners",
    ),
    _sm(
        "lessor_quality", "Aircraft Lessor Quality", "network_authority",
        INFERRED_PROXY, _TTL_WEEKLY, ["AircraftLessorExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_AEROSPACE],
        "Quality tier of aircraft lessors",
    ),
    _sm(
        "oem_relationship", "OEM Relationship", "network_authority",
        INFERRED_PROXY, _TTL_WEEKLY, ["OEMRelationshipExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_AEROSPACE],
        "Direct relationships with Boeing, Airbus, Embraer",
    ),
    _sm(
        "mro_quality", "MRO Provider Quality", "network_authority",
        INFERRED_PROXY, _TTL_WEEKLY, ["MROQualityExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_AEROSPACE],
        "Quality of maintenance, repair, and overhaul providers",
    ),
    # -- Safety Record --
    _sm(
        "accident_history", "Accident History", "safety",
        DIRECT_OBSERVABLE, _TTL_DAILY, ["AccidentHistoryExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_AEROSPACE],
        "Hull loss and major accidents (10-year lookback)",
    ),
    _sm(
        "incident_history", "Incident History", "safety",
        DIRECT_OBSERVABLE, _TTL_DAILY, ["IncidentHistoryExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_AEROSPACE],
        "Serious incidents, runway excursions, near-misses",
    ),
    _sm(
        "accident_rate", "Accident Rate vs Industry", "safety",
        INFERRED_PROXY, _TTL_DAILY, ["AccidentRateExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_AEROSPACE],
        "Accidents per million departures vs industry average",
    ),
    _sm(
        "fatality_history", "Fatality History", "safety",
        DIRECT_OBSERVABLE, _TTL_DAILY, ["FatalityHistoryExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_AEROSPACE, COVERAGE_ENERGY],
        "Fatal accident history (10-year lookback)",
    ),
    _sm(
        "investigation_findings", "Investigation Findings", "safety",
        DIRECT_OBSERVABLE, _TTL_WEEKLY, ["InvestigationFindingsExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_AEROSPACE],
        "Operator cited as causal factor in investigations",
    ),
    # -- Regulatory Compliance --
    _sm(
        "certificate_status", "Operating Certificate Status", "regulatory",
        DIRECT_OBSERVABLE, _TTL_DAILY, ["CertificateStatusExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_AEROSPACE],
        "AOC/Part 121/135 certificate status",
    ),
    _sm(
        "iosa_audit_status", "IOSA Audit Status", "regulatory",
        DIRECT_OBSERVABLE, _TTL_DAILY, ["IOSAAuditExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_AEROSPACE],
        "IOSA registration and audit findings",
    ),
    _sm(
        "ramp_inspection", "Ramp Inspection Results", "regulatory",
        DIRECT_OBSERVABLE, _TTL_WEEKLY, ["RampInspectionExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_AEROSPACE],
        "SAFA/SACA ramp inspection findings rate",
    ),
    _sm(
        "eu_safety_list", "EU Air Safety List Status", "regulatory",
        DIRECT_OBSERVABLE, _TTL_DAILY, ["EUSafetyListExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_AEROSPACE],
        "Presence on EU banned carrier list",
    ),
    _sm(
        "state_safety_rating", "State of Registry Safety Rating", "regulatory",
        DIRECT_OBSERVABLE, _TTL_WEEKLY, ["StateSafetyExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_AEROSPACE],
        "ICAO USOAP audit results for state of registry",
    ),
    # -- Operational Quality --
    _sm(
        "otp_score", "On-Time Performance", "operational",
        DIRECT_OBSERVABLE, _TTL_DAILY, ["OTPScoreExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_AEROSPACE],
        "Departure/arrival punctuality vs benchmarks",
    ),
    _sm(
        "dispatch_reliability", "Dispatch Reliability", "operational",
        DIRECT_OBSERVABLE, _TTL_DAILY, ["DispatchReliabilityExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_AEROSPACE],
        "Completion rate and technical dispatch reliability",
    ),
    # -- Fleet Quality --
    _sm(
        "fleet_age", "Fleet Average Age", "operational",
        INFERRED_PROXY, _TTL_WEEKLY, ["FleetAgeExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_AEROSPACE, COVERAGE_MARINE],
        "Average aircraft or vessel age vs benchmarks",
    ),
    _sm(
        "fleet_homogeneity", "Fleet Homogeneity", "operational",
        INFERRED_PROXY, _TTL_WEEKLY, ["FleetHomogeneityExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_AEROSPACE],
        "Fleet type standardization score",
    ),
    _sm(
        "aircraft_generation", "Aircraft Generation", "operational",
        INFERRED_PROXY, _TTL_WEEKLY, ["AircraftGenerationExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_AEROSPACE],
        "Percentage of current-generation aircraft in fleet",
    ),
    # -- Route Risk --
    _sm(
        "conflict_zone_exposure", "Conflict Zone Exposure", "operational",
        INFERRED_PROXY, _TTL_DAILY, ["ConflictZoneExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_AEROSPACE],
        "Operations through or near conflict zones",
    ),
]


# =========================================================================
# CYBER SIGNALS
# =========================================================================

_CYBER_SIGNALS: List[SignalMetadata] = [
    # -- Categorical --
    _sm(
        "industry_classification", "Industry Classification", "categorical",
        INFERRED_PROXY, _TTL_WEEKLY, ["IndustryClassificationExtractor"],
        OUTPUT_CATEGORY, None, [COVERAGE_CYBER, COVERAGE_DO],
        "Industry classification derived from public records",
    ),
    _sm(
        "size_band", "Company Size Band", "categorical",
        INFERRED_PROXY, _TTL_WEEKLY, ["CompanySizeExtractor"],
        OUTPUT_CATEGORY, None, [COVERAGE_CYBER],
        "Company size classification from employee and revenue signals",
    ),
    _sm(
        "geography", "Operational Geography", "categorical",
        INFERRED_PROXY, _TTL_WEEKLY, ["OperationalBaseExtractor"],
        OUTPUT_CATEGORY, None, [COVERAGE_CYBER],
        "Primary operational geography for regulatory exposure",
    ),
    # -- Technical Infrastructure --
    _sm(
        "tls_configuration", "TLS Configuration", "security",
        DIRECT_OBSERVABLE, _TTL_HOURLY, ["TLSConfigurationExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_CYBER, COVERAGE_FI, COVERAGE_PI],
        "TLS/SSL configuration quality using SSL Labs methodology",
    ),
    _sm(
        "security_headers", "Security Headers", "security",
        DIRECT_OBSERVABLE, _TTL_HOURLY, ["SecurityHeadersExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_CYBER, COVERAGE_FI, COVERAGE_PI],
        "HTTP security headers implementation quality",
    ),
    _sm(
        "email_authentication", "Email Authentication", "security",
        DIRECT_OBSERVABLE, _TTL_HOURLY, ["EmailAuthenticationExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_CYBER, COVERAGE_FI, COVERAGE_PI],
        "SPF, DMARC, DKIM email authentication configuration",
    ),
    _sm(
        "dnssec_status", "DNSSEC Status", "security",
        DIRECT_OBSERVABLE, _TTL_DAILY, ["DNSSECExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_CYBER],
        "DNSSEC deployment status",
    ),
    _sm(
        "network_exposure", "Network Exposure", "security",
        DIRECT_OBSERVABLE, _TTL_HOURLY, ["NetworkExposureExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_CYBER, COVERAGE_FI],
        "Exposed services and ports on the public internet",
    ),
    _sm(
        "software_currency", "Software Currency", "security",
        INFERRED_PROXY, _TTL_DAILY, ["SoftwareCurrencyExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_CYBER],
        "How current detected software versions are vs latest releases",
    ),
    _sm(
        "cve_exposure", "CVE Exposure", "security",
        DIRECT_OBSERVABLE, _TTL_HOURLY, ["CVEExposureExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_CYBER, COVERAGE_FI],
        "Known CVE exposure in externally detected software",
    ),
    _sm(
        "cloud_infrastructure", "Cloud Infrastructure", "security",
        INFERRED_PROXY, _TTL_DAILY, ["CloudInfrastructureExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_CYBER],
        "Cloud provider usage and configuration quality",
    ),
    _sm(
        "waf_presence", "WAF Presence", "security",
        DIRECT_OBSERVABLE, _TTL_DAILY, ["WAFPresenceExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_CYBER],
        "Web application firewall detection",
    ),
    _sm(
        "cdn_usage", "CDN Usage", "security",
        DIRECT_OBSERVABLE, _TTL_DAILY, ["CDNUsageExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_CYBER],
        "Content delivery network usage for DDoS protection",
    ),
    # -- Public Record --
    _sm(
        "breach_history", "Data Breach History", "security",
        DIRECT_OBSERVABLE, _TTL_DAILY,
        ["BreachHistoryExtractor", "HaveIBeenPwnedExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE,
        [COVERAGE_CYBER, COVERAGE_FI, COVERAGE_PI],
        "Historical data breaches from public databases",
    ),
    _sm(
        "regulatory_actions", "Regulatory Actions", "regulatory",
        DIRECT_OBSERVABLE, _TTL_DAILY, ["RegulatoryActionExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_CYBER, COVERAGE_DO],
        "Public regulatory enforcement actions",
    ),
    _sm(
        "litigation_history", "Litigation History", "financial",
        DIRECT_OBSERVABLE, _TTL_DAILY, ["LitigationHistoryExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_CYBER, COVERAGE_DO],
        "Civil litigation and class action history",
    ),
    _sm(
        "credential_exposure", "Credential Exposure", "security",
        DIRECT_OBSERVABLE, _TTL_DAILY, ["CredentialExposureExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_CYBER],
        "Exposed credentials in public breach databases",
    ),
    _sm(
        "dark_web_presence", "Dark Web Presence", "security",
        INFERRED_PROXY, _TTL_DAILY, ["DarkWebExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_CYBER],
        "Presence of corporate data on dark web marketplaces",
    ),
    # -- Corporate Footprint --
    _sm(
        "security_page_presence", "Security Page Presence", "corporate_footprint",
        DIRECT_OBSERVABLE, _TTL_WEEKLY, ["SecurityPageExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_CYBER, COVERAGE_FI],
        "Dedicated security or trust page on corporate website",
    ),
    _sm(
        "bug_bounty_presence", "Bug Bounty Presence", "corporate_footprint",
        DIRECT_OBSERVABLE, _TTL_WEEKLY, ["BugBountyExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_CYBER],
        "Active bug bounty or vulnerability disclosure programme",
    ),
    _sm(
        "security_hiring_activity", "Security Hiring Activity", "corporate_footprint",
        INFERRED_PROXY, _TTL_WEEKLY, ["SecurityHiringExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_CYBER],
        "Job postings for security roles as proxy for investment",
    ),
    # -- Structured Data --
    _sm(
        "security_rating", "Third-Party Security Rating", "structured_data",
        DIRECT_OBSERVABLE, _TTL_DAILY, ["SecurityRatingExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_CYBER, COVERAGE_FI],
        "BitSight, SecurityScorecard, or similar third-party rating",
    ),
]


# =========================================================================
# FINANCIAL INSTITUTIONS SIGNALS
# =========================================================================

_FI_SIGNALS: List[SignalMetadata] = [
    # -- Network Authority --
    _sm(
        "correspondent_quality", "Correspondent Banking Quality",
        "network_authority", INFERRED_PROXY, _TTL_WEEKLY,
        ["CorrespondentQualityExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_FI],
        "Quality of correspondent banking relationships",
    ),
    _sm(
        "fhlb_membership", "FHLB Membership", "network_authority",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["FHLBMembershipExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_FI],
        "Federal Home Loan Bank membership and standing",
    ),
    _sm(
        "auditor_quality", "External Auditor Quality", "network_authority",
        INFERRED_PROXY, _TTL_WEEKLY, ["AuditorQualityExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_FI, COVERAGE_DO],
        "Quality tier of external auditor (Big 4, national, regional)",
    ),
    _sm(
        "clearing_relationship", "Clearing Relationships", "network_authority",
        INFERRED_PROXY, _TTL_WEEKLY, ["ClearingRelationshipExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_FI],
        "Quality of clearing and settlement relationships",
    ),
    _sm(
        "credit_rating", "Credit Rating", "structured_data",
        DIRECT_OBSERVABLE, _TTL_DAILY, ["CreditRatingExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE,
        [COVERAGE_FI, COVERAGE_AEROSPACE, COVERAGE_DO, COVERAGE_ENERGY, COVERAGE_MARINE],
        "Credit rating from major rating agencies",
    ),
    # -- Regulatory Compliance --
    _sm(
        "examination_rating", "Examination Rating Proxy", "regulatory",
        INFERRED_PROXY, _TTL_WEEKLY, ["ExaminationRatingExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_FI],
        "Inferred examination quality from observable indicators",
    ),
    _sm(
        "enforcement_action", "Enforcement Actions", "regulatory",
        DIRECT_OBSERVABLE, _TTL_DAILY, ["EnforcementActionExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_FI, COVERAGE_AEROSPACE],
        "Formal enforcement actions (C&D, CMPs, consent orders)",
    ),
    _sm(
        "bsa_aml", "BSA/AML Compliance", "regulatory",
        INFERRED_PROXY, _TTL_WEEKLY, ["BSAAMLExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_FI],
        "Bank Secrecy Act / Anti-Money Laundering compliance indicators",
    ),
    _sm(
        "cra_rating", "CRA Rating", "regulatory",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["CRARatingExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_FI],
        "Community Reinvestment Act examination rating",
    ),
    # -- Financial Condition --
    _sm(
        "capital_ratio", "Capital Adequacy", "financial",
        DIRECT_OBSERVABLE, _TTL_DAILY, ["CapitalRatioExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_FI],
        "CET1, Tier 1, Total capital ratios vs requirements",
    ),
    _sm(
        "asset_quality", "Asset Quality", "financial",
        DIRECT_OBSERVABLE, _TTL_DAILY, ["AssetQualityExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_FI],
        "NPL ratio, charge-off rates, classified assets",
    ),
    _sm(
        "liquidity", "Liquidity Position", "financial",
        DIRECT_OBSERVABLE, _TTL_DAILY, ["LiquidityExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_FI],
        "Liquidity coverage ratio and funding stability",
    ),
    _sm(
        "earnings", "Earnings Quality", "financial",
        DIRECT_OBSERVABLE, _TTL_DAILY, ["EarningsExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_FI],
        "ROA, ROE, net interest margin stability",
    ),
    # -- Governance --
    _sm(
        "board_independence", "Board Independence", "governance",
        INFERRED_PROXY, _TTL_WEEKLY, ["BoardIndependenceExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_FI, COVERAGE_DO],
        "Independent director ratio and quality",
    ),
    _sm(
        "executive_stability", "Executive Stability", "governance",
        INFERRED_PROXY, _TTL_WEEKLY, ["ExecutiveStabilityExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_FI, COVERAGE_DO],
        "CEO and executive team tenure and turnover",
    ),
]


# =========================================================================
# ENERGY SIGNALS
# =========================================================================

_ENERGY_SIGNALS: List[SignalMetadata] = [
    # -- Safety Performance --
    _sm(
        "osha_trir", "OSHA Total Recordable Incident Rate", "safety",
        DIRECT_OBSERVABLE, _TTL_DAILY, ["OSHATRIRExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_ENERGY],
        "TRIR vs industry benchmark",
    ),
    _sm(
        "osha_violations", "OSHA Serious Violations", "safety",
        DIRECT_OBSERVABLE, _TTL_DAILY, ["OSHAViolationsExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_ENERGY],
        "History of serious/willful OSHA violations",
    ),
    _sm(
        "process_safety", "Process Safety Events", "safety",
        DIRECT_OBSERVABLE, _TTL_DAILY, ["ProcessSafetyExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_ENERGY],
        "Tier 1 and Tier 2 process safety events",
    ),
    _sm(
        "bsee_incident", "BSEE Incidents", "safety",
        DIRECT_OBSERVABLE, _TTL_DAILY, ["BSEEIncidentExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_ENERGY],
        "Offshore incidents reported to BSEE",
    ),
    _sm(
        "major_incident", "Major Incident History", "safety",
        DIRECT_OBSERVABLE, _TTL_DAILY, ["MajorIncidentExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_ENERGY],
        "Explosions, blowouts, major spills",
    ),
    # -- Environmental Compliance --
    _sm(
        "epa_violation", "EPA Violations", "environmental",
        DIRECT_OBSERVABLE, _TTL_DAILY, ["EPAViolationExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_ENERGY],
        "CAA, CWA, RCRA violations from EPA ECHO database",
    ),
    _sm(
        "spill_history", "Spill History", "environmental",
        DIRECT_OBSERVABLE, _TTL_DAILY, ["SpillHistoryExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_ENERGY],
        "Oil/chemical spill history from NRC and state records",
    ),
    _sm(
        "flaring_intensity", "Flaring Intensity", "environmental",
        DIRECT_OBSERVABLE, _TTL_WEEKLY, ["FlaringIntensityExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_ENERGY],
        "Flaring intensity from VIIRS satellite data",
    ),
    _sm(
        "methane_emissions", "Methane Emissions", "environmental",
        DIRECT_OBSERVABLE, _TTL_WEEKLY, ["MethaneEmissionsExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_ENERGY],
        "Methane emissions from satellite and ground monitoring",
    ),
    _sm(
        "emissions_compliance", "Air Emissions Compliance", "environmental",
        DIRECT_OBSERVABLE, _TTL_WEEKLY, ["EmissionsComplianceExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_ENERGY],
        "Air permit compliance and emissions data",
    ),
    # -- Operational Telemetry --
    _sm(
        "production_consistency", "Production Consistency", "operational",
        INFERRED_PROXY, _TTL_DAILY, ["ProductionConsistencyExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_ENERGY],
        "Volatility in reported production volumes",
    ),
    _sm(
        "well_integrity", "Well Integrity Indicators", "operational",
        INFERRED_PROXY, _TTL_WEEKLY, ["WellIntegrityExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_ENERGY],
        "Shut-in patterns, workovers, P&A activity",
    ),
    # -- Financial --
    _sm(
        "aro_coverage", "ARO Coverage", "financial",
        DIRECT_OBSERVABLE, _TTL_DAILY, ["AROCoverageExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_ENERGY],
        "Asset retirement obligation funding status",
    ),
    _sm(
        "restructuring", "Bankruptcy/Restructuring History", "financial",
        DIRECT_OBSERVABLE, _TTL_WEEKLY, ["RestructuringExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_ENERGY],
        "Bankruptcy or debt restructuring history",
    ),
]


# =========================================================================
# DIRECTORS & OFFICERS SIGNALS
# =========================================================================

_DO_SIGNALS: List[SignalMetadata] = [
    # -- Governance --
    _sm(
        "board_diversity", "Board Diversity", "governance",
        INFERRED_PROXY, _TTL_WEEKLY, ["BoardDiversityExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_DO],
        "Gender, ethnic, and experiential diversity on board",
    ),
    _sm(
        "ceo_chair_separation", "CEO/Chair Separation", "governance",
        DIRECT_OBSERVABLE, _TTL_WEEKLY, ["CEOChairSeparationExtractor"],
        OUTPUT_BOOLEAN, None, [COVERAGE_DO],
        "Whether CEO and Board Chair roles are separated",
    ),
    _sm(
        "committee_structure", "Committee Structure", "governance",
        INFERRED_PROXY, _TTL_WEEKLY, ["CommitteeStructureExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_DO],
        "Quality of audit, compensation, and nominating committees",
    ),
    _sm(
        "shareholder_rights", "Shareholder Rights", "governance",
        INFERRED_PROXY, _TTL_WEEKLY, ["ShareholderRightsExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_DO],
        "Shareholder-friendly provisions vs takeover defenses",
    ),
    _sm(
        "compensation_structure", "Executive Compensation Structure", "governance",
        INFERRED_PROXY, _TTL_WEEKLY, ["CompensationStructureExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_DO],
        "Pay-for-performance alignment analysis",
    ),
    # -- Financial Integrity --
    _sm(
        "audit_opinion", "Audit Opinion", "financial",
        DIRECT_OBSERVABLE, _TTL_DAILY, ["AuditOpinionExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_DO],
        "Type of external audit opinion received",
    ),
    _sm(
        "internal_controls", "Internal Controls Assessment", "financial",
        DIRECT_OBSERVABLE, _TTL_DAILY, ["InternalControlsExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_DO],
        "SOX 404 internal controls assessment results",
    ),
    _sm(
        "restatement", "Financial Restatement History", "financial",
        DIRECT_OBSERVABLE, _TTL_DAILY, ["RestatementExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_DO],
        "History of financial restatements (5-year lookback)",
    ),
    _sm(
        "stock_volatility", "Stock Price Volatility", "financial",
        DIRECT_OBSERVABLE, _TTL_DAILY, ["StockVolatilityExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_DO],
        "Historical stock price volatility vs peer group",
    ),
    _sm(
        "short_interest", "Short Interest", "financial",
        DIRECT_OBSERVABLE, _TTL_DAILY, ["ShortInterestExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_DO],
        "Short interest as percentage of float",
    ),
    # -- Litigation --
    _sm(
        "securities_litigation", "Securities Class Action History", "litigation",
        DIRECT_OBSERVABLE, _TTL_DAILY, ["SecuritiesLitigationExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_DO],
        "History of securities class action lawsuits (SCAS database)",
    ),
    _sm(
        "sec_enforcement", "SEC Enforcement History", "regulatory",
        DIRECT_OBSERVABLE, _TTL_DAILY, ["SECEnforcementExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_DO],
        "SEC enforcement actions and investigations",
    ),
    _sm(
        "insider_trading", "Insider Trading Patterns", "governance",
        DIRECT_OBSERVABLE, _TTL_DAILY, ["InsiderTradingExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_DO],
        "Form 4 insider trading pattern analysis",
    ),
    # -- Structured Data --
    _sm(
        "governance_rating", "Governance Rating", "structured_data",
        DIRECT_OBSERVABLE, _TTL_DAILY, ["GovernanceRatingExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_DO],
        "Third-party governance quality rating (ISS, Glass Lewis)",
    ),
    _sm(
        "iss_governance", "ISS Governance QualityScore", "structured_data",
        DIRECT_OBSERVABLE, _TTL_DAILY, ["ISSGovernanceExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_DO],
        "ISS Governance QualityScore assessment",
    ),
]


# =========================================================================
# MARINE SIGNALS
# =========================================================================

_MARINE_SIGNALS: List[SignalMetadata] = [
    # -- Network Authority --
    _sm(
        "classification_society", "Classification Society Quality",
        "network_authority", DIRECT_OBSERVABLE, _TTL_WEEKLY,
        ["ClassificationSocietyExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_MARINE],
        "IACS member vs non-IACS classification society",
    ),
    _sm(
        "pi_club", "P&I Club Membership", "network_authority",
        DIRECT_OBSERVABLE, _TTL_WEEKLY, ["PIClubExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_MARINE],
        "International Group P&I club vs fixed premium market",
    ),
    _sm(
        "charterer_quality", "Charterer Relationships", "network_authority",
        INFERRED_PROXY, _TTL_WEEKLY, ["ChartererQualityExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_MARINE],
        "Quality of major charterers (oil majors, commodity traders)",
    ),
    _sm(
        "flag_state", "Flag State Quality", "regulatory",
        DIRECT_OBSERVABLE, _TTL_WEEKLY, ["FlagStateExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_MARINE],
        "Paris MoU white/grey/black list flag state quality",
    ),
    # -- Operational Telemetry --
    _sm(
        "ais_compliance", "AIS Transmission Compliance", "operational",
        DIRECT_OBSERVABLE, _TTL_DAILY, ["AISComplianceExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_MARINE],
        "Consistency of AIS transmission across fleet",
    ),
    _sm(
        "dark_activity", "Dark Activity Patterns", "operational",
        DIRECT_OBSERVABLE, _TTL_DAILY, ["DarkActivityExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_MARINE],
        "AIS gaps in suspicious locations or patterns",
    ),
    _sm(
        "route_risk", "Trading Route Risk Profile", "operational",
        INFERRED_PROXY, _TTL_DAILY, ["RouteRiskExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_MARINE],
        "Exposure to high-risk areas (piracy zones, war zones)",
    ),
    # -- Safety Compliance --
    _sm(
        "psc_detention", "PSC Detention Rate", "safety",
        DIRECT_OBSERVABLE, _TTL_DAILY, ["PSCDetentionExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_MARINE],
        "Port state control detention history",
    ),
    _sm(
        "psc_deficiency", "PSC Deficiency Rate", "safety",
        DIRECT_OBSERVABLE, _TTL_DAILY, ["PSCDeficiencyExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_MARINE],
        "Average deficiencies per PSC inspection vs benchmark",
    ),
    _sm(
        "class_status", "Classification Status", "safety",
        DIRECT_OBSERVABLE, _TTL_DAILY, ["ClassStatusExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_MARINE],
        "Class status, conditions of class, recommendations outstanding",
    ),
    _sm(
        "ism_compliance", "ISM/ISPS Compliance", "safety",
        DIRECT_OBSERVABLE, _TTL_WEEKLY, ["ISMComplianceExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_MARINE],
        "Document of Compliance and safety management status",
    ),
    # -- Sanctions Compliance --
    _sm(
        "sanctions_status", "Direct Sanctions Status", "sanctions",
        DIRECT_OBSERVABLE, _TTL_DAILY, ["SanctionsStatusExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_MARINE],
        "OFAC, EU, UN sanctions list status",
    ),
    _sm(
        "ownership_transparency", "Beneficial Ownership Transparency",
        "sanctions", INFERRED_PROXY, _TTL_WEEKLY,
        ["OwnershipTransparencyExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_MARINE],
        "Clarity of beneficial ownership structure",
    ),
    _sm(
        "sts_pattern", "STS Transfer Patterns", "sanctions",
        DIRECT_OBSERVABLE, _TTL_DAILY, ["STSPatternExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_MARINE],
        "Ship-to-ship transfer activity analysis",
    ),
    # -- Environmental --
    _sm(
        "cii_rating", "CII Rating", "environmental",
        DIRECT_OBSERVABLE, _TTL_WEEKLY, ["CIIRatingExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_MARINE],
        "Carbon Intensity Indicator rating (A-E)",
    ),
    # -- Structured Data --
    _sm(
        "vetting", "RightShip/Vetting Score", "structured_data",
        DIRECT_OBSERVABLE, _TTL_DAILY, ["VettingExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_MARINE],
        "Third-party vetting scores (RightShip, SIRE, CDI)",
    ),
]


# =========================================================================
# PROFESSIONAL INDEMNITY SIGNALS
# =========================================================================

_PI_SIGNALS: List[SignalMetadata] = [
    # -- Network Authority --
    _sm(
        "peer_ranking", "Peer Rankings", "network_authority",
        INFERRED_PROXY, _TTL_WEEKLY, ["PeerRankingExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_PI],
        "Recognition in Chambers, Legal 500, Best Lawyers, etc.",
    ),
    _sm(
        "client_quality", "Client Quality", "network_authority",
        INFERRED_PROXY, _TTL_WEEKLY, ["ClientQualityExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_PI, COVERAGE_ENERGY],
        "Quality of client base (public companies, Fortune 500)",
    ),
    _sm(
        "thought_leadership", "Thought Leadership", "network_authority",
        INFERRED_PROXY, _TTL_WEEKLY, ["ThoughtLeadershipExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_PI],
        "Publications, speaking engagements, CLE presentations",
    ),
    # -- Regulatory Standing --
    _sm(
        "license_status", "License Status", "regulatory",
        DIRECT_OBSERVABLE, _TTL_DAILY, ["LicenseStatusExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_PI],
        "Current status of all professional licenses",
    ),
    _sm(
        "disciplinary_history", "Disciplinary History", "regulatory",
        DIRECT_OBSERVABLE, _TTL_DAILY, ["DisciplinaryHistoryExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_PI],
        "Sanctions, censures, suspensions, reprimands from bar/board",
    ),
    _sm(
        "malpractice_record", "Public Malpractice Record", "regulatory",
        DIRECT_OBSERVABLE, _TTL_DAILY, ["MalpracticeRecordExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_PI],
        "Public judgments and disclosed malpractice settlements",
    ),
    _sm(
        "specialty_certification", "Specialty Certifications", "regulatory",
        INFERRED_PROXY, _TTL_MONTHLY, ["SpecialtyCertificationExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_PI],
        "Board certifications, specialty designations",
    ),
    # -- Firm Stability --
    _sm(
        "partner_stability", "Partner/Principal Stability", "operational",
        INFERRED_PROXY, _TTL_WEEKLY, ["PartnerStabilityExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_PI],
        "Partner retention and turnover patterns",
    ),
    _sm(
        "financial_stability", "Financial Stability", "financial",
        INFERRED_PROXY, _TTL_WEEKLY, ["FinancialStabilityExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_PI],
        "Firm financial health indicators",
    ),
    # -- Practice Quality --
    _sm(
        "client_reviews", "Client Reviews", "operational",
        INFERRED_PROXY, _TTL_WEEKLY, ["ClientReviewsExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_PI],
        "Client ratings on professional review platforms",
    ),
    _sm(
        "complaint_history", "Professional Complaints", "operational",
        DIRECT_OBSERVABLE, _TTL_DAILY, ["ComplaintHistoryExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_PI],
        "Complaints filed with professional regulatory bodies",
    ),
    # -- Litigation History --
    _sm(
        "malpractice_suits", "Malpractice Suits", "litigation",
        DIRECT_OBSERVABLE, _TTL_DAILY, ["MalpracticeSuitsExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_PI],
        "Professional negligence suits filed against firm/principals",
    ),
    _sm(
        "regulatory_enforcement", "Regulatory Enforcement", "regulatory",
        DIRECT_OBSERVABLE, _TTL_DAILY, ["RegulatoryEnforcementExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_PI],
        "Regulatory enforcement actions against professionals",
    ),
]


# =========================================================================
# CROSS-COVERAGE SIGNALS
# These appear in multiple coverages under shared inference functions.
# =========================================================================

_CROSS_COVERAGE_SIGNALS: List[SignalMetadata] = [
    _sm(
        "esg_rating", "ESG Rating", "structured_data",
        INFERRED_PROXY, _TTL_DAILY, ["ESGRatingExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE,
        [COVERAGE_FI, COVERAGE_DO, COVERAGE_ENERGY, COVERAGE_MARINE, COVERAGE_PROPERTY, COVERAGE_CASUALTY, COVERAGE_AEROSPACE, COVERAGE_FPR],
        "Third-party ESG rating from major providers",
    ),
    _sm(
        "esg_reporting", "ESG/Sustainability Reporting", "corporate_footprint",
        INFERRED_PROXY, _TTL_WEEKLY, ["ESGReportingExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE,
        [COVERAGE_FI, COVERAGE_DO, COVERAGE_ENERGY, COVERAGE_PROPERTY, COVERAGE_CASUALTY],
        "Quality of ESG and sustainability reporting",
    ),
    _sm(
        "investor_relations", "Investor Relations Quality", "corporate_footprint",
        INFERRED_PROXY, _TTL_WEEKLY, ["InvestorRelationsExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_FI, COVERAGE_DO],
        "Quality of investor communications and transparency",
    ),
    _sm(
        "disclosure_quality", "Disclosure Quality", "corporate_footprint",
        INFERRED_PROXY, _TTL_WEEKLY, ["DisclosureQualityExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_FI, COVERAGE_ENERGY],
        "Quality and timeliness of regulatory disclosures",
    ),
    _sm(
        "hiring_signals", "Risk/Compliance Hiring", "corporate_footprint",
        INFERRED_PROXY, _TTL_WEEKLY, ["HiringSignalsExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_FI, COVERAGE_DO],
        "Risk, compliance, and security hiring activity",
    ),
    _sm(
        "industry_association", "Industry Association Membership",
        "network_authority", INFERRED_PROXY, _TTL_MONTHLY,
        ["IndustryAssociationExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE,
        [COVERAGE_FI, COVERAGE_DO, COVERAGE_ENERGY, COVERAGE_MARINE, COVERAGE_PROPERTY, COVERAGE_CASUALTY, COVERAGE_AEROSPACE, COVERAGE_FPR],
        "Active membership and leadership in industry associations",
    ),
    _sm(
        "banking_relationship", "Banking/Finance Relationships",
        "network_authority", INFERRED_PROXY, _TTL_WEEKLY,
        ["BankingRelationshipExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE,
        [COVERAGE_DO, COVERAGE_ENERGY, COVERAGE_MARINE, COVERAGE_PROPERTY, COVERAGE_CASUALTY, COVERAGE_FPR],
        "Quality of banking and financing relationships",
    ),
]


# ---------------------------------------------------------------------------
# Register all entries
# ---------------------------------------------------------------------------

SIGNAL_METADATA_REGISTRY.register_many(_AEROSPACE_SIGNALS)
SIGNAL_METADATA_REGISTRY.register_many(_CYBER_SIGNALS)
SIGNAL_METADATA_REGISTRY.register_many(_FI_SIGNALS)
SIGNAL_METADATA_REGISTRY.register_many(_ENERGY_SIGNALS)
SIGNAL_METADATA_REGISTRY.register_many(_DO_SIGNALS)
SIGNAL_METADATA_REGISTRY.register_many(_MARINE_SIGNALS)
SIGNAL_METADATA_REGISTRY.register_many(_PI_SIGNALS)
SIGNAL_METADATA_REGISTRY.register_many(_CROSS_COVERAGE_SIGNALS)


# =========================================================================
# NEW PROPERTY SIGNALS (phase_2)
# =========================================================================

_PROPERTY_SIGNALS: List[SignalMetadata] = [
    # -- Construction Quality --
    _sm(
        "construction_class", "Construction Class", "construction_quality",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["ConstructionClassExtractor"],
        OUTPUT_CATEGORY, None, [COVERAGE_PROPERTY],
        "ISO/COPE construction classification — frame, joisted masonry, non-combustible, masonry non-combu...",
    ),
    _sm(
        "building_age_condition", "Building Age & Condition", "construction_quality",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["BuildingAgeConditionExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_PROPERTY],
        "Composite score of building age, last major renovation, and overall condition rating",
    ),
    _sm(
        "building_code_compliance", "Building Code Compliance", "construction_quality",
        INFERRED_PROXY, _TTL_MONTHLY, ["BuildingCodeComplianceExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_PROPERTY],
        "Current compliance with local building codes; grandfathered non-conformities flagged",
    ),
    _sm(
        "roof_condition", "Roof Condition", "construction_quality",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["RoofConditionExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_PROPERTY],
        "Roof age, material, condition, and recent inspection results — primary water damage driver",
    ),
    _sm(
        "electrical_system_quality", "Electrical System Quality", "construction_quality",
        INFERRED_PROXY, _TTL_MONTHLY, ["ElectricalSystemQualityExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_PROPERTY],
        "Age of electrical systems, panel capacity, wiring type, recent inspection",
    ),
    _sm(
        "renovation_history", "Renovation History", "construction_quality",
        INFERRED_PROXY, _TTL_MONTHLY, ["RenovationHistoryExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_PROPERTY],
        "Track record of capital investment; recent renovations reduce age-related risk",
    ),
    # -- Occupancy Risk --
    _sm(
        "occupancy_hazard_grade", "Occupancy Hazard Grade", "occupancy_risk",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["OccupancyHazardGradeExtractor"],
        OUTPUT_CATEGORY, None, [COVERAGE_PROPERTY],
        "ISO occupancy hazard classification — from low (office) to special (chemical storage)",
    ),
    _sm(
        "tenant_concentration", "Tenant Concentration", "occupancy_risk",
        INFERRED_PROXY, _TTL_MONTHLY, ["TenantConcentrationExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_PROPERTY],
        "Number and diversity of tenants; single-tenant risk vs multi-tenant diversification",
    ),
    _sm(
        "contents_value_density", "Contents Value Density", "occupancy_risk",
        INFERRED_PROXY, _TTL_MONTHLY, ["ContentsValueDensityExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_PROPERTY],
        "Value of contents per square foot — drives severity; high-value stock amplifies loss",
    ),
    _sm(
        "vacancy_rate", "Vacancy Rate", "occupancy_risk",
        DIRECT_OBSERVABLE, _TTL_WEEKLY, ["VacancyRateExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_PROPERTY],
        "Percentage of space unoccupied — vacant properties have higher arson and vandalism rates",
    ),
    _sm(
        "housekeeping_quality", "Housekeeping & Maintenance Quality", "occupancy_risk",
        INFERRED_PROXY, _TTL_MONTHLY, ["HousekeepingQualityExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_PROPERTY],
        "General upkeep, cleanliness, storage practices — proxy for management attention to risk",
    ),
    # -- Catastrophe Exposure --
    _sm(
        "wind_zone", "Wind Zone Exposure", "cat_exposure",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["WindZoneExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_PROPERTY],
        "Proximity to named-storm-exposed coastline; hurricane/typhoon return periods",
    ),
    _sm(
        "earthquake_zone", "Earthquake Zone Exposure", "cat_exposure",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["EarthquakeZoneExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_PROPERTY],
        "Seismic zone classification; proximity to known fault lines; soil liquefaction risk",
    ),
    _sm(
        "flood_zone", "Flood Zone Exposure", "cat_exposure",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["FloodZoneExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_PROPERTY],
        "FEMA flood zone classification; proximity to waterways; historical flood events",
    ),
    _sm(
        "wildfire_zone", "Wildfire Zone Exposure", "cat_exposure",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["WildfireZoneExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_PROPERTY],
        "Wildland-urban interface proximity; vegetation density; historical fire events",
    ),
    _sm(
        "convective_storm_exposure", "Convective Storm Exposure", "cat_exposure",
        INFERRED_PROXY, _TTL_MONTHLY, ["ConvectiveStormExposureExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_PROPERTY],
        "Hail, tornado, and severe thunderstorm frequency for location",
    ),
    _sm(
        "geographic_concentration", "Geographic Concentration", "cat_exposure",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["GeographicConcentrationExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_PROPERTY],
        "Single-location vs multi-site; distance between sites; aggregation risk",
    ),
    # -- Fire Protection --
    _sm(
        "sprinkler_coverage", "Sprinkler System Coverage", "fire_protection",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["SprinklerCoverageExtractor"],
        OUTPUT_CATEGORY, None, [COVERAGE_PROPERTY],
        "Extent and type of automatic sprinkler protection — full, partial, or none",
    ),
    _sm(
        "fire_alarm_quality", "Fire Alarm & Detection Quality", "fire_protection",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["FireAlarmQualityExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_PROPERTY],
        "Alarm system type — central station, proprietary, local, or none",
    ),
    _sm(
        "fire_department_response", "Fire Department Response", "fire_protection",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["FireDepartmentResponseExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_PROPERTY],
        "Distance to nearest fire station; ISO public protection class; response time",
    ),
    _sm(
        "fire_separation", "Fire Separation & Compartmentation", "fire_protection",
        INFERRED_PROXY, _TTL_MONTHLY, ["FireSeparationExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_PROPERTY],
        "Fire walls, fire doors, compartmentation between occupancies or sections",
    ),
    _sm(
        "water_supply_adequacy", "Water Supply Adequacy", "fire_protection",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["WaterSupplyAdequacyExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_PROPERTY],
        "Hydrant distance, water pressure, supply duration for fire suppression",
    ),
    # -- Business Interruption --
    _sm(
        "revenue_concentration", "Revenue Concentration at Location", "business_interruption",
        INFERRED_PROXY, _TTL_MONTHLY, ["RevenueConcentrationExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_PROPERTY],
        "Percentage of total enterprise revenue generated at or dependent on insured location",
    ),
    _sm(
        "recovery_time_estimate", "Recovery Time Estimate", "business_interruption",
        INFERRED_PROXY, _TTL_MONTHLY, ["RecoveryTimeEstimateExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_PROPERTY],
        "Estimated time to restore operations after total loss — months to rebuild, re-equip, re-staff",
    ),
    _sm(
        "supply_chain_dependency", "Supply Chain Dependency", "business_interruption",
        INFERRED_PROXY, _TTL_MONTHLY, ["SupplyChainDependencyExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_PROPERTY],
        "Reliance on single-source suppliers or critical supply chains affected by same peril zone",
    ),
    _sm(
        "contingent_bi_exposure", "Contingent BI Exposure", "business_interruption",
        COHORT_INFERENCE, _TTL_MONTHLY, ["ContingentBiExposureExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_PROPERTY],
        "Exposure from key customers or suppliers suffering property loss — contingent and dependent BI",
    ),
    _sm(
        "business_continuity_planning", "Business Continuity Planning", "business_interruption",
        INFERRED_PROXY, _TTL_MONTHLY, ["BusinessContinuityPlanningExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_PROPERTY],
        "Quality of BCP/DRP; backup facilities; tested recovery procedures",
    ),
]


# =========================================================================
# EXPANSION MARINE SIGNALS (phase_3)
# =========================================================================

_MARINE_EXPANSION_SIGNALS: List[SignalMetadata] = [
    # -- Cargo Quality --
    _sm(
        "cargo_commodity_class", "Cargo Commodity Classification", "cargo_quality",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["CargoCommodityClassExtractor"],
        OUTPUT_CATEGORY, None, [COVERAGE_MARINE],
        "Commodity hazard class — from low (finished goods) to high (hazmat, perishable, livestock)",
    ),
    _sm(
        "packaging_quality", "Packaging & Stowage Quality", "cargo_quality",
        INFERRED_PROXY, _TTL_MONTHLY, ["PackagingQualityExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_MARINE],
        "Container condition, packaging standards, stowage compliance with IMDG/CTU codes",
    ),
    _sm(
        "transit_mode", "Transit Mode Risk", "cargo_quality",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["TransitModeExtractor"],
        OUTPUT_CATEGORY, None, [COVERAGE_MARINE],
        "Primary transit mode — ocean, multimodal, inland waterway; transhipment count increases loss freq...",
    ),
    _sm(
        "storage_exposure", "Storage & Warehousing Exposure", "cargo_quality",
        INFERRED_PROXY, _TTL_WEEKLY, ["StorageExposureExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_MARINE],
        "Duration and quality of intermediate storage; port congestion and dwell time",
    ),
    _sm(
        "theft_pilferage_exposure", "Theft & Pilferage Exposure", "cargo_quality",
        INFERRED_PROXY, _TTL_MONTHLY, ["TheftPilferageExposureExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_MARINE],
        "Route-specific theft risk; high-value cargo attractiveness; security measures in transit",
    ),
    _sm(
        "temperature_control", "Temperature Control Adequacy", "cargo_quality",
        INFERRED_PROXY, _TTL_MONTHLY, ["TemperatureControlExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_MARINE],
        "Reefer container condition, cold chain integrity, monitoring systems for perishable/pharma cargo",
    ),
    # -- Tanker Risk --
    _sm(
        "tanker_vetting_status", "Tanker Vetting Status", "tanker_risk",
        DIRECT_OBSERVABLE, _TTL_WEEKLY, ["TankerVettingStatusExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_MARINE],
        "SIRE/CDI inspection results; oil major vetting approval status",
    ),
    _sm(
        "pollution_liability_exposure", "Pollution Liability Exposure", "tanker_risk",
        INFERRED_PROXY, _TTL_MONTHLY, ["PollutionLiabilityExposureExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_MARINE],
        "CLC/IOPC exposure; P&I club pollution cover adequacy; spill response capability",
    ),
    _sm(
        "double_hull_compliance", "Double Hull Compliance", "tanker_risk",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["DoubleHullComplianceExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_MARINE],
        "MARPOL double-hull status; structural condition of hull; age of coating systems",
    ),
    _sm(
        "cargo_compatibility", "Cargo Compatibility & History", "tanker_risk",
        INFERRED_PROXY, _TTL_MONTHLY, ["CargoCompatibilityExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_MARINE],
        "Grade-specific tank cleaning compliance; cargo contamination claim history",
    ),
    _sm(
        "sts_operations", "Ship-to-Ship Transfer Operations", "tanker_risk",
        INFERRED_PROXY, _TTL_MONTHLY, ["StsOperationsExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_MARINE],
        "Frequency and quality of STS operations; compliance with OCIMF guidelines",
    ),
    # -- Offshore Marine --
    _sm(
        "unit_type", "Offshore Unit Type", "offshore_marine",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["UnitTypeExtractor"],
        OUTPUT_CATEGORY, None, [COVERAGE_MARINE],
        "Classification of offshore unit — FPSO, jack-up, semi-sub, drill ship, OSV, construction",
    ),
    _sm(
        "mooring_integrity", "Mooring System Integrity", "offshore_marine",
        INFERRED_PROXY, _TTL_MONTHLY, ["MooringIntegrityExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_MARINE],
        "Mooring system age, inspection compliance, chain/anchor condition for stationary units",
    ),
    _sm(
        "dp_system_reliability", "Dynamic Positioning Reliability", "offshore_marine",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["DpSystemReliabilityExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_MARINE],
        "DP class, redundancy level, incident history, annual DP trials compliance",
    ),
    _sm(
        "metocean_exposure", "Metocean Exposure", "offshore_marine",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["MetoceanExposureExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_MARINE],
        "Operating location weather severity — wave height, wind speed, current, ice exposure",
    ),
    _sm(
        "offshore_class_compliance", "Offshore Classification Compliance", "offshore_marine",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["OffshoreClassComplianceExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_MARINE],
        "Class society survey status; special survey compliance; conditions of class outstanding",
    ),
    # -- Port State & Regulatory Compliance --
    _sm(
        "psc_detention_rate", "PSC Detention Rate", "port_state_compliance",
        DIRECT_OBSERVABLE, _TTL_WEEKLY, ["PscDetentionRateExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_MARINE],
        "Port state control detention frequency relative to fleet size; deficiency categories",
    ),
    _sm(
        "ism_audit_quality", "ISM Audit Quality", "port_state_compliance",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["IsmAuditQualityExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_MARINE],
        "ISM Code Document of Compliance status; major non-conformities; audit frequency",
    ),
    _sm(
        "isps_compliance", "ISPS Compliance", "port_state_compliance",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["IspsComplianceExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_MARINE],
        "International Ship and Port Facility Security code compliance; security plan quality",
    ),
    _sm(
        "sanctions_screening_depth", "Sanctions Screening Depth", "port_state_compliance",
        INFERRED_PROXY, _TTL_WEEKLY, ["SanctionsScreeningDepthExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_MARINE],
        "Thoroughness of sanctions and restricted party screening across charterers, cargo owners, ports",
    ),
    _sm(
        "class_survey_currency", "Classification Survey Currency", "port_state_compliance",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["ClassSurveyCurrencyExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_MARINE],
        "Currency of class surveys — annual, intermediate, special; overdue survey flags",
    ),
]


# =========================================================================
# NEW CASUALTY SIGNALS (phase_4)
# =========================================================================

_CASUALTY_SIGNALS: List[SignalMetadata] = [
    # -- General Liability Class Risk --
    _sm(
        "gl_class_code", "GL Classification Code", "gl_class_risk",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["GlClassCodeExtractor"],
        OUTPUT_CATEGORY, None, [COVERAGE_CASUALTY],
        "ISO CGL classification — drives base rate; captures industry-specific hazard profile",
    ),
    _sm(
        "premises_condition", "Premises Condition & Maintenance", "gl_class_risk",
        INFERRED_PROXY, _TTL_MONTHLY, ["PremisesConditionExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_CASUALTY],
        "Physical condition of insured premises; slip-trip-fall exposure; ADA compliance",
    ),
    _sm(
        "products_completed_ops", "Products & Completed Operations Exposure", "gl_class_risk",
        INFERRED_PROXY, _TTL_MONTHLY, ["ProductsCompletedOpsExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_CASUALTY],
        "Products liability tail; completed operations exposure for contractors; recall potential",
    ),
    _sm(
        "contractual_liability", "Contractual Liability Exposure", "gl_class_risk",
        INFERRED_PROXY, _TTL_MONTHLY, ["ContractualLiabilityExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_CASUALTY],
        "Hold-harmless agreements, indemnification clauses; assumption of others' liability",
    ),
    _sm(
        "subcontractor_management", "Subcontractor Management", "gl_class_risk",
        INFERRED_PROXY, _TTL_MONTHLY, ["SubcontractorManagementExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_CASUALTY],
        "Quality of subcontractor vetting, certificate tracking, additional insured compliance",
    ),
    _sm(
        "litigation_environment", "Litigation Environment", "gl_class_risk",
        COHORT_INFERENCE, _TTL_MONTHLY, ["LitigationEnvironmentExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_CASUALTY],
        "Jurisdictional exposure; nuclear verdict trends; plaintiff bar activity in domicile state",
    ),
    # -- Workplace Safety --
    _sm(
        "experience_modification", "Experience Modification Factor", "workplace_safety",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["ExperienceModificationExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_CASUALTY],
        "NCCI experience mod — actual vs expected losses; most direct predictor of WC performance",
    ),
    _sm(
        "osha_compliance", "OSHA Compliance Record", "workplace_safety",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["OshaComplianceExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_CASUALTY],
        "OSHA citation history; serious/willful violations; injury/illness rates vs industry average",
    ),
    _sm(
        "safety_programme_quality", "Safety Programme Quality", "workplace_safety",
        INFERRED_PROXY, _TTL_MONTHLY, ["SafetyProgrammeQualityExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_CASUALTY],
        "Formal safety programme maturity; training frequency; near-miss reporting; safety culture",
    ),
    _sm(
        "return_to_work_programme", "Return-to-Work Programme", "workplace_safety",
        INFERRED_PROXY, _TTL_MONTHLY, ["ReturnToWorkProgrammeExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_CASUALTY],
        "Modified duty programme; early intervention; medical case management effectiveness",
    ),
    _sm(
        "occupational_disease_exposure", "Occupational Disease Exposure", "workplace_safety",
        INFERRED_PROXY, _TTL_MONTHLY, ["OccupationalDiseaseExposureExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_CASUALTY],
        "Exposure to silica, asbestos, noise, repetitive motion, chemical agents — latent disease risk",
    ),
    # -- Auto Fleet Risk --
    _sm(
        "fleet_composition", "Fleet Composition", "auto_fleet_risk",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["FleetCompositionExtractor"],
        OUTPUT_CATEGORY, None, [COVERAGE_CASUALTY],
        "Vehicle types in fleet — light vehicles, medium trucks, heavy trucks, specialized equipment",
    ),
    _sm(
        "driver_quality", "Driver Quality & MVR Screening", "auto_fleet_risk",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["DriverQualityExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_CASUALTY],
        "MVR screening programme; violation rates; CDL compliance; driver training programme",
    ),
    _sm(
        "telematics_adoption", "Telematics & Safety Technology", "auto_fleet_risk",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["TelematicsAdoptionExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_CASUALTY],
        "Telematics penetration; dashcam deployment; collision avoidance systems; ELD compliance",
    ),
    _sm(
        "route_hazard", "Route Hazard Profile", "auto_fleet_risk",
        INFERRED_PROXY, _TTL_MONTHLY, ["RouteHazardExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_CASUALTY],
        "Typical operating radius; highway vs urban; seasonal exposure; state-specific hazards",
    ),
    _sm(
        "accident_frequency", "Accident Frequency & Severity", "auto_fleet_risk",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["AccidentFrequencyExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_CASUALTY],
        "Historical accident rate per million miles; DOT reportable incidents; severity trend",
    ),
    _sm(
        "fleet_maintenance", "Fleet Maintenance Programme", "auto_fleet_risk",
        INFERRED_PROXY, _TTL_MONTHLY, ["FleetMaintenanceExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_CASUALTY],
        "Preventive maintenance programme; DOT inspection pass rate; vehicle age distribution",
    ),
    # -- Environmental Liability --
    _sm(
        "pollution_conditions", "Known Pollution Conditions", "environmental_liability",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["PollutionConditionsExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_CASUALTY],
        "Existing contamination on-site; Phase I/II ESA results; remediation status",
    ),
    _sm(
        "ust_ast_compliance", "Underground/Aboveground Storage Tank Compliance", "environmental_liability",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["UstAstComplianceExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_CASUALTY],
        "UST/AST regulatory compliance; leak detection; spill prevention; tank age and construction",
    ),
    _sm(
        "regulatory_enforcement_history", "Environmental Regulatory Enforcement", "environmental_liability",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["RegulatoryEnforcementHistoryExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_CASUALTY],
        "EPA/state agency enforcement actions; consent orders; NOVs; penalty history",
    ),
    _sm(
        "waste_management_practices", "Waste Management Practices", "environmental_liability",
        INFERRED_PROXY, _TTL_MONTHLY, ["WasteManagementPracticesExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_CASUALTY],
        "Hazardous waste generation; disposal practices; RCRA compliance; manifest tracking",
    ),
    _sm(
        "third_party_site_exposure", "Third-Party Site Exposure", "environmental_liability",
        COHORT_INFERENCE, _TTL_MONTHLY, ["ThirdPartySiteExposureExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_CASUALTY],
        "CERCLA/Superfund potential; off-site disposal location quality; PRP exposure",
    ),
    # -- Umbrella & Excess Exposure --
    _sm(
        "underlying_programme_quality", "Underlying Programme Quality", "umbrella_exposure",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["UnderlyingProgrammeQualityExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_CASUALTY],
        "Adequacy of underlying GL/auto/WC/EL limits; gaps in underlying coverage",
    ),
    _sm(
        "attachment_point_adequacy", "Attachment Point Adequacy", "umbrella_exposure",
        INFERRED_PROXY, _TTL_MONTHLY, ["AttachmentPointAdequacyExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_CASUALTY],
        "Whether underlying limits are sufficient to absorb expected frequency losses",
    ),
    _sm(
        "nuclear_verdict_exposure", "Nuclear Verdict Exposure", "umbrella_exposure",
        COHORT_INFERENCE, _TTL_MONTHLY, ["NuclearVerdictExposureExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_CASUALTY],
        "Exposure to jurisdiction-specific outsized verdicts; class action potential; mass tort",
    ),
    _sm(
        "tower_position", "Tower Position & Layer Exposure", "umbrella_exposure",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["TowerPositionExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_CASUALTY],
        "Position in excess tower — lead umbrella vs high-excess; buffer layer adequacy",
    ),
    # -- Premises & Operations --
    _sm(
        "public_access_volume", "Public Access Volume", "premises_operations",
        INFERRED_PROXY, _TTL_MONTHLY, ["PublicAccessVolumeExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_CASUALTY],
        "Footfall/visitor volume at insured locations; public-facing operations scale",
    ),
    _sm(
        "security_measures", "Security & Surveillance Measures", "premises_operations",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["SecurityMeasuresExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_CASUALTY],
        "CCTV, access control, security personnel, lighting — reduces assault/negligence claims",
    ),
    _sm(
        "incident_response_capability", "Incident Response Capability", "premises_operations",
        INFERRED_PROXY, _TTL_MONTHLY, ["IncidentResponseCapabilityExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_CASUALTY],
        "First aid, emergency action plans, incident documentation, claims reporting speed",
    ),
    _sm(
        "alcohol_service", "Alcohol Service Exposure", "premises_operations",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["AlcoholServiceExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_CASUALTY],
        "Liquor liability exposure; TIPS/responsible service training; dram shop liability states",
    ),
    _sm(
        "multi_location_complexity", "Multi-Location Complexity", "premises_operations",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["MultiLocationComplexityExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_CASUALTY],
        "Number of insured locations; geographic spread; jurisdictional diversity",
    ),
]


# =========================================================================
# EXPANSION AEROSPACE SIGNALS (phase_5)
# =========================================================================

_AEROSPACE_EXPANSION_SIGNALS: List[SignalMetadata] = [
    # -- Space Risk --
    _sm(
        "launch_vehicle_reliability", "Launch Vehicle Reliability", "space_risk",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["LaunchVehicleReliabilityExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_AEROSPACE],
        "Historical success rate of launch vehicle family; consecutive success count; provider track record",
    ),
    _sm(
        "satellite_technology_maturity", "Satellite Technology Maturity", "space_risk",
        INFERRED_PROXY, _TTL_MONTHLY, ["SatelliteTechnologyMaturityExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_AEROSPACE],
        "Heritage vs novel bus/payload design; technology readiness level; manufacturer track record",
    ),
    _sm(
        "orbital_debris_exposure", "Orbital Debris & Collision Exposure", "space_risk",
        INFERRED_PROXY, _TTL_WEEKLY, ["OrbitalDebrisExposureExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_AEROSPACE],
        "Orbital regime congestion; conjunction assessment capability; manoeuvre capacity",
    ),
    _sm(
        "in_orbit_anomaly_history", "In-Orbit Anomaly History", "space_risk",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["InOrbitAnomalyHistoryExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_AEROSPACE],
        "Prior in-orbit anomalies on same bus/payload family; degradation patterns",
    ),
    _sm(
        "ground_segment_quality", "Ground Segment Quality", "space_risk",
        INFERRED_PROXY, _TTL_MONTHLY, ["GroundSegmentQualityExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_AEROSPACE],
        "Ground station network redundancy; command/control reliability; telemetry monitoring",
    ),
    # -- Rotary Wing Risk --
    _sm(
        "mission_profile", "Mission Profile", "rotary_wing_risk",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["MissionProfileExtractor"],
        OUTPUT_CATEGORY, None, [COVERAGE_AEROSPACE],
        "Primary mission type — drives frequency and severity characteristics",
    ),
    _sm(
        "rotary_pilot_experience", "Pilot Experience & Currency", "rotary_wing_risk",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["RotaryPilotExperienceExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_AEROSPACE],
        "Total rotary hours; type-specific hours; instrument currency; NVG qualification",
    ),
    _sm(
        "rotary_maintenance_quality", "Maintenance Programme Quality", "rotary_wing_risk",
        INFERRED_PROXY, _TTL_MONTHLY, ["RotaryMaintenanceQualityExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_AEROSPACE],
        "Overhaul compliance; component tracking; AD/SB compliance rate; maintenance provider quality",
    ),
    _sm(
        "landing_zone_quality", "Landing Zone & Operating Environment", "rotary_wing_risk",
        INFERRED_PROXY, _TTL_MONTHLY, ["LandingZoneQualityExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_AEROSPACE],
        "Helipad standards; offshore platform conditions; confined area operations frequency",
    ),
    _sm(
        "passenger_liability_exposure", "Passenger Liability Exposure", "rotary_wing_risk",
        INFERRED_PROXY, _TTL_MONTHLY, ["PassengerLiabilityExposureExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_AEROSPACE],
        "Passenger volume; passenger profile (workers vs public); contractual liability assumptions",
    ),
    # -- Unmanned Aircraft Systems --
    _sm(
        "uas_operational_scope", "UAS Operational Scope", "unmanned_systems",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["UasOperationalScopeExtractor"],
        OUTPUT_CATEGORY, None, [COVERAGE_AEROSPACE],
        "VLOS vs BVLOS; urban vs rural; altitude regime; autonomous vs pilot-controlled",
    ),
    _sm(
        "uas_regulatory_compliance", "UAS Regulatory Compliance", "unmanned_systems",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["UasRegulatoryComplianceExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_AEROSPACE],
        "Part 107 / EASA UAS category compliance; waiver status; remote ID compliance",
    ),
    _sm(
        "airspace_integration", "Airspace Integration Safety", "unmanned_systems",
        INFERRED_PROXY, _TTL_MONTHLY, ["AirspaceIntegrationExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_AEROSPACE],
        "UTM participation; detect-and-avoid capability; ATC coordination for controlled airspace",
    ),
    _sm(
        "uas_payload_risk", "Payload & Third-Party Risk", "unmanned_systems",
        INFERRED_PROXY, _TTL_MONTHLY, ["UasPayloadRiskExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_AEROSPACE],
        "Payload type (camera, LiDAR, delivery); overflown population density; ground risk",
    ),
    _sm(
        "uas_fleet_reliability", "UAS Fleet Reliability", "unmanned_systems",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["UasFleetReliabilityExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_AEROSPACE],
        "Aircraft type certification status; failure rate data; flyaway/lost-link incidents",
    ),
    # -- MRO Facility Risk --
    _sm(
        "mro_certification_scope", "MRO Certification Scope", "mro_risk",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["MroCertificationScopeExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_AEROSPACE],
        "FAR 145 / EASA Part 145 ratings scope; capability list breadth; authority limitations",
    ),
    _sm(
        "workmanship_claims_history", "Workmanship Claims History", "mro_risk",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["WorkmanshipClaimsHistoryExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_AEROSPACE],
        "Prior claims arising from maintenance errors; AD non-compliance incidents; return-to-service fail...",
    ),
    _sm(
        "hangarkeepers_exposure", "Hangarkeepers Exposure", "mro_risk",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["HangarkeepersExposureExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_AEROSPACE],
        "Value of customer aircraft in care, custody, control; hangar fire protection; security",
    ),
    _sm(
        "quality_system_maturity", "Quality Management System Maturity", "mro_risk",
        INFERRED_PROXY, _TTL_MONTHLY, ["QualitySystemMaturityExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_AEROSPACE],
        "AS9110 certification; internal audit programme; findings closure rate; continuous improvement",
    ),
    _sm(
        "parts_traceability", "Parts Traceability & Supply Chain", "mro_risk",
        INFERRED_PROXY, _TTL_MONTHLY, ["PartsTraceabilityExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_AEROSPACE],
        "Parts provenance controls; suspected unapproved parts screening; PMA/DER parts usage",
    ),
]


# =========================================================================
# EXPANSION DO SIGNALS (phase_6)
# =========================================================================

_DO_EXPANSION_SIGNALS: List[SignalMetadata] = [
    # -- Public Company Governance --
    _sm(
        "sec_filing_quality", "SEC Filing Quality", "public_company_governance",
        DIRECT_OBSERVABLE, _TTL_WEEKLY, ["SecFilingQualityExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_DO],
        "10-K/10-Q filing timeliness; material weakness disclosures; restatement history",
    ),
    _sm(
        "board_composition_quality", "Board Composition Quality", "public_company_governance",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["BoardCompositionQualityExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_DO],
        "Independent director ratio; board diversity; committee structure; CEO/Chair separation",
    ),
    _sm(
        "shareholder_activism", "Shareholder Activism Exposure", "public_company_governance",
        INFERRED_PROXY, _TTL_WEEKLY, ["ShareholderActivismExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_DO],
        "Activist campaign history; proxy fight risk; 13D filing patterns in sector",
    ),
    _sm(
        "securities_litigation_exposure", "Securities Litigation Exposure", "public_company_governance",
        COHORT_INFERENCE, _TTL_WEEKLY, ["SecuritiesLitigationExposureExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_DO],
        "Stock volatility; options backdating; insider trading patterns; SCA frequency in sector",
    ),
    _sm(
        "executive_compensation_structure", "Executive Compensation Structure", "public_company_governance",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["ExecutiveCompensationStructureExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_DO],
        "Say-on-pay results; compensation vs performance alignment; golden parachute provisions",
    ),
    # -- Transaction & Event Risk --
    _sm(
        "ma_activity", "M&A Transaction Activity", "transaction_event_risk",
        DIRECT_OBSERVABLE, _TTL_WEEKLY, ["MaActivityExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_DO],
        "Pending or recent M&A; hostile bid exposure; go-private transactions",
    ),
    _sm(
        "ipo_spac_exposure", "IPO/SPAC Exposure", "transaction_event_risk",
        DIRECT_OBSERVABLE, _TTL_WEEKLY, ["IpoSpacExposureExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_DO],
        "Time since IPO; SPAC de-SPAC litigation risk; S-1 disclosure quality",
    ),
    _sm(
        "pe_sponsor_dynamics", "PE/VC Sponsor Dynamics", "transaction_event_risk",
        INFERRED_PROXY, _TTL_MONTHLY, ["PeSponsorDynamicsExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_DO],
        "Sponsor-controlled board; portfolio company oversight; exit timeline pressure",
    ),
    _sm(
        "bankruptcy_distress_risk", "Bankruptcy & Financial Distress", "transaction_event_risk",
        INFERRED_PROXY, _TTL_WEEKLY, ["BankruptcyDistressRiskExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_DO],
        "Altman Z-score proxy; debt covenants; going concern qualifications; liquidity stress",
    ),
    _sm(
        "regulatory_investigation_exposure", "Regulatory Investigation Exposure", "transaction_event_risk",
        DIRECT_OBSERVABLE, _TTL_WEEKLY, ["RegulatoryInvestigationExposureExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_DO],
        "SEC/DOJ/FTC investigation history; FCPA exposure; whistleblower complaints",
    ),
]


# =========================================================================
# EXPANSION FI SIGNALS (phase_7)
# =========================================================================

_FI_EXPANSION_SIGNALS: List[SignalMetadata] = [
    # -- Banking Risk --
    _sm(
        "capital_adequacy", "Capital Adequacy Ratio", "banking_risk",
        DIRECT_OBSERVABLE, _TTL_WEEKLY, ["CapitalAdequacyExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_FI],
        "Tier 1 capital ratio; leverage ratio; stress test results; CCAR compliance",
    ),
    _sm(
        "loan_portfolio_quality", "Loan Portfolio Quality", "banking_risk",
        DIRECT_OBSERVABLE, _TTL_WEEKLY, ["LoanPortfolioQualityExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_FI],
        "NPL ratio; charge-off rate; loan concentration by sector; CRE exposure",
    ),
    _sm(
        "regulatory_exam_results", "Regulatory Examination Results", "banking_risk",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["RegulatoryExamResultsExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_FI],
        "CAMELS rating proxy; MRA/MRIA findings; consent orders; cease-and-desist actions",
    ),
    _sm(
        "bsa_aml_compliance", "BSA/AML Compliance", "banking_risk",
        INFERRED_PROXY, _TTL_MONTHLY, ["BsaAmlComplianceExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_FI],
        "Bank Secrecy Act compliance; SAR filing quality; KYC programme maturity; sanctions screening",
    ),
    _sm(
        "interest_rate_sensitivity", "Interest Rate Sensitivity", "banking_risk",
        INFERRED_PROXY, _TTL_WEEKLY, ["InterestRateSensitivityExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_FI],
        "Asset-liability duration mismatch; unrealised losses in HTM portfolio; NIM volatility",
    ),
    # -- Fintech & Digital Risk --
    _sm(
        "regulatory_licensing_status", "Regulatory Licensing Status", "fintech_risk",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["RegulatoryLicensingStatusExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_FI],
        "Money transmitter licences; broker-dealer registration; state-by-state compliance",
    ),
    _sm(
        "crypto_asset_exposure", "Crypto/Digital Asset Exposure", "fintech_risk",
        INFERRED_PROXY, _TTL_WEEKLY, ["CryptoAssetExposureExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_FI],
        "Cryptocurrency custody; DeFi protocol exposure; stablecoin reserves; exchange risk",
    ),
    _sm(
        "platform_technology_risk", "Platform Technology Risk", "fintech_risk",
        INFERRED_PROXY, _TTL_WEEKLY, ["PlatformTechnologyRiskExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_FI],
        "Platform uptime; smart contract audit status; API security; third-party dependency",
    ),
    _sm(
        "consumer_protection_compliance", "Consumer Protection Compliance", "fintech_risk",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["ConsumerProtectionComplianceExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_FI],
        "CFPB/FCA complaint rates; fair lending compliance; UDAAP risk; disclosure quality",
    ),
    _sm(
        "partner_bank_dependency", "Partner Bank / BaaS Dependency", "fintech_risk",
        INFERRED_PROXY, _TTL_MONTHLY, ["PartnerBankDependencyExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_FI],
        "Banking-as-a-Service dependency; partner bank concentration; regulatory through risk",
    ),
]


# =========================================================================
# NEW FPR SIGNALS (phase_8)
# =========================================================================

_FPR_SIGNALS: List[SignalMetadata] = [
    # -- Trade Credit Risk --
    _sm(
        "buyer_creditworthiness", "Buyer Creditworthiness", "trade_credit_risk",
        DIRECT_OBSERVABLE, _TTL_WEEKLY, ["BuyerCreditworthinessExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_FPR],
        "Buyer credit rating, financial stability, payment history, industry sector health",
    ),
    _sm(
        "payment_terms_exposure", "Payment Terms Exposure", "trade_credit_risk",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["PaymentTermsExposureExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_FPR],
        "Average payment terms (days); extended terms increase exposure duration and default probability",
    ),
    _sm(
        "buyer_concentration", "Buyer Concentration", "trade_credit_risk",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["BuyerConcentrationExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_FPR],
        "Top 10 buyer share of insured turnover; single-buyer maximum exposure",
    ),
    _sm(
        "country_risk_exposure", "Country Risk Exposure", "trade_credit_risk",
        INFERRED_PROXY, _TTL_WEEKLY, ["CountryRiskExposureExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_FPR],
        "Buyer domicile country risk; currency transfer risk; sovereign default proximity",
    ),
    _sm(
        "trade_dispute_frequency", "Trade Dispute Frequency", "trade_credit_risk",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["TradeDisputeFrequencyExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_FPR],
        "Historical frequency of trade disputes, set-offs, quality claims by buyers",
    ),
    _sm(
        "sector_cyclicality", "Sector Cyclicality", "trade_credit_risk",
        COHORT_INFERENCE, _TTL_MONTHLY, ["SectorCyclicalityExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_FPR],
        "Insured's industry sector vulnerability to economic downturns; commodity price sensitivity",
    ),
    # -- Political Risk --
    _sm(
        "sovereign_risk_rating", "Sovereign Risk Rating", "political_risk",
        DIRECT_OBSERVABLE, _TTL_WEEKLY, ["SovereignRiskRatingExtractor"],
        OUTPUT_CATEGORY, None, [COVERAGE_FPR],
        "Country sovereign risk classification; political stability index; governance indicators",
    ),
    _sm(
        "expropriation_risk", "Expropriation & Nationalisation Risk", "political_risk",
        INFERRED_PROXY, _TTL_MONTHLY, ["ExpropriationRiskExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_FPR],
        "History of expropriation; nationalisation trends; creeping expropriation indicators",
    ),
    _sm(
        "currency_inconvertibility", "Currency Inconvertibility & Transfer Risk", "political_risk",
        INFERRED_PROXY, _TTL_WEEKLY, ["CurrencyInconvertibilityExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_FPR],
        "FX controls; capital account restrictions; central bank reserve adequacy",
    ),
    _sm(
        "contract_frustration", "Contract Frustration Risk", "political_risk",
        INFERRED_PROXY, _TTL_MONTHLY, ["ContractFrustrationExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_FPR],
        "Government contract cancellation; licence revocation; regulatory change risk",
    ),
    _sm(
        "political_violence_exposure", "Political Violence Exposure", "political_risk",
        INFERRED_PROXY, _TTL_WEEKLY, ["PoliticalViolenceExposureExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_FPR],
        "Civil unrest frequency; terrorism threat level; armed conflict proximity; coup risk",
    ),
    # -- Surety & Bond Risk --
    _sm(
        "principal_financial_strength", "Principal Financial Strength", "surety_risk",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["PrincipalFinancialStrengthExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_FPR],
        "Contractor/principal financial ratios; working capital; debt-to-equity; liquidity",
    ),
    _sm(
        "project_execution_track_record", "Project Execution Track Record", "surety_risk",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["ProjectExecutionTrackRecordExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_FPR],
        "On-time/on-budget delivery history; completed project count; scope creep frequency",
    ),
    _sm(
        "backlog_to_capacity", "Backlog-to-Capacity Ratio", "surety_risk",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["BacklogToCapacityExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_FPR],
        "Work-in-progress relative to bonding capacity; over-extension risk",
    ),
    _sm(
        "bond_default_history", "Bond Default & Claim History", "surety_risk",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["BondDefaultHistoryExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_FPR],
        "Prior surety claims; performance bond calls; completion guarantor involvement",
    ),
    _sm(
        "obligee_complexity", "Obligee & Contract Complexity", "surety_risk",
        INFERRED_PROXY, _TTL_MONTHLY, ["ObligeeComplexityExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_FPR],
        "Government vs private obligee; contract terms; liquidated damages provisions",
    ),
    # -- Kidnap & Ransom Risk --
    _sm(
        "travel_exposure_profile", "Travel Exposure Profile", "kidnap_ransom_risk",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["TravelExposureProfileExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_FPR],
        "Volume and frequency of employee travel to high-risk jurisdictions",
    ),
    _sm(
        "country_threat_level", "Country Threat Level", "kidnap_ransom_risk",
        INFERRED_PROXY, _TTL_WEEKLY, ["CountryThreatLevelExtractor"],
        OUTPUT_CATEGORY, None, [COVERAGE_FPR],
        "Destination-specific kidnap/extortion threat; crime index; express kidnap frequency",
    ),
    _sm(
        "executive_protection", "Executive Protection Measures", "kidnap_ransom_risk",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["ExecutiveProtectionExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_FPR],
        "Close protection; secure transportation; safe houses; journey management plans",
    ),
    _sm(
        "crisis_response_capability", "Crisis Response Capability", "kidnap_ransom_risk",
        INFERRED_PROXY, _TTL_MONTHLY, ["CrisisResponseCapabilityExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_FPR],
        "Retained crisis response consultant; crisis management plan; communication protocols",
    ),
    _sm(
        "expatriate_population", "Expatriate Population", "kidnap_ransom_risk",
        DIRECT_OBSERVABLE, _TTL_MONTHLY, ["ExpatriatePopulationExtractor"],
        OUTPUT_SCORE, _SCORE_RANGE, [COVERAGE_FPR],
        "Number of expatriate employees; dependency ratio; family members in high-risk locations",
    ),
]



SIGNAL_METADATA_REGISTRY.register_many(_PROPERTY_SIGNALS)
SIGNAL_METADATA_REGISTRY.register_many(_MARINE_EXPANSION_SIGNALS)
SIGNAL_METADATA_REGISTRY.register_many(_CASUALTY_SIGNALS)
SIGNAL_METADATA_REGISTRY.register_many(_AEROSPACE_EXPANSION_SIGNALS)
SIGNAL_METADATA_REGISTRY.register_many(_DO_EXPANSION_SIGNALS)
SIGNAL_METADATA_REGISTRY.register_many(_FI_EXPANSION_SIGNALS)
SIGNAL_METADATA_REGISTRY.register_many(_FPR_SIGNALS)
