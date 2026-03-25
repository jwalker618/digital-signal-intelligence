"""
DSI Comprehensive Bench Seed Script
====================================
Seeds the database with realistic, end-to-end data covering every coverage,
configuration, tier, decision path, signal group, and UI component.

**Uses the production workflow components** (ModelScorer, ModelPricer,
QueryEvaluator, compiled CoverageConfig) for all calculation logic.
Signal scores are synthetic (from SIGNAL_PROFILES), but scoring, pricing,
ILF scaling, modifier application, tier resolution, and query evaluation
all flow through the same code paths as a real submission.

Coverage lines seeded:
  - Cyber (cyber_general + cyber_sme)
  - Directors & Officers (do_general + do_sme)
  - Financial Institutions (fi_general + fi_sme)
  - Energy (energy_general, energy_upstream_deepwater, energy_upstream_onshore,
           energy_upstream_unconventional, energy_midstream, energy_downstream,
           energy_offshore_wind, energy_onshore_renewable, energy_storage, energy_sme)
  - Marine (marine_general)
  - Professional Indemnity (pi_general + pi_sme)
  - Aerospace (aerospace_general)

Each company entry creates:
  1. Submission (with submission_data and direct_query_responses)
  2. ModelVersionRecord (full signal_outputs, group_scores, conditions, pricing)
  3. Quote (with recommended premium/limit, composite_score, confidence)
  4. Referral (for refer/decline decisions)
  5. SignalCache entries (per-signal cached data)
  5b. ModelVersionSignal entries (config-to-signal binding — which signals each model used)
  6. SignalAuditRecord (override examples for referred cases)
  7. AuditLog entry
  8. CommercialTermsRecord (entity economics, FX, commission, taxes, offered premium)
  9. RiskTermsRecord (deductible nuance, SIR, waiting periods, sub-limits, coverage terms)

Run:
  python seed_dsi_bench.py
"""

import uuid
import random
import logging
from dataclasses import asdict
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from infrastructure.db.config import Base, DATABASE_URL_SYNC
from infrastructure.db.models import (
    Submission,
    Quote,
    ModelVersionRecord,
    ModelVersionSignal,
    Referral,
    Signal,
    SignalSource,
    SignalCache,
    SignalAuditRecord,
    User,
    AuditLog,
    CommercialTermsRecord,
    RiskTermsRecord,
    SubmissionStatus,
    QuoteStatus,
    DecisionType,
    ReferralStatus,
)

# Production workflow components
from infrastructure.models.compiler import get_config
from layers.risk.appetite import evaluate_appetite
from layers.risk.scorer import ModelScorer
from layers.risk.pricer import ModelPricer
from layers.risk.query_evaluator import QueryEvaluator
from layers.risk.rol_validator import ROLValidator
from layers.risk.rol_recommender import ROLRecommender
from layers.risk.types import SignalOutput, CategoricalOutput, utcnow

# Commercial terms and FX
from infrastructure.models.commercial_schema import (
    CommercialEntity,
    load_entity,
    load_all_entities,
)
from layers.risk.fx import FXConverter, StaticRateProvider, Currency
from layers.risk.premium_assembly import PremiumAssembler

# =============================================================================
# HELPERS
# =============================================================================

NOW = datetime.now(timezone.utc)

logger = logging.getLogger("dsi.seed")


def _uid():
    return uuid.uuid4()


def _hex(n=8):
    return uuid.uuid4().hex[:n]


def _score(base, jitter=10):
    """Generate a score around a base value, clamped 0-100."""
    return max(0, min(100, base + random.randint(-jitter, jitter)))


# Maps COMPANIES coverage field -> compiler coverage_id (directory name)
COVERAGE_DIR_MAP = {
    "cyber": "cyber",
    "directors_officers": "do",
    "financial_institutions": "fi",
    "energy": "energy",
    "marine": "marine",
    "professional_indemnity": "pi",
    "aerospace": "aerospace",
}

# Production singletons — instantiated once, reused for all companies
_scorer = ModelScorer()
_pricer = ModelPricer()
_query_evaluator = QueryEvaluator()

# Config cache — avoids recompiling the same config for every company
_config_cache = {}


def _get_compiled_config(co):
    """Load and cache the compiled CoverageConfig for a company record."""
    config_id = co["configuration"]
    if config_id in _config_cache:
        return _config_cache[config_id]
    coverage_dir = COVERAGE_DIR_MAP[co["coverage"]]
    config = get_config(coverage_dir, config_id)
    _config_cache[config_id] = config
    return config


# =============================================================================
# COMPREHENSIVE COMPANY DATASET
# =============================================================================

COMPANIES = [
    # -------------------------------------------------------------------------
    # CYBER - cyber_general (mid-market / enterprise)
    # -------------------------------------------------------------------------
    {
        "entity_name": "Cloudflare",
        "domain": "cloudflare.com",
        "ticker": "NET",
        "coverage": "cyber",
        "configuration": "cyber_general",
        "tier": 1,
        "decision": "approve",
        "premium": 125000,
        "revenue": 1_200_000_000,
        "industry": "TECHNOLOGY",
        "size_band": "ENTERPRISE",
        "geography": "US",
        "description": "Elite cybersecurity posture, robust TLS, full email auth, WAF leader.",
        "signal_profile": "strong_tech",
        "product_type": "cyber_liability",
        "limit": 25_000_000,
        "deductible": 100_000,
    },
    {
        "entity_name": "CrowdStrike",
        "domain": "crowdstrike.com",
        "ticker": "CRWD",
        "coverage": "cyber",
        "configuration": "cyber_general",
        "tier": 1,
        "decision": "approve",
        "premium": 98_000,
        "revenue": 3_000_000_000,
        "industry": "TECHNOLOGY",
        "size_band": "ENTERPRISE",
        "geography": "US",
        "description": "Market-leading EDR vendor, exemplary security infrastructure.",
        "signal_profile": "strong_tech",
        "product_type": "network_security",
        "limit": 10_000_000,
        "deductible": 50_000,
    },
    {
        "entity_name": "Salesforce",
        "domain": "salesforce.com",
        "ticker": "CRM",
        "coverage": "cyber",
        "configuration": "cyber_general",
        "tier": 2,
        "decision": "approve",
        "premium": 340_000,
        "revenue": 34_000_000_000,
        "industry": "TECHNOLOGY",
        "size_band": "ENTERPRISE",
        "geography": "US",
        "description": "Strong tech posture, large data footprint increases exposure.",
        "signal_profile": "good_tech",
        "product_type": "privacy_liability",
        "limit": 25_000_000,
        "deductible": 250_000,
    },
    {
        "entity_name": "HCA Healthcare",
        "domain": "hcahealthcare.com",
        "ticker": "HCA",
        "coverage": "cyber",
        "configuration": "cyber_general",
        "tier": 3,
        "decision": "refer",
        "premium": 520_000,
        "revenue": 60_000_000_000,
        "industry": "HEALTHCARE",
        "size_band": "ENTERPRISE",
        "geography": "US",
        "description": "Massive PHI exposure, past breach history, high regulatory risk.",
        "signal_profile": "healthcare_elevated",
        "product_type": "cyber_liability",
        "limit": 25_000_000,
        "deductible": 500_000,
        "referral_reasons": ["PHI handler - HIPAA exposure", "Prior breach in 2023", "Elevated network exposure score"],
    },
    {
        "entity_name": "Boeing",
        "domain": "boeing.com",
        "ticker": "BA",
        "coverage": "cyber",
        "configuration": "cyber_general",
        "tier": 3,
        "decision": "refer",
        "premium": 450_000,
        "revenue": 78_000_000_000,
        "industry": "MANUFACTURING",
        "size_band": "ENTERPRISE",
        "geography": "US",
        "description": "Large attack surface, legacy systems, OT/IT convergence risk.",
        "signal_profile": "manufacturing_legacy",
        "product_type": "network_security",
        "limit": 25_000_000,
        "deductible": 250_000,
        "referral_reasons": ["Elevated network exposure", "Legacy software detected", "High complexity score"],
    },
    {
        "entity_name": "Petrobras",
        "domain": "petrobras.com.br",
        "ticker": "PBR",
        "coverage": "cyber",
        "configuration": "cyber_general",
        "tier": 4,
        "decision": "refer",
        "premium": 820_000,
        "revenue": 90_000_000_000,
        "industry": "ENERGY",
        "size_band": "ENTERPRISE",
        "geography": "OTHER",
        "description": "State-owned oil company, massive OT exposure, weak email auth.",
        "signal_profile": "energy_weak",
        "product_type": "cyber_extortion",
        "limit": 100_000_000,
        "deductible": 500_000,
        "referral_reasons": ["Missing MFA", "Critical OT/ICS exposure", "Weak email authentication", "Non-US jurisdiction"],
    },
    {
        "entity_name": "Pemex",
        "domain": "pemex.com",
        "ticker": "PMX",
        "coverage": "cyber",
        "configuration": "cyber_general",
        "tier": 5,
        "decision": "decline",
        "premium": 0,
        "revenue": 65_000_000_000,
        "industry": "ENERGY",
        "size_band": "ENTERPRISE",
        "geography": "OTHER",
        "description": "Prior ransomware attack, no MFA, critical vulnerabilities.",
        "signal_profile": "catastrophic",
        "product_type": "cyber_extortion",
        "limit": 100_000_000,
        "deductible": 250_000,
        "referral_reasons": ["Active breach history", "No MFA", "Critical CVE exposure", "No EDR", "No immutable backups"],
    },
    # -------------------------------------------------------------------------
    # CYBER SME
    # -------------------------------------------------------------------------
    {
        "entity_name": "Acme Widgets LLC",
        "domain": "acmewidgets.com",
        "ticker": None,
        "coverage": "cyber",
        "configuration": "cyber_sme",
        "tier": 1,
        "decision": "approve",
        "premium": 1_800,
        "revenue": 5_000_000,
        "industry": "MANUFACTURING",
        "size_band": "SMALL",
        "geography": "US",
        "description": "Small manufacturer with solid security basics.",
        "signal_profile": "sme_clean",
        "product_type": "cyber_liability",
        "limit": 1_000_000,
        "deductible": 5_000,
    },
    {
        "entity_name": "TechStart AI",
        "domain": "techstart.ai",
        "ticker": None,
        "coverage": "cyber",
        "configuration": "cyber_sme",
        "tier": 2,
        "decision": "approve",
        "premium": 3_200,
        "revenue": 12_000_000,
        "industry": "TECH",
        "size_band": "SMALL",
        "geography": "US",
        "description": "Growing SaaS startup, decent posture, some gaps.",
        "signal_profile": "sme_moderate",
        "product_type": "network_security",
        "limit": 2_000_000,
        "deductible": 10_000,
    },
    {
        "entity_name": "QuickMed Clinic",
        "domain": "quickmedclinic.com",
        "ticker": None,
        "coverage": "cyber",
        "configuration": "cyber_sme",
        "tier": 4,
        "decision": "refer",
        "premium": 6_800,
        "revenue": 8_000_000,
        "industry": "HEALTHCARE",
        "size_band": "SMALL",
        "geography": "US",
        "description": "Small clinic handling PHI with weak email security.",
        "signal_profile": "sme_weak",
        "product_type": "cyber_liability",
        "limit": 1_000_000,
        "deductible": 5_000,
        "referral_reasons": ["Missing email authentication", "Prior breach history"],
    },

    # -------------------------------------------------------------------------
    # D&O GENERAL
    # -------------------------------------------------------------------------
    {
        "entity_name": "Microsoft Corporation",
        "domain": "microsoft.com",
        "ticker": "MSFT",
        "coverage": "directors_officers",
        "configuration": "do_general",
        "tier": 1,
        "decision": "approve",
        "premium": 2_100_000,
        "revenue": 230_000_000_000,
        "industry": "TECHNOLOGY",
        "size_band": "ENTERPRISE",
        "geography": "US",
        "company_type": "PUBLIC_LARGE_CAP",
        "stock_exchange": "NASDAQ",
        "description": "Exemplary governance, strong financials, clean litigation profile.",
        "signal_profile": "do_excellent",
        "product_type": "side_a",
        "limit": 100_000_000,
        "deductible": 1_000_000,
    },
    {
        "entity_name": "JPMorgan Chase",
        "domain": "jpmorganchase.com",
        "ticker": "JPM",
        "coverage": "directors_officers",
        "configuration": "do_general",
        "tier": 2,
        "decision": "approve",
        "premium": 1_800_000,
        "revenue": 160_000_000_000,
        "industry": "FINANCIAL_SERVICES",
        "size_band": "ENTERPRISE",
        "geography": "US",
        "company_type": "PUBLIC_LARGE_CAP",
        "stock_exchange": "NYSE",
        "description": "Strong governance, minor regulatory actions, excellent financials.",
        "signal_profile": "do_strong",
        "product_type": "side_b",
        "limit": 50_000_000,
        "deductible": 500_000,
    },
    {
        "entity_name": "Tesla Inc",
        "domain": "tesla.com",
        "ticker": "TSLA",
        "coverage": "directors_officers",
        "configuration": "do_general",
        "tier": 3,
        "decision": "refer",
        "premium": 3_500_000,
        "revenue": 96_000_000_000,
        "industry": "MANUFACTURING",
        "size_band": "ENTERPRISE",
        "geography": "US",
        "company_type": "PUBLIC_LARGE_CAP",
        "stock_exchange": "NASDAQ",
        "description": "High stock volatility, SEC scrutiny, governance concentration.",
        "signal_profile": "do_volatile",
        "product_type": "side_c",
        "limit": 100_000_000,
        "deductible": 1_000_000,
        "referral_reasons": ["Active SEC investigation", "CEO-chair duality", "High stock volatility", "Securities litigation history"],
    },
    {
        "entity_name": "Nikola Corporation",
        "domain": "nikolamotor.com",
        "ticker": "NKLA",
        "coverage": "directors_officers",
        "configuration": "do_general",
        "tier": 5,
        "decision": "decline",
        "premium": 0,
        "revenue": 50_000_000,
        "industry": "MANUFACTURING",
        "size_band": "SMALL",
        "geography": "US",
        "company_type": "PUBLIC_MICRO_CAP",
        "stock_exchange": "NASDAQ",
        "description": "Founder fraud conviction, SEC settlement, going concern risk.",
        "signal_profile": "do_catastrophic",
        "product_type": "side_a",
        "limit": 10_000_000,
        "deductible": 250_000,
        "referral_reasons": ["Active securities fraud litigation", "SEC enforcement action", "Going concern audit opinion", "Founder convicted of fraud"],
    },

    # D&O SME
    {
        "entity_name": "GreenLeaf Organics",
        "domain": "greenleaforganics.com",
        "ticker": None,
        "coverage": "directors_officers",
        "configuration": "do_sme",
        "tier": 1,
        "decision": "approve",
        "premium": 2_800,
        "revenue": 15_000_000,
        "industry": "RETAIL_CONSUMER",
        "size_band": "SMALL",
        "geography": "US",
        "company_type": "PRIVATE_OTHER",
        "stock_exchange": "NONE",
        "description": "Clean private company, stable management, no litigation.",
        "signal_profile": "sme_clean",
        "product_type": "side_a",
        "limit": 1_000_000,
        "deductible": 10_000,
    },
    {
        "entity_name": "Apex Ventures Fund III",
        "domain": "apexventures.com",
        "ticker": None,
        "coverage": "directors_officers",
        "configuration": "do_sme",
        "tier": 3,
        "decision": "refer",
        "premium": 5_500,
        "revenue": 30_000_000,
        "industry": "FINANCIAL_SERVICES",
        "size_band": "SMALL",
        "geography": "US",
        "company_type": "PRIVATE_BACKED",
        "stock_exchange": "NONE",
        "description": "PE-backed fund with investor dispute history.",
        "signal_profile": "sme_moderate",
        "product_type": "fiduciary",
        "limit": 2_000_000,
        "deductible": 25_000,
        "referral_reasons": ["Investor dispute pending", "High related-party transactions"],
    },

    # -------------------------------------------------------------------------
    # FINANCIAL INSTITUTIONS GENERAL
    # -------------------------------------------------------------------------
    {
        "entity_name": "First Republic Bank",
        "domain": "firstrepublic.com",
        "ticker": "FRC",
        "coverage": "financial_institutions",
        "configuration": "fi_general",
        "tier": 2,
        "decision": "approve",
        "premium": 380_000,
        "revenue": 6_000_000_000,
        "industry": "REGIONAL_BANK",
        "size_band": "LARGE",
        "geography": "US",
        "institution_type": "REGIONAL_BANK",
        "regulatory_framework": "OCC",
        "asset_size_band": "LARGE",
        "publicly_traded": "PUBLIC",
        "description": "Well-capitalized regional bank, strong exam ratings.",
        "signal_profile": "fi_strong",
        "product_type": "financial_institution_bond",
        "limit": 25_000_000,
        "deductible": 100_000,
        "total_assets": 212_000_000_000,
    },
    {
        "entity_name": "Goldman Sachs",
        "domain": "goldmansachs.com",
        "ticker": "GS",
        "coverage": "financial_institutions",
        "configuration": "fi_general",
        "tier": 1,
        "decision": "approve",
        "premium": 950_000,
        "revenue": 47_000_000_000,
        "industry": "MONEY_CENTER_BANK",
        "size_band": "MEGA",
        "geography": "US",
        "institution_type": "BROKER_DEALER",
        "regulatory_framework": "MULTI",
        "asset_size_band": "MEGA",
        "publicly_traded": "PUBLIC",
        "description": "Tier-1 global bank, exemplary governance, strong capital ratios.",
        "signal_profile": "fi_excellent",
        "product_type": "directors_officers",
        "limit": 100_000_000,
        "deductible": 1_000_000,
        "total_assets": 1_600_000_000_000,
    },
    {
        "entity_name": "SVB Financial Group",
        "domain": "svb.com",
        "ticker": "SIVB",
        "coverage": "financial_institutions",
        "configuration": "fi_general",
        "tier": 4,
        "decision": "refer",
        "premium": 780_000,
        "revenue": 7_400_000_000,
        "industry": "REGIONAL_BANK",
        "size_band": "LARGE",
        "geography": "US",
        "institution_type": "REGIONAL_BANK",
        "regulatory_framework": "FDIC",
        "asset_size_band": "LARGE",
        "publicly_traded": "PUBLIC",
        "description": "Concentration risk, interest rate exposure, rapid growth.",
        "signal_profile": "fi_stressed",
        "product_type": "professional_liability",
        "limit": 50_000_000,
        "deductible": 250_000,
        "total_assets": 211_000_000_000,
        "referral_reasons": ["Concentration risk >25% tech sector", "Interest rate sensitivity", "Rapid asset growth >20%", "Liquidity concerns"],
    },
    {
        "entity_name": "Wirecard AG",
        "domain": "wirecard.com",
        "ticker": "WDI",
        "coverage": "financial_institutions",
        "configuration": "fi_general",
        "tier": 5,
        "decision": "decline",
        "premium": 0,
        "revenue": 3_200_000_000,
        "industry": "PAYMENT_PROCESSOR",
        "size_band": "MID",
        "geography": "EU",
        "institution_type": "PAYMENT_PROCESSOR",
        "regulatory_framework": "OTHER",
        "asset_size_band": "MID",
        "publicly_traded": "PUBLIC",
        "description": "Accounting fraud, regulatory collapse, criminal proceedings.",
        "signal_profile": "fi_catastrophic",
        "product_type": "financial_institution_bond",
        "limit": 25_000_000,
        "deductible": 100_000,
        "total_assets": 26_000_000_000,
        "referral_reasons": ["Active criminal fraud proceedings", "Regulatory license revoked", "Qualified audit opinion", "BSA/AML violations"],
    },

    # FI SME
    {
        "entity_name": "Heritage Community Bank",
        "domain": "heritagecommunitybank.com",
        "ticker": None,
        "coverage": "financial_institutions",
        "configuration": "fi_sme",
        "tier": 1,
        "decision": "approve",
        "premium": 5_500,
        "revenue": 45_000_000,
        "industry": "COMMUNITY_BANK",
        "size_band": "COMMUNITY",
        "geography": "US",
        "institution_type": "COMMUNITY_BANK",
        "regulatory_framework": "FDIC",
        "asset_size_band": "COMMUNITY",
        "publicly_traded": "PRIVATE",
        "description": "Well-run community bank, clean exam history.",
        "signal_profile": "fi_sme_clean",
        "product_type": "financial_institution_bond",
        "limit": 1_000_000,
        "deductible": 10_000,
        "total_assets": 400_000_000,
    },

    # -------------------------------------------------------------------------
    # ENERGY GENERAL
    # -------------------------------------------------------------------------
    {
        "entity_name": "Shell plc",
        "domain": "shell.com",
        "ticker": "SHEL",
        "coverage": "energy",
        "configuration": "energy_general",
        "tier": 1,
        "decision": "approve",
        "premium": 4_200_000,
        "revenue": 380_000_000_000,
        "industry": "SUPERMAJOR",
        "size_band": "ENTERPRISE",
        "geography": "UK",
        "operator_type": "SUPERMAJOR",
        "operation_segment": "MIXED",
        "geographic_focus": "GLOBAL_DIVERSIFIED",
        "description": "Global supermajor, industry-leading HSE program, diversified portfolio.",
        "signal_profile": "energy_excellent",
        "product_type": "property_damage",
        "limit": 500_000_000,
        "deductible": 1_000_000,
        "tiv": 85_000_000_000,
    },
    {
        "entity_name": "Devon Energy",
        "domain": "devonenergy.com",
        "ticker": "DVN",
        "coverage": "energy",
        "configuration": "energy_general",
        "tier": 2,
        "decision": "approve",
        "premium": 1_800_000,
        "revenue": 20_000_000_000,
        "industry": "UPSTREAM",
        "size_band": "LARGE",
        "geography": "US",
        "operator_type": "LARGE_INDEPENDENT",
        "operation_segment": "UPSTREAM_CONVENTIONAL",
        "geographic_focus": "US_ONSHORE",
        "description": "US shale operator, solid safety record, moderate environmental risk.",
        "signal_profile": "energy_good",
        "product_type": "control_of_well",
        "limit": 500_000_000,
        "deductible": 1_000_000,
        "tiv": 8_000_000_000,
    },
    {
        "entity_name": "Transocean Ltd",
        "domain": "deepwater.com",
        "ticker": "RIG",
        "coverage": "energy",
        "configuration": "energy_general",
        "tier": 4,
        "decision": "refer",
        "premium": 8_500_000,
        "revenue": 2_800_000_000,
        "industry": "OFFSHORE_DRILLING",
        "size_band": "LARGE",
        "geography": "US",
        "operator_type": "LARGE_INDEPENDENT",
        "operation_segment": "UPSTREAM_DEEPWATER",
        "geographic_focus": "US_GULF_DEEPWATER",
        "description": "Deepwater Horizon operator history, aging fleet, high leverage.",
        "signal_profile": "energy_elevated",
        "product_type": "third_party_liability",
        "limit": 250_000_000,
        "deductible": 1_000_000,
        "tiv": 12_000_000_000,
        "referral_reasons": ["Catastrophic loss history (Deepwater Horizon)", "Aging fleet >15 years average", "High debt-to-equity ratio", "Environmental violations"],
    },

    # -------------------------------------------------------------------------
    # ENERGY UPSTREAM DEEPWATER
    # -------------------------------------------------------------------------
    {
        "entity_name": "Hess Corporation",
        "domain": "hess.com",
        "ticker": "HES",
        "coverage": "energy",
        "configuration": "energy_upstream_deepwater",
        "tier": 1,
        "decision": "approve",
        "premium": 5_000_000,
        "revenue": 10_500_000_000,
        "industry": "UPSTREAM_DEEPWATER",
        "size_band": "LARGE",
        "geography": "US",
        "operator_type": "LARGE_INDEPENDENT",
        "operation_segment": "UPSTREAM_DEEPWATER",
        "geographic_focus": "LATIN_AMERICA",
        "description": "Guyana deepwater programme (Stabroek Block). Exceptional safety record, ExxonMobil as JV operator.",
        "signal_profile": "energy_deepwater_excellent",
        "product_type": "property_damage",
        "limit": 500_000_000,
        "deductible": 5_000_000,
        "tiv": 8_200_000_000,
    },
    {
        "entity_name": "Murphy Oil Corporation",
        "domain": "murphyoilcorp.com",
        "ticker": "MUR",
        "coverage": "energy",
        "configuration": "energy_upstream_deepwater",
        "tier": 3,
        "decision": "refer",
        "premium": 5_580_000,
        "revenue": 3_200_000_000,
        "industry": "UPSTREAM_DEEPWATER",
        "size_band": "LARGE",
        "geography": "US",
        "operator_type": "MID_INDEPENDENT",
        "operation_segment": "UPSTREAM_DEEPWATER",
        "geographic_focus": "US_GULF_SHELF",
        "description": "Gulf of Mexico shelf & deepwater. Mixed safety record, aging Medusa spar platform.",
        "signal_profile": "energy_deepwater_elevated",
        "product_type": "control_of_well",
        "limit": 250_000_000,
        "deductible": 1_000_000,
        "tiv": 3_100_000_000,
        "referral_reasons": ["Process safety events in 5 years", "Aging subsea infrastructure"],
    },
    {
        "entity_name": "Vaalco Energy",
        "domain": "vaalco.com",
        "ticker": "EGY",
        "coverage": "energy",
        "configuration": "energy_upstream_deepwater",
        "tier": 5,
        "decision": "decline",
        "premium": 2_940_000,
        "revenue": 450_000_000,
        "industry": "UPSTREAM_DEEPWATER",
        "size_band": "MID",
        "geography": "WEST_AFRICA",
        "operator_type": "SMALL_INDEPENDENT",
        "operation_segment": "UPSTREAM_DEEPWATER",
        "geographic_focus": "WEST_AFRICA",
        "description": "Offshore Gabon. Fatality on Etame platform, spill events, single-asset concentration.",
        "signal_profile": "energy_deepwater_catastrophic",
        "product_type": "property_damage",
        "limit": 100_000_000,
        "deductible": 500_000,
        "tiv": 420_000_000,
    },

    # -------------------------------------------------------------------------
    # ENERGY UPSTREAM ONSHORE
    # -------------------------------------------------------------------------
    {
        "entity_name": "ConocoPhillips",
        "domain": "conocophillips.com",
        "ticker": "COP",
        "coverage": "energy",
        "configuration": "energy_upstream_onshore",
        "tier": 1,
        "decision": "approve",
        "premium": 5_800_000,
        "revenue": 58_000_000_000,
        "industry": "UPSTREAM_CONVENTIONAL",
        "size_band": "ENTERPRISE",
        "geography": "US",
        "operator_type": "MAJOR_INTEGRATED",
        "operation_segment": "UPSTREAM_CONVENTIONAL",
        "geographic_focus": "US_ONSHORE",
        "description": "Permian Basin & Eagle Ford conventional operations. Industry-leading safety, 20+ year track record.",
        "signal_profile": "energy_upstream_onshore_excellent",
        "product_type": "property_damage",
        "limit": 500_000_000,
        "deductible": 1_000_000,
        "tiv": 12_000_000_000,
    },
    {
        "entity_name": "Callon Petroleum",
        "domain": "callon.com",
        "ticker": "CPE",
        "coverage": "energy",
        "configuration": "energy_upstream_onshore",
        "tier": 3,
        "decision": "refer",
        "premium": 6_720_000,
        "revenue": 2_800_000_000,
        "industry": "UPSTREAM_CONVENTIONAL",
        "size_band": "LARGE",
        "geography": "US",
        "operator_type": "MID_INDEPENDENT",
        "operation_segment": "UPSTREAM_CONVENTIONAL",
        "geographic_focus": "US_ONSHORE",
        "description": "Permian Basin conventional & unconventional mix. Moderate safety record, acquisition integration.",
        "signal_profile": "energy_upstream_onshore_standard",
        "product_type": "property_damage",
        "limit": 250_000_000,
        "deductible": 500_000,
        "tiv": 4_200_000_000,
        "referral_reasons": ["Aging well inventory", "Elevated leverage from acquisitions"],
    },
    {
        "entity_name": "Distressed Conventional Operator",
        "domain": "distressedconv.example.com",
        "ticker": None,
        "coverage": "energy",
        "configuration": "energy_upstream_onshore",
        "tier": 5,
        "decision": "decline",
        "premium": 1_520_000,
        "revenue": 180_000_000,
        "industry": "UPSTREAM_CONVENTIONAL",
        "size_band": "SMALL",
        "geography": "US",
        "operator_type": "SMALL_INDEPENDENT",
        "operation_segment": "UPSTREAM_CONVENTIONAL",
        "geographic_focus": "US_ONSHORE",
        "description": "Multiple state regulatory violations, orphaned well obligations, declining production, financial distress.",
        "signal_profile": "energy_upstream_onshore_distressed",
        "product_type": "property_damage",
        "limit": 50_000_000,
        "deductible": 100_000,
        "tiv": 380_000_000,
    },

    # -------------------------------------------------------------------------
    # ENERGY UPSTREAM UNCONVENTIONAL
    # -------------------------------------------------------------------------
    {
        "entity_name": "Pioneer Natural Resources",
        "domain": "pxd.com",
        "ticker": "PXD",
        "coverage": "energy",
        "configuration": "energy_upstream_unconventional",
        "tier": 1,
        "decision": "approve",
        "premium": 18_500_000,
        "revenue": 23_000_000_000,
        "industry": "UPSTREAM_UNCONVENTIONAL",
        "size_band": "ENTERPRISE",
        "geography": "US",
        "operator_type": "LARGE_INDEPENDENT",
        "operation_segment": "UPSTREAM_UNCONVENTIONAL",
        "geographic_focus": "US_ONSHORE",
        "description": "Permian Basin pure-play. Best-in-class safety, 100% water recycling, zero induced seismicity events.",
        "signal_profile": "energy_unconventional_excellent",
        "product_type": "property_damage",
        "limit": 500_000_000,
        "deductible": 1_000_000,
        "tiv": 28_000_000_000,
    },
    {
        "entity_name": "Chesapeake Energy",
        "domain": "chk.com",
        "ticker": "CHK",
        "coverage": "energy",
        "configuration": "energy_upstream_unconventional",
        "tier": 3,
        "decision": "refer",
        "premium": 18_700_000,
        "revenue": 8_000_000_000,
        "industry": "UPSTREAM_UNCONVENTIONAL",
        "size_band": "LARGE",
        "geography": "US",
        "operator_type": "MID_INDEPENDENT",
        "operation_segment": "UPSTREAM_UNCONVENTIONAL",
        "geographic_focus": "US_ONSHORE",
        "description": "Marcellus/Haynesville shale gas. Post-bankruptcy restructured 2021, legacy well spacing issues.",
        "signal_profile": "energy_unconventional_elevated",
        "product_type": "property_damage",
        "limit": 250_000_000,
        "deductible": 1_000_000,
        "tiv": 8_500_000_000,
        "referral_reasons": ["Prior bankruptcy restructuring", "Well spacing optimisation concerns"],
    },
    {
        "entity_name": "Distressed Shale Operator",
        "domain": "distressedshale.example.com",
        "ticker": None,
        "coverage": "energy",
        "configuration": "energy_upstream_unconventional",
        "tier": 5,
        "decision": "decline",
        "premium": 6_600_000,
        "revenue": 600_000_000,
        "industry": "UPSTREAM_UNCONVENTIONAL",
        "size_band": "MID",
        "geography": "US",
        "operator_type": "SMALL_INDEPENDENT",
        "operation_segment": "UPSTREAM_UNCONVENTIONAL",
        "geographic_focus": "US_ONSHORE",
        "description": "Multiple frac-related safety incidents, induced seismicity violations, EPA consent decree pending.",
        "signal_profile": "energy_unconventional_distressed",
        "product_type": "property_damage",
        "limit": 100_000_000,
        "deductible": 500_000,
        "tiv": 1_200_000_000,
    },

    # -------------------------------------------------------------------------
    # ENERGY MIDSTREAM
    # -------------------------------------------------------------------------
    {
        "entity_name": "Enterprise Products Partners",
        "domain": "enterpriseproducts.com",
        "ticker": "EPD",
        "coverage": "energy",
        "configuration": "energy_midstream",
        "tier": 1,
        "decision": "approve",
        "premium": 10_500_000,
        "revenue": 55_000_000_000,
        "industry": "MIDSTREAM_PIPELINE",
        "size_band": "ENTERPRISE",
        "geography": "US",
        "operator_type": "MIDSTREAM_MAJOR",
        "operation_segment": "MIDSTREAM_PIPELINE",
        "geographic_focus": "US_ONSHORE",
        "description": "Largest US midstream operator. 50,000-mile pipeline network, industry-leading integrity management.",
        "signal_profile": "energy_midstream_excellent",
        "product_type": "property_damage",
        "limit": 500_000_000,
        "deductible": 1_000_000,
        "tiv": 22_000_000_000,
    },
    {
        "entity_name": "ONEOK Inc",
        "domain": "oneok.com",
        "ticker": "OKE",
        "coverage": "energy",
        "configuration": "energy_midstream",
        "tier": 2,
        "decision": "approve",
        "premium": 12_600_000,
        "revenue": 22_000_000_000,
        "industry": "MIDSTREAM_PROCESSING",
        "size_band": "LARGE",
        "geography": "US",
        "operator_type": "MIDSTREAM_MAJOR",
        "operation_segment": "MIDSTREAM_PROCESSING",
        "geographic_focus": "US_ONSHORE",
        "description": "Natural gas gathering & processing. Good safety, recent expansion, solid financials.",
        "signal_profile": "energy_midstream_good",
        "product_type": "property_damage",
        "limit": 250_000_000,
        "deductible": 1_000_000,
        "tiv": 14_000_000_000,
    },
    {
        "entity_name": "Genesis Energy",
        "domain": "genesisenergy.com",
        "ticker": "GEL",
        "coverage": "energy",
        "configuration": "energy_midstream",
        "tier": 4,
        "decision": "refer",
        "premium": 5_600_000,
        "revenue": 2_800_000_000,
        "industry": "MIDSTREAM_PIPELINE",
        "size_band": "MID",
        "geography": "US",
        "operator_type": "MID_INDEPENDENT",
        "operation_segment": "MIDSTREAM_PIPELINE",
        "geographic_focus": "US_GULF_SHELF",
        "description": "Offshore pipeline & terminal operator. High leverage, aging deepwater pipeline assets.",
        "signal_profile": "energy_midstream_elevated",
        "product_type": "third_party_liability",
        "limit": 100_000_000,
        "deductible": 500_000,
        "tiv": 2_800_000_000,
        "referral_reasons": ["High leverage (debt/EBITDA > 5x)", "Aging pipeline assets", "Environmental violations"],
    },

    # -------------------------------------------------------------------------
    # ENERGY DOWNSTREAM
    # -------------------------------------------------------------------------
    {
        "entity_name": "Valero Energy",
        "domain": "valero.com",
        "ticker": "VLO",
        "coverage": "energy",
        "configuration": "energy_downstream",
        "tier": 1,
        "decision": "approve",
        "premium": 25_800_000,
        "revenue": 176_000_000_000,
        "industry": "DOWNSTREAM_REFINING",
        "size_band": "ENTERPRISE",
        "geography": "US",
        "operator_type": "DOWNSTREAM_MAJOR",
        "operation_segment": "DOWNSTREAM_REFINING",
        "geographic_focus": "US_ONSHORE",
        "description": "Largest independent US refiner. 14 refineries, excellent turnaround compliance, best-in-class PSM.",
        "signal_profile": "energy_downstream_excellent",
        "product_type": "property_damage",
        "limit": 500_000_000,
        "deductible": 2_500_000,
        "tiv": 38_000_000_000,
    },
    {
        "entity_name": "PBF Energy",
        "domain": "pbfenergy.com",
        "ticker": "PBF",
        "coverage": "energy",
        "configuration": "energy_downstream",
        "tier": 3,
        "decision": "refer",
        "premium": 24_200_000,
        "revenue": 38_000_000_000,
        "industry": "DOWNSTREAM_REFINING",
        "size_band": "LARGE",
        "geography": "US",
        "operator_type": "DOWNSTREAM_MAJOR",
        "operation_segment": "DOWNSTREAM_REFINING",
        "geographic_focus": "US_ONSHORE",
        "description": "US East Coast & Gulf Coast refineries. Moderate safety, deferred turnaround at Paulsboro.",
        "signal_profile": "energy_downstream_elevated",
        "product_type": "business_interruption",
        "limit": 500_000_000,
        "deductible": 2_500_000,
        "tiv": 11_000_000_000,
        "referral_reasons": ["Turnaround deferral at Paulsboro", "Elevated leverage"],
    },
    {
        "entity_name": "Philadelphia Energy Solutions",
        "domain": "pes-energy.example.com",
        "ticker": None,
        "coverage": "energy",
        "configuration": "energy_downstream",
        "tier": 5,
        "decision": "decline",
        "premium": 11_440_000,
        "revenue": 8_000_000_000,
        "industry": "DOWNSTREAM_REFINING",
        "size_band": "LARGE",
        "geography": "US",
        "operator_type": "MID_INDEPENDENT",
        "operation_segment": "DOWNSTREAM_REFINING",
        "geographic_focus": "US_ONSHORE",
        "description": "Single-site, bankrupt, known HF alkylation unit risk, multiple OSHA citations, deferred maintenance.",
        "signal_profile": "energy_downstream_catastrophic",
        "product_type": "property_damage",
        "limit": 250_000_000,
        "deductible": 1_000_000,
        "tiv": 5_200_000_000,
    },

    # -------------------------------------------------------------------------
    # ENERGY OFFSHORE WIND
    # -------------------------------------------------------------------------
    {
        "entity_name": "Orsted A/S",
        "domain": "orsted.com",
        "ticker": "ORSTED",
        "coverage": "energy",
        "configuration": "energy_offshore_wind",
        "tier": 1,
        "decision": "approve",
        "premium": 16_800_000,
        "revenue": 17_000_000_000,
        "industry": "RENEWABLE",
        "size_band": "ENTERPRISE",
        "geography": "EU",
        "operator_type": "LARGE_INDEPENDENT",
        "operation_segment": "RENEWABLE",
        "geographic_focus": "NORTH_SEA",
        "description": "World's largest offshore wind developer. 25+ years experience, zero construction-phase total losses.",
        "signal_profile": "energy_offshore_wind_excellent",
        "product_type": "property_damage",
        "limit": 750_000_000,
        "deductible": 2_500_000,
        "tiv": 28_000_000_000,
    },
    {
        "entity_name": "Equinor Renewables",
        "domain": "equinor.com",
        "ticker": "EQNR",
        "coverage": "energy",
        "configuration": "energy_offshore_wind",
        "tier": 3,
        "decision": "refer",
        "premium": 24_000_000,
        "revenue": 105_000_000_000,
        "industry": "RENEWABLE",
        "size_band": "ENTERPRISE",
        "geography": "EU",
        "operator_type": "SUPERMAJOR",
        "operation_segment": "RENEWABLE",
        "geographic_focus": "NORTH_SEA",
        "description": "Dogger Bank & Empire Wind. Oil & gas heritage transitioning, using 13MW Haliade-X turbines.",
        "signal_profile": "energy_offshore_wind_standard",
        "product_type": "property_damage",
        "limit": 500_000_000,
        "deductible": 2_500_000,
        "tiv": 12_000_000_000,
        "referral_reasons": ["New turbine platform (Haliade-X)", "Single mega-project concentration"],
    },
    {
        "entity_name": "First-Time Offshore Wind Developer",
        "domain": "newoffshorewind.example.com",
        "ticker": None,
        "coverage": "energy",
        "configuration": "energy_offshore_wind",
        "tier": 4,
        "decision": "refer",
        "premium": 10_240_000,
        "revenue": 500_000_000,
        "industry": "RENEWABLE",
        "size_band": "MID",
        "geography": "US",
        "operator_type": "SMALL_INDEPENDENT",
        "operation_segment": "RENEWABLE",
        "geographic_focus": "US_ONSHORE",
        "description": "No track record, floating wind technology, construction phase, single-asset concentration.",
        "signal_profile": "energy_offshore_wind_elevated",
        "product_type": "delay_in_start_up",
        "limit": 250_000_000,
        "deductible": 2_500_000,
        "tiv": 3_200_000_000,
        "referral_reasons": ["Technology immaturity (floating wind)", "Unproven EPC contractor", "Single-asset concentration"],
    },

    # -------------------------------------------------------------------------
    # ENERGY ONSHORE RENEWABLE
    # -------------------------------------------------------------------------
    {
        "entity_name": "NextEra Energy Resources",
        "domain": "nexteraenergyresources.com",
        "ticker": "NEE",
        "coverage": "energy",
        "configuration": "energy_onshore_renewable",
        "tier": 1,
        "decision": "approve",
        "premium": 18_500_000,
        "revenue": 28_000_000_000,
        "industry": "RENEWABLE",
        "size_band": "ENTERPRISE",
        "geography": "US",
        "operator_type": "LARGE_INDEPENDENT",
        "operation_segment": "RENEWABLE",
        "geographic_focus": "US_ONSHORE",
        "description": "Largest US onshore wind & solar. 200+ projects across 30+ states, best-in-class SCADA.",
        "signal_profile": "energy_onshore_renewable_excellent",
        "product_type": "property_damage",
        "limit": 500_000_000,
        "deductible": 2_500_000,
        "tiv": 45_000_000_000,
    },
    {
        "entity_name": "Regional Solar Developer",
        "domain": "regionalsolar.example.com",
        "ticker": None,
        "coverage": "energy",
        "configuration": "energy_onshore_renewable",
        "tier": 3,
        "decision": "refer",
        "premium": 3_250_000,
        "revenue": 350_000_000,
        "industry": "RENEWABLE",
        "size_band": "MID",
        "geography": "US",
        "operator_type": "SMALL_INDEPENDENT",
        "operation_segment": "RENEWABLE",
        "geographic_focus": "US_ONSHORE",
        "description": "15 utility solar projects, Texas-concentrated. Moderate operational history, hail zone exposure.",
        "signal_profile": "energy_onshore_renewable_standard",
        "product_type": "property_damage",
        "limit": 100_000_000,
        "deductible": 500_000,
        "tiv": 2_500_000_000,
        "referral_reasons": ["Hail exposure (Texas concentration)", "Limited portfolio diversification"],
    },
    {
        "entity_name": "Distressed Solar Developer",
        "domain": "distressedsolar.example.com",
        "ticker": None,
        "coverage": "energy",
        "configuration": "energy_onshore_renewable",
        "tier": 5,
        "decision": "decline",
        "premium": 2_800_000,
        "revenue": 80_000_000,
        "industry": "RENEWABLE",
        "size_band": "SMALL",
        "geography": "US",
        "operator_type": "SMALL_INDEPENDENT",
        "operation_segment": "RENEWABLE",
        "geographic_focus": "US_ONSHORE",
        "description": "Serial hail damage claims, panel degradation 3x manufacturer curve, PPA counterparty defaulted.",
        "signal_profile": "energy_onshore_renewable_elevated",
        "product_type": "property_damage",
        "limit": 50_000_000,
        "deductible": 250_000,
        "tiv": 800_000_000,
    },

    # -------------------------------------------------------------------------
    # ENERGY STORAGE
    # -------------------------------------------------------------------------
    {
        "entity_name": "Fluence Energy",
        "domain": "fluenceenergy.com",
        "ticker": "FLNC",
        "coverage": "energy",
        "configuration": "energy_storage",
        "tier": 1,
        "decision": "approve",
        "premium": 4_200_000,
        "revenue": 2_200_000_000,
        "industry": "RENEWABLE",
        "size_band": "LARGE",
        "geography": "US",
        "operator_type": "LARGE_INDEPENDENT",
        "operation_segment": "MIDSTREAM_STORAGE",
        "geographic_focus": "US_ONSHORE",
        "description": "Leading BESS integrator. 200+ projects, LFP chemistry, proprietary BMS, NFPA 855 compliant.",
        "signal_profile": "energy_storage_excellent",
        "product_type": "property_damage",
        "limit": 250_000_000,
        "deductible": 1_000_000,
        "tiv": 5_000_000_000,
    },
    {
        "entity_name": "Mid-Market BESS Developer",
        "domain": "midmarketbess.example.com",
        "ticker": None,
        "coverage": "energy",
        "configuration": "energy_storage",
        "tier": 3,
        "decision": "refer",
        "premium": 4_200_000,
        "revenue": 500_000_000,
        "industry": "RENEWABLE",
        "size_band": "MID",
        "geography": "US",
        "operator_type": "SMALL_INDEPENDENT",
        "operation_segment": "MIDSTREAM_STORAGE",
        "geographic_focus": "US_ONSHORE",
        "description": "NMC chemistry, adequate BMS, water-mist suppression, some pre-NFPA 855 installations.",
        "signal_profile": "energy_storage_standard",
        "product_type": "property_damage",
        "limit": 100_000_000,
        "deductible": 500_000,
        "tiv": 1_500_000_000,
        "referral_reasons": ["NMC chemistry (higher thermal runaway risk)", "Fire suppression gaps"],
    },
    {
        "entity_name": "Green Hydrogen Startup",
        "domain": "greenh2startup.example.com",
        "ticker": None,
        "coverage": "energy",
        "configuration": "energy_storage",
        "tier": 5,
        "decision": "decline",
        "premium": 3_500_000,
        "revenue": 50_000_000,
        "industry": "RENEWABLE",
        "size_band": "SMALL",
        "geography": "US",
        "operator_type": "SMALL_INDEPENDENT",
        "operation_segment": "MIDSTREAM_STORAGE",
        "geographic_focus": "US_ONSHORE",
        "description": "First-of-kind SOEC electrolyser, 700 bar storage, no operational track record.",
        "signal_profile": "energy_storage_elevated",
        "product_type": "property_damage",
        "limit": 50_000_000,
        "deductible": 250_000,
        "tiv": 500_000_000,
    },

    # -------------------------------------------------------------------------
    # ENERGY SME
    # -------------------------------------------------------------------------
    {
        "entity_name": "Diamondback Energy (Pre-Scale)",
        "domain": "diamondbackenergy.com",
        "ticker": "FANG",
        "coverage": "energy",
        "configuration": "energy_sme",
        "tier": 1,
        "decision": "approve",
        "premium": 68_000,
        "revenue": 800_000_000,
        "industry": "UPSTREAM_CONVENTIONAL",
        "size_band": "SMALL",
        "geography": "US",
        "operator_type": "MID_INDEPENDENT",
        "operation_segment": "UPSTREAM_CONVENTIONAL",
        "geographic_focus": "US_ONSHORE",
        "description": "Early-stage Permian operator. Clean OSHA record, no EPA violations, strong production consistency.",
        "signal_profile": "energy_sme_excellent",
        "product_type": "combined_property_liability",
        "limit": 25_000_000,
        "deductible": 100_000,
        "tiv": 85_000_000,
    },
    {
        "entity_name": "Small Appalachian Gas Producer",
        "domain": "appalachiangas.example.com",
        "ticker": None,
        "coverage": "energy",
        "configuration": "energy_sme",
        "tier": 3,
        "decision": "approve",
        "premium": 124_000,
        "revenue": 120_000_000,
        "industry": "UPSTREAM_CONVENTIONAL",
        "size_band": "SMALL",
        "geography": "US",
        "operator_type": "SMALL_INDEPENDENT",
        "operation_segment": "UPSTREAM_CONVENTIONAL",
        "geographic_focus": "US_ONSHORE",
        "description": "Adequate safety record, aging well inventory, minor state citations, moderate leverage.",
        "signal_profile": "energy_sme_elevated",
        "product_type": "combined_property_liability",
        "limit": 10_000_000,
        "deductible": 50_000,
        "tiv": 62_000_000,
    },
    {
        "entity_name": "Distressed Permian Operator",
        "domain": "distressedpermian.example.com",
        "ticker": None,
        "coverage": "energy",
        "configuration": "energy_sme",
        "tier": 5,
        "decision": "decline",
        "premium": 110_000,
        "revenue": 35_000_000,
        "industry": "UPSTREAM_CONVENTIONAL",
        "size_band": "MICRO",
        "geography": "US",
        "operator_type": "SMALL_INDEPENDENT",
        "operation_segment": "UPSTREAM_CONVENTIONAL",
        "geographic_focus": "US_ONSHORE",
        "description": "Multiple OSHA willful violations, EPA enforcement, recent bankruptcy, orphaned well obligations.",
        "signal_profile": "energy_sme_catastrophic",
        "product_type": "combined_property_liability",
        "limit": 10_000_000,
        "deductible": 50_000,
        "tiv": 55_000_000,
    },

    # -------------------------------------------------------------------------
    # MARINE GENERAL
    # -------------------------------------------------------------------------
    {
        "entity_name": "Maersk",
        "domain": "maersk.com",
        "ticker": "MAERSK-B",
        "coverage": "marine",
        "configuration": "marine_general",
        "tier": 1,
        "decision": "approve",
        "premium": 12_000_000,
        "revenue": 81_000_000_000,
        "industry": "CONTAINER_SHIPPING",
        "size_band": "ENTERPRISE",
        "geography": "EU",
        "operator_type": "MAJOR_LINER",
        "vessel_category": "CONTAINER",
        "trading_pattern": "LINER_REGULAR",
        "flag_state_quality": "WHITE_LIST",
        "fleet_age_band": "AGE_5_10",
        "description": "World's largest container line, excellent safety management.",
        "signal_profile": "marine_excellent",
        "product_type": "hull_machinery",
        "limit": 500_000_000,
        "deductible": 1_000_000,
        "hull_value": 25_000_000_000,
        "tiv": 25_000_000_000,
    },
    {
        "entity_name": "Pacific Basin Shipping",
        "domain": "pacificbasin.com",
        "ticker": "2343.HK",
        "coverage": "marine",
        "configuration": "marine_general",
        "tier": 2,
        "decision": "approve",
        "premium": 2_400_000,
        "revenue": 4_500_000_000,
        "industry": "DRY_BULK",
        "size_band": "LARGE",
        "geography": "APAC",
        "operator_type": "MAJOR_BULK",
        "vessel_category": "DRY_BULK",
        "trading_pattern": "SPOT_TRAMP",
        "flag_state_quality": "WHITE_LIST",
        "fleet_age_band": "AGE_10_15",
        "description": "Dry bulk specialist, modern fleet, Hong Kong flag state.",
        "signal_profile": "marine_good",
        "product_type": "hull_machinery",
        "limit": 100_000_000,
        "deductible": 500_000,
        "hull_value": 3_000_000_000,
        "tiv": 3_000_000_000,
    },
    {
        "entity_name": "Iran Shipping Lines",
        "domain": "irisl.net",
        "ticker": None,
        "coverage": "marine",
        "configuration": "marine_general",
        "tier": 5,
        "decision": "decline",
        "premium": 0,
        "revenue": 800_000_000,
        "industry": "STATE_OWNED_CARRIER",
        "size_band": "LARGE",
        "geography": "OTHER",
        "operator_type": "STATE_OWNED",
        "vessel_category": "MIXED",
        "trading_pattern": "MIXED",
        "flag_state_quality": "BLACK_LIST",
        "fleet_age_band": "AGE_25_PLUS",
        "description": "Sanctioned entity, flag state risk, aging fleet.",
        "signal_profile": "marine_sanctioned",
        "product_type": "hull_machinery",
        "limit": 50_000_000,
        "deductible": 1_000_000,
        "hull_value": 2_000_000_000,
        "tiv": 2_000_000_000,
        "referral_reasons": ["OFAC sanctions list", "Sanctioned flag state", "Fleet age >25 years average", "No classification society membership"],
    },

    # -------------------------------------------------------------------------
    # PROFESSIONAL INDEMNITY GENERAL
    # -------------------------------------------------------------------------
    {
        "entity_name": "McKinsey & Company",
        "domain": "mckinsey.com",
        "ticker": None,
        "coverage": "professional_indemnity",
        "configuration": "pi_general",
        "tier": 1,
        "decision": "approve",
        "premium": 1_500_000,
        "revenue": 16_000_000_000,
        "industry": "CONSULTING",
        "size_band": "ENTERPRISE",
        "geography": "US",
        "profession_type": "MANAGEMENT_CONSULTING",
        "firm_size": "MAJOR",
        "revenue_size": "OVER_500M",
        "description": "Global consulting leader, strong risk management, clean claims.",
        "signal_profile": "pi_excellent",
        "product_type": "professional_liability",
        "limit": 100_000_000,
        "deductible": 500_000,
    },
    {
        "entity_name": "Deloitte",
        "domain": "deloitte.com",
        "ticker": None,
        "coverage": "professional_indemnity",
        "configuration": "pi_general",
        "tier": 2,
        "decision": "approve",
        "premium": 2_200_000,
        "revenue": 65_000_000_000,
        "industry": "ACCOUNTING",
        "size_band": "ENTERPRISE",
        "geography": "US",
        "profession_type": "ACCOUNTING_FIRM",
        "firm_size": "MAJOR",
        "revenue_size": "OVER_500M",
        "description": "Big 4 firm, comprehensive QC, some audit-related claims.",
        "signal_profile": "pi_strong",
        "product_type": "errors_omissions",
        "limit": 150_000_000,
        "deductible": 1_000_000,
    },
    {
        "entity_name": "KPMG",
        "domain": "kpmg.com",
        "ticker": None,
        "coverage": "professional_indemnity",
        "configuration": "pi_general",
        "tier": 3,
        "decision": "refer",
        "premium": 3_800_000,
        "revenue": 36_000_000_000,
        "industry": "ACCOUNTING",
        "size_band": "ENTERPRISE",
        "geography": "US",
        "profession_type": "ACCOUNTING_FIRM",
        "firm_size": "MAJOR",
        "revenue_size": "OVER_500M",
        "description": "Material audit failures (Carillion, Wirecard), regulatory scrutiny.",
        "signal_profile": "pi_elevated",
        "product_type": "professional_liability",
        "limit": 150_000_000,
        "deductible": 1_000_000,
        "referral_reasons": ["Audit failure history (Carillion)", "FRC regulatory investigation", "Elevated malpractice claims frequency"],
    },

    # PI SME
    {
        "entity_name": "Bright Ideas Architecture",
        "domain": "brightideasarch.com",
        "ticker": None,
        "coverage": "professional_indemnity",
        "configuration": "pi_sme",
        "tier": 1,
        "decision": "approve",
        "premium": 3_200,
        "revenue": 8_000_000,
        "industry": "ARCHITECTURE",
        "size_band": "SMALL",
        "geography": "US",
        "description": "Boutique architecture firm, clean claims history.",
        "signal_profile": "sme_clean",
        "product_type": "professional_liability",
        "limit": 1_000_000,
        "deductible": 10_000,
    },

    # -------------------------------------------------------------------------
    # AEROSPACE GENERAL
    # -------------------------------------------------------------------------
    {
        "entity_name": "Delta Air Lines",
        "domain": "delta.com",
        "ticker": "DAL",
        "coverage": "aerospace",
        "configuration": "aerospace_general",
        "tier": 1,
        "decision": "approve",
        "premium": 45_000_000,
        "revenue": 58_000_000_000,
        "industry": "MAJOR_AIRLINE",
        "size_band": "ENTERPRISE",
        "geography": "US",
        "operator_type": "MAJOR_AIRLINE",
        "fleet_category": "NARROWBODY",
        "fleet_size": "MAJOR",
        "regulatory_framework": "FAA",
        "iosa_status": "REGISTERED",
        "description": "Top-tier safety record, modern fleet, strong financials.",
        "signal_profile": "aero_excellent",
        "product_type": "aviation_hull_liability_combined",
        "limit": 1_500_000_000,
        "deductible": 500_000,
        "hull_value": 35_000_000_000,
    },
    {
        "entity_name": "Ryanair",
        "domain": "ryanair.com",
        "ticker": "RYAAY",
        "coverage": "aerospace",
        "configuration": "aerospace_general",
        "tier": 2,
        "decision": "approve",
        "premium": 22_000_000,
        "revenue": 13_000_000_000,
        "industry": "LOW_COST_CARRIER",
        "size_band": "LARGE",
        "geography": "EU",
        "operator_type": "LOW_COST_CARRIER",
        "fleet_category": "NARROWBODY",
        "fleet_size": "LARGE",
        "regulatory_framework": "EASA",
        "iosa_status": "REGISTERED",
        "description": "Young fleet, solid safety record, cost-conscious maintenance.",
        "signal_profile": "aero_good",
        "product_type": "aviation_hull_liability_combined",
        "limit": 500_000_000,
        "deductible": 500_000,
        "hull_value": 15_000_000_000,
    },
    {
        "entity_name": "Lion Air Group",
        "domain": "lionair.co.id",
        "ticker": None,
        "coverage": "aerospace",
        "configuration": "aerospace_general",
        "tier": 4,
        "decision": "refer",
        "premium": 35_000_000,
        "revenue": 3_500_000_000,
        "industry": "LOW_COST_CARRIER",
        "size_band": "LARGE",
        "geography": "APAC",
        "operator_type": "LOW_COST_CARRIER",
        "fleet_category": "NARROWBODY",
        "fleet_size": "LARGE",
        "regulatory_framework": "OTHER_ICAO",
        "iosa_status": "EXPIRED",
        "description": "Fatal crash history (JT610), safety concerns, regulatory issues.",
        "signal_profile": "aero_elevated",
        "product_type": "aviation_hull_liability_combined",
        "limit": 500_000_000,
        "deductible": 500_000,
        "hull_value": 8_000_000_000,
        "referral_reasons": ["Fatal hull loss (JT610, 2018)", "ICAO safety audit concerns", "Maintenance quality deficiencies", "Rapid fleet expansion without proportional training"],
    },
]


# =============================================================================
# SIGNAL GENERATION PER COVERAGE
# =============================================================================

SIGNAL_PROFILES = {
    # Cyber signals (cyber_general groups: network_authority, technical_infrastructure,
    #                corporate_footprint, public_record, structured_data)
    "strong_tech": {
        "network_authority": {"security_vendor_presence": 92, "customer_quality": 85, "partner_quality": 88, "certification_authority_presence": 90, "network_centrality": 80},
        "technical_infrastructure": {"tls_configuration": 95, "security_headers": 92, "email_authentication": 95, "dnssec_status": 85, "network_exposure": 90, "software_currency": 88, "cve_exposure": 92, "cloud_infrastructure": 85, "waf_presence": 95, "cdn_usage": 90},
        "corporate_footprint": {"security_page_presence": 95, "privacy_policy_presence": 90, "security_txt_presence": 85, "bug_bounty_presence": 90, "security_hiring_activity": 88, "compliance_badges": 92},
        "public_record": {"breach_history": 92, "regulatory_actions": 90, "credential_exposure": 85, "dark_web_presence": 88},
        "structured_data": {"security_rating": 90, "esg_cyber_alignment": 82, "credit_rating": 88},
    },
    "good_tech": {
        "network_authority": {"security_vendor_presence": 78, "customer_quality": 75, "partner_quality": 72},
        "technical_infrastructure": {"tls_configuration": 82, "security_headers": 78, "email_authentication": 85, "network_exposure": 75, "cve_exposure": 72, "waf_presence": 80},
        "corporate_footprint": {"security_page_presence": 80, "privacy_policy_presence": 85, "compliance_badges": 78},
        "public_record": {"breach_history": 80, "regulatory_actions": 85, "credential_exposure": 70},
        "structured_data": {"security_rating": 78, "credit_rating": 82},
    },
    "healthcare_elevated": {
        "network_authority": {"security_vendor_presence": 55, "customer_quality": 60},
        "technical_infrastructure": {"tls_configuration": 65, "security_headers": 55, "email_authentication": 60, "network_exposure": 40, "cve_exposure": 50},
        "corporate_footprint": {"security_page_presence": 50, "privacy_policy_presence": 70},
        "public_record": {"breach_history": 35, "regulatory_actions": 45, "credential_exposure": 40},
        "structured_data": {"security_rating": 55},
    },
    "manufacturing_legacy": {
        "network_authority": {"security_vendor_presence": 50, "customer_quality": 65},
        "technical_infrastructure": {"tls_configuration": 60, "security_headers": 50, "email_authentication": 55, "network_exposure": 38, "software_currency": 35, "cve_exposure": 42},
        "corporate_footprint": {"security_page_presence": 55, "compliance_badges": 60},
        "public_record": {"breach_history": 60, "regulatory_actions": 55},
        "structured_data": {"security_rating": 52, "credit_rating": 45},
    },
    "energy_weak": {
        "network_authority": {"security_vendor_presence": 35, "customer_quality": 45},
        "technical_infrastructure": {"tls_configuration": 40, "security_headers": 35, "email_authentication": 25, "network_exposure": 30, "cve_exposure": 28},
        "corporate_footprint": {"security_page_presence": 30},
        "public_record": {"breach_history": 40, "regulatory_actions": 35, "credential_exposure": 25},
        "structured_data": {"security_rating": 35},
    },
    "catastrophic": {
        "network_authority": {"security_vendor_presence": 15, "customer_quality": 20},
        "technical_infrastructure": {"tls_configuration": 20, "security_headers": 15, "email_authentication": 10, "network_exposure": 12, "cve_exposure": 8},
        "corporate_footprint": {"security_page_presence": 10},
        "public_record": {"breach_history": 10, "regulatory_actions": 15, "credential_exposure": 5},
        "structured_data": {"security_rating": 12},
    },
    # D&O signals
    "do_excellent": {
        "governance": {"board_independence": 95, "board_diversity": 88, "ceo_chair_separation": 100, "committee_structure": 92, "compensation_structure": 85, "shareholder_rights": 90},
        "financial": {"audit_opinion": 95, "internal_controls": 92, "filing_timeliness": 98, "revenue_recognition": 90},
        "litigation": {"securities_litigation": 92, "sec_enforcement": 95, "regulatory_action": 90},
        "executive": {"executive_stability": 90, "cfo_quality": 88, "insider_trading": 92},
        "network_authority": {"auditor_quality": 95, "legal_counsel": 88, "investor_quality": 90},
        "corporate_footprint": {"investor_relations": 92, "governance_page": 90, "esg_reporting": 85},
    },
    "do_strong": {
        "governance": {"board_independence": 82, "board_diversity": 75, "committee_structure": 80},
        "financial": {"audit_opinion": 88, "internal_controls": 85, "filing_timeliness": 92},
        "litigation": {"securities_litigation": 80, "sec_enforcement": 85},
        "executive": {"executive_stability": 82, "cfo_quality": 80},
        "network_authority": {"auditor_quality": 90, "investor_quality": 82},
    },
    "do_volatile": {
        "governance": {"board_independence": 45, "ceo_chair_separation": 20, "shareholder_rights": 40},
        "financial": {"audit_opinion": 70, "internal_controls": 65, "stock_volatility": 25, "short_interest": 30},
        "litigation": {"securities_litigation": 35, "sec_enforcement": 30, "regulatory_action": 40},
        "executive": {"executive_stability": 55, "insider_trading": 35, "executive_background": 45},
        "network_authority": {"auditor_quality": 75},
    },
    "do_catastrophic": {
        "governance": {"board_independence": 20, "committee_structure": 15},
        "financial": {"audit_opinion": 10, "internal_controls": 12, "restatement": 8},
        "litigation": {"securities_litigation": 5, "sec_enforcement": 8, "derivative_litigation": 10},
        "executive": {"executive_stability": 15, "executive_background": 10},
    },
    # FI signals
    "fi_excellent": {
        "regulatory_compliance": {"examination_rating": 92, "enforcement_action": 95, "bsa_aml": 90, "fair_lending": 88},
        "financial_condition": {"capital_ratio": 95, "asset_quality": 92, "liquidity": 90, "earnings": 88},
        "governance": {"board_independence": 90, "board_expertise": 88, "risk_committee": 92},
        "network_authority": {"correspondent_quality": 90, "auditor_quality": 95, "credit_rating": 92},
    },
    "fi_strong": {
        "regulatory_compliance": {"examination_rating": 82, "enforcement_action": 88},
        "financial_condition": {"capital_ratio": 85, "asset_quality": 80, "liquidity": 78},
        "governance": {"board_independence": 80, "risk_committee": 82},
        "network_authority": {"auditor_quality": 85, "credit_rating": 80},
    },
    "fi_stressed": {
        "regulatory_compliance": {"examination_rating": 55, "enforcement_action": 60},
        "financial_condition": {"capital_ratio": 45, "asset_quality": 40, "liquidity": 35, "concentration": 25, "interest_rate_risk": 20},
        "governance": {"board_independence": 60, "risk_committee": 55},
        "operational_risk": {"litigation": 50, "breach_history": 55},
    },
    "fi_catastrophic": {
        "regulatory_compliance": {"examination_rating": 10, "enforcement_action": 5, "bsa_aml": 8},
        "financial_condition": {"capital_ratio": 12, "asset_quality": 10, "liquidity": 15},
        "governance": {"board_independence": 20},
        "operational_risk": {"litigation": 15, "breach_history": 20},
    },
    "fi_sme_clean": {
        "regulatory_compliance": {"examination_rating": 85, "enforcement_action": 90},
        "financial_condition": {"capital_ratio": 82, "asset_quality": 80},
        "cyber_security": {"tls_score": 78, "breach_history": 85},
    },
    # Energy signals
    "energy_excellent": {
        "safety_record": {"osha_trir": 92, "fatality_history": 95, "safety_certification": 90},
        "environmental": {"emissions_compliance": 88, "spill_history": 92, "environmental_certification": 85},
        "operational": {"uptime_reliability": 90, "maintenance_quality": 88, "workforce_training": 92},
        "financial_health": {"credit_rating": 90, "revenue_stability": 85, "capex_ratio": 82},
    },
    "energy_good": {
        "safety_record": {"osha_trir": 78, "fatality_history": 85},
        "environmental": {"emissions_compliance": 75, "spill_history": 80},
        "operational": {"uptime_reliability": 78, "maintenance_quality": 75},
        "financial_health": {"credit_rating": 78},
    },
    "energy_elevated": {
        "safety_record": {"osha_trir": 30, "fatality_history": 15},
        "environmental": {"emissions_compliance": 40, "spill_history": 25},
        "operational": {"uptime_reliability": 55, "maintenance_quality": 35},
        "financial_health": {"credit_rating": 40},
    },
    # Energy Upstream Deepwater profiles
    "energy_deepwater_excellent": {
        "safety_performance": {"osha_trir": 95, "bsee_incident": 92, "process_safety": 90, "fatality": 98, "bop_testing_compliance": 95, "well_control_events": 92},
        "environmental_compliance": {"epa_violation": 90, "spill_history": 95, "emissions_compliance": 88},
        "operational_telemetry": {"production_consistency": 85, "maintenance_pattern": 90, "spud_to_production": 88},
        "asset_portfolio": {"asset_age": 90, "concentration": 80, "subsea_equipment_age": 88, "water_depth_profile": 75, "metocean_exposure": 70},
        "financial_stability": {"credit_rating": 92, "leverage": 85},
        "network_authority": {"partner_quality": 91, "rig_contractor_quality": 90},
    },
    "energy_deepwater_elevated": {
        "safety_performance": {"osha_trir": 55, "process_safety": 40, "bop_testing_compliance": 60, "well_control_events": 50},
        "environmental_compliance": {"epa_violation": 55, "spill_history": 50},
        "operational_telemetry": {"production_consistency": 55, "maintenance_pattern": 50},
        "asset_portfolio": {"asset_age": 35, "subsea_equipment_age": 40, "water_depth_profile": 50},
        "financial_stability": {"credit_rating": 55, "leverage": 45},
    },
    "energy_deepwater_catastrophic": {
        "safety_performance": {"osha_trir": 15, "fatality": 10, "process_safety": 12, "bop_testing_compliance": 20, "well_control_events": 15},
        "environmental_compliance": {"epa_violation": 15, "spill_history": 10},
        "asset_portfolio": {"asset_age": 20, "concentration": 10, "subsea_equipment_age": 15},
        "financial_stability": {"credit_rating": 20, "leverage": 15},
    },
    # Energy Upstream Onshore profiles
    "energy_upstream_onshore_excellent": {
        "safety_performance": {"osha_trir": 92, "process_safety": 88, "fatality": 95, "h2s_exposure": 85, "state_regulatory_compliance": 92},
        "environmental_compliance": {"epa_violation": 90, "spill_history": 88, "produced_water_management": 90},
        "operational_telemetry": {"production_consistency": 90, "well_integrity": 88, "artificial_lift_reliability": 85},
        "asset_portfolio": {"asset_age": 82, "well_vintage_profile": 80, "permit_status": 90},
        "financial_stability": {"credit_rating": 90, "leverage": 85},
    },
    "energy_upstream_onshore_standard": {
        "safety_performance": {"osha_trir": 60, "process_safety": 55, "h2s_exposure": 50, "state_regulatory_compliance": 55},
        "environmental_compliance": {"epa_violation": 55, "produced_water_management": 50},
        "operational_telemetry": {"production_consistency": 55, "artificial_lift_reliability": 50},
        "asset_portfolio": {"asset_age": 40, "well_vintage_profile": 45},
        "financial_stability": {"credit_rating": 55, "leverage": 35},
    },
    "energy_upstream_onshore_distressed": {
        "safety_performance": {"osha_trir": 15, "process_safety": 12, "state_regulatory_compliance": 10},
        "environmental_compliance": {"epa_violation": 10, "spill_history": 15},
        "asset_portfolio": {"asset_age": 15, "well_vintage_profile": 10},
        "financial_stability": {"credit_rating": 15, "leverage": 10},
    },
    # Energy Upstream Unconventional profiles
    "energy_unconventional_excellent": {
        "safety_performance": {"osha_trir": 95, "process_safety": 90, "fatality": 98},
        "environmental_compliance": {"epa_violation": 92, "water_recycling_rate": 95, "induced_seismicity_score": 90},
        "operational_telemetry": {"frac_fleet_quality": 92, "completion_efficiency": 90, "pad_drilling_intensity": 85},
        "asset_portfolio": {"well_spacing_optimisation": 90, "asset_age": 88},
        "financial_stability": {"credit_rating": 92, "leverage": 88},
    },
    "energy_unconventional_elevated": {
        "safety_performance": {"osha_trir": 55, "process_safety": 50},
        "environmental_compliance": {"water_recycling_rate": 50, "induced_seismicity_score": 45},
        "operational_telemetry": {"frac_fleet_quality": 50, "completion_efficiency": 45},
        "asset_portfolio": {"well_spacing_optimisation": 40, "asset_age": 50},
        "financial_stability": {"credit_rating": 50, "restructuring": 40},
    },
    "energy_unconventional_distressed": {
        "safety_performance": {"osha_trir": 12, "process_safety": 10, "fatality": 8},
        "environmental_compliance": {"induced_seismicity_score": 10, "epa_violation": 12},
        "operational_telemetry": {"frac_fleet_quality": 15},
        "financial_stability": {"credit_rating": 12, "leverage": 8},
    },
    # Energy Midstream profiles
    "energy_midstream_excellent": {
        "safety_performance": {"osha_trir": 90, "phmsa_compliance": 95},
        "environmental_compliance": {"epa_violation": 88, "spill_history": 92},
        "operational_telemetry": {"inline_inspection": 95, "cathodic_protection": 92, "scada_maturity": 90, "throughput_consistency": 88},
        "asset_portfolio": {"pipeline_vintage": 82, "right_of_way": 90, "concentration": 85},
        "financial_stability": {"credit_rating": 92, "leverage": 85},
    },
    "energy_midstream_good": {
        "safety_performance": {"osha_trir": 75, "phmsa_compliance": 78},
        "operational_telemetry": {"inline_inspection": 78, "cathodic_protection": 75, "scada_maturity": 72},
        "asset_portfolio": {"pipeline_vintage": 70, "right_of_way": 75},
        "financial_stability": {"credit_rating": 78, "leverage": 72},
    },
    "energy_midstream_elevated": {
        "safety_performance": {"osha_trir": 40, "phmsa_compliance": 35},
        "environmental_compliance": {"epa_violation": 45, "spill_history": 35},
        "operational_telemetry": {"inline_inspection": 35, "cathodic_protection": 30},
        "asset_portfolio": {"pipeline_vintage": 25, "right_of_way": 30},
        "financial_stability": {"credit_rating": 40, "leverage": 30},
    },
    # Energy Downstream profiles
    "energy_downstream_excellent": {
        "safety_performance": {"osha_trir": 95, "process_safety": 92, "psm_audit_findings": 95},
        "operational_telemetry": {"mechanical_integrity": 90, "maintenance_pattern": 92},
        "asset_portfolio": {"turnaround_compliance": 95, "feedstock_complexity": 75, "asset_age": 82, "process_unit_count": 80},
        "financial_stability": {"credit_rating": 90, "bi_exposure_ratio": 80},
        "corporate_footprint": {"safety_communication": 88, "esg_reporting": 85},
    },
    "energy_downstream_elevated": {
        "safety_performance": {"osha_trir": 55, "process_safety": 50, "psm_audit_findings": 48},
        "operational_telemetry": {"mechanical_integrity": 50, "maintenance_pattern": 48},
        "asset_portfolio": {"turnaround_compliance": 40, "feedstock_complexity": 50, "asset_age": 40},
        "financial_stability": {"credit_rating": 50, "leverage": 35},
    },
    "energy_downstream_catastrophic": {
        "safety_performance": {"osha_trir": 10, "process_safety": 8, "psm_audit_findings": 12},
        "asset_portfolio": {"turnaround_compliance": 10, "concentration": 5, "asset_age": 12},
        "financial_stability": {"credit_rating": 10, "restructuring": 8},
    },
    # Energy Offshore Wind profiles
    "energy_offshore_wind_excellent": {
        "safety_performance": {"osha_trir": 88, "crew_transfer_safety": 90},
        "construction_quality": {"epc_contractor_quality": 95, "commissioning_defects": 92, "epc_track_record": 95, "installation_vessel_quality": 92},
        "operational_telemetry": {"capacity_factor": 90, "grid_interconnection": 88, "degradation_rate": 85},
        "asset_portfolio": {"technology_maturity": 92, "natcat_exposure": 75, "marine_weather_exposure": 70, "turbine_platform_generation": 90, "cable_route_risk": 80},
        "financial_stability": {"credit_rating": 92, "offtake_contract_quality": 95, "ppa_quality": 95},
    },
    "energy_offshore_wind_standard": {
        "safety_performance": {"osha_trir": 60, "crew_transfer_safety": 55},
        "construction_quality": {"epc_contractor_quality": 60, "commissioning_defects": 55, "installation_vessel_quality": 55},
        "asset_portfolio": {"technology_maturity": 45, "turbine_platform_generation": 45, "marine_weather_exposure": 55},
        "financial_stability": {"credit_rating": 70, "offtake_contract_quality": 60},
    },
    "energy_offshore_wind_elevated": {
        "safety_performance": {"osha_trir": 40},
        "construction_quality": {"epc_contractor_quality": 35, "commissioning_defects": 30, "installation_vessel_quality": 30},
        "asset_portfolio": {"technology_maturity": 30, "concentration": 20, "marine_weather_exposure": 35},
        "financial_stability": {"credit_rating": 45},
    },
    # Energy Onshore Renewable profiles
    "energy_onshore_renewable_excellent": {
        "safety_performance": {"osha_trir": 88},
        "construction_quality": {"epc_contractor_quality": 90, "commissioning_defects": 88},
        "operational_telemetry": {"capacity_factor": 92, "inverter_reliability": 90, "curtailment_rate": 85, "degradation_rate": 88},
        "asset_portfolio": {"hail_exposure": 80, "panel_technology_vintage": 85, "portfolio_geographic_spread": 95, "natcat_exposure": 75, "technology_maturity": 92},
        "financial_stability": {"credit_rating": 90, "ppa_quality": 88},
    },
    "energy_onshore_renewable_standard": {
        "safety_performance": {"osha_trir": 60},
        "construction_quality": {"epc_contractor_quality": 55},
        "operational_telemetry": {"capacity_factor": 58, "inverter_reliability": 55, "curtailment_rate": 50},
        "asset_portfolio": {"hail_exposure": 35, "panel_technology_vintage": 50, "portfolio_geographic_spread": 40, "technology_maturity": 60},
        "financial_stability": {"ppa_quality": 50},
    },
    "energy_onshore_renewable_elevated": {
        "asset_portfolio": {"hail_exposure": 15, "panel_technology_vintage": 20, "portfolio_geographic_spread": 15, "natcat_exposure": 15},
        "operational_telemetry": {"capacity_factor": 25, "inverter_reliability": 20},
        "financial_stability": {"ppa_quality": 20},
    },
    # Energy Storage profiles
    "energy_storage_excellent": {
        "safety_performance": {"osha_trir": 85, "safety_standard_compliance": 95},
        "construction_quality": {"epc_contractor_quality": 92, "commissioning_defects": 90},
        "operational_telemetry": {"bms_sophistication": 95, "capacity_factor": 88},
        "asset_portfolio": {"thermal_management_system": 95, "fire_suppression_capability": 95, "cell_format_maturity": 88, "technology_maturity": 90},
        "financial_stability": {"credit_rating": 88},
    },
    "energy_storage_standard": {
        "safety_performance": {"safety_standard_compliance": 55},
        "construction_quality": {"epc_contractor_quality": 55},
        "operational_telemetry": {"bms_sophistication": 50},
        "asset_portfolio": {"thermal_management_system": 50, "fire_suppression_capability": 40, "cell_format_maturity": 50, "technology_maturity": 55},
        "financial_stability": {"credit_rating": 55},
    },
    "energy_storage_elevated": {
        "safety_performance": {"safety_standard_compliance": 15},
        "asset_portfolio": {"thermal_management_system": 12, "fire_suppression_capability": 10, "technology_maturity": 10, "hydrogen_storage_pressure": 15},
        "financial_stability": {"credit_rating": 15},
    },
    # Energy SME profiles
    "energy_sme_excellent": {
        "safety_performance": {"osha_trir": 90, "osha_violations": 92, "process_safety": 85, "fatality": 95},
        "environmental_compliance": {"epa_violation": 88, "spill_history": 90, "emissions_compliance": 85},
        "operational_telemetry": {"production_consistency": 88, "well_integrity": 85, "maintenance_pattern": 82},
        "financial_stability": {"credit_rating": 85, "leverage": 80, "capex_trend": 82},
        "asset_portfolio": {"asset_age": 80, "concentration": 75, "permit_status": 88},
    },
    "energy_sme_elevated": {
        "safety_performance": {"osha_trir": 55, "osha_violations": 50, "process_safety": 48},
        "environmental_compliance": {"epa_violation": 50, "spill_history": 48},
        "operational_telemetry": {"production_consistency": 52, "well_integrity": 48},
        "financial_stability": {"credit_rating": 50, "leverage": 42},
        "asset_portfolio": {"asset_age": 45, "concentration": 40},
    },
    "energy_sme_catastrophic": {
        "safety_performance": {"osha_trir": 10, "osha_violations": 8, "fatality": 12},
        "environmental_compliance": {"epa_violation": 8, "spill_history": 10},
        "financial_stability": {"credit_rating": 10, "restructuring": 5},
        "asset_portfolio": {"asset_age": 12, "permit_status": 10},
    },
    # Marine signals
    "marine_excellent": {
        "safety_management": {"ism_compliance": 95, "port_state_control": 92, "casualty_record": 90},
        "fleet_quality": {"fleet_age": 88, "classification_society": 95, "flag_state_quality": 90},
        "operational": {"crew_certification": 92, "navigation_equipment": 90, "maintenance_standard": 88},
    },
    "marine_good": {
        "safety_management": {"ism_compliance": 82, "port_state_control": 78, "casualty_record": 80},
        "fleet_quality": {"fleet_age": 75, "classification_society": 82, "flag_state_quality": 78},
    },
    "marine_sanctioned": {
        "safety_management": {"ism_compliance": 10, "port_state_control": 5, "casualty_record": 15},
        "fleet_quality": {"fleet_age": 8, "classification_society": 5, "flag_state_quality": 5},
    },
    # PI signals
    "pi_excellent": {
        "professional_standards": {"certification_status": 92, "peer_review": 90, "continuing_education": 88},
        "claims_history": {"frequency": 95, "severity": 92, "reserves": 88},
        "client_quality": {"client_concentration": 85, "engagement_quality": 90, "conflict_management": 88},
    },
    "pi_strong": {
        "professional_standards": {"certification_status": 82, "peer_review": 78},
        "claims_history": {"frequency": 85, "severity": 80},
        "client_quality": {"client_concentration": 75, "engagement_quality": 78},
    },
    "pi_elevated": {
        "professional_standards": {"certification_status": 60, "peer_review": 45},
        "claims_history": {"frequency": 40, "severity": 35},
        "client_quality": {"client_concentration": 55},
    },
    # Aerospace signals
    "aero_excellent": {
        "safety_record": {"accident_rate": 95, "incident_rate": 92, "faa_compliance": 95},
        "fleet_quality": {"fleet_age": 90, "airworthiness": 95, "maintenance_program": 92},
        "operations": {"pilot_training": 95, "route_risk": 85, "load_factor": 80},
        "financial": {"credit_rating": 88, "profitability": 85},
    },
    "aero_good": {
        "safety_record": {"accident_rate": 82, "incident_rate": 78, "faa_compliance": 85},
        "fleet_quality": {"fleet_age": 85, "airworthiness": 88},
        "operations": {"pilot_training": 82, "route_risk": 78},
    },
    "aero_elevated": {
        "safety_record": {"accident_rate": 25, "incident_rate": 30, "faa_compliance": 40},
        "fleet_quality": {"fleet_age": 55, "airworthiness": 45, "maintenance_program": 35},
        "operations": {"pilot_training": 40, "route_risk": 35},
    },
    # Generic SME profiles
    "sme_clean": {
        "technical_security": {"tls_configuration": 80, "email_authentication": 78, "security_headers": 75},
        "public_record": {"breach_history": 90, "security_rating": 78},
        "corporate_footprint": {"security_page_presence": 70, "privacy_policy_presence": 75},
    },
    "sme_moderate": {
        "technical_security": {"tls_configuration": 65, "email_authentication": 60, "security_headers": 55},
        "public_record": {"breach_history": 72, "security_rating": 60},
        "corporate_footprint": {"security_page_presence": 55, "privacy_policy_presence": 60},
    },
    "sme_weak": {
        "technical_security": {"tls_configuration": 40, "email_authentication": 30, "security_headers": 35},
        "public_record": {"breach_history": 35, "security_rating": 40},
        "corporate_footprint": {"security_page_presence": 25},
    },
}


