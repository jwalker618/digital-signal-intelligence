"""
DSI Comprehensive Bench Seed Script
====================================
Seeds the database with realistic, end-to-end data covering every coverage,
configuration, tier, decision path, signal group, and UI component.

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
  3. Quote (with premium_options, composite_score, confidence)
  4. Referral (for refer/decline decisions)
  5. SignalCache entries (per-signal cached data)
  5b. ModelVersionSignal entries (config-to-signal binding — which signals each model used)
  6. SignalAuditRecord (override examples for referred cases)

Run:
  python seed_dsi_bench.py
"""

import uuid
import random
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
    SubmissionStatus,
    QuoteStatus,
    DecisionType,
    ReferralStatus,
)

# =============================================================================
# HELPERS
# =============================================================================

NOW = datetime.now(timezone.utc)


def _uid():
    return uuid.uuid4()


def _hex(n=8):
    return uuid.uuid4().hex[:n]


def _score(base, jitter=10):
    """Generate a score around a base value, clamped 0-100."""
    return max(0, min(100, base + random.randint(-jitter, jitter)))


def _composite(tier):
    """Map tier -> approximate composite score on the 0-1000 scale."""
    return {1: 880, 2: 720, 3: 570, 4: 420, 5: 200}.get(tier, 500)


TIER_LABELS = {1: "PREFERRED", 2: "STANDARD_PLUS", 3: "STANDARD", 4: "SUBSTANDARD", 5: "DECLINE"}


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
        "limit": 50_000_000,
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
        "limit": 50_000_000,
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
        "limit": 25_000_000,
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
        "limit": 10_000_000,
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
        "description": "Concentration risk, interest rate exposure, rapid growth.",
        "signal_profile": "fi_stressed",
        "product_type": "professional_liability",
        "limit": 25_000_000,
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
        "description": "Accounting fraud, regulatory collapse, criminal proceedings.",
        "signal_profile": "fi_catastrophic",
        "product_type": "financial_institution_bond",
        "limit": 10_000_000,
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
        "description": "Global supermajor, industry-leading HSE program, diversified portfolio.",
        "signal_profile": "energy_excellent",
        "product_type": "property_damage",
        "limit": 500_000_000,
        "deductible": 5_000_000,
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
        "description": "US shale operator, solid safety record, moderate environmental risk.",
        "signal_profile": "energy_good",
        "product_type": "control_of_well",
        "limit": 100_000_000,
        "deductible": 1_000_000,
        "tiv": 25_000_000_000,
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
        "description": "Deepwater Horizon operator history, aging fleet, high leverage.",
        "signal_profile": "energy_elevated",
        "product_type": "third_party_liability",
        "limit": 250_000_000,
        "deductible": 5_000_000,
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
        "description": "Permian Basin & Eagle Ford conventional operations. Industry-leading safety, 20+ year track record.",
        "signal_profile": "energy_upstream_onshore_excellent",
        "product_type": "property_damage",
        "limit": 500_000_000,
        "deductible": 2_500_000,
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
        "description": "Permian Basin pure-play. Best-in-class safety, 100% water recycling, zero induced seismicity events.",
        "signal_profile": "energy_unconventional_excellent",
        "product_type": "property_damage",
        "limit": 750_000_000,
        "deductible": 5_000_000,
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
        "description": "Largest US midstream operator. 50,000-mile pipeline network, industry-leading integrity management.",
        "signal_profile": "energy_midstream_excellent",
        "product_type": "property_damage",
        "limit": 500_000_000,
        "deductible": 2_500_000,
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
        "description": "Largest independent US refiner. 14 refineries, excellent turnaround compliance, best-in-class PSM.",
        "signal_profile": "energy_downstream_excellent",
        "product_type": "property_damage",
        "limit": 1_000_000_000,
        "deductible": 10_000_000,
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
        "description": "US East Coast & Gulf Coast refineries. Moderate safety, deferred turnaround at Paulsboro.",
        "signal_profile": "energy_downstream_elevated",
        "product_type": "business_interruption",
        "limit": 500_000_000,
        "deductible": 5_000_000,
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
        "description": "World's largest offshore wind developer. 25+ years experience, zero construction-phase total losses.",
        "signal_profile": "energy_offshore_wind_excellent",
        "product_type": "property_damage",
        "limit": 750_000_000,
        "deductible": 5_000_000,
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
        "description": "Dogger Bank & Empire Wind. Oil & gas heritage transitioning, using 13MW Haliade-X turbines.",
        "signal_profile": "energy_offshore_wind_standard",
        "product_type": "property_damage",
        "limit": 500_000_000,
        "deductible": 5_000_000,
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
        "description": "World's largest container line, excellent safety management.",
        "signal_profile": "marine_excellent",
        "product_type": "hull_machinery",
        "limit": 500_000_000,
        "deductible": 2_000_000,
        "hull_value": 25_000_000_000,
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
        "description": "Dry bulk specialist, modern fleet, Hong Kong flag state.",
        "signal_profile": "marine_good",
        "product_type": "hull_machinery",
        "limit": 100_000_000,
        "deductible": 500_000,
        "hull_value": 3_000_000_000,
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
        "description": "Sanctioned entity, flag state risk, aging fleet.",
        "signal_profile": "marine_sanctioned",
        "product_type": "hull_machinery",
        "limit": 50_000_000,
        "deductible": 1_000_000,
        "hull_value": 2_000_000_000,
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
        "description": "Big 4 firm, comprehensive QC, some audit-related claims.",
        "signal_profile": "pi_strong",
        "product_type": "errors_omissions",
        "limit": 100_000_000,
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
        "description": "Material audit failures (Carillion, Wirecard), regulatory scrutiny.",
        "signal_profile": "pi_elevated",
        "product_type": "professional_liability",
        "limit": 50_000_000,
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
        "description": "Top-tier safety record, modern fleet, strong financials.",
        "signal_profile": "aero_excellent",
        "product_type": "aviation_hull_liability_combined",
        "limit": 2_000_000_000,
        "deductible": 5_000_000,
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
        "description": "Young fleet, solid safety record, cost-conscious maintenance.",
        "signal_profile": "aero_good",
        "product_type": "aviation_hull_liability_combined",
        "limit": 1_000_000_000,
        "deductible": 2_500_000,
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
        "description": "Fatal crash history (JT610), safety concerns, regulatory issues.",
        "signal_profile": "aero_elevated",
        "product_type": "aviation_hull_liability_combined",
        "limit": 500_000_000,
        "deductible": 5_000_000,
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


def build_signal_outputs(profile_name, resolved_scores):
    """Build signal_outputs list using pre-resolved scores."""
    profile = SIGNAL_PROFILES.get(profile_name, {})
    outputs = []
    for group_id, signals in profile.items():
        for signal_id in signals:
            score = resolved_scores.get((group_id, signal_id), 50)
            outputs.append({
                "signal_id": signal_id,
                "group_id": group_id,
                "score": score,
                "confidence": round(random.uniform(0.7, 0.99), 2),
                "proxy_tier": random.choice(["DIRECT_OBSERVABLE", "INFERRED_PROXY"]),
                "extraction_time_ms": round(random.uniform(50, 800), 1),
            })
    return outputs


def build_group_scores(profile_name, resolved_scores):
    """Build group-level scores using pre-resolved scores."""
    profile = SIGNAL_PROFILES.get(profile_name, {})
    group_scores = {}
    for group_id, signals in profile.items():
        scores = [resolved_scores.get((group_id, sid), 50) for sid in signals]
        avg = sum(scores) / len(scores) if scores else 50
        group_scores[group_id] = {
            "risk_score": round(avg + random.uniform(-3, 3), 1),
            "loss_score": round(avg + random.uniform(-5, 5), 1),
            "exposure_score": round(avg + random.uniform(-8, 8), 1),
            "signal_count": len(scores),
            "coverage_ratio": round(len(scores) / max(len(scores) + 2, 1), 2),
        }
    return group_scores


def build_signal_conditions(co, resolved_scores):
    """Build signal_conditions from company data - these drive the UI's condition display."""
    conditions = []
    tier = co["tier"]
    profile = SIGNAL_PROFILES.get(co.get("signal_profile", ""), {})

    # Add conditions based on resolved scores (not raw profile values)
    for group_id, signals in profile.items():
        for signal_id in signals:
            score = resolved_scores.get((group_id, signal_id), 50)
            if score <= 30:
                conditions.append({
                    "signal_id": signal_id,
                    "group_id": group_id,
                    "action": "refer",
                    "note": f"Critical: {signal_id.replace('_', ' ').title()} score {score}/100",
                    "applied_modifier": 0.0,
                    "threshold": 30,
                    "comparison": "<=",
                })
            elif score <= 45:
                conditions.append({
                    "signal_id": signal_id,
                    "group_id": group_id,
                    "action": "flag",
                    "note": f"Warning: {signal_id.replace('_', ' ').title()} score {score}/100",
                    "applied_modifier": 0.0,
                    "threshold": 45,
                    "comparison": "<=",
                })
            elif score >= 90:
                conditions.append({
                    "signal_id": signal_id,
                    "group_id": group_id,
                    "action": "modifier",
                    "note": f"Strong {signal_id.replace('_', ' ').title()} - credit applied",
                    "applied_modifier": -0.05,
                    "threshold": 90,
                    "comparison": ">=",
                })

    # Add query-based conditions
    if co.get("referral_reasons"):
        for reason in co["referral_reasons"]:
            conditions.append({
                "signal_id": "direct_query",
                "group_id": "query_conditions",
                "action": "refer" if tier >= 3 else "flag",
                "note": reason,
                "applied_modifier": 0.0,
            })

    return conditions


def build_modifiers_applied(co):
    """Build the modifiers_applied list for the ModelVersionRecord."""
    modifiers = []
    tier = co["tier"]

    # Industry modifier
    industry_mods = {
        "TECHNOLOGY": 1.15, "FINANCIAL_SERVICES": 1.4, "HEALTHCARE": 1.5,
        "RETAIL": 1.25, "MANUFACTURING": 0.95, "ENERGY": 1.2,
    }
    ind = co.get("industry", "OTHER")
    if ind in industry_mods:
        modifiers.append({
            "type": "categorical",
            "source": "industry_classification",
            "applied": industry_mods[ind],
            "note": f"Industry: {ind}",
        })

    # Size modifier
    size_mods = {"MICRO": 0.4, "SMALL": 0.6, "MEDIUM": 1.0, "LARGE": 2.0, "ENTERPRISE": 4.0}
    size = co.get("size_band", "MEDIUM")
    if size in size_mods:
        modifiers.append({
            "type": "categorical",
            "source": "size_band",
            "applied": size_mods[size],
            "note": f"Size: {size}",
        })

    # Signal-derived modifiers (use resolved scores if available)
    profile = SIGNAL_PROFILES.get(co.get("signal_profile", ""), {})
    _resolved = co.get("_resolved_scores", {})
    for group_id, signals in profile.items():
        scores = [_resolved.get((group_id, sid), base) for sid, base in signals.items()]
        avg = sum(scores) / len(scores) if scores else 50
        if avg >= 85:
            modifiers.append({
                "type": "score_condition",
                "source": group_id,
                "applied": 0.92,
                "note": f"Strong {group_id.replace('_', ' ')} credit",
            })
        elif avg <= 30:
            modifiers.append({
                "type": "score_condition",
                "source": group_id,
                "applied": 1.20,
                "note": f"Poor {group_id.replace('_', ' ')} loading",
            })

    return modifiers


def calculate_base_premium(co):
    """Derive base premium from the intended final premium.

    Works backward from co["premium"] to produce a realistic base_premium
    that, when modifiers and ILF are applied, lands near the intended value.
    Uses MULTIPLIER method when revenue is available; PREMIUM_BASE otherwise.
    """
    tier = co["tier"]
    revenue = co.get("revenue", 0)
    intended = co.get("premium", 0)

    if intended <= 0:
        return 0, "premium_base"

    if revenue > 0:
        # Derive an implied rate so the audit trail shows a sensible calculation
        # base = intended / (product of modifiers × ILF) — but we approximate
        # by simply scaling the intended premium down by a tier factor
        tier_divisors = {1: 1.0, 2: 1.2, 3: 1.5, 4: 2.0, 5: 2.5}
        divisor = tier_divisors.get(tier, 1.5)
        return round(intended / divisor, 2), "multiplier"
    else:
        return intended, "premium_base"


def apply_modifiers_to_premium(base_premium, modifiers, target_premium):
    """Apply modifiers to base premium, scaling so the result lands at target_premium.

    Each modifier dict gets premium_before / premium_after fields
    added so the audit trail is complete.  The modifiers are applied
    as a narrative (showing their individual effects) but the final
    value is anchored to the intended premium to avoid runaway values.
    """
    if target_premium <= 0 or not modifiers:
        return target_premium, modifiers

    # Calculate the raw product of all modifier factors
    raw_product = 1.0
    for mod in modifiers:
        raw_product *= mod["applied"]

    # Scale factor so base × scaled_modifiers ≈ target
    # This keeps relative modifier proportions but prevents explosion
    scale = target_premium / (base_premium * raw_product) if (base_premium * raw_product) > 0 else 1.0

    current = base_premium
    enriched = []
    for mod in modifiers:
        factor = mod["applied"] * (scale ** (1.0 / len(modifiers)))  # distribute scale evenly
        before = current
        current = round(current * factor, 2)
        enriched.append({
            **mod,
            "applied": round(factor, 4),
            "premium_before": before,
            "premium_after": current,
        })

    # Snap to target to avoid floating-point drift
    if enriched:
        enriched[-1]["premium_after"] = target_premium
    return target_premium, enriched


def build_premium_options_from_base(premium_after_modifiers):
    """Build premium_options dict using ILF-style scaling from premium_after_modifiers."""
    if premium_after_modifiers <= 0:
        return {}
    p = premium_after_modifiers
    return {
        "1000000": int(p * 0.30),
        "5000000": int(p * 0.80),
        "10000000": int(p * 1.00),
        "25000000": int(p * 1.80),
        "50000000": int(p * 3.00),
    }


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


def build_direct_query_responses(co):
    """Build direct_query_responses based on company risk profile."""
    tier = co["tier"]
    coverage = co["coverage"]

    responses = {}
    if coverage == "cyber":
        responses["mfa_enabled"] = tier <= 2
        responses["security_training"] = tier <= 3
        responses["incident_response_plan"] = tier <= 2
        responses["edr_deployed"] = tier <= 3
        responses["immutable_backups"] = tier <= 3
        responses["recent_incident"] = tier >= 4
        if co.get("industry") == "HEALTHCARE":
            responses["phi_handler"] = True
    elif coverage == "directors_officers":
        responses["pending_claims"] = tier >= 4
        responses["regulatory_investigation"] = tier >= 4
        responses["planned_transaction"] = False
        responses["executive_dispute"] = tier >= 4
    elif coverage == "financial_institutions":
        responses["regulatory_action"] = tier >= 4
        responses["examination_issues"] = tier >= 3
        responses["cyber_incident"] = tier >= 4
        responses["significant_growth"] = False
    elif coverage == "energy":
        responses["major_incident_5yr"] = tier >= 4
        responses["environmental_violation"] = tier >= 3
        responses["shutdown_order"] = tier >= 5
    elif coverage == "marine":
        responses["total_loss_5yr"] = tier >= 4
        responses["detention_12mo"] = tier >= 4
        responses["sanctions_exposure"] = tier >= 5
    elif coverage == "professional_indemnity":
        responses["claims_history"] = tier >= 3
        responses["prior_coverage"] = True
        responses["prior_litigation"] = tier >= 4
    elif coverage == "aerospace":
        responses["hull_loss_5yr"] = tier >= 4
        responses["faa_enforcement"] = tier >= 4
        responses["pilot_shortage"] = tier >= 3

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


def build_loss_propensity(co):
    """Build loss propensity columns keyed for ModelVersionRecord kwargs."""
    tier = co["tier"]
    # Higher tier = higher loss propensity
    base_score = {1: 15, 2: 30, 3: 50, 4: 70, 5: 90}.get(tier, 50)
    loss_score = _score(base_score, 8)
    sev_score = _score(base_score + 5, 10)

    bands_loss = {1: "very_low", 2: "low", 3: "moderate", 4: "elevated", 5: "high"}
    bands_sev = {1: "minimal", 2: "moderate", 3: "significant", 4: "severe", 5: "catastrophic"}

    freq_mult = {1: 0.60, 2: 0.80, 3: 1.00, 4: 1.25, 5: 1.50}.get(tier, 1.0)
    sev_mult = {1: 0.70, 2: 0.90, 3: 1.10, 4: 1.30, 5: 1.50}.get(tier, 1.0)
    combined = round(freq_mult * 0.6 + sev_mult * 0.4, 3)

    return {
        "loss_propensity_score": loss_score,
        "severity_propensity_score": sev_score,
        "loss_propensity_band": bands_loss.get(tier, "moderate"),
        "severity_propensity_band": bands_sev.get(tier, "significant"),
        "loss_confidence": round(random.uniform(0.65, 0.95), 2),
        "loss_cohort_code": f"cohort_{co.get('industry', 'general').lower()}",
        "loss_cohort_name": f"{co.get('industry', 'General')} Cohort",
        "loss_cohort_confidence": round(random.uniform(0.5, 0.9), 2),
        "loss_frequency_multiplier": freq_mult,
        "loss_severity_multiplier": sev_mult,
        "loss_combined_modifier": combined,
        "loss_trend_direction": random.choice(["stable", "improving", "deteriorating"]),
        "loss_previous_score": _score(base_score, 12) if random.random() > 0.3 else None,
        "loss_score_velocity": round(random.uniform(-3, 3), 2) if random.random() > 0.3 else None,
        "loss_last_refresh": NOW - timedelta(days=random.randint(1, 30)) if random.random() > 0.3 else None,
        "correlation_matrix_version": "v1.0.0",
    }


def build_exposure_assessment(co):
    """Build exposure assessment columns keyed for ModelVersionRecord kwargs."""
    # Use revenue or hull_value as the primary exposure metric
    exposure_value = co.get("revenue", 0) or co.get("hull_value", 0) or co.get("tiv", 0) or 0

    # Map to bands based on value ranges (simplified)
    if exposure_value <= 0:
        band_id, band_label, magnitude, modifier = 1, "Minimal", 10.0, 0.80
    elif exposure_value < 50_000_000:
        band_id, band_label, magnitude, modifier = 1, "Small", 20.0, 0.85
    elif exposure_value < 500_000_000:
        band_id, band_label, magnitude, modifier = 2, "Mid-Market", 40.0, 0.95
    elif exposure_value < 5_000_000_000:
        band_id, band_label, magnitude, modifier = 3, "Large", 60.0, 1.05
    elif exposure_value < 50_000_000_000:
        band_id, band_label, magnitude, modifier = 4, "Major", 80.0, 1.15
    else:
        band_id, band_label, magnitude, modifier = 5, "Mega", 95.0, 1.30

    return {
        "exposure_value": float(exposure_value),
        "exposure_band_id": band_id,
        "exposure_band_label": band_label,
        "exposure_magnitude_score": round(magnitude + random.uniform(-5, 5), 1),
        "exposure_modifier": modifier,
        "exposure_assessment_method": "config_band_lookup",
    }


# =============================================================================
# SEED FUNCTION
# =============================================================================

def seed_data():
    print("=" * 70)
    print("  DSI COMPREHENSIVE BENCH SEED")
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
        # Seed each company
        # -----------------------------------------------------------------
        print(f"\n[2/2] Seeding {len(COMPANIES)} companies across all coverages...\n")

        # Caches for signal/source reference table IDs (populated on first encounter)
        _signal_id_cache = {}   # signal_code -> signals.id
        _source_id_cache = {}   # source_name -> signal_sources.id

        stats = {"approve": 0, "refer": 0, "decline": 0}
        coverage_counts = {}

        for i, co in enumerate(COMPANIES, 1):
            decision_enum = DecisionType(co["decision"])
            tier = co["tier"]
            composite = _composite(tier)
            confidence = round(0.6 + (0.35 * (1 - tier / 5)), 2)

            coverage_key = f"{co['coverage']}/{co['configuration']}"
            coverage_counts[coverage_key] = coverage_counts.get(coverage_key, 0) + 1
            stats[co["decision"]] += 1

            print(f"   [{i:2d}/{len(COMPANIES)}] {co['entity_name']:<30s} "
                  f"| {coverage_key:<30s} | Tier {tier} | {co['decision'].upper()}")

            # === 1. SUBMISSION ===
            sub_id = _uid()
            processing_start = NOW - timedelta(minutes=random.randint(5, 60))
            processing_end = processing_start + timedelta(seconds=random.randint(3, 45))

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
                submission_data=build_submission_data(co),
                direct_query_responses=build_direct_query_responses(co),
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
            resolved_scores = resolve_signal_scores(co.get("signal_profile", ""))
            signal_outputs = build_signal_outputs(co.get("signal_profile", ""), resolved_scores)
            group_scores = build_group_scores(co.get("signal_profile", ""), resolved_scores)
            signal_conditions = build_signal_conditions(co, resolved_scores)
            co["_resolved_scores"] = resolved_scores  # pass to build_modifiers_applied
            raw_modifiers = build_modifiers_applied(co)
            discovery = build_discovery_output(co)

            # --- PREMIUM CALCULATION ---
            # Use co["premium"] as the intended final premium (realistic values)
            # and derive intermediate values backward for audit trail consistency.
            intended_premium = co.get("premium", 0)
            base_premium, base_premium_method = calculate_base_premium(co)
            if co["decision"] == "decline":
                base_premium = 0
                premium_after_mods = 0
                final_premium = 0
                enriched_modifiers = raw_modifiers
            else:
                premium_after_mods, enriched_modifiers = apply_modifiers_to_premium(
                    base_premium, raw_modifiers, intended_premium
                )
                final_premium = intended_premium
            limit_premiums = build_premium_options_from_base(final_premium)

            # Build categorical outputs from submission data
            categorical_outputs = []
            for cat_field in ["industry", "size_band", "geography"]:
                val = co.get(cat_field)
                if val:
                    categorical_outputs.append({
                        "group_id": cat_field if cat_field != "industry" else "industry_classification",
                        "selected_cat": val,
                        "source": f"metadata.{cat_field}",
                    })

            # Build loss propensity + exposure assessment
            loss_kwargs = build_loss_propensity(co)
            exposure_kwargs = build_exposure_assessment(co)

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
                signal_outputs=signal_outputs,
                categorical_outputs=categorical_outputs,
                group_scores=group_scores,
                pure_composite_score=composite + random.randint(-20, 20),
                confidence=confidence,
                signal_coverage=round(random.uniform(0.65, 0.95), 2),
                signal_conditions=signal_conditions,
                query_conditions=[
                    {"query_id": k, "response": v, "action": "flag" if not v else "none"}
                    for k, v in build_direct_query_responses(co).items()
                ],
                tier_overrides=[],
                score_based_tier=tier,
                final_tier=tier,
                tier_label=TIER_LABELS.get(tier, "UNKNOWN"),
                base_premium=base_premium,
                base_premium_method=base_premium_method,
                modifiers_applied=enriched_modifiers,
                premium_after_modifiers=premium_after_mods,
                limit_premiums=limit_premiums,
                final_premium=final_premium,
                decision=decision_enum,
                auto_approve=co["decision"] == "approve",
                referral_reasons=co.get("referral_reasons", []),
                notes=[{"note": co.get("description", ""), "source": "seed_script"}],
                created_by="seed_dsi_bench",
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
            }[co["decision"]]

            quote = Quote(
                id=quote_id,
                quote_code=f"Q-{(co['ticker'] or co['entity_name'][:4]).upper().replace(' ', '')}-{_hex(4)}",
                submission_id=sub_id,
                model_version_id=mv_id,
                status=quote_status,
                recommended_premium=final_premium,
                recommended_limit=co.get("limit", 1_000_000),
                premium_options=limit_premiums,
                valid_from=NOW,
                valid_until=NOW + timedelta(days=30),
            )
            db.add(quote)
            db.flush()

            # === 4. REFERRAL (for refer/decline decisions) ===
            if co["decision"] in ("refer", "decline"):
                ref_status = ReferralStatus.PENDING
                reviewed_by = None
                reviewed_at = None
                review_notes = None
                review_decision = None

                # Make some referrals already reviewed
                if co["decision"] == "refer" and random.random() > 0.5:
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
                    reasons=co.get("referral_reasons", ["Tier-based referral"]),
                    priority=min(tier, 5),
                    assigned_to=uw_user_id if ref_status != ReferralStatus.PENDING else None,
                    assigned_at=NOW - timedelta(hours=random.randint(2, 72)) if ref_status != ReferralStatus.PENDING else None,
                    reviewed_by=reviewed_by,
                    reviewed_at=reviewed_at,
                    review_decision=review_decision,
                    review_notes=review_notes,
                    tier_override=tier - 1 if review_decision == "approve" and tier > 1 else None,
                    premium_adjustment=final_premium * 0.1 if review_decision == "approve" else None,
                )
                db.add(referral)
                db.flush()

            # === 5. SIGNAL CACHE ENTRIES ===
            profile = SIGNAL_PROFILES.get(co.get("signal_profile", ""), {})
            cache_id_map = {}  # (group_id, signal_id) -> cache UUID
            for group_id, signals in profile.items():
                for sig_code in signals:
                    resolved = resolved_scores.get((group_id, sig_code), 50)
                    cache_uuid = _uid()
                    cache_id_map[(group_id, sig_code)] = cache_uuid

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
                            "score": resolved,
                            "raw_data": {"source": "seed", "entity": co["entity_name"]},
                            "metadata": {"group_code": group_id},
                        },
                        confidence=round(random.uniform(0.7, 0.99), 2),
                        ttl_seconds=86400,
                        expires_at=NOW + timedelta(days=1),
                        extraction_time_ms=round(random.uniform(30, 500), 1),
                    )
                    db.add(cache)
            db.flush()

            # === 5b. MODEL VERSION SIGNALS (Layer 2 — config-to-signal binding) ===
            signal_output_lookup = {s["signal_id"]: s for s in signal_outputs}
            mvs_id_map = {}  # (group_id, sig_code) -> mvs UUID
            num_groups = len(profile)
            for group_id, signals_in_group in profile.items():
                group_weight = 1.0 / max(num_groups, 1)
                num_in_group = len(signals_in_group)
                signal_weight = round(group_weight / max(num_in_group, 1), 4)

                for sig_code in signals_in_group:
                    cache_ref = cache_id_map.get((group_id, sig_code))
                    if not cache_ref:
                        continue
                    so = signal_output_lookup.get(sig_code, {})
                    resolved = resolved_scores.get((group_id, sig_code), 50)
                    contribution = round(resolved * signal_weight, 2)
                    mvs_uuid = _uid()
                    mvs_id_map[(group_id, sig_code)] = mvs_uuid
                    mvs = ModelVersionSignal(
                        id=mvs_uuid,
                        model_version_id=mv_id,
                        signal_cache_id=cache_ref,
                        signal_id=_signal_id_cache[sig_code],
                        entity_code=co["domain"],
                        score=resolved,
                        weight=signal_weight,
                        contribution=contribution,
                        group_code=group_id,
                        proxy_tier=so.get("proxy_tier", "INFERRED_PROXY"),
                        expectation_level=random.choice(["UNIVERSAL", "ENTERPRISE", "CORPORATE"]),
                        was_absent=False,
                    )
                    db.add(mvs)
            db.flush()

            # === 6. SIGNAL AUDIT RECORDS (for overridden signals) ===
            if co["decision"] == "refer" and profile:
                overridable_signals = [
                    (gid, sid, resolved_scores.get((gid, sid), 50))
                    for gid, sigs in profile.items()
                    for sid in sigs
                    if resolved_scores.get((gid, sid), 50) <= 50
                ]
                for gid, sid, resolved in overridable_signals[:2]:
                    mvs_ref = mvs_id_map.get((gid, sid))
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
                    "decision": co["decision"],
                    "tier": tier,
                    "premium": co["premium"],
                    "source": "seed_dsi_bench",
                },
            )
            db.add(audit_log)

        # -----------------------------------------------------------------
        # Commit everything
        # -----------------------------------------------------------------
        db.commit()

        print("\n" + "=" * 70)
        print("  SEED COMPLETE")
        print("=" * 70)
        print(f"\n  Companies seeded: {len(COMPANIES)}")
        print(f"  Decisions: {stats}")
        print(f"\n  Coverage breakdown:")
        for cov, count in sorted(coverage_counts.items()):
            print(f"    {cov:<35s} {count} companies")

        total_signals = sum(
            len(sigs)
            for co in COMPANIES
            for sigs in SIGNAL_PROFILES.get(co.get("signal_profile", ""), {}).values()
        )
        print(f"\n  Signal cache entries: ~{total_signals}")
        print(f"  Users created: 3 (system, underwriter, analyst)")
        print(f"  Referrals created: {stats['refer'] + stats['decline']}")
        print("=" * 70)

    except Exception as e:
        db.rollback()
        print(f"\n  ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()