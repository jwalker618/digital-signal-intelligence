"""
DSI Comprehensive Project Assessor
==================================
Evaluates the Python codebase, API infrastructure, and mathematical
validity of YAML configurations against project_completeness_checklist.md.

This assessor covers:
- Infrastructure file existence (API, DB, Builder, Analytics, Integrations)
- Three-layer engine components
- Coverage configuration validation
- Actuarial math validation
- Schema compliance
- Signal architecture validation
- Tests infrastructure validation
- Deploy (Docker, Kubernetes, CI/CD, Monitoring)
- Rust accelerators
- Data persistence and continuous monitoring
- Phase 8 deterministic referral architecture
"""

import os
import yaml
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict


class DSIProjectAssessor:
    def __init__(self, project_root: str = "."):
        self.root = Path(project_root)
        self.scores = {
            "infrastructure": {"pass": 0, "total": 0, "gaps": []},
            "layers": {"pass": 0, "total": 0, "gaps": []},
            "tests": {"pass": 0, "total": 0, "gaps": []},
            "deploy": {"pass": 0, "total": 0, "gaps": []},
            "docs": {"pass": 0, "total": 0, "gaps": []},
            "rust": {"pass": 0, "total": 0, "gaps": []},
            "schemas": {"pass": 0, "total": 0, "gaps": []},
            "signal_arch_files": {"pass": 0, "total": 0, "gaps": []},
            "extractors": {"pass": 0, "total": 0, "gaps": []},
            "data_persistence": {"pass": 0, "total": 0, "gaps": []},
            "coverages": {"pass": 0, "total": 0, "gaps": []},
            "schema_compliance": {"pass": 0, "total": 0, "gaps": []},
            "signal_architecture": {"pass": 0, "total": 0, "gaps": []},
            "actuarial_math": {"pass": 0, "total": 0, "gaps": []},
        }

    def _assert(self, category: str, condition: bool, gap_message: str):
        """Record a check result."""
        self.scores[category]["total"] += 1
        if condition:
            self.scores[category]["pass"] += 1
        else:
            self.scores[category]["gaps"].append(gap_message)

    # =========================================================================
    # INFRASTRUCTURE CHECKS (Expanded per checklist)
    # =========================================================================

    def check_infrastructure(self):
        """Check core infrastructure files exist."""
        cat = "infrastructure"

        # -----------------------------------------------------------------
        # API (`infrastructure/api/`)
        # -----------------------------------------------------------------
        self._assert(cat, (self.root / "infrastructure/api/main.py").exists(),
                     "API main.py missing (infrastructure/api/)")
        self._assert(cat, (self.root / "infrastructure/api/routes").exists(),
                     "API routes directory missing (infrastructure/api/routes/)")

        # API route files
        routes_dir = self.root / "infrastructure/api/routes"
        if routes_dir.exists():
            self._assert(cat, (routes_dir / "submissions.py").exists(),
                         "API route submissions.py missing")
            self._assert(cat, (routes_dir / "quotes.py").exists(),
                         "API route quotes.py missing")
            self._assert(cat, (routes_dir / "referrals.py").exists(),
                         "API route referrals.py missing")
            self._assert(cat, (routes_dir / "analytics.py").exists(),
                         "API route analytics.py missing")

        # Auth
        self._assert(cat, (self.root / "infrastructure/api/auth").exists(),
                     "API auth directory missing (infrastructure/api/auth/)")

        # -----------------------------------------------------------------
        # Database (`infrastructure/db/`)
        # -----------------------------------------------------------------
        self._assert(cat, (self.root / "infrastructure/db/models.py").exists(),
                     "Database models missing (infrastructure/db/models.py)")
        self._assert(cat, (self.root / "infrastructure/db/repositories.py").exists(),
                     "Database repositories missing (infrastructure/db/repositories.py)")
        self._assert(cat, (self.root / "infrastructure/db/config.py").exists(),
                     "Database config missing (infrastructure/db/config.py)")

        # Alembic migrations
        self._assert(cat, (self.root / "alembic").exists() or
                     (self.root / "infrastructure/db/migrations").exists(),
                     "Alembic migrations directory missing")

        # -----------------------------------------------------------------
        # Analytics (`infrastructure/analytics/`)
        # -----------------------------------------------------------------
        analytics_dir = self.root / "infrastructure/analytics"
        self._assert(cat, analytics_dir.exists(),
                     "Analytics directory missing (infrastructure/analytics/)")
        if analytics_dir.exists():
            self._assert(cat, (analytics_dir / "performance.py").exists() or
                         len(list(analytics_dir.glob("*.py"))) > 1,
                         "Performance metrics module missing (infrastructure/analytics/)")
            self._assert(cat, (analytics_dir / "portfolio.py").exists() or
                         any("portfolio" in f.name for f in analytics_dir.glob("*.py")),
                         "Portfolio analytics module missing")

        # -----------------------------------------------------------------
        # Builder (`infrastructure/builder/`)
        # -----------------------------------------------------------------
        builder_dir = self.root / "infrastructure/builder"
        self._assert(cat, builder_dir.exists(),
                     "Coverage builder missing (infrastructure/builder/)")
        if builder_dir.exists():
            self._assert(cat, (builder_dir / "coverage_builder.py").exists(),
                         "coverage_builder.py missing")
            self._assert(cat, (builder_dir / "validator.py").exists(),
                         "builder validator.py missing")
            self._assert(cat, (builder_dir / "signal_library.py").exists(),
                         "signal_library.py missing")
            self._assert(cat, (builder_dir / "types.py").exists(),
                         "builder types.py missing")

        # -----------------------------------------------------------------
        # Validation (`infrastructure/validation/`)
        # -----------------------------------------------------------------
        self._assert(cat, (self.root / "infrastructure/validation/config_validator.py").exists(),
                     "config_validator.py missing (infrastructure/validation/)")

        # -----------------------------------------------------------------
        # Integrations (`infrastructure/integrations/`)
        # -----------------------------------------------------------------
        integrations_dir = self.root / "infrastructure/integrations"
        self._assert(cat, integrations_dir.exists(),
                     "Integrations directory missing (infrastructure/integrations/)")

        # -----------------------------------------------------------------
        # Multiplexer & Arbiter (in signal_architecture/)
        # -----------------------------------------------------------------
        self._assert(cat, (self.root / "signal_architecture/multiplexer/arbiter.py").exists(),
                     "ConfigArbiter missing (signal_architecture/multiplexer/arbiter.py)")
        self._assert(cat, (self.root / "signal_architecture/multiplexer/broker.py").exists(),
                     "SignalBroker missing (signal_architecture/multiplexer/broker.py)")

    def check_layers(self):
        """Check three-layer engine components exist."""
        cat = "layers"

        # Risk layer
        risk_dir = self.root / "layers/risk"
        self._assert(cat, (risk_dir / "scorer.py").exists(),
                     "Risk scorer missing (layers/risk/scorer.py)")
        self._assert(cat, (risk_dir / "workflow.py").exists(),
                     "Risk workflow missing (layers/risk/workflow.py)")
        self._assert(cat, (risk_dir / "pricer.py").exists(),
                     "Risk pricer missing (layers/risk/pricer.py)")
        self._assert(cat, (risk_dir / "config_manager.py").exists(),
                     "Config manager missing (layers/risk/config_manager.py)")
        self._assert(cat, (risk_dir / "query_evaluator.py").exists(),
                     "Query evaluator missing (layers/risk/query_evaluator.py)")
        self._assert(cat, (risk_dir / "model_data.py").exists(),
                     "Model data missing (layers/risk/model_data.py)")
        self._assert(cat, (risk_dir / "types.py").exists(),
                     "Risk types missing (layers/risk/types.py)")
        self._assert(cat, (risk_dir / "modifiers").exists(),
                     "Traditional modifiers directory missing (layers/risk/modifiers/)")

        # Loss layer
        loss_dir = self.root / "layers/loss"
        self._assert(cat, (loss_dir / "scorer.py").exists(),
                     "Loss scorer missing (layers/loss/scorer.py)")
        self._assert(cat, (loss_dir / "matrix.py").exists() or
                     (loss_dir / "correlation.py").exists(),
                     "Loss correlation matrix missing (layers/loss/)")
        self._assert(cat, (loss_dir / "config_adapter.py").exists(),
                     "Loss config adapter missing (layers/loss/config_adapter.py)")

        # Exposure layer
        exposure_dir = self.root / "layers/exposure"
        self._assert(cat, (exposure_dir / "scorer.py").exists(),
                     "Exposure scorer missing (layers/exposure/scorer.py)")

    # =========================================================================
    # TESTS CHECKS (New section per checklist)
    # =========================================================================

    def check_tests(self):
        """Check test infrastructure and organization."""
        cat = "tests"

        tests_dir = self.root / "tests"
        self._assert(cat, tests_dir.exists(),
                     "tests/ directory missing")

        if not tests_dir.exists():
            return

        # Core test infrastructure
        self._assert(cat, (tests_dir / "conftest.py").exists(),
                     "tests/conftest.py missing (shared fixtures)")
        self._assert(cat, (tests_dir / "README.md").exists(),
                     "tests/README.md missing (test documentation)")

        # Organization by type
        self._assert(cat, (tests_dir / "unit").exists(),
                     "tests/unit/ directory missing")
        self._assert(cat, (tests_dir / "integration").exists(),
                     "tests/integration/ directory missing")
        self._assert(cat, (tests_dir / "api").exists(),
                     "tests/api/ directory missing")
        self._assert(cat, (tests_dir / "performance").exists(),
                     "tests/performance/ directory missing")

        # Count test files by category
        self.test_stats = {
            'unit': 0, 'integration': 0, 'api': 0, 'performance': 0, 'total': 0
        }

        for category in ['unit', 'integration', 'api', 'performance']:
            cat_dir = tests_dir / category
            if cat_dir.exists():
                count = len(list(cat_dir.glob("test_*.py")))
                self.test_stats[category] = count
                self.test_stats['total'] += count

        # Minimum test coverage checks
        self._assert(cat, self.test_stats['unit'] >= 10,
                     f"Insufficient unit tests ({self.test_stats['unit']} < 10 minimum)")
        self._assert(cat, self.test_stats['integration'] >= 2,
                     f"Insufficient integration tests ({self.test_stats['integration']} < 2 minimum)")
        self._assert(cat, self.test_stats['api'] >= 1,
                     f"No API tests found")
        self._assert(cat, self.test_stats['performance'] >= 1,
                     f"No performance benchmarks found")

        # Critical test files exist
        unit_dir = tests_dir / "unit"
        if unit_dir.exists():
            critical_tests = [
                'test_workflow.py', 'test_scorer.py', 'test_pricer.py',
                'test_config_validator.py', 'test_builder.py'
            ]
            for test_file in critical_tests:
                self._assert(cat, (unit_dir / test_file).exists(),
                             f"Critical test file missing: tests/unit/{test_file}")

    # =========================================================================
    # DEPLOY CHECKS (Expanded per checklist)
    # =========================================================================

    def check_deploy(self):
        """Check deployment configuration files exist."""
        cat = "deploy"

        # -----------------------------------------------------------------
        # Docker
        # -----------------------------------------------------------------
        # Check multiple possible locations for Dockerfile
        dockerfile_exists = (
            (self.root / "Dockerfile").exists() or
            (self.root / "deploy/docker/Dockerfile").exists()
        )
        self._assert(cat, dockerfile_exists,
                     "Dockerfile missing (Dockerfile or deploy/docker/Dockerfile)")

        compose_exists = (
            (self.root / "docker-compose.yml").exists() or
            (self.root / "deploy/docker/docker-compose.yml").exists()
        )
        self._assert(cat, compose_exists,
                     "docker-compose.yml missing")

        self._assert(cat, (self.root / "deploy/docker/docker-compose.prod.yml").exists(),
                     "docker-compose.prod.yml missing (deploy/docker/)")

        # -----------------------------------------------------------------
        # Kubernetes
        # -----------------------------------------------------------------
        k8s_dir = self.root / "deploy/kubernetes"
        self._assert(cat, k8s_dir.exists(),
                     "Kubernetes manifests directory missing (deploy/kubernetes/)")

        if k8s_dir.exists():
            k8s_files = [
                ('deployment.yaml', 'Deployment manifest'),
                ('service.yaml', 'Service manifest'),
                ('ingress.yaml', 'Ingress manifest'),
                ('configmap.yaml', 'ConfigMap manifest'),
                ('secrets-template.yaml', 'Secrets template'),
                ('namespace.yaml', 'Namespace manifest'),
                ('kustomization.yaml', 'Kustomization file'),
            ]
            for fname, desc in k8s_files:
                self._assert(cat, (k8s_dir / fname).exists(),
                             f"Kubernetes {desc} missing ({fname})")

            # HPA is optional but recommended
            if (k8s_dir / "hpa.yaml").exists():
                self.scores[cat]["pass"] += 1
                self.scores[cat]["total"] += 1
            else:
                self._assert(cat, False, "HPA manifest recommended but missing (hpa.yaml)")

        # -----------------------------------------------------------------
        # Monitoring
        # -----------------------------------------------------------------
        monitoring_dir = self.root / "deploy/monitoring"
        self._assert(cat, monitoring_dir.exists(),
                     "Monitoring directory missing (deploy/monitoring/)")
        if monitoring_dir.exists():
            self._assert(cat, (monitoring_dir / "prometheus-config.yaml").exists(),
                         "Prometheus config missing (deploy/monitoring/prometheus-config.yaml)")

        # -----------------------------------------------------------------
        # CI/CD
        # -----------------------------------------------------------------
        cicd_exists = (
            (self.root / ".github/workflows").exists() or
            (self.root / ".gitlab-ci.yml").exists()
        )
        self._assert(cat, cicd_exists,
                     "CI/CD configuration missing (.github/workflows/ or .gitlab-ci.yml)")

        # Check for specific workflow stages if GitHub Actions
        workflows_dir = self.root / ".github/workflows"
        if workflows_dir.exists():
            workflow_files = list(workflows_dir.glob("*.yml")) + list(workflows_dir.glob("*.yaml"))
            self._assert(cat, len(workflow_files) >= 1,
                         "No CI/CD workflow files found in .github/workflows/")

    # =========================================================================
    # DOCS CHECKS (Expanded per checklist)
    # =========================================================================

    def check_docs(self):
        """Check core documentation files exist."""
        cat = "docs"

        # Core documents (check multiple possible locations/formats)
        whitepaper_exists = (
            (self.root / "docs/DSI_Whitepaper.md").exists() or
            (self.root / "docs/overview/Whitepaper_Digital_Signal_Intelligence.pdf").exists()
        )
        self._assert(cat, whitepaper_exists,
                     "DSI Whitepaper missing")

        vision_paper_exists = (
            (self.root / "docs/DSI_Vision_Paper.md").exists() or
            (self.root / "docs/overview/Visionpaper_Digital_Signal_Intelligence.pdf").exists()
        )
        self._assert(cat, vision_paper_exists,
                     "DSI Vision Paper missing")

        pricing_methodology_exists = (
            (self.root / "docs/DSI_Pricing_Methodology.md").exists() or
            (self.root / "docs/overview/Premium_Calculation_Methodology.md").exists()
        )
        self._assert(cat, pricing_methodology_exists,
                     "Premium Calculation Methodology missing")

        # Referral methodology (Phase 8)
        referral_exists = (
            (self.root / "docs/overview/Referral_Methodology.md").exists() or
            (self.root / "docs/Referral_Methodology.md").exists()
        )
        self._assert(cat, referral_exists,
                     "Referral Methodology missing (Phase 8)")

        # Configuration architecture
        self._assert(cat, (self.root / "docs/overview/Configuration_Architecture.md").exists(),
                     "Configuration Architecture documentation missing")

        # Foundational principles
        foundational_exists = (
            (self.root / "docs/overview/Foundational Principles.md").exists() or
            (self.root / "docs/overview/Foundational_Principles.md").exists()
        )
        self._assert(cat, foundational_exists,
                     "Foundational Principles document missing")

        # API documentation
        self._assert(cat, (self.root / "docs/api").exists(),
                     "API documentation directory missing (docs/api/)")

        # Agent interaction spec
        self._assert(cat, (self.root / "docs/agent_interaction/dsi_specification.md").exists(),
                     "Agent interaction specification missing")

        # Project root docs
        self._assert(cat, (self.root / "README.md").exists(),
                     "README.md missing at project root")
        self._assert(cat, (self.root / "SKILL.md").exists(),
                     "SKILL.md missing (development guide)")

    # =========================================================================
    # RUST CHECKS (Expanded per checklist)
    # =========================================================================

    def check_rust(self):
        """Check Rust performance layer files exist."""
        cat = "rust"

        rust_dir = self.root / "rust"
        dsi_core_dir = rust_dir / "dsi-core" if (rust_dir / "dsi-core").exists() else rust_dir

        # Cargo project
        cargo_exists = (
            (rust_dir / "Cargo.toml").exists() or
            (dsi_core_dir / "Cargo.toml").exists()
        )
        self._assert(cat, cargo_exists,
                     "Cargo.toml missing (rust/Cargo.toml or rust/dsi-core/Cargo.toml)")

        # Core source directory
        src_dir = dsi_core_dir / "src" if (dsi_core_dir / "src").exists() else rust_dir / "src"

        # Core modules
        self._assert(cat, (src_dir / "lib.rs").exists(),
                     "Rust lib.rs missing")
        self._assert(cat, (src_dir / "graph.rs").exists(),
                     "Rust graph.rs missing (PageRank, risk propagation)")
        self._assert(cat, (src_dir / "derivatives.rs").exists(),
                     "Rust derivatives.rs missing (entropy, velocity, drift)")

        # Validation module (optional but recommended)
        validation_exists = (src_dir / "validation.rs").exists()
        if validation_exists:
            self.scores[cat]["pass"] += 1
            self.scores[cat]["total"] += 1
        else:
            self._assert(cat, False, "Rust validation.rs recommended but missing")

        # PyO3 bindings
        bindings_exists = (
            (src_dir / "bindings.rs").exists() or
            (src_dir / "python.rs").exists() or
            (src_dir / "lib.rs").exists()  # Bindings often in lib.rs
        )
        self._assert(cat, bindings_exists,
                     "PyO3 bindings missing (rust/src/bindings.rs or python.rs)")

        # Benchmarks
        benches_dir = dsi_core_dir / "benches"
        self._assert(cat, benches_dir.exists() and len(list(benches_dir.glob("*.rs"))) > 0,
                     "Criterion benchmarks missing (rust/dsi-core/benches/)")

    # =========================================================================
    # SCHEMAS CHECKS
    # =========================================================================

    def check_schemas(self):
        """Check schema definition files exist."""
        cat = "schemas"

        self._assert(cat, (self.root / "schemas/organisational_graph.yaml").exists(),
                     "organisational_graph.yaml missing (schemas/)")
        self._assert(cat, (self.root / "schemas/master_config_layout.yaml").exists() or
                     (self.root / "coverages/master_config_layout.yaml").exists(),
                     "master_config_layout.yaml missing")

    # =========================================================================
    # SIGNAL ARCHITECTURE FILES CHECKS
    # =========================================================================

    def check_signal_arch_files(self):
        """Check signal architecture component files exist."""
        cat = "signal_arch_files"

        signal_arch = self.root / "signal_architecture"

        # Extractors
        extractors_exist = (
            (signal_arch / "extractors").exists() or
            (signal_arch / "signals/extractors").exists()
        )
        self._assert(cat, extractors_exist,
                     "Extractors directory missing")

        # Aggregators
        aggregators_exist = (
            (signal_arch / "aggregators").exists() or
            (signal_arch / "signals/aggregators").exists()
        )
        self._assert(cat, aggregators_exist,
                     "Aggregators directory missing")

        # Categorizers
        categorizers_exist = (
            (signal_arch / "categorizers").exists() or
            (signal_arch / "signals/categorisers").exists() or
            (signal_arch / "signals/categorizers").exists()
        )
        self._assert(cat, categorizers_exist,
                     "Categorizers directory missing")

        # Inference registry
        inference_exists = (
            (signal_arch / "inference_utilities").exists() or
            (signal_arch / "signals/inference").exists()
        )
        self._assert(cat, inference_exists,
                     "Inference utilities missing")

        # Discovery engine
        self._assert(cat, (signal_arch / "discovery").exists(),
                     "Discovery engine missing (signal_architecture/discovery/)")

        # Graph
        self._assert(cat, (signal_arch / "graph").exists(),
                     "Graph types directory missing (signal_architecture/graph/)")

        # Graph sub-components
        graph_dir = signal_arch / "graph"
        if graph_dir.exists():
            self._assert(cat, (graph_dir / "types.py").exists(),
                         "Graph types.py missing")
            self._assert(cat, (graph_dir / "node_factory.py").exists(),
                         "Graph node_factory.py missing")
            self._assert(cat, (graph_dir / "edge_inferencer.py").exists(),
                         "Graph edge_inferencer.py missing")
            self._assert(cat, (graph_dir / "graph_builder.py").exists(),
                         "Graph graph_builder.py missing")

            # Derivatives
            derivatives_exist = (
                (graph_dir / "derivatives").exists() or
                (graph_dir / "derivatives.py").exists()
            )
            self._assert(cat, derivatives_exist,
                         "Graph derivatives module missing")

        # Orchestration
        self._assert(cat, (signal_arch / "orchestration").exists(),
                     "Orchestration directory missing")

        # Multiplexer
        self._assert(cat, (signal_arch / "multiplexer").exists(),
                     "Multiplexer directory missing")

    # =========================================================================
    # EXTRACTOR COVERAGE CHECKS (Expanded and fixed)
    # =========================================================================

    def check_extractor_coverage(self):
        """Comprehensive signal extractor validation."""
        cat = "extractors"

        production_dir = self.root / "signal_architecture/signals/extractors/production"
        stubs_dir = self.root / "signal_architecture/signals/extractors/stubs"

        # Initialize extractor stats
        self.extractor_stats = {
            'production_count': 0,
            'stub_count': 0,
            'production_ratio': 0,
            'categories': {},
            'production_files': [],
            'stub_files': []
        }

        exclude_files = {'__init__.py', 'base.py', 'config.py', 'factory.py', 'common.py'}

        # Expected production extractor categories
        expected_categories = {
            'dns': ['email_auth', 'dnssec', 'dns_records', 'whois'],
            'http': ['security_headers', 'security_txt'],
            'network': ['cloud_infra', 'cdn', 'waf', 'tls'],
            'sec': ['filings', 'financials', 'governance', 'litigation'],
            'regulatory': ['ofac', 'epa', 'cfpb', 'osha', 'faa'],
            'sanctions': ['opensanctions', 'worldbank', 'interpol'],
            'security': ['nvd_cve', 'hhs_breach'],
            'corporate': ['companies_house', 'opencorporates', 'gleif'],
        }

        # Count production extractors by category
        if production_dir.exists():
            for category_dir in production_dir.iterdir():
                if category_dir.is_dir():
                    cat_name = category_dir.name
                    cat_count = 0
                    for f in category_dir.glob("*.py"):
                        if f.name not in exclude_files:
                            cat_count += 1
                            self.extractor_stats['production_files'].append(
                                f"{cat_name}/{f.name}"
                            )
                    self.extractor_stats['categories'][cat_name] = cat_count
                    self.extractor_stats['production_count'] += cat_count

            # Also count top-level production files
            for f in production_dir.glob("*.py"):
                if f.name not in exclude_files:
                    self.extractor_stats['production_count'] += 1
                    self.extractor_stats['production_files'].append(f.name)

        # Count stub extractors
        if stubs_dir.exists():
            for f in stubs_dir.rglob("*.py"):
                if f.name not in exclude_files:
                    self.extractor_stats['stub_count'] += 1
                    try:
                        rel_path = f.relative_to(stubs_dir)
                        self.extractor_stats['stub_files'].append(str(rel_path))
                    except ValueError:
                        self.extractor_stats['stub_files'].append(f.name)

        # Calculate ratio
        total = self.extractor_stats['production_count'] + self.extractor_stats['stub_count']
        if total > 0:
            self.extractor_stats['production_ratio'] = round(
                self.extractor_stats['production_count'] / total * 100, 1
            )

        # -----------------------------------------------------------------
        # Assertions
        # -----------------------------------------------------------------

        # Production extractor minimum (at least 40 production extractors)
        self._assert(cat, self.extractor_stats['production_count'] >= 40,
                     f"Insufficient production extractors ({self.extractor_stats['production_count']} < 40)")

        # Production ratio (at least 50%)
        self._assert(cat, self.extractor_stats['production_ratio'] >= 50,
                     f"Production ratio too low ({self.extractor_stats['production_ratio']}% < 50%)")

        # Category coverage checks
        for category, expected_signals in expected_categories.items():
            actual_count = self.extractor_stats['categories'].get(category, 0)
            min_expected = len(expected_signals) // 2 + 1  # At least half
            self._assert(cat, actual_count >= min_expected,
                         f"Category '{category}' has {actual_count} extractors (expected {min_expected}+)")

        # Check for specific critical extractors
        critical_extractors = [
            'dns', 'http', 'corporate', 'regulatory', 'security'
        ]
        for crit_cat in critical_extractors:
            self._assert(cat, self.extractor_stats['categories'].get(crit_cat, 0) > 0,
                         f"Critical extractor category '{crit_cat}' has no production extractors")

        # Stub coverage (at least one stub per coverage domain)
        expected_stub_domains = ['aerospace', 'cyber', 'do', 'energy', 'fi', 'marine', 'pi']
        for domain in expected_stub_domains:
            domain_stubs = [s for s in self.extractor_stats['stub_files'] if domain in s.lower()]
            self._assert(cat, len(domain_stubs) > 0,
                         f"No stub extractors for coverage domain '{domain}'")

    # =========================================================================
    # DATA PERSISTENCE & CONTINUOUS MONITORING CHECKS (New)
    # =========================================================================

    def check_data_persistence(self):
        """Check data persistence model for continuous monitoring support."""
        cat = "data_persistence"

        # -----------------------------------------------------------------
        # Database Models
        # -----------------------------------------------------------------
        models_path = self.root / "infrastructure/db/models.py"
        if models_path.exists():
            with open(models_path, 'r') as f:
                models_content = f.read()

            # Check for required tables/models
            required_models = [
                ('SignalCache', 'Time-series signal cache'),
                ('AuditLog', 'Audit trail'),
                ('Submission', 'Submission records'),
                ('Quote', 'Quote records'),
                ('ModelVersionRecord', 'Model version tracking'),
            ]
            for model_name, desc in required_models:
                self._assert(cat, f"class {model_name}" in models_content,
                             f"Database model '{model_name}' missing ({desc})")

            # Check for TTL support in SignalCache
            self._assert(cat, 'ttl' in models_content.lower() or 'expires' in models_content.lower(),
                         "SignalCache missing TTL/expiration support")

            # Check for timestamp tracking
            self._assert(cat, 'extracted_at' in models_content or 'created_at' in models_content,
                         "Missing timestamp tracking in signal storage")

        else:
            self._assert(cat, False, "Database models.py not found")

        # -----------------------------------------------------------------
        # Repositories
        # -----------------------------------------------------------------
        repos_path = self.root / "infrastructure/db/repositories.py"
        if repos_path.exists():
            with open(repos_path, 'r') as f:
                repos_content = f.read()

            required_repos = [
                ('SignalCacheRepository', 'Signal cache operations'),
                ('AuditLogRepository', 'Audit log operations'),
                ('SubmissionRepository', 'Submission CRUD'),
            ]
            for repo_name, desc in required_repos:
                self._assert(cat, f"class {repo_name}" in repos_content,
                             f"Repository '{repo_name}' missing ({desc})")

            # Check for cache operations
            self._assert(cat, 'get_valid_cache' in repos_content or 'get_cached' in repos_content,
                         "SignalCache repository missing TTL-aware get method")
            self._assert(cat, 'cleanup' in repos_content or 'expire' in repos_content,
                         "SignalCache repository missing cleanup/expiration method")

        else:
            self._assert(cat, False, "Database repositories.py not found")

        # -----------------------------------------------------------------
        # Phase 8: Signal Audit Trail Support
        # -----------------------------------------------------------------
        # Check for inferred_value / audited_value support
        if models_path.exists():
            with open(models_path, 'r') as f:
                models_content = f.read()

            # Phase 8 audit trail fields (can be in models or schema)
            phase8_fields = ['inferred_value', 'audited_value', 'is_overridden', 'audit_trail']
            phase8_support = any(field in models_content for field in phase8_fields)
            self._assert(cat, phase8_support,
                         "Phase 8 signal audit fields not found (inferred_value, audited_value)")

        # -----------------------------------------------------------------
        # Continuous Monitoring Support
        # -----------------------------------------------------------------
        # Check for refresh scheduling or TTL-based re-extraction
        signal_arch = self.root / "signal_architecture"

        # Check for monitoring/scheduling infrastructure
        monitoring_exists = (
            (signal_arch / "monitoring").exists() or
            (signal_arch / "scheduler").exists() or
            (signal_arch / "signals" / "refresh").exists()
        )

        # Also check in infrastructure
        infra_monitoring = (self.root / "infrastructure/monitoring").exists()

        self._assert(cat, monitoring_exists or infra_monitoring,
                     "Continuous monitoring infrastructure not found")

        # Check for derivative time-series tracking
        graph_dir = signal_arch / "graph"
        if graph_dir.exists():
            derivatives_dir = graph_dir / "derivatives"
            if derivatives_dir.exists():
                derivatives_files = list(derivatives_dir.glob("*.py"))
                self._assert(cat, len(derivatives_files) > 0,
                             "Derivative calculators not found")

                # Check for time-series tracking in derivatives
                for df in derivatives_files:
                    with open(df, 'r') as f:
                        content = f.read()
                    if 'time_series' in content or 'historical' in content or 'temporal' in content:
                        self.scores[cat]["pass"] += 1
                        self.scores[cat]["total"] += 1
                        break
                else:
                    self._assert(cat, False,
                                 "Derivatives missing time-series tracking (Vision Paper requirement)")

    # =========================================================================
    # COVERAGE CONFIGURATION CHECKS
    # =========================================================================

    def check_coverage_structure(self, cov_name: str, cov_path: Path, config: dict):
        """Check structural requirements for a coverage configuration."""
        cat = "coverages"

        # logic.md exists
        self._assert(cat, (cov_path / "logic.md").exists(),
                     f"[{cov_name}] logic.md missing (run doc_generator.py)")

        for config_name, cfg in config.items():
            if not isinstance(cfg, dict):
                continue

            prefix = f"[{cov_name}/{config_name}]"
            metadata = cfg.get('metadata', {})

            # Metadata completeness
            self._assert(cat, metadata.get('name'),
                         f"{prefix} metadata.name missing")
            self._assert(cat, metadata.get('version'),
                         f"{prefix} metadata.version missing")
            self._assert(cat, metadata.get('product_types'),
                         f"{prefix} metadata.product_types missing")
            self._assert(cat, metadata.get('minimum_viable_input'),
                         f"{prefix} metadata.minimum_viable_input missing")
            self._assert(cat, metadata.get('min_premium') is not None,
                         f"{prefix} metadata.min_premium missing")
            self._assert(cat, metadata.get('default_currency'),
                         f"{prefix} metadata.default_currency missing")

            # Phase V4: Model specificity and routing
            self._assert(cat, metadata.get('model_specificity') is not None,
                         f"{prefix} metadata.model_specificity missing (Phase V4)")
            self._assert(cat, 'routing_constraints' in metadata,
                         f"{prefix} metadata.routing_constraints not defined (Phase V4)")

            # Required sections exist
            required_sections = [
                'signal_registry', 'groups', 'risk_tier_bands',
                'loss_tier_bands', 'exposure', 'pricing'
            ]
            for section in required_sections:
                self._assert(cat, section in cfg,
                             f"{prefix} {section} section missing")

            # limit_configuration (Phase V5)
            self._assert(cat, 'limit_configuration' in cfg,
                         f"{prefix} limit_configuration missing (Phase V5)")

            # Direct queries constraint
            direct_queries = cfg.get('direct_queries', [])
            self._assert(cat, len(direct_queries) <= 10,
                         f"{prefix} Too many direct_queries ({len(direct_queries)} > 10)")

    # =========================================================================
    # SCHEMA COMPLIANCE CHECKS
    # =========================================================================

    def check_schema_compliance(self, cov_name: str, config_name: str, cfg: dict):
        """Check schema version and structural compliance."""
        cat = "schema_compliance"
        prefix = f"[{cov_name}/{config_name}]"

        # Schema version
        version = cfg.get('metadata', {}).get('version', '0.0.0')
        version_parts = version.split('.')
        try:
            major, minor = int(version_parts[0]), int(version_parts[1])
            self._assert(cat, major >= 2 and minor >= 2,
                         f"{prefix} Schema version {version} below 2.2.0")
        except (ValueError, IndexError):
            self._assert(cat, False, f"{prefix} Invalid version format: {version}")

        # Risk tier bands structure
        risk_bands = cfg.get('risk_tier_bands', {}).get('bands', [])
        self._assert(cat, len(risk_bands) == 5,
                     f"{prefix} risk_tier_bands must have exactly 5 bands (has {len(risk_bands)})")

        # Check tier bands cover 0-1000 range
        if risk_bands:
            min_score = min(b.get('interpretation', {}).get('bands', {}).get('min', 1000) for b in risk_bands)
            max_score = max(b.get('interpretation', {}).get('bands', {}).get('max', 0) for b in risk_bands)
            self._assert(cat, min_score == 0,
                         f"{prefix} risk_tier_bands min is {min_score}, should be 0")
            self._assert(cat, max_score >= 999,
                         f"{prefix} risk_tier_bands max is {max_score}, should cover 1000")

        # Loss tier bands have floor/cap
        loss_bands = cfg.get('loss_tier_bands', {})
        constraints = loss_bands.get('constraints', {})
        self._assert(cat, 'floor' in constraints and 'cap' in constraints,
                     f"{prefix} loss_tier_bands missing floor/cap constraints")

        # Exposure has size and complexity
        exposure = cfg.get('exposure', {})
        self._assert(cat, 'size' in exposure,
                     f"{prefix} exposure.size missing")
        self._assert(cat, 'complexity' in exposure,
                     f"{prefix} exposure.complexity missing")

        # Legacy fields removed (Phase 5 deprecation)
        legacy_fields = ['deductible_credits', 'deductible_buy_down_rates', 'limit_bandings']
        for field in legacy_fields:
            self._assert(cat, field not in cfg,
                         f"{prefix} Legacy field '{field}' present (Phase 5 deprecation)")

        # Query actions validation (FLAG | MODIFIER | REFER only, no DECLINE)
        direct_queries = cfg.get('direct_queries', [])
        for i, query in enumerate(direct_queries):
            conditions = query.get('query_condition', [])
            for cond in conditions:
                action = cond.get('action')
                if action:
                    self._assert(cat, action in ['FLAG', 'MODIFIER', 'REFER'],
                                 f"{prefix} direct_queries[{i}] has invalid action '{action}' (DECLINE is tier-level only)")

    # =========================================================================
    # SIGNAL ARCHITECTURE CHECKS
    # =========================================================================

    def check_signal_architecture(self, cov_name: str, config_name: str, cfg: dict):
        """Check signal registry structure and completeness."""
        cat = "signal_architecture"
        prefix = f"[{cov_name}/{config_name}]"

        signals = cfg.get('signal_registry', [])

        # Signal count
        self._assert(cat, len(signals) >= 15,
                     f"{prefix} Insufficient signals ({len(signals)} < 15 minimum)")

        # Signal ID uniqueness
        signal_ids = [s.get('id') for s in signals]
        unique_ids = set(signal_ids)
        self._assert(cat, len(signal_ids) == len(unique_ids),
                     f"{prefix} Duplicate signal IDs detected")

        # Proxy tier assignment
        valid_tiers = ['DIRECT_OBSERVABLE', 'INFERRED_PROXY', 'COHORT_INFERENCE']
        for sig in signals:
            sig_id = sig.get('id', 'unknown')
            proxy_tier = sig.get('proxy_tier')
            self._assert(cat, proxy_tier in valid_tiers,
                         f"{prefix} Signal '{sig_id}' has invalid proxy_tier: {proxy_tier}")

        # Inference function check
        for sig in signals:
            sig_id = sig.get('id', 'unknown')
            inf_func = sig.get('inference_utility_function')
            self._assert(cat, inf_func is not None,
                         f"{prefix} Signal '{sig_id}' missing inference_utility_function")

        # Group ID validation
        defined_groups = set()
        for g in cfg.get('groups', {}).get('three_layer_assessment', []):
            defined_groups.add(g.get('id'))
        for g in cfg.get('groups', {}).get('categories', []):
            defined_groups.add(g.get('id'))

        for sig in signals:
            sig_id = sig.get('id', 'unknown')
            # Check three_layer_assessment group
            tla = sig.get('three_layer_assessment', {})
            if tla:
                group_id = tla.get('group_id')
                if group_id:
                    self._assert(cat, group_id in defined_groups,
                                 f"{prefix} Signal '{sig_id}' references undefined group '{group_id}'")
            # Check categories group
            cats = sig.get('categories', {})
            if cats:
                group_id = cats.get('group_id')
                if group_id:
                    self._assert(cat, group_id in defined_groups,
                                 f"{prefix} Signal '{sig_id}' references undefined category group '{group_id}'")

        # Three-layer completeness (risk, loss, exposure)
        for sig in signals:
            sig_id = sig.get('id', 'unknown')
            tla = sig.get('three_layer_assessment', {})
            if tla and not sig.get('categories'):  # Only for TLA signals
                self._assert(cat, 'risk' in tla,
                             f"{prefix} Signal '{sig_id}' missing risk dimension")
                # Loss and exposure are recommended but not always required

    # =========================================================================
    # ACTUARIAL MATH CHECKS
    # =========================================================================

    def check_actuarial_math(self, cov_name: str, config_name: str, cfg: dict):
        """Check actuarial constraints and pricing logic."""
        cat = "actuarial_math"
        prefix = f"[{cov_name}/{config_name}]"

        # ---------------------------------------------------------------------
        # 1. Weights sum to 1.0 across groups (per layer)
        # ---------------------------------------------------------------------
        groups = cfg.get('groups', {}).get('three_layer_assessment', [])
        totals = {'risk': 0.0, 'loss': 0.0, 'exposure': 0.0}

        for g in groups:
            totals['risk'] += g.get('risk', {}).get('weight', 0)
            totals['loss'] += g.get('loss', {}).get('weight', 0)
            totals['exposure'] += g.get('exposure', {}).get('weight', 0)

        self._assert(cat, 0.95 <= totals['risk'] <= 1.05,
                     f"{prefix} Risk weights sum to {totals['risk']:.3f}, not ~1.0")
        self._assert(cat, 0.95 <= totals['loss'] <= 1.05,
                     f"{prefix} Loss weights sum to {totals['loss']:.3f}, not ~1.0")
        self._assert(cat, 0.95 <= totals['exposure'] <= 1.05,
                     f"{prefix} Exposure weights sum to {totals['exposure']:.3f}, not ~1.0")

        # ---------------------------------------------------------------------
        # 2. Scalability Trap Check
        # ---------------------------------------------------------------------
        bands = cfg.get('risk_tier_bands', {}).get('bands', [])
        tier_1 = next((b for b in bands if b.get('id') == 1), {})
        method = tier_1.get('interpretation', {}).get('application', {}).get('method')
        routing = cfg.get('metadata', {}).get('routing_constraints', [])

        if method == "PREMIUM_BASE":
            # Must have ceiling constraint (revenue <= X or similar)
            has_ceiling = any(r.get('operator') in ['<', '<='] for r in routing if isinstance(r, dict))
            self._assert(cat, has_ceiling,
                         f"{prefix} Scalability Trap: PREMIUM_BASE requires maximum size routing constraint")

        # ---------------------------------------------------------------------
        # 3. Monotonicity Check (Tier 5 must cost >= 2x Tier 1)
        # ---------------------------------------------------------------------
        if len(bands) == 5:
            t1_app = bands[0].get('interpretation', {}).get('application', {})
            t5_app = bands[4].get('interpretation', {}).get('application', {})

            t1_val = t1_app.get('value', t1_app.get('applied', 0))
            t5_val = t5_app.get('value', t5_app.get('applied', 0))

            if t1_val and t1_val > 0:
                ratio = t5_val / t1_val
                self._assert(cat, ratio >= 2.0,
                             f"{prefix} Penalty ratio is {ratio:.1f}x (must be >= 2.0x)")

        # ---------------------------------------------------------------------
        # 4. Pricing Anchor Validation (Phase V5)
        # ---------------------------------------------------------------------
        pricing = cfg.get('pricing', {})
        b_limit = pricing.get('base_limit_reference')
        b_ded = pricing.get('base_deductible_reference')

        self._assert(cat, b_limit is not None,
                     f"{prefix} Missing pricing.base_limit_reference (Phase V5)")
        self._assert(cat, b_ded is not None,
                     f"{prefix} Missing pricing.base_deductible_reference (Phase V5)")

        # ILF curve and deductible factor anchor checks
        for prod, data in pricing.get('by_product_type', {}).items():
            # ILF curve anchor check
            ilf_curve = data.get('ilf_curve', {})
            ilf_factors = ilf_curve.get('factors', [])
            anchor_factor = next((f['factor'] for f in ilf_factors if f.get('limit') == b_limit), None)
            self._assert(cat, anchor_factor == 1.0,
                         f"{prefix}/{prod} ILF anchor: limit {b_limit} factor is {anchor_factor}, must be 1.0")

            # Deductible anchor check
            ded_factors = data.get('deductible_factors', [])
            ded_anchor = next((f['factor'] for f in ded_factors if f.get('deductible') == b_ded), None)
            self._assert(cat, ded_anchor == 1.0,
                         f"{prefix}/{prod} Deductible anchor: {b_ded} factor is {ded_anchor}, must be 1.0")

        # ---------------------------------------------------------------------
        # 5. MULTIPLIER basis validation
        # ---------------------------------------------------------------------
        if method == "MULTIPLIER":
            basis = tier_1.get('interpretation', {}).get('application', {}).get('basis')
            mvi = cfg.get('metadata', {}).get('minimum_viable_input', {})
            if isinstance(mvi, list):
                # MVI is a list of required fields
                required_fields = [f.lower() for f in mvi if isinstance(f, str)]
            elif isinstance(mvi, dict):
                required_fields = [f.get('field', '').lower() for f in mvi.get('required', [])]
            else:
                required_fields = []

            if basis:
                self._assert(cat, basis.lower() in required_fields or any(basis.lower() in f for f in required_fields),
                             f"{prefix} MULTIPLIER basis '{basis}' not in minimum_viable_input")

        # ---------------------------------------------------------------------
        # 6. Modifiers are multiplicative (no additive dollar amounts)
        # ---------------------------------------------------------------------
        for sig in cfg.get('signal_registry', []):
            tla = sig.get('three_layer_assessment', {})
            for dim in ['risk', 'loss']:
                dim_data = tla.get(dim, {})
                for cond in dim_data.get('score_conditions', []):
                    if cond.get('action') == 'MODIFIER':
                        applied = cond.get('applied')
                        if applied is not None:
                            # Should be a multiplier (typically 0.5 - 2.0 range)
                            self._assert(cat, 0.1 <= applied <= 10.0,
                                         f"{prefix} Signal '{sig.get('id')}' has non-multiplicative modifier: {applied}")

    # =========================================================================
    # RUN ASSESSMENT
    # =========================================================================

    def run_assessment(self):
        """Execute all assessment checks."""
        # Initialize stats
        self.extractor_stats = {'production_count': 0, 'stub_count': 0, 'production_ratio': 0, 'categories': {}}
        self.test_stats = {'unit': 0, 'integration': 0, 'api': 0, 'performance': 0, 'total': 0}

        # Core structure checks
        self.check_infrastructure()
        self.check_layers()
        self.check_tests()
        self.check_deploy()
        self.check_docs()
        self.check_rust()
        self.check_schemas()
        self.check_signal_arch_files()
        self.check_extractor_coverage()
        self.check_data_persistence()

        # Coverage configurations
        cov_dir = self.root / "coverages"
        if not cov_dir.exists():
            self._assert("coverages", False, "coverages/ directory not found")
            return

        coverage_count = 0
        for root_dir, _, files in os.walk(cov_dir):
            if "config.yaml" in files:
                cov_path = Path(root_dir)
                cov_name = cov_path.name
                coverage_count += 1

                with open(cov_path / "config.yaml", 'r') as f:
                    try:
                        data = yaml.safe_load(f)
                    except yaml.YAMLError as e:
                        self._assert("coverages", False, f"[{cov_name}] YAML parse error: {e}")
                        continue

                config = data.get(cov_name, {})
                self.check_coverage_structure(cov_name, cov_path, config)

                for config_name, cfg in config.items():
                    if isinstance(cfg, dict):
                        self.check_schema_compliance(cov_name, config_name, cfg)
                        self.check_signal_architecture(cov_name, config_name, cfg)
                        self.check_actuarial_math(cov_name, config_name, cfg)

        self.coverage_count = coverage_count

    # =========================================================================
    # REPORT GENERATION
    # =========================================================================

    def save_report(self):
        """Run assessment and save detailed report."""
        self.run_assessment()

        out_dir = self.root / "development/project/assessments/results"
        out_dir.mkdir(parents=True, exist_ok=True)
        report_path = out_dir / f"Assessment_Report_{datetime.now().strftime('%Y-%m-%d')}.md"

        t_pass = sum(s["pass"] for s in self.scores.values())
        t_checks = sum(s["total"] for s in self.scores.values())
        pct = (t_pass / t_checks * 100) if t_checks > 0 else 0

        with open(report_path, 'w') as f:
            f.write("# DSI Project Completeness Assessment\n\n")
            f.write("```text\n")
            f.write("=" * 77 + "\n")
            f.write("DSI PROJECT COMPLETENESS ASSESSMENT\n")
            f.write("=" * 77 + "\n")
            f.write(f"Assessment Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            f.write(f"Assessed By: DSI Unified Assessor v2.0\n")
            f.write(f"Coverages Analyzed: {getattr(self, 'coverage_count', 0)}\n\n")

            f.write("-" * 77 + "\n")
            f.write("1. HIGH-LEVEL SCORECARD\n")
            f.write("-" * 77 + "\n")
            for cat, s in self.scores.items():
                status = "PASS" if s['pass'] == s['total'] else "GAPS"
                cat_display = cat.replace('_', ' ').title()
                f.write(f"  {cat_display.ljust(24)} {s['pass']:3d} / {s['total']:3d}  [{status}]\n")
            f.write(f"\n  {'OVERALL SCORE'.ljust(24)} {t_pass:3d} / {t_checks:3d}  ({pct:.1f}%)\n")
            f.write(f"  STATUS: {'PASS' if pct >= 80 else 'ACTION REQUIRED'}\n")
            f.write("```\n\n")

            # Signal Extractor Stats
            f.write("## Signal Extractor Coverage\n\n")
            f.write("| Metric | Count |\n")
            f.write("|--------|-------|\n")
            f.write(f"| Production Extractors | {self.extractor_stats['production_count']} |\n")
            f.write(f"| Stub Extractors | {self.extractor_stats['stub_count']} |\n")
            f.write(f"| Production Ratio | {self.extractor_stats['production_ratio']}% |\n\n")

            if self.extractor_stats.get('categories'):
                f.write("### Extractor Categories\n\n")
                f.write("| Category | Count |\n")
                f.write("|----------|-------|\n")
                for cat_name, count in sorted(self.extractor_stats['categories'].items()):
                    f.write(f"| {cat_name} | {count} |\n")
                f.write("\n")

            # Test Stats
            f.write("## Test Coverage\n\n")
            f.write("| Category | Test Files |\n")
            f.write("|----------|------------|\n")
            f.write(f"| Unit | {self.test_stats['unit']} |\n")
            f.write(f"| Integration | {self.test_stats['integration']} |\n")
            f.write(f"| API | {self.test_stats['api']} |\n")
            f.write(f"| Performance | {self.test_stats['performance']} |\n")
            f.write(f"| **Total** | **{self.test_stats['total']}** |\n\n")

            # Summary
            total_gaps = sum(len(s['gaps']) for s in self.scores.values())
            if total_gaps == 0:
                f.write("## Status: ALL CHECKS PASSED\n\n")
            else:
                f.write(f"## Action Items ({total_gaps} gaps identified)\n\n")
                for cat, s in self.scores.items():
                    if s["gaps"]:
                        cat_display = cat.replace('_', ' ').upper()
                        f.write(f"### {cat_display}\n\n")
                        for gap in s["gaps"]:
                            f.write(f"- [ ] {gap}\n")
                        f.write("\n")

        print(f"Assessment complete: {pct:.1f}% ({t_pass}/{t_checks} checks)")
        print(f"Report saved: {report_path}")

        if total_gaps > 0:
            print(f"\n{total_gaps} gaps require attention. See report for details.")

        return {
            'score': pct,
            'passed': t_pass,
            'total': t_checks,
            'gaps': total_gaps,
            'report_path': str(report_path)
        }


if __name__ == "__main__":
    assessor = DSIProjectAssessor()
    result = assessor.save_report()