def resolve_signal_scores(profile_name):
    """Roll each signal's score ONCE from the profile.

    Returns a dict keyed by (group_id, signal_id) -> resolved_score.
    All downstream tables (signal_cache, signal_outputs, model_version_signals,
    signal_audit_records) must use these values to stay consistent.
    """
    profile = SIGNAL_PROFILES.get(profile_name, {})
    resolved = {}
    for group_id, signals in profile.items():
        for signal_id, base_score in signals.items():
            resolved[(group_id, signal_id)] = _score(base_score, 5)
    return resolved


def build_synthetic_signal_outputs(config, resolved_scores, default_score=50.0, jitter=5):
    """Build SignalOutput dataclass instances using the production config's signal registry.

    Iterates every signal in config.signal_registry that has three_layer_assessment.
    Uses resolved_scores for signals we have profile data for; defaults to
    default_score for signals not covered by the profile.

    Args:
        config: Compiled coverage config
        resolved_scores: Dict keyed by (group_id, signal_id) -> score
        default_score: Score used for signals not in the profile.
            Tier-aligned defaults (e.g. 82 for tier 1, 35 for tier 5)
            prevent score compression where sparse profiles drag composites
            away from the intended tier band.
        jitter: Random variance applied to default scores (±jitter).
            Use 5 for curated profiles, 15 for synthetic companies.
    """
    signal_outputs = []

    for signal_def in config.signal_registry:
        if not signal_def.three_layer_assessment:
            continue

        tla = signal_def.three_layer_assessment
        group_id = tla.group_id
        weight = tla.risk.weight if tla.risk else 0.0

        # Look up score from resolved_scores keyed by (group_id, signal_id) tuples
        score = resolved_scores.get((group_id, signal_def.id))
        if score is None:
            # Try matching by signal_id alone (may appear under a different group)
            for (g, s), v in resolved_scores.items():
                if s == signal_def.id:
                    score = v
                    break
        if score is None:
            score = _score(default_score, jitter)  # Jittered default aligned to intended tier

        signal_outputs.append(SignalOutput(
            signal_id=signal_def.id,
            signal_name=signal_def.id.replace("_", " ").title(),
            group_id=group_id,
            raw_score=score,
            confidence=round(random.uniform(0.7, 0.99), 2),
            weighted_score=score * weight,
            weight=weight,
            data_sources=["seed"],
            extracted_at=utcnow(),
            execution_time_ms=round(random.uniform(50, 800), 1),
        ))

    return signal_outputs


def build_synthetic_categorical_outputs(config, co):
    """Build CategoricalOutput instances from config's categorical signal definitions.

    Maps company metadata (industry, size_band, geography) to the config's
    categorical group features to get the correct modifier values.
    """
    categorical_outputs = []

    # Build a map of group_id -> company field value
    field_value_map = {
        "industry_classification": co.get("industry", "OTHER"),
        "size_band": co.get("size_band", "MEDIUM"),
        "geography": co.get("geography", "US"),
    }

    for signal_def in config.signal_registry:
        if not signal_def.categories:
            continue

        cat_def = signal_def.categories
        group_id = cat_def.group_id

        # Find the matching category group for label
        cat_group = None
        for cg in config.groups.categories:
            if cg.id == group_id:
                cat_group = cg
                break

        group_name = cat_group.label if cat_group else group_id
        default_cat = cat_group.default_cat if cat_group else "OTHER"

        # Determine which category value applies
        # Try source field first (e.g. "metadata.industry")
        selected_cat = None
        if cat_def.source:
            field_name = cat_def.source.replace("metadata.", "")
            selected_cat = co.get(field_name)

        # Fallback: try the group_id in our field map, then direct company field
        if selected_cat is None:
            selected_cat = field_value_map.get(group_id)
        if selected_cat is None:
            selected_cat = co.get(group_id)

        if selected_cat is None:
            selected_cat = default_cat

        # Find modifier from features
        modifier = 1.0
        label = selected_cat
        matched = False
        for feat in cat_def.features:
            if feat.cat == selected_cat:
                modifier = feat.applied if feat.applied is not None else 1.0
                label = feat.label or selected_cat
                matched = True
                break

        # If no match, try default_cat
        if not matched and default_cat:
            for feat in cat_def.features:
                if feat.cat == default_cat:
                    modifier = feat.applied if feat.applied is not None else 1.0
                    label = feat.label or default_cat
                    selected_cat = default_cat
                    break

        categorical_outputs.append(CategoricalOutput(
            group_id=group_id,
            group_name=group_name,
            category=selected_cat,
            label=label,
            modifier=modifier,
            confidence=round(random.uniform(0.8, 0.99), 2),
            extracted_at=utcnow(),
        ))

    return categorical_outputs


def run_production_scoring(config, signal_outputs):
    """Run Steps 5-6 through the production ModelScorer.

    Uses scorer.calculate_composite() for weighted group scores and composite,
    and scorer.evaluate_signal_conditions() for config-defined conditions.

    Returns (composite, group_scores, confidence, coverage,
             conditions, tier_overrides, referrals, notes, signal_modifiers)
    """
    composite, group_scores, confidence, signal_coverage = _scorer.calculate_composite(
        signal_outputs=signal_outputs,
        config=config,
    )
    conditions, tier_overrides, referrals, notes, signal_modifiers = _scorer.evaluate_signal_conditions(
        signal_outputs=signal_outputs,
        group_scores=group_scores,
        config=config,
    )
    return (composite, group_scores, confidence, signal_coverage,
            conditions, tier_overrides, referrals, notes, signal_modifiers)


def run_production_query_evaluation(config, direct_query_responses):
    """Run Step 7 through the production QueryEvaluator.

    Returns the QueryEvaluationResult with conditions, tier_overrides,
    referrals, notes, and modifiers — all derived from config.yaml definitions.
    """
    return _query_evaluator.evaluate_queries(
        responses=direct_query_responses,
        config=config,
    )


def run_production_pricing(config, composite, signal_tier_overrides,
                           query_tier_overrides, all_modifiers,
                           categorical_outputs, submission_data):
    """Run Steps 8-12 through the production ModelPricer.

    Returns PricingResult with tier resolution, base premium, modifiers,
    ILF scaling, and final premium — all from config.yaml definitions.
    """
    return _pricer.price_submission(
        pure_composite_score=composite,
        signal_tier_overrides=signal_tier_overrides,
        query_tier_overrides=query_tier_overrides,
        query_modifiers=all_modifiers,
        categorical_outputs=categorical_outputs,
        submission_data=submission_data,
        config=config,
    )


def build_submission_data(co):
    """Build the submission_data JSONB field."""
    data = {
        "revenue": co.get("revenue", 0),
        "industry": co.get("industry", "OTHER"),
        "size_band": co.get("size_band", "MEDIUM"),
        "geography": co.get("geography", "US"),
        "product_type": co.get("product_type", ""),
        "limit": co.get("limit", 1_000_000),
        "deductible": co.get("deductible", 50_000),
    }
    if co.get("total_assets"):
        data["total_assets"] = co["total_assets"]
    if co.get("tiv"):
        data["tiv"] = co["tiv"]
    if co.get("hull_value"):
        data["hull_value"] = co["hull_value"]
    return data


def build_direct_query_responses(co, config):
    """Build direct_query_responses using the config's actual query IDs.

    Iterates config.direct_queries to discover what queries exist,
    then generates plausible boolean responses based on the company's
    risk tier. Higher tiers (worse risk) answer risk-affirmative queries True.
    """
    tier = co["tier"]
    responses = {}

    for query in config.direct_queries:
        qid = query.id

        # Determine the "risk-affirmative" response for each query by
        # inspecting its conditions — which response triggers REFER/MODIFIER
        risk_response = True  # default: True is the risky answer
        for qc in query.query_condition:
            if qc.action.value in ("REFER", "MODIFIER"):
                risk_response = qc.return_value
                break

        # Assign response based on tier:
        # Tier 1-2: safe answer, Tier 3: mixed, Tier 4-5: risky answer
        if tier <= 2:
            responses[qid] = not risk_response
        elif tier == 3:
            # 50/50 for tier 3 — some queries trigger, some don't
            responses[qid] = random.choice([risk_response, not risk_response])
        else:
            responses[qid] = risk_response

    return responses


def build_discovery_output(co):
    """Build discovery_output for the ModelVersionRecord."""
    return {
        "entity_name": co["entity_name"],
        "discovered_domain": co["domain"],
        "domain_confidence": round(random.uniform(0.85, 0.99), 2),
        "discovery_method": "dns_lookup",
        "ip_addresses": [f"104.{random.randint(16,31)}.{random.randint(0,255)}.{random.randint(1,254)}"],
        "nameservers": [f"ns1.{co['domain']}", f"ns2.{co['domain']}"],
        "mx_records": [f"mail.{co['domain']}"],
        "registrar": random.choice(["Cloudflare", "GoDaddy", "MarkMonitor", "CSC Global"]),
        "country": co.get("geography", "US"),
        "industry_inferred": co.get("industry", "OTHER"),
        "employee_estimate": random.choice([50, 200, 500, 1000, 5000, 10000, 50000, 100000]),
    }


def build_tier_margin(composite, final_tier, config):
    """Build tier margin context from composite score and config tier bands.

    Computes percentile within current tier, distances to adjacent tier
    boundaries, and adjacent tier IDs — same as pricer.calculate_tier_margin().
    """
    bands = config.risk_tier_bands.bands
    current_band = None
    band_idx = None
    for idx, band in enumerate(bands):
        if band.id == final_tier:
            current_band = band
            band_idx = idx
            break

    if current_band is None:
        return {}

    tier_min = current_band.interpretation.bands.min
    tier_max = current_band.interpretation.bands.max
    span = tier_max - tier_min
    percentile = (composite - tier_min) / span if span > 0 else 0.5
    percentile = max(0.0, min(1.0, percentile))

    # Adjacent tiers (lower ID = better tier)
    adjacent_better = bands[band_idx - 1].id if band_idx > 0 else None
    adjacent_worse = bands[band_idx + 1].id if band_idx < len(bands) - 1 else None

    # Always compute distances — even at boundary tiers these show
    # headroom within the tier (e.g. 150 points from ceiling in best tier)
    distance_better = composite - tier_min
    distance_worse = tier_max - composite

    return {
        "tier_margin_percentile": round(percentile, 4),
        "tier_margin_tier_min": tier_min,
        "tier_margin_tier_max": tier_max,
        "tier_margin_distance_better": round(distance_better, 2),
        "tier_margin_distance_worse": round(distance_worse, 2),
        "tier_margin_adjacent_better": adjacent_better,
        "tier_margin_adjacent_worse": adjacent_worse,
    }


def build_tier_band_interpretation(final_tier, config):
    """Snapshot ALL tier bands from config, marking the current tier.

    Provides full tier landscape so underwriters can see adjacent tiers'
    actions, score ranges, and pricing applications alongside the current tier.
    """
    if not config.risk_tier_bands or not config.risk_tier_bands.bands:
        return None

    def _band_dict(band):
        return {
            "tier_id": band.id,
            "label": band.label,
            "description": band.description,
            "action": band.interpretation.action.value,
            "bands": {"min": band.interpretation.bands.min, "max": band.interpretation.bands.max},
            "application": {
                "method": band.interpretation.application.method.value if hasattr(band.interpretation.application.method, 'value') else str(band.interpretation.application.method),
                "value": band.interpretation.application.value,
                "applied": band.interpretation.application.applied,
                "basis": band.interpretation.application.basis,
            },
        }

    return {
        "current_tier": final_tier,
        "tiers": [_band_dict(b) for b in config.risk_tier_bands.bands],
    }


def build_loss_band_interpretation(config):
    """Snapshot loss tier band config into JSONB for audit trail."""
    if not config.loss_tier_bands:
        return None
    result = {"bands": [], "constraints": None}
    for band in config.loss_tier_bands.bands:
        result["bands"].append({
            "id": band.id,
            "label": band.label,
            "bands": {"min": band.interpretation.bands.min, "max": band.interpretation.bands.max},
            "frequency_modifier": band.interpretation.application.frequency_modifier,
            "severity_modifier": band.interpretation.application.severity_modifier,
        })
    if config.loss_tier_bands.constraints:
        c = config.loss_tier_bands.constraints
        result["constraints"] = {
            "floor": c.floor,
            "cap": c.cap,
        }
    return result


def build_exposure_band_interpretation(config):
    """Snapshot exposure config (size/complexity bands) into JSONB."""
    if not config.exposure:
        return None
    result = {}
    if config.exposure.size:
        result["size"] = {
            "weight": config.exposure.size.weight,
            "bands": [
                {
                    "id": b.id, "label": b.label,
                    "bands": {"min": b.interpretation.bands.min, "max": b.interpretation.bands.max},
                    "modifier": b.interpretation.application.applied,
                }
                for b in config.exposure.size.bands
            ],
        }
    if config.exposure.complexity:
        result["complexity"] = {
            "weight": config.exposure.complexity.weight,
            "bands": [
                {
                    "id": b.id, "label": b.label,
                    "bands": {"min": b.interpretation.bands.min, "max": b.interpretation.bands.max},
                    "modifier": b.interpretation.application.applied,
                }
                for b in config.exposure.complexity.bands
            ],
        }
    return result if result else None


def build_loss_correlation_config():
    """Snapshot the loss correlation calculation config for client-side recalculation.

    Captures: band thresholds, multiplier maps, combination weights, and caps.
    This allows the frontend ScenarioTab to recalculate loss_combined_modifier
    from overridden signal scores without a backend round-trip.
    """
    return {
        "frequency_weight": 0.6,
        "severity_weight": 0.4,
        "frequency_impact_floor": 0.60,
        "frequency_impact_cap": 1.50,
        "severity_impact_floor": 0.70,
        "severity_impact_cap": 1.50,
        "propensity_bands": [
            {"name": "very_low", "min_score": 0, "max_score": 20, "frequency_multiplier": 0.60},
            {"name": "low", "min_score": 20, "max_score": 40, "frequency_multiplier": 0.80},
            {"name": "moderate", "min_score": 40, "max_score": 60, "frequency_multiplier": 1.00},
            {"name": "elevated", "min_score": 60, "max_score": 80, "frequency_multiplier": 1.25},
            {"name": "high", "min_score": 80, "max_score": 100, "frequency_multiplier": 1.50},
        ],
        "severity_bands": [
            {"name": "minimal", "min_score": 0, "max_score": 20, "severity_multiplier": 0.70},
            {"name": "moderate", "min_score": 20, "max_score": 40, "severity_multiplier": 0.90},
            {"name": "significant", "min_score": 40, "max_score": 60, "severity_multiplier": 1.10},
            {"name": "severe", "min_score": 60, "max_score": 80, "severity_multiplier": 1.30},
            {"name": "catastrophic", "min_score": 80, "max_score": 100, "severity_multiplier": 1.50},
        ],
    }


def build_ilf_curve_config(config, product_type):
    """Snapshot ILF curve parameters for client-side limit recalculation."""
    pt_pricing = config.pricing.by_product_type.get(product_type) if config.pricing else None
    if not pt_pricing or not pt_pricing.ilf_curve:
        return None
    curve = pt_pricing.ilf_curve
    return {
        "anchor_limit": curve.anchor_limit,
        "curve": curve.curve,
        "params": curve.params or {},
    }


def build_deductible_factor_table(config):
    """Snapshot all deductible factor tables across product types."""
    if not config.pricing or not config.pricing.by_product_type:
        return None
    result = {}
    for pt_name, pt_pricing in config.pricing.by_product_type.items():
        if pt_pricing.deductible_factors:
            result[pt_name] = [
                {"deductible": df.deductible, "factor": df.factor}
                for df in pt_pricing.deductible_factors
            ]
    return result if result else None


def build_exposure_modifier_config(config):
    """Snapshot exposure modifier config (size curve, thresholds) for client-side recalc."""
    # For config-band-based exposure (the common path in DSI)
    # the exposure_band_interpretation already captures the band lookup.
    # This captures any additional traditional modifier config if present.
    if not config.exposure:
        return None
    result = {
        "method": "config_band_lookup",
    }
    # If size bands exist, snapshot as a simple lookup
    if config.exposure.size and config.exposure.size.bands:
        result["size_curve"] = [
            {
                "label": b.label,
                "min": b.interpretation.bands.min,
                "max": b.interpretation.bands.max,
                "modifier": b.interpretation.application.applied,
            }
            for b in config.exposure.size.bands
        ]
        result["size_weight"] = config.exposure.size.weight
    if config.exposure.complexity and config.exposure.complexity.bands:
        result["complexity_curve"] = [
            {
                "label": b.label,
                "min": b.interpretation.bands.min,
                "max": b.interpretation.bands.max,
                "modifier": b.interpretation.application.applied,
            }
            for b in config.exposure.complexity.bands
        ]
        result["complexity_weight"] = config.exposure.complexity.weight
    return result


def build_guardrails_config(config):
    """Snapshot guardrail thresholds for client-side premium capping."""
    if not config.guardrails:
        return None
    g = config.guardrails
    return {
        "modifier_floor": g.modifier_floor,
        "modifier_cap": g.modifier_cap,
        "max_premium_to_limit_ratio": g.max_premium_to_limit_ratio,
        "max_premium_to_revenue_ratio": g.max_premium_to_revenue_ratio,
        "max_ilf_factor": g.max_ilf_factor,
    }


def build_rol_recommendation(limit_premiums, requested_limit):
    """Build ROL dual recommendation from limit_premiums menu.

    Returns dict of rol_* columns for ModelVersionRecord, or empty dict.
    """
    if not limit_premiums:
        return {}

    recommender = ROLRecommender(validator=ROLValidator())
    try:
        rec = recommender.recommend(
            limit_premiums=limit_premiums,
            requested_limit=requested_limit,
        )
    except Exception as e:
        logger.warning("ROL recommendation failed: %s", e)
        return {}

    return {
        "rol_upper_limit": rec.upper.limit if rec.upper.limit > 0 else None,
        "rol_upper_premium": rec.upper.premium if rec.upper.limit > 0 else None,
        "rol_upper_rol": rec.upper.rol if rec.upper.limit > 0 else None,
        "rol_upper_rationale": rec.upper.rationale or None,
        "rol_lower_limit": rec.lower.limit if rec.lower.limit > 0 else None,
        "rol_lower_premium": rec.lower.premium if rec.lower.limit > 0 else None,
        "rol_lower_rol": rec.lower.rol if rec.lower.limit > 0 else None,
        "rol_lower_rationale": rec.lower.rationale or None,
        "rol_structure_type": rec.structure_type,
    }


def build_loss_propensity(co, group_scores):
    """Build loss propensity columns derived from actual signal group scores.

    Loss Modifier Calculation Chain
    ================================
    The loss modifier combines FREQUENCY and SEVERITY propensity, both derived
    from signal group scores:

    1. FREQUENCY PROPENSITY (weight: 0.6 in combined modifier):
       - Input: signal group scores weighted by each group's loss_weight
       - Inverted: high risk_score (good) → low frequency propensity (good)
       - loss_propensity_score = 100 - weighted_avg(group_scores)
       - Mapped to band: very_low / low / moderate / elevated / high
       - Band → frequency_multiplier (0.60 .. 1.50)

    2. SEVERITY PROPENSITY (weight: 0.4 in combined modifier):
       - Slight random offset from frequency score
       - severity_propensity_score
       - Mapped to band: minimal / moderate / significant / severe / catastrophic
       - Band → severity_multiplier (0.70 .. 1.50)

    3. COMBINED MODIFIER:
       loss_combined_modifier = (frequency_multiplier × 0.6) + (severity_multiplier × 0.4)
       This is what gets applied to the premium as the "loss_propensity" modifier.

    4. TREND / VELOCITY (freq/sev splits + combined):
       - Previous scores: random jitter from current (simulates prior period)
       - Velocity: rate of change in points/month
       - Trend direction: stable / improving / deteriorating
       - Combined values are weighted averages (0.6 freq + 0.4 sev)
    """
    # Derive loss propensity score from group scores using loss weights
    loss_weighted_sum = 0.0
    loss_weight_total = 0.0
    for gid, gs in group_scores.items():
        lw = gs.get("loss_weight")
        if lw and lw > 0:
            loss_weighted_sum += gs["risk_score"] * lw
            loss_weight_total += lw

    # Loss propensity: invert so high risk_score → low loss propensity
    # (high scores are good, high loss propensity is bad)
    if loss_weight_total > 0:
        avg_signal_score = loss_weighted_sum / loss_weight_total  # 0-100, high=good
        loss_score = round(100.0 - avg_signal_score, 2)          # invert: high=bad
    else:
        loss_score = 50.0

    # Severity: slight offset from frequency
    sev_score = round(min(100, max(0, loss_score + random.uniform(-5, 5))), 2)

    # Map to bands based on score thresholds (same as real scorer)
    def _loss_band(s):
        if s < 20: return "very_low"
        if s < 40: return "low"
        if s < 60: return "moderate"
        if s < 80: return "elevated"
        return "high"

    def _sev_band(s):
        if s < 20: return "minimal"
        if s < 40: return "moderate"
        if s < 60: return "significant"
        if s < 80: return "severe"
        return "catastrophic"

    loss_band = _loss_band(loss_score)
    sev_band = _sev_band(sev_score)

    # Map bands to multipliers (same as real scorer defaults)
    freq_mult_map = {"very_low": 0.60, "low": 0.80, "moderate": 1.00, "elevated": 1.25, "high": 1.50}
    sev_mult_map = {"minimal": 0.70, "moderate": 0.90, "significant": 1.10, "severe": 1.30, "catastrophic": 1.50}
    freq_mult = freq_mult_map.get(loss_band, 1.0)
    sev_mult = sev_mult_map.get(sev_band, 1.0)
    combined = round(freq_mult * 0.6 + sev_mult * 0.4, 3)

    # Loss group scores for full reconstructability
    loss_group_scores = {}
    for gid, gs in group_scores.items():
        lw = gs.get("loss_weight")
        if lw and lw > 0:
            inverted = round(100.0 - gs["risk_score"], 2)
            loss_group_scores[gid] = {
                "frequency_score": inverted,
                "severity_score": round(min(100, max(0, inverted + random.uniform(-3, 3))), 2),
                "confidence": round(random.uniform(0.7, 0.95), 4),
            }

    loss_confidence = round(random.uniform(0.65, 0.95), 2)

    return {
        "loss_propensity_score": loss_score,
        "severity_propensity_score": sev_score,
        "loss_propensity_band": loss_band,
        "severity_propensity_band": sev_band,
        "loss_confidence": loss_confidence,
        "loss_cohort_code": f"cohort_{co.get('industry', 'general').lower()}",
        "loss_cohort_name": f"{co.get('industry', 'General')} Cohort",
        "loss_cohort_confidence": round(random.uniform(0.5, 0.9), 2),
        "loss_frequency_multiplier": freq_mult,
        "loss_severity_multiplier": sev_mult,
        "loss_combined_modifier": combined,
        "loss_group_scores": loss_group_scores,
        # --- Previous period scores (freq/sev splits + combined) ---
        "loss_previous_frequency_score": (prev_freq := round(max(0, min(100, loss_score + random.uniform(-15, 15))), 1)),
        "loss_previous_severity_score": (prev_sev := round(max(0, min(100, sev_score + random.uniform(-15, 15))), 1)),
        "loss_previous_score": round(prev_freq * 0.6 + prev_sev * 0.4, 1),
        # --- Velocity: rate of change in score (points/month) ---
        "loss_frequency_velocity": (freq_vel := round(random.uniform(-3, 3), 2)),
        "loss_severity_velocity": (sev_vel := round(random.uniform(-3, 3), 2)),
        "loss_score_velocity": round(freq_vel * 0.6 + sev_vel * 0.4, 2),
        # --- Trend direction: derived from velocity ---
        "loss_frequency_trend_direction": (freq_trend := random.choice(["stable", "improving", "deteriorating"])),
        "loss_severity_trend_direction": (sev_trend := random.choice(["stable", "improving", "deteriorating"])),
        "loss_trend_direction": (
            "stable" if freq_trend == sev_trend == "stable"
            else "improving" if freq_trend == "improving" and sev_trend != "deteriorating"
            else "deteriorating" if freq_trend == "deteriorating" or sev_trend == "deteriorating"
            else "mixed"
        ),
        "loss_last_refresh": NOW - timedelta(days=random.randint(1, 30)),
        "correlation_matrix_version": "v1.0.0",
    }


def build_exposure_assessment(co, config):
    """Build exposure assessment columns keyed for ModelVersionRecord kwargs.

    Exposure Modifier Calculation Chain
    ====================================
    The exposure modifier is a weighted combination of SIZE and COMPLEXITY,
    both driven by config-defined bands:

    1. SIZE (weight from config, e.g. 0.6):
       - Input: exposure_value (revenue, hull_value, or TIV)
       - Matched to a config size band via implied_thresholds
       - Band provides: label, score range, modifier
       - Size score: interpolated within the matched band's score range

    2. COMPLEXITY (weight from config, e.g. 0.4):
       - Input: derived from industry + size_band heuristics
       - Matched to a config complexity band via score thresholds
       - Band provides: label, score range, modifier

    3. COMBINED MODIFIER:
       combined = (size_modifier × size_weight) + (complexity_modifier × complexity_weight)
       This is what gets applied to the premium as the "exposure" modifier.
    """
    # Use revenue or hull_value as the primary exposure metric
    exposure_value = co.get("revenue", 0) or co.get("hull_value", 0) or co.get("tiv", 0) or 0

    # --- SIZE: match to config-defined bands via implied_thresholds ---
    size_band_id = 1
    size_band_label = "UNKNOWN"
    size_modifier = 1.0
    size_score = 50.0
    size_weight = 0.6  # default
    size_band_boundaries = {"min_value": 0, "max_value": None, "modifier": 1.0}

    if config.exposure and config.exposure.size:
        size_weight = config.exposure.size.weight
        # Match exposure_value to a size band using implied_thresholds
        matched_size = config.exposure.size.bands[-1]  # default: largest band
        for band in config.exposure.size.bands:
            thresholds = band.interpretation.application.implied_thresholds
            if thresholds:
                band_max = thresholds.get("max")
                if band_max is not None and exposure_value <= band_max:
                    matched_size = band
                    break
            else:
                # No thresholds — match by score range (fallback)
                matched_size = band
                break

        size_band_id = matched_size.id
        size_band_label = matched_size.label
        size_modifier = matched_size.interpretation.application.applied
        # Interpolate score within the band's score range
        s_min = matched_size.interpretation.bands.min
        s_max = matched_size.interpretation.bands.max
        size_score = round(s_min + random.uniform(0, s_max - s_min), 1)
        thresholds = matched_size.interpretation.application.implied_thresholds or {}
        size_band_boundaries = {
            "min_value": thresholds.get("min", 0),
            "max_value": thresholds.get("max"),
            "modifier": size_modifier,
        }

    # --- COMPLEXITY: derive score from industry/size heuristic, match to config band ---
    industry = co.get("industry", "OTHER")
    complexity_base = {"TECHNOLOGY": 65, "HEALTHCARE": 60, "ENERGY": 55, "FINANCIAL_SERVICES": 70,
                       "MANUFACTURING": 50, "RETAIL": 40, "PROFESSIONAL_SERVICES": 45}.get(industry, 45)
    size_bump = {"ENTERPRISE": 15, "LARGE": 10, "MEDIUM": 5, "SMALL": 0, "MICRO": -5}.get(
        co.get("size_band", "MEDIUM"), 5)
    complexity_score = round(max(0, min(100, complexity_base + size_bump + random.uniform(-8, 8))), 1)

    complexity_band_id = 1
    complexity_band_label = "UNKNOWN"
    complexity_modifier = 1.0
    complexity_weight = 0.4  # default

    if config.exposure and config.exposure.complexity:
        complexity_weight = config.exposure.complexity.weight
        matched_complexity = config.exposure.complexity.bands[-1]
        for band in config.exposure.complexity.bands:
            if complexity_score <= band.interpretation.bands.max:
                matched_complexity = band
                break
        complexity_band_id = matched_complexity.id
        complexity_band_label = matched_complexity.label
        complexity_modifier = matched_complexity.interpretation.application.applied

    # --- COMBINED MODIFIER (weighted average of size + complexity) ---
    combined_modifier = round(
        size_modifier * size_weight + complexity_modifier * complexity_weight,
        4,
    )

    return {
        "exposure_value": float(exposure_value),
        "exposure_band_id": size_band_id,
        "exposure_band_label": size_band_label,
        "exposure_band_boundaries": size_band_boundaries,
        "exposure_size_score": size_score,
        "exposure_complexity_score": complexity_score,
        "exposure_modifier": combined_modifier,
        "exposure_assessment_method": "config_band_lookup",
        "exposure_components": {
            "size": {
                "score": size_score,
                "band_id": size_band_id,
                "band_label": size_band_label,
                "modifier": size_modifier,
                "weight": size_weight,
            },
            "complexity": {
                "score": complexity_score,
                "band_id": complexity_band_id,
                "band_label": complexity_band_label,
                "modifier": complexity_modifier,
                "weight": complexity_weight,
            },
            "combined_modifier": combined_modifier,
        },
    }


# =============================================================================
# COMMERCIAL TERMS HELPERS
# =============================================================================

# Maps coverage → commercial entity ID for seed data.
# The MGA writes cyber + D&O, the syndicate writes energy + marine + aerospace.
# FI and PI get a generated direct-writer entity.
COVERAGE_ENTITY_MAP = {
    "cyber": "mga_us_cyber",
    "directors_officers": "mga_us_cyber",
    "energy": "syndicate_example",
    "marine": "syndicate_example",
    "aerospace": "syndicate_example",
    "financial_institutions": None,  # Direct writer (generated)
    "professional_indemnity": None,  # Direct writer (generated)
}


def _get_entity_for_coverage(
    coverage: str, entity_override: str = None, _entity_cache: dict = {},
) -> CommercialEntity:
    """Get the commercial entity for a coverage, loading from YAML or generating.

    Args:
        coverage: Coverage identifier.
        entity_override: If provided, load this entity ID instead of using the
            coverage→entity mapping. Used by synthetic companies.
    """
    cache_key = entity_override or coverage
    if cache_key in _entity_cache:
        return _entity_cache[cache_key]

    entity_id = entity_override or COVERAGE_ENTITY_MAP.get(coverage)
    entity = None
    if entity_id:
        entity = load_entity(entity_id)

    if entity is None:
        # Generate a simple direct-writer entity for unmapped coverages
        from infrastructure.models.commercial_schema import (
            CoverageBinding, DistributionConfig, DistributionType,
            CommissionStructure, TaxesAndLevies, PricingAdjustments,
        )
        entity = CommercialEntity(
            id=f"direct_{coverage}",
            name=f"Direct Writer ({coverage.replace('_', ' ').title()})",
            market="us",
            base_currency="USD",
            coverages=[
                CoverageBinding(coverage=coverage, max_single_limit=500_000_000),
            ],
            distribution=DistributionConfig(type=DistributionType.DIRECT),
            commission=CommissionStructure(brokerage_rate=0.15),
            taxes_and_levies=TaxesAndLevies(insurance_premium_tax_rate=0.04),
            pricing_adjustments=PricingAdjustments(
                offered_premium_discretion=0.10,
                minimum_gross_premium=5000,
            ),
        )

    _entity_cache[cache_key] = entity
    return entity


def build_commercial_terms(
    mv_id,
    entity: CommercialEntity,
    technical_premium_usd: float,
    submission_data: dict,
    config,
    uw_user_id,
) -> tuple:
    """Build CommercialTermsRecord and RiskTermsRecord for a seeded company.

    Returns (CommercialTermsRecord, RiskTermsRecord).
    """
    fx_converter = FXConverter(StaticRateProvider())
    assembler = PremiumAssembler(fx_converter)

    breakdown = assembler.assemble(
        technical_premium_usd=technical_premium_usd,
        submission_data=submission_data,
        config=config,
        entity=entity,
    )

    # FX context
    target_ccy = entity.base_currency.upper()
    if target_ccy != "USD":
        try:
            fx_rate = fx_converter._provider.get_rate(Currency.USD, Currency(target_ccy))
        except (ValueError, KeyError):
            fx_rate = 1.0
    else:
        fx_rate = 1.0

    # Deductions breakdown (JSONB)
    deductions = {
        "brokerage": {
            "rate": entity.commission.brokerage_rate,
            "amount": breakdown.commission.brokerage,
        },
    }
    if entity.commission.overrider_rate > 0:
        deductions["overrider"] = {
            "rate": entity.commission.overrider_rate,
            "amount": breakdown.commission.overrider,
        }
    if entity.fronting.enabled:
        deductions["fronting_fee"] = {
            "rate": entity.fronting.fronting_fee_rate,
            "amount": breakdown.commission.fronting_fee,
        }
    if entity.commission.profit_commission_rate > 0:
        deductions["profit_commission"] = {
            "rate": entity.commission.profit_commission_rate,
            "threshold": entity.commission.profit_commission_threshold,
            "amount": 0.0,  # Earned at reporting time
        }

    # Taxes breakdown (JSONB)
    taxes_json = {
        "ipt": {
            "rate": entity.taxes_and_levies.insurance_premium_tax_rate,
            "amount": breakdown.taxes.insurance_premium_tax,
        },
    }
    if entity.taxes_and_levies.stamp_duty_rate > 0:
        taxes_json["stamp_duty"] = {
            "rate": entity.taxes_and_levies.stamp_duty_rate,
            "amount": breakdown.taxes.stamp_duty,
        }
    if entity.taxes_and_levies.regulatory_levy_rate > 0:
        taxes_json["regulatory_levy"] = {
            "rate": entity.taxes_and_levies.regulatory_levy_rate,
            "amount": breakdown.taxes.regulatory_levy,
        }

    # Distribution
    dist = entity.distribution
    signed_line = 1.0
    role = None
    lead_loading = 1.0
    if dist.subscription:
        signed_line = dist.subscription.default_signed_line
        role = dist.subscription.role.value
        if dist.subscription.role.value == "LEAD":
            lead_loading = dist.subscription.lead_loading_factor

    # Offered premium — apply random discretion within allowed range
    discretion_range = entity.pricing_adjustments.offered_premium_discretion
    if discretion_range > 0:
        discretion_applied = round(random.uniform(-discretion_range, discretion_range), 4)
    else:
        discretion_applied = 0.0
    offered_premium = round(breakdown.gross_premium * (1 + discretion_applied), 2)

    # Minimum premium enforcement
    min_gross = entity.pricing_adjustments.minimum_gross_premium
    at_minimum = breakdown.gross_premium <= min_gross if min_gross > 0 else False

    # Written/earned dates
    inception = NOW + timedelta(days=random.randint(7, 90))
    expiry = inception + timedelta(days=365)

    ct = CommercialTermsRecord(
        id=_uid(),
        model_version_id=mv_id,
        entity_id=entity.id,
        entity_name=entity.name,
        entity_market=entity.market,
        base_currency=entity.base_currency,
        fx_rate_to_usd=fx_rate,
        fx_rate_source="static_reference",
        fx_rate_date=NOW,
        technical_premium_usd=technical_premium_usd,
        technical_premium_local=breakdown.technical_premium_local,
        distribution_type=dist.type.value,
        signed_line=signed_line,
        role=role,
        lead_loading_factor=lead_loading,
        net_premium=breakdown.net_premium,
        deductions=deductions,
        total_commission=breakdown.commission.total_commission,
        taxes_and_levies=taxes_json,
        total_taxes=breakdown.taxes.total_taxes,
        gross_premium=breakdown.gross_premium,
        offered_premium=offered_premium,
        offered_premium_discretion=discretion_applied,
        offered_premium_rationale=(
            "Seed: underwriter discretion applied within entity guidelines"
            if discretion_applied != 0 else None
        ),
        offered_premium_set_by=uw_user_id if discretion_applied != 0 else None,
        offered_premium_set_at=NOW if discretion_applied != 0 else None,
        minimum_gross_premium=min_gross if min_gross > 0 else None,
        at_minimum_premium=at_minimum,
        written_date=NOW,
        earned_start=inception,
        earned_end=expiry,
        earned_method="pro_rata",
    )

    # Risk terms — deductible nuance from submission data
    deductible = submission_data.get("deductible", 50_000)
    limit = submission_data.get("limit", 10_000_000)
    coverage = submission_data.get("coverage", "")

    # Determine deductible type based on coverage
    deductible_types = {
        "cyber": ("per_occurrence", "each_and_every_loss"),
        "directors_officers": ("per_occurrence", "each_and_every_claim"),
        "financial_institutions": ("aggregate", "per_policy_period"),
        "professional_indemnity": ("per_occurrence", "each_and_every_claim"),
        "energy": ("per_occurrence", "each_and_every_loss"),
        "marine": ("franchise", "each_and_every_loss"),
        "aerospace": ("per_occurrence", "each_and_every_loss"),
    }
    ded_type, ded_basis = deductible_types.get(coverage, ("per_occurrence", "each_and_every_loss"))

    # Waiting period for cyber (business interruption)
    waiting_hours = None
    waiting_type = None
    if coverage == "cyber":
        waiting_hours = random.choice([8.0, 12.0, 24.0, 48.0])
        waiting_type = "business_interruption"

    # SIR for D&O and PI
    sir_applies = coverage in ("directors_officers", "professional_indemnity")
    sir_amount = deductible * 0.5 if sir_applies else None

    # Aggregate for FI
    aggregate_limit = limit * 2 if coverage == "financial_institutions" else None
    aggregate_deductible = deductible * 3 if coverage == "financial_institutions" else None

    # Sub-limits based on coverage type
    sub_limits_map = {
        "cyber": [
            {"peril": "ransomware", "sub_limit": int(limit * 0.5), "sub_deductible": deductible},
            {"peril": "business_interruption", "sub_limit": int(limit * 0.75), "sub_deductible": deductible},
            {"peril": "regulatory_fines", "sub_limit": int(limit * 0.25), "sub_deductible": 0},
        ],
        "energy": [
            {"peril": "well_control", "sub_limit": int(limit * 0.5), "sub_deductible": deductible * 2},
            {"peril": "pollution", "sub_limit": int(limit * 0.25), "sub_deductible": deductible * 5},
        ],
        "marine": [
            {"peril": "salvage", "sub_limit": int(limit * 0.1), "sub_deductible": 0},
        ],
    }
    sub_limits = sub_limits_map.get(coverage, [])

    # Coverage terms
    coverage_terms_map = {
        "cyber": {
            "extensions": ["social_engineering", "reputational_harm", "system_failure"],
            "exclusions": ["war", "infrastructure_failure", "prior_known_events"],
        },
        "directors_officers": {
            "extensions": ["entity_coverage", "employment_practices"],
            "exclusions": ["fraud", "criminal_acts", "prior_knowledge"],
        },
        "energy": {
            "extensions": ["operators_extra_expense", "control_of_well"],
            "exclusions": ["war", "nuclear", "gradual_pollution"],
        },
        "marine": {
            "extensions": ["sue_and_labour", "general_average"],
            "exclusions": ["war", "strikes", "malicious_damage"],
        },
        "aerospace": {
            "extensions": ["passenger_liability", "war_risks"],
            "exclusions": ["nuclear", "war_on_ground"],
        },
    }
    coverage_terms = coverage_terms_map.get(coverage, {"extensions": [], "exclusions": []})

    rt = RiskTermsRecord(
        id=_uid(),
        commercial_terms_id=ct.id,
        deductible_type=ded_type,
        deductible_amount=float(deductible),
        deductible_currency=entity.base_currency,
        deductible_basis=ded_basis,
        sir_amount=float(sir_amount) if sir_amount else None,
        sir_applies=sir_applies,
        waiting_period_hours=waiting_hours,
        waiting_period_type=waiting_type,
        aggregate_limit=float(aggregate_limit) if aggregate_limit else None,
        aggregate_deductible=float(aggregate_deductible) if aggregate_deductible else None,
        aggregate_basis="per_policy_period" if aggregate_limit else None,
        reinstatements=random.choice([0, 1, 2]) if coverage in ("energy", "marine", "aerospace") else 0,
        reinstatement_rate=1.0 if coverage in ("energy", "marine", "aerospace") else None,
        attachment_point=None,  # Ground-up for primary layer
        layer_limit=float(limit),
        sub_limits=sub_limits,
        coverage_terms=coverage_terms,
    )

    return ct, rt


# =============================================================================
# SEED FUNCTION
# =============================================================================

def seed_data(
    include_synthetic: bool = False,
    synthetic_only: bool = False,
    synthetic_count: int = 1000,
    synthetic_seed: int = 42,
):
    print("=" * 70)
    print("  DSI COMPREHENSIVE BENCH SEED")
    if include_synthetic:
        mode = "synthetic only" if synthetic_only else f"curated + {synthetic_count} synthetic"
        print(f"  Mode: {mode} (seed={synthetic_seed})")
    print("=" * 70)

    engine = create_engine(DATABASE_URL_SYNC)
    SessionLocal = sessionmaker(bind=engine)

    print("\n[1/2] Rebuilding database schema from ORM models...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # -----------------------------------------------------------------
        # Create a system user for audit trails
        # -----------------------------------------------------------------
        system_user_id = _uid()
        system_user = User(
            id=system_user_id,
            email="system@dsi-platform.io",
            hashed_password="$2b$12$SYSTEM_SEED_HASH_NOT_FOR_LOGIN",
            full_name="DSI System",
            is_active=True,
            is_superuser=True,
            permissions=["admin", "underwriter", "analyst"],
        )
        db.add(system_user)

        uw_user_id = _uid()
        uw_user = User(
            id=uw_user_id,
            email="underwriter@dsi-platform.io",
            hashed_password="$2b$12$UW_SEED_HASH_NOT_FOR_LOGIN",
            full_name="Sarah Chen",
            is_active=True,
            is_superuser=False,
            permissions=["underwriter", "referral_review"],
        )
        db.add(uw_user)

        analyst_user_id = _uid()
        analyst_user = User(
            id=analyst_user_id,
            email="analyst@dsi-platform.io",
            hashed_password="$2b$12$ANALYST_SEED_HASH_NOT_FOR_LOGIN",
            full_name="James Walker",
            is_active=True,
            is_superuser=False,
            permissions=["analyst", "read_only"],
        )
        db.add(analyst_user)
        db.flush()
        print(f"   Created 3 users (system, underwriter, analyst)")

        # -----------------------------------------------------------------
        # Build the company list (curated + optional synthetic)
        # -----------------------------------------------------------------
        all_companies = []
        if not synthetic_only:
            all_companies.extend(COMPANIES)

        if include_synthetic:
            from synthetic_generator import generate_synthetic_companies
            synth = generate_synthetic_companies(
                count=synthetic_count, seed=synthetic_seed,
            )
            all_companies.extend(synth)
            print(f"   Generated {len(synth)} synthetic companies")

        # -----------------------------------------------------------------
        # Seed each company
        # -----------------------------------------------------------------
        print(f"\n[2/2] Seeding {len(all_companies)} companies across all coverages...\n")

        # Caches for signal/source reference table IDs (populated on first encounter)
        _signal_id_cache = {}   # signal_code -> signals.id
        _source_id_cache = {}   # source_name -> signal_sources.id

        stats = {"approve": 0, "refer": 0, "decline": 0, "outside_appetite": 0}
        coverage_counts = {}
        validation_inputs = []  # Collected for ROL validation
        _rol_validator = ROLValidator()

        for i, co in enumerate(all_companies, 1):
            is_synthetic = co.get("_synthetic", False)
            coverage_key = f"{co['coverage']}/{co['configuration']}"
            coverage_counts[coverage_key] = coverage_counts.get(coverage_key, 0) + 1

            # === LOAD PRODUCTION CONFIG ===
            config = _get_compiled_config(co)

            # === 1. SUBMISSION ===
            sub_id = _uid()
            # Synthetic companies have temporal spread; curated use NOW
            ref_time = co.get("_created_at", NOW) if is_synthetic else NOW
            processing_start = ref_time - timedelta(minutes=random.randint(5, 60))
            processing_end = processing_start + timedelta(seconds=random.randint(3, 45))

            submission_data = build_submission_data(co)

            # Step 0a: Appetite check — reject before running the model
            appetite_result = evaluate_appetite(co["coverage"], submission_data)
            if not appetite_result.fit:
                stats["outside_appetite"] += 1
                print(f"  [{i:>2}/{len(COMPANIES)}] {co['entity_name']:30s}  "
                      f"OUTSIDE_APPETITE  ({'; '.join(appetite_result.reasons)})")
                continue

            direct_query_responses = build_direct_query_responses(co, config)

            sub = Submission(
                id=sub_id,
                submission_code=f"sub_{(co['ticker'] or co['entity_name'][:4]).lower().replace(' ', '_')}_{_hex(6)}",
                entity_name=co["entity_name"],
                domain_hint=co["domain"],
                discovered_domain=co["domain"],
                country_hint=co.get("geography", "US"),
                coverage=co["coverage"],
                configuration=co["configuration"],
                locale="US" if co.get("geography") == "US" else co.get("geography", "US"),
                status=SubmissionStatus.READY,
                submission_data=submission_data,
                direct_query_responses=direct_query_responses,
                processing_started_at=processing_start,
                processing_completed_at=processing_end,
                processing_duration_ms=(processing_end - processing_start).total_seconds() * 1000,
                created_by=system_user_id,
            )
            db.add(sub)
            db.flush()

            # === 2. MODEL VERSION RECORD ===
            mv_id = _uid()

            # Roll all signal scores ONCE — every table uses these same values
            if is_synthetic:
                # Synthetic companies use a target score instead of named profiles.
                # Generate per-signal scores from a normal distribution centered
                # on the target, giving natural variation within the tier band.
                target = co.get("_target_signal_score", 50)
                resolved_scores = {}
                default_score = max(5, min(95, target))
            else:
                resolved_scores = resolve_signal_scores(co.get("signal_profile", ""))
                # Tier-aligned default score for signals not covered by the profile.
                tier_default_scores = {1: 82, 2: 68, 3: 50, 4: 35, 5: 20}
                default_score = tier_default_scores.get(co.get("tier", 3), 50)

            # Build synthetic SignalOutput instances from config signal registry
            # Synthetic companies get wider jitter (±15) for natural variation
            sig_jitter = 15 if is_synthetic else 5
            signal_outputs = build_synthetic_signal_outputs(config, resolved_scores, default_score, jitter=sig_jitter)

            # Build categorical outputs from config definitions
            categorical_outputs = build_synthetic_categorical_outputs(config, co)

            # --- PRODUCTION SCORING (Steps 5-6) ---
            (composite, group_scores, confidence, signal_cov,
             signal_conditions, signal_tier_overrides, scoring_referrals,
             scoring_notes, signal_modifiers) = run_production_scoring(config, signal_outputs)

            # --- PRODUCTION QUERY EVALUATION (Step 7) ---
            query_result = run_production_query_evaluation(config, direct_query_responses)

            # Build loss propensity + exposure assessment BEFORE pricing
            # so their modifiers feed into the premium calculation
            loss_kwargs = build_loss_propensity(co, group_scores)
            exposure_kwargs = build_exposure_assessment(co, config)

            # Combine signal + query + loss + exposure modifiers (same as workflow.py)
            all_modifiers = signal_modifiers + query_result.modifiers

            # Add loss propensity modifier if non-neutral
            if loss_kwargs["loss_combined_modifier"] != 1.0:
                all_modifiers.append({
                    "name": "loss_propensity",
                    "factor": loss_kwargs["loss_combined_modifier"],
                    "confidence": loss_kwargs["loss_confidence"],
                    "source": "loss_propensity",
                    "source_id": "loss_propensity",
                })

            # Add exposure modifier if non-neutral
            if abs(exposure_kwargs["exposure_modifier"] - 1.0) > 0.001:
                all_modifiers.append({
                    "name": "exposure",
                    "factor": exposure_kwargs["exposure_modifier"],
                    "confidence": 0.85,
                    "source": "exposure",
                    "source_id": "exposure",
                })

            # --- PRODUCTION PRICING (Steps 8-12) ---
            pricing_result = run_production_pricing(
                config, composite, signal_tier_overrides,
                query_result.tier_overrides, all_modifiers,
                categorical_outputs, submission_data,
            )

            # Collect for premium accumulation validation
            validation_inputs.append({
                "config": config,
                "pricing_result": pricing_result,
                "submission_data": submission_data,
                "categorical_outputs": categorical_outputs,
                "entity_name": co["entity_name"],
            })

            # Combine referral reasons and notes
            all_referrals = scoring_referrals + query_result.referrals
            all_notes = scoring_notes + query_result.notes

            # Determine decision from tier (same as workflow.py)
            final_tier = pricing_result.final_tier
            tier_band = config.get_tier_band(final_tier)
            if tier_band and tier_band.interpretation.action.value == "DECLINE":
                decision_str = "decline"
            elif all_referrals or (tier_band and tier_band.interpretation.action.value == "REFER"):
                decision_str = "refer"
            else:
                decision_str = "approve"

            decision_enum = DecisionType(decision_str)
            auto_approve = decision_str == "approve"

            stats[decision_str] += 1

            # Use referral_reasons from company if provided (for richer demo data),
            # otherwise use production-derived referrals
            referral_reasons = co.get("referral_reasons", all_referrals) if decision_str != "approve" else []

            # Print progress — show every curated company, every 50th synthetic
            total_co = len(all_companies)
            if not is_synthetic or i % 50 == 0 or i == total_co:
                tag = " [S]" if is_synthetic else ""
                print(f"   [{i:>4d}/{total_co}] {co['entity_name']:<30s} "
                      f"| {coverage_key:<30s} | Tier {final_tier} ({pricing_result.tier_label}) "
                      f"| {decision_str.upper():<8s} | ${pricing_result.final_premium:,.0f}{tag}")

            discovery = build_discovery_output(co)

            # loss_kwargs and exposure_kwargs already computed above (before pricing)

            # Serialise production dataclass outputs to dicts for JSONB storage
            signal_outputs_json = [
                {
                    "signal_id": s.signal_id,
                    "group_id": s.group_id,
                    "score": s.raw_score,
                    "confidence": s.confidence,
                    "weight": s.weight,
                    "weighted_score": s.weighted_score,
                    "proxy_tier": random.choice(["DIRECT_OBSERVABLE", "INFERRED_PROXY"]),
                    "extraction_time_ms": s.execution_time_ms,
                }
                for s in signal_outputs
            ]

            categorical_outputs_json = [
                {
                    "group_id": c.group_id,
                    "group_name": c.group_name,
                    "selected_cat": c.category,
                    "label": c.label,
                    "modifier": c.modifier,
                    "source": f"metadata.{c.group_id}",
                }
                for c in categorical_outputs
            ]

            signal_conditions_json = [
                {
                    "source_type": c.source_type,
                    "source_id": c.source_id,
                    "source_name": c.source_name,
                    "score": c.score,
                    "response": c.response,
                    "action": c.action.value if hasattr(c.action, 'value') else str(c.action),
                    "action_value": c.action_value,
                    "note": c.note,
                }
                for c in signal_conditions
            ]

            query_conditions_json = [
                {
                    "source_type": c.source_type,
                    "source_id": c.source_id,
                    "source_name": c.source_name,
                    "score": c.score,
                    "response": c.response,
                    "action": c.action.value if hasattr(c.action, 'value') else str(c.action),
                    "action_value": c.action_value,
                    "note": c.note,
                }
                for c in query_result.conditions_triggered
            ]

            modifiers_applied_json = [
                {
                    "source": m.source,
                    "source_id": m.source_id,
                    "name": m.name,
                    "applied": m.factor,
                    "premium_before": m.premium_before,
                    "premium_after": m.premium_after,
                }
                for m in pricing_result.modifiers_applied
            ]

            # Resolve ILF for the requested limit for audit trail
            requested_limit = co.get("limit", 10_000_000)
            product_type = submission_data.get("product_type", "")
            ilf_factor = config.get_ilf(product_type, requested_limit)

            # Determine ILF method and anchor from the curve config
            _pt_pricing = config.pricing.by_product_type.get(product_type)
            if _pt_pricing:
                ilf_method = f"parametric:{_pt_pricing.ilf_curve.curve}"
                ilf_anchor = _pt_pricing.ilf_curve.anchor_limit
            else:
                ilf_method = "unknown"
                ilf_anchor = config.pricing.base_limit_reference

            # Build tier override audit records
            all_tier_overrides = signal_tier_overrides + query_result.tier_overrides
            resolved_tier_overrides = []
            score_based_tier = pricing_result.score_based_tier
            for sc in signal_conditions:
                if hasattr(sc.action, 'value'):
                    action_val = sc.action.value
                else:
                    action_val = str(sc.action)
                if action_val == "refer" and isinstance(sc.action_value, int):
                    resolved_tier_overrides.append({
                        "source": "signal_condition",
                        "source_id": sc.source_id,
                        "override_tier": sc.action_value,
                        "note": sc.note,
                        "applied": sc.action_value > score_based_tier,
                    })
            for qc in query_result.conditions_triggered:
                if hasattr(qc.action, 'value'):
                    action_val = qc.action.value
                else:
                    action_val = str(qc.action)
                if action_val == "refer" and isinstance(qc.action_value, int):
                    resolved_tier_overrides.append({
                        "source": "direct_query",
                        "source_id": qc.source_id,
                        "override_tier": qc.action_value,
                        "note": qc.note,
                        "applied": qc.action_value > score_based_tier,
                    })

            # Always preserve computed premiums — even declined risks have
            # indicative pricing (a different ROL option might be in appetite)
            final_premium = pricing_result.final_premium
            base_premium = pricing_result.base_premium
            premium_after_mods = pricing_result.premium_after_modifiers
            limit_premiums = pricing_result.limit_premiums

            # --- Phase A: Uncapped premium & guardrail detail ---
            uncapped_premium = pricing_result.uncapped_premium
            premium_was_capped = pricing_result.premium_was_capped
            guardrail_warnings = pricing_result.guardrail_warnings or []

            # --- Extract single final_premium_detail for the selected limit ---
            final_premium_detail_json = {}
            if pricing_result.limit_premium_details:
                # Find the detail matching the requested/final limit
                target_limit = requested_limit
                for lpd in pricing_result.limit_premium_details:
                    if lpd.limit == target_limit:
                        final_premium_detail_json = {
                            "limit": lpd.limit,
                            "deductible": lpd.deductible,
                            "attachment_point": lpd.attachment_point,
                            "ilf_factor": lpd.ilf_factor,
                            "deductible_factor": lpd.deductible_factor,
                            "premium_before_scaling": lpd.premium_before_scaling,
                            "premium_after_scaling": lpd.premium_after_scaling,
                            "uncapped_premium": lpd.uncapped_premium,
                        }
                        break
                # Fallback: use the first detail if no exact match
                if not final_premium_detail_json and pricing_result.limit_premium_details:
                    lpd = pricing_result.limit_premium_details[0]
                    final_premium_detail_json = {
                        "limit": lpd.limit,
                        "deductible": lpd.deductible,
                        "attachment_point": lpd.attachment_point,
                        "ilf_factor": lpd.ilf_factor,
                        "deductible_factor": lpd.deductible_factor,
                        "premium_before_scaling": lpd.premium_before_scaling,
                        "premium_after_scaling": lpd.premium_after_scaling,
                        "uncapped_premium": lpd.uncapped_premium,
                    }

            # --- Phase A: Tier margin context ---
            tier_margin_kwargs = build_tier_margin(composite, final_tier, config)

            # --- Phase A: Tier band config snapshot ---
            tier_band_snap = build_tier_band_interpretation(final_tier, config)

            # --- Phase A: Loss/exposure band config snapshots ---
            loss_band_snap = build_loss_band_interpretation(config)
            exposure_band_snap = build_exposure_band_interpretation(config)

            # --- Config snapshots for client-side scenario recalculation ---
            loss_corr_config = build_loss_correlation_config()
            ilf_curve_snap = build_ilf_curve_config(config, product_type)
            ded_factor_snap = build_deductible_factor_table(config)
            exposure_mod_snap = build_exposure_modifier_config(config)
            guardrails_snap = build_guardrails_config(config)

            # --- Phase C: ROL dual recommendation ---
            rol_kwargs = build_rol_recommendation(limit_premiums, requested_limit)

            mv = ModelVersionRecord(
                id=mv_id,
                version_code=f"mv_{_hex(8)}",
                submission_id=sub_id,
                version_number=1,
                version_type="initial",
                is_latest=True,
                coverage=co["coverage"],
                configuration_name=co["configuration"],
                config_hash=_hex(16),
                discovery_output=discovery,
                signal_outputs=signal_outputs_json,
                categorical_outputs=categorical_outputs_json,
                group_scores=group_scores,
                pure_composite_score=composite,
                confidence=confidence,
                signal_coverage=signal_cov,
                signal_conditions=signal_conditions_json,
                query_conditions=query_conditions_json,
                tier_overrides=resolved_tier_overrides,
                score_based_tier=score_based_tier,
                final_tier=final_tier,
                tier_label=pricing_result.tier_label,
                base_premium=base_premium,
                base_premium_method=pricing_result.base_premium_method,
                base_premium_derivation=asdict(pricing_result.base_premium_derivation) if pricing_result.base_premium_derivation else None,
                modifiers_applied=modifiers_applied_json,
                premium_after_modifiers=premium_after_mods,
                final_premium=final_premium,
                final_premium_detail=final_premium_detail_json,
                uncapped_premium=uncapped_premium,
                premium_was_capped=premium_was_capped,
                guardrail_warnings=guardrail_warnings,
                ilf_factor=ilf_factor,
                ilf_method=ilf_method,
                ilf_anchor_limit=ilf_anchor,
                # Tier band config snapshot
                tier_band_interpretation=tier_band_snap,
                # Loss/exposure band config snapshots
                loss_band_interpretation=loss_band_snap,
                exposure_band_interpretation=exposure_band_snap,
                # Config snapshots for scenario recalculation
                loss_correlation_config=loss_corr_config,
                ilf_curve_config=ilf_curve_snap,
                deductible_factor_table=ded_factor_snap,
                exposure_modifier_config=exposure_mod_snap,
                guardrails_config=guardrails_snap,
                decision=decision_enum,
                auto_approve=auto_approve,
                referral_reasons=referral_reasons,
                notes=[{"note": co.get("description", ""), "source": "seed_script"}],
                created_by="seed_dsi_bench",
                # Tier margin context (Phase A)
                **tier_margin_kwargs,
                # ROL recommendation (Phase C)
                **rol_kwargs,
                # Loss propensity columns
                **loss_kwargs,
                # Exposure assessment columns
                **exposure_kwargs,
            )
            db.add(mv)
            db.flush()

            # === 3. QUOTE (de-duplicated: scoring lives on model_version) ===
            quote_id = _uid()
            quote_status = {
                "approve": QuoteStatus.READY,
                "refer": QuoteStatus.DRAFT,
                "decline": QuoteStatus.DECLINED,
            }[decision_str]

            # Recommended limit from company config; premium from production pricing
            rec_limit = co.get("limit", 10_000_000)
            rec_premium = limit_premiums.get(str(rec_limit), final_premium)

            quote = Quote(
                id=quote_id,
                quote_code=f"Q-{(co['ticker'] or co['entity_name'][:4]).upper().replace(' ', '')}-{_hex(4)}",
                submission_id=sub_id,
                model_version_id=mv_id,
                status=quote_status,
                recommended_premium=rec_premium,
                recommended_limit=rec_limit,
                valid_from=NOW,
                valid_until=NOW + timedelta(days=30),
            )
            db.add(quote)
            db.flush()

            # === 4. REFERRAL (for refer/decline decisions) ===
            if decision_str in ("refer", "decline"):
                ref_status = ReferralStatus.PENDING
                reviewed_by = None
                reviewed_at = None
                review_notes = None
                review_decision = None

                # Make some referrals already reviewed
                if decision_str == "refer" and random.random() > 0.5:
                    ref_status = random.choice([ReferralStatus.APPROVED, ReferralStatus.IN_REVIEW])
                    if ref_status == ReferralStatus.APPROVED:
                        reviewed_by = uw_user_id
                        reviewed_at = NOW - timedelta(hours=random.randint(1, 48))
                        review_decision = "approve"
                        review_notes = f"Reviewed {co['entity_name']} - acceptable risk with conditions."

                referral = Referral(
                    id=_uid(),
                    referral_code=f"ref_{_hex(8)}",
                    quote_id=quote_id,
                    status=ref_status,
                    reasons=referral_reasons or ["Tier-based referral"],
                    priority=min(final_tier, 5),
                    assigned_to=uw_user_id if ref_status != ReferralStatus.PENDING else None,
                    assigned_at=NOW - timedelta(hours=random.randint(2, 72)) if ref_status != ReferralStatus.PENDING else None,
                    reviewed_by=reviewed_by,
                    reviewed_at=reviewed_at,
                    review_decision=review_decision,
                    review_notes=review_notes,
                    tier_override=final_tier - 1 if review_decision == "approve" and final_tier > 1 else None,
                    premium_adjustment=final_premium * 0.1 if review_decision == "approve" else None,
                )
                db.add(referral)
                db.flush()

            # === 5. SIGNAL CACHE ENTRIES ===
            # Build from production signal_outputs (SignalOutput dataclass instances)
            cache_id_map = {}  # signal_id -> cache UUID
            for so in signal_outputs:
                sig_code = so.signal_id
                cache_uuid = _uid()
                cache_id_map[sig_code] = cache_uuid

                sig_ref_id = _signal_id_cache.get(sig_code)
                if sig_ref_id is None:
                    sig_ref = Signal(code=sig_code)
                    db.add(sig_ref)
                    db.flush()
                    sig_ref_id = sig_ref.id
                    _signal_id_cache[sig_code] = sig_ref_id

                src_name = f"{sig_code}_extractor"
                src_ref_id = _source_id_cache.get(src_name)
                if src_ref_id is None:
                    src_ref = SignalSource(name=src_name)
                    db.add(src_ref)
                    db.flush()
                    src_ref_id = src_ref.id
                    _source_id_cache[src_name] = src_ref_id

                cache = SignalCache(
                    id=cache_uuid,
                    entity_code=co["domain"],
                    signal_id=sig_ref_id,
                    source_id=src_ref_id,
                    data={
                        "score": so.raw_score,
                        "raw_data": {"source": "seed", "entity": co["entity_name"]},
                        "metadata": {"group_code": so.group_id},
                    },
                    confidence=so.confidence,
                    ttl_seconds=86400,
                    expires_at=NOW + timedelta(days=1),
                    extraction_time_ms=so.execution_time_ms,
                )
                db.add(cache)
            db.flush()

            # === 5b. MODEL VERSION SIGNALS (Layer 2 — config-to-signal binding) ===
            # Uses production signal outputs with weights from config signal registry.
            mvs_id_map = {}  # signal_id -> mvs UUID

            for so in signal_outputs:
                sig_code = so.signal_id
                cache_ref = cache_id_map.get(sig_code)
                if not cache_ref or sig_code not in _signal_id_cache:
                    continue

                # Get group detail for contribution calculation
                gs_detail = group_scores.get(so.group_id, {})
                g_risk_weight = gs_detail.get("risk_weight", 0.0) if isinstance(gs_detail, dict) else 0.0
                signal_count = gs_detail.get("signal_count", 1) if isinstance(gs_detail, dict) else 1

                # Per-signal contribution mirrors scorer.py formula
                contribution = round(so.weighted_score * 10, 4) if so.weight > 0 else 0.0

                mvs_uuid = _uid()
                mvs_id_map[sig_code] = mvs_uuid
                mvs = ModelVersionSignal(
                    id=mvs_uuid,
                    model_version_id=mv_id,
                    signal_cache_id=cache_ref,
                    signal_id=_signal_id_cache[sig_code],
                    entity_code=co["domain"],
                    score=so.raw_score,
                    weight=so.weight,
                    group_weight=g_risk_weight,
                    contribution=contribution,
                    group_code=so.group_id,
                    proxy_tier=random.choice(["DIRECT_OBSERVABLE", "INFERRED_PROXY"]),
                    expectation_level=random.choice(["UNIVERSAL", "ENTERPRISE", "CORPORATE"]),
                    was_absent=False,
                )
                db.add(mvs)
            db.flush()

            # === 6. SIGNAL AUDIT RECORDS (for overridden signals) ===
            if decision_str == "refer" and signal_outputs:
                overridable_signals = [
                    (so.signal_id, so.raw_score)
                    for so in signal_outputs
                    if so.raw_score <= 50
                ]
                for sid, resolved in overridable_signals[:2]:
                    mvs_ref = mvs_id_map.get(sid)
                    if not mvs_ref:
                        continue
                    audited = min(100.0, resolved + 15.0)
                    audit_record = SignalAuditRecord(
                        id=_uid(),
                        model_version_signal_id=mvs_ref,
                        audited_value=audited,
                        overridden_by=uw_user_id,
                        overridden_at=NOW - timedelta(hours=random.randint(1, 24)),
                        override_rationale=f"Underwriter adjustment: {sid.replace('_', ' ').title()} "
                                           f"score revised after manual review of {co['entity_name']}",
                        evidence_reference=f"UW-NOTE-{_hex(6)}",
                        score_impact=round((audited - resolved) * 0.5, 1),
                        tier_impact=0,
                    )
                    db.add(audit_record)

            # === 7. AUDIT LOG ===
            audit_log = AuditLog(
                id=_uid(),
                event_type="submission",
                event_action="create",
                resource_type="submission",
                resource_code=str(sub_id),
                user_id=system_user_id,
                details={
                    "entity_name": co["entity_name"],
                    "coverage": co["coverage"],
                    "configuration": co["configuration"],
                    "decision": decision_str,
                    "tier": final_tier,
                    "premium": final_premium,
                    "source": "seed_dsi_bench",
                },
            )
            db.add(audit_log)

            # === 8. COMMERCIAL TERMS & RISK TERMS ===
            if is_synthetic and co.get("_entity_id"):
                entity = _get_entity_for_coverage(
                    co["coverage"], entity_override=co["_entity_id"]
                )
            else:
                entity = _get_entity_for_coverage(co["coverage"])
            ct, rt = build_commercial_terms(
                mv_id=mv_id,
                entity=entity,
                technical_premium_usd=final_premium,
                submission_data=submission_data,
                config=config,
                uw_user_id=uw_user_id,
            )
            db.add(ct)
            db.add(rt)
            db.flush()

        # -----------------------------------------------------------------
        # Commit everything
        # -----------------------------------------------------------------
        db.commit()

        print("\n" + "=" * 70)
        print("  SEED COMPLETE")
        print("=" * 70)
        print(f"\n  Companies seeded: {len(all_companies)}")
        print(f"  Decisions: {stats}")
        print(f"\n  Coverage breakdown:")
        for cov, count in sorted(coverage_counts.items()):
            print(f"    {cov:<35s} {count} companies")

        total_signals = sum(
            len(sigs)
            for co in all_companies
            for sigs in SIGNAL_PROFILES.get(co.get("signal_profile", ""), {}).values()
        )
        print(f"\n  Signal cache entries: ~{total_signals}")
        print(f"  Users created: 3 (system, underwriter, analyst)")
        print(f"  Referrals created: {stats['refer'] + stats['decline']}")
        seeded_count = len(all_companies) - stats.get("outside_appetite", 0)
        print(f"  Commercial terms created: {seeded_count}")
        print(f"  Risk terms created: {seeded_count}")
        if stats.get("outside_appetite", 0) > 0:
            print(f"  Outside appetite (skipped): {stats['outside_appetite']}")
        print("=" * 70)

        # ROL validation summary
        if validation_inputs:
            ok = warn = fail = 0
            for vi in validation_inputs:
                limit = int(vi["submission_data"].get("limit", 0))
                premium = vi["pricing_result"].final_premium
                if limit > 0:
                    r = _rol_validator.validate_rol(premium, limit)
                    if r.severity == "OK":
                        ok += 1
                    elif r.severity == "WARNING":
                        warn += 1
                    else:
                        fail += 1
            total = ok + warn + fail
            print(f"\n  ROL Validation: {total} checked — "
                  f"{ok} OK, {warn} WARNING, {fail} FAIL")

        # =================================================================
        # Phase E Demonstration — Tower, Subscription, Lead/Follow
        # =================================================================
        if not synthetic_only:
            _demonstrate_phase_e(config_cache=_config_cache)

    except Exception as e:
        db.rollback()
        print(f"\n  ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


def _demonstrate_phase_e(config_cache=None):
    """Demonstrate Phase E concepts: towers, subscriptions, lead/follow, bespoke, LayerPremiumDetail.

    Uses the production ModelPricer to run tower and subscription pricing,
    printing detailed per-layer breakdowns.
    """
    from infrastructure.models.config_schema import (
        LimitConfiguration, LimitConfigType, TowerLayer,
        SubscriptionOrder, SubscriptionLine, LineRole,
        CoverageConfig as PydanticCoverageConfig,
        Pricing, ProductTypePricing, ILFCurve, DeductibleFactor,
        RiskTierBands, RiskTierBand, RiskTierInterpretation,
        TierBandRange, TierAction, RiskTierApplication, PricingMethod,
        ConfigMetadata, Groups,
    )
    from layers.risk.pricer import ModelPricer
    from layers.risk.rol_validator import ROLValidator

    pricer = ModelPricer()
    validator = ROLValidator()

    print("\n" + "=" * 70)
    print("  PHASE E — Tower & Subscription Market Structure Demos")
    print("=" * 70)

    # Shared pricing config for demos
    _ilf = ILFCurve(anchor_limit=1_000_000, curve="power", params={"alpha": 0.569})
    _ded_factors = [
        DeductibleFactor(deductible=25_000, factor=1.0),
        DeductibleFactor(deductible=50_000, factor=0.95),
        DeductibleFactor(deductible=100_000, factor=0.90),
    ]
    _pricing = Pricing(
        base_limit_reference=1_000_000,
        base_deductible_reference=25_000,
        by_product_type={
            "cyber_liability": ProductTypePricing(
                ilf_curve=_ilf,
                deductible_factors=_ded_factors,
                lead_loading_factor=1.10,
            ),
        },
    )
    _tier_bands = RiskTierBands(bands=[
        RiskTierBand(id=1, label="PREFERRED", interpretation=RiskTierInterpretation(
            bands=TierBandRange(min=700, max=1000), action=TierAction.APPROVE,
            application=RiskTierApplication(method=PricingMethod.PREMIUM_BASE, value=50000),
        )),
        RiskTierBand(id=2, label="STANDARD", interpretation=RiskTierInterpretation(
            bands=TierBandRange(min=500, max=699), action=TierAction.APPROVE,
            application=RiskTierApplication(method=PricingMethod.PREMIUM_BASE, value=75000),
        )),
        RiskTierBand(id=3, label="REFER", interpretation=RiskTierInterpretation(
            bands=TierBandRange(min=300, max=499), action=TierAction.REFER,
            application=RiskTierApplication(method=PricingMethod.PREMIUM_BASE, value=100000),
        )),
    ])

    # ── E2 Example 1: Standard contiguous tower ──
    print("\n  [E2] Standard Contiguous Tower (Primary $1M + $4M xs $1M + $5M xs $5M)")
    tower_config = _build_demo_config(
        _pricing, _tier_bands,
        limit_configuration=LimitConfiguration(
            type=LimitConfigType.TOWER,
            layers=[
                TowerLayer(id=1, label="Primary", attachment=0, limit=1_000_000),
                TowerLayer(id=2, label="1st Excess", attachment=1_000_000, limit=4_000_000),
                TowerLayer(id=3, label="2nd Excess", attachment=5_000_000, limit=5_000_000),
            ],
        ),
    )
    layers = pricer.price_tower_layers(
        premium=50_000,
        submission_data={"deductible": 25_000, "product_type": "cyber_liability"},
        config=tower_config,
    )
    _print_layer_breakdown(layers, "Standard Tower")

    # ── E2 Example 2: Bespoke tower with gap ──
    print("\n  [E2] Bespoke Tower with Gap (Primary $500K, gap $500K-$2M, Excess $3M xs $2M)")
    bespoke_config = _build_demo_config(
        _pricing, _tier_bands,
        limit_configuration=LimitConfiguration(
            type=LimitConfigType.TOWER,
            layers=[
                TowerLayer(id=1, label="Primary", attachment=0, limit=500_000),
                TowerLayer(id=2, label="Excess (above gap)", attachment=2_000_000, limit=3_000_000),
            ],
        ),
    )
    bespoke_layers = pricer.price_tower_layers(
        premium=50_000,
        submission_data={"deductible": 25_000, "product_type": "cyber_liability"},
        config=bespoke_config,
    )
    _print_layer_breakdown(bespoke_layers, "Bespoke Tower (gap)")

    # ── E3 Example: Cumulative ILF differential ──
    print("\n  [E3] Cumulative ILF Differential Pricing")
    _ilf_demo = tower_config.pricing.by_product_type["cyber_liability"].ilf_curve
    demo_points = [0, 500_000, 1_000_000, 2_000_000, 5_000_000, 10_000_000]
    print(f"        {'Limit':>12s}  {'Cumul. ILF':>10s}  {'Standard ILF':>12s}")
    for pt in demo_points:
        cum = _ilf_demo.get_cumulative_factor(pt)
        std = _ilf_demo.get_factor_for_limit(pt) if pt > 0 else 0.0
        print(f"        ${pt:>11,d}  {cum:>10.4f}  {std:>12.4f}")

    # ── E4 Example 1: Subscription — Follow line ──
    print("\n  [E4] Subscription Order/Line — FOLLOW (10% signed line)")
    sub_follow_config = _build_demo_config(
        _pricing, _tier_bands,
        limit_configuration=LimitConfiguration(
            type=LimitConfigType.SUBSCRIPTION,
            subscription_order=SubscriptionOrder(total_limit=10_000_000),
            subscription_line=SubscriptionLine(
                minimum_line=0.05, maximum_line=0.25,
                signed_line=0.10, role=LineRole.FOLLOW,
            ),
        ),
    )
    follow_layers = pricer.price_tower_layers(
        premium=50_000,
        submission_data={"deductible": 25_000, "product_type": "cyber_liability"},
        config=sub_follow_config,
    )
    _print_layer_breakdown(follow_layers, "Subscription FOLLOW")

    # ── E4 Example 2: Subscription — Lead line ──
    print("\n  [E4] Subscription Order/Line — LEAD (15% signed line, 1.10x loading)")
    sub_lead_config = _build_demo_config(
        _pricing, _tier_bands,
        limit_configuration=LimitConfiguration(
            type=LimitConfigType.SUBSCRIPTION,
            subscription_order=SubscriptionOrder(total_limit=10_000_000),
            subscription_line=SubscriptionLine(
                minimum_line=0.10, maximum_line=0.30,
                signed_line=0.15, role=LineRole.LEAD,
            ),
        ),
    )
    lead_layers = pricer.price_tower_layers(
        premium=50_000,
        submission_data={"deductible": 25_000, "product_type": "cyber_liability"},
        config=sub_lead_config,
    )
    _print_layer_breakdown(lead_layers, "Subscription LEAD")

    # ── E4+E2 Example: Tower with subscription allocation ──
    print("\n  [E4+E2] Tower with Subscription Line (FOLLOW 10% on each layer)")
    tower_sub_config = _build_demo_config(
        _pricing, _tier_bands,
        limit_configuration=LimitConfiguration(
            type=LimitConfigType.TOWER,
            layers=[
                TowerLayer(id=1, label="Primary", attachment=0, limit=1_000_000),
                TowerLayer(id=2, label="1st Excess", attachment=1_000_000, limit=4_000_000),
                TowerLayer(id=3, label="2nd Excess", attachment=5_000_000, limit=5_000_000),
            ],
            subscription_order=SubscriptionOrder(total_limit=10_000_000),
            subscription_line=SubscriptionLine(
                minimum_line=0.05, maximum_line=0.20,
                signed_line=0.10, role=LineRole.FOLLOW,
            ),
        ),
    )
    tower_sub_layers = pricer.price_tower_layers(
        premium=50_000,
        submission_data={"deductible": 25_000, "product_type": "cyber_liability"},
        config=tower_sub_config,
    )
    _print_layer_breakdown(tower_sub_layers, "Tower + Subscription")

    # ── E5 Example: LayerPremiumDetail output fields ──
    if tower_sub_layers:
        print("\n  [E5] LayerPremiumDetail Output Fields (first layer):")
        lp = tower_sub_layers[0]
        for field_name in [
            "layer_id", "layer_label", "attachment", "limit",
            "order_premium", "signed_line", "role", "lead_loading",
            "line_premium", "rol", "ilf_top", "ilf_bottom", "layer_ilf",
        ]:
            val = getattr(lp, field_name, "N/A")
            if isinstance(val, float):
                print(f"        {field_name:<20s} = {val:,.6f}")
            else:
                print(f"        {field_name:<20s} = {val}")

    # ── ROL validation on tower layers ──
    print("\n  [E3] ROL Validation per Tower Layer:")
    for lp in layers:
        rol_result = validator.validate_rol(lp.order_premium, lp.limit, lp.attachment)
        print(f"        {lp.layer_label:<15s} ROL={lp.rol:.4f}  "
              f"Severity={rol_result.severity:<8s} {rol_result.reason}")

    print("\n  Phase E demonstration complete.\n")


def _build_demo_config(pricing, tier_bands, limit_configuration):
    """Build a minimal Pydantic CoverageConfig for Phase E demos."""
    from infrastructure.models.config_schema import (
        CoverageConfig as PydanticCoverageConfig,
        ConfigMetadata, Groups, Guardrails,
    )
    return PydanticCoverageConfig(
        coverage_id="demo",
        config_id="demo_general",
        metadata=ConfigMetadata(name="Phase E Demo", version="1.0.0", product_types=["cyber_liability"]),
        signal_registry=[],
        groups=Groups(),
        risk_tier_bands=tier_bands,
        pricing=pricing,
        guardrails=Guardrails(),
        limit_configuration=limit_configuration,
    )


def _print_layer_breakdown(layers, label):
    """Print a table of layer pricing details."""
    if not layers:
        print(f"        (No layers generated for {label})")
        return
    print(f"        {'Layer':<15s} {'Attach':>10s} {'Limit':>10s} "
          f"{'ILF Diff':>8s} {'Order Prem':>11s} {'Line%':>6s} {'Role':>6s} "
          f"{'Loading':>7s} {'Line Prem':>11s} {'ROL':>8s}")
    for lp in layers:
        print(f"        {lp.layer_label:<15s} ${lp.attachment:>9,d} ${lp.limit:>9,d} "
              f"{lp.layer_ilf:>8.4f} ${lp.order_premium:>10,.0f} "
              f"{lp.signed_line:>5.0%} {lp.role:>6s} "
              f"{lp.lead_loading:>6.2f}x ${lp.line_premium:>10,.0f} "
              f"{lp.rol:>7.4f}")
    total_order = sum(lp.order_premium for lp in layers)
    total_line = sum(lp.line_premium for lp in layers)
    print(f"        {'TOTAL':<15s} {'':>10s} {'':>10s} "
          f"{'':>8s} ${total_order:>10,.0f} "
          f"{'':>6s} {'':>6s} "
          f"{'':>7s} ${total_line:>10,.0f}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="DSI Bench Seed Script")
    parser.add_argument("--synthetic", action="store_true",
                        help="Include synthetic companies alongside curated seed data")
    parser.add_argument("--synthetic-only", action="store_true",
                        help="Only seed synthetic companies (skip curated)")
    parser.add_argument("--count", type=int, default=1000,
                        help="Number of synthetic companies (default: 1000)")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for reproducibility (default: 42)")
    args = parser.parse_args()

    seed_data(
        include_synthetic=args.synthetic or args.synthetic_only,
        synthetic_only=args.synthetic_only,
        synthetic_count=args.count,
        synthetic_seed=args.seed,
    )