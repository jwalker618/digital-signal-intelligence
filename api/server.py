"""
Digital Signal Intelligence API Server
=======================================

REST API for DSI pricing models and portfolio analytics

Author: John Walker
Date: November 2025
Version: 1.0
"""

import os
import sys
from pathlib import Path

# Add models directory to path
models_path = Path(__file__).parent.parent / "models"
sys.path.insert(0, str(models_path))

import logging  # noqa: E402
from datetime import datetime  # noqa: E402

from flask import Flask, jsonify, request  # noqa: E402
from flask_cors import CORS  # noqa: E402
from flask_restx import Api, Namespace, Resource, fields  # noqa: E402

# Import pricing models
try:
    from cyber.dsi_cyber_pricing import (
        CompanySize,
        CyberCompanyProfile,
        CyberCoverageType,
        CyberInsurancePricingModel,
        CyberSecuritySignals,
        IndustryVertical,
    )
    from energy.dsi_energy_pricing import CompanyProfile as EnergyProfile
    from energy.dsi_energy_pricing import (
        DigitalSignals,
    )
    from energy.dsi_energy_pricing import create_pricing_models as create_energy_models
    from financial_institutions.dsi_financial_institutions import (
        FICoverageType,
        FinancialInstitutionPricingModel,
        FinancialInstitutionProfile,
        FinancialInstitutionSignals,
        FinancialInstitutionType,
    )
    from portfolio.dsi_portfolio_analytics import DSIPortfolioAnalytics

    MODELS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Some models could not be imported: {e}")
    MODELS_AVAILABLE = False


# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize Flask-RESTX API
api = Api(
    app,
    version="1.0",
    title="Digital Signal Intelligence API",
    description="Insurance pricing API using digital footprint analysis",
    doc="/docs",
    prefix="/api/v1",
)

# Create namespaces for each model
cyber_ns = Namespace("cyber", description="Cyber insurance pricing operations")
energy_ns = Namespace("energy", description="Energy sector pricing operations")
fi_ns = Namespace("financial", description="Financial institutions pricing operations")
portfolio_ns = Namespace("portfolio", description="Portfolio analytics operations")

# Add namespaces to API
api.add_namespace(cyber_ns, path="/cyber")
api.add_namespace(energy_ns, path="/energy")
api.add_namespace(fi_ns, path="/financial")
api.add_namespace(portfolio_ns, path="/portfolio")


# ==============================================================================
# API Models (Request/Response schemas)
# ==============================================================================

# Cyber Insurance Models
cyber_signals_model = cyber_ns.model(
    "CyberSecuritySignals",
    {
        "ssl_certificate": fields.Float(required=True, min=0, max=100),
        "tls_version": fields.Float(required=True, min=0, max=100),
        "security_headers": fields.Float(required=True, min=0, max=100),
        "dnssec_implementation": fields.Float(required=True, min=0, max=100),
        "known_vulnerabilities": fields.Float(required=True, min=0, max=100),
        "patch_discipline": fields.Float(required=True, min=0, max=100),
        # Add other signals as needed
    },
)

cyber_profile_model = cyber_ns.model(
    "CyberCompanyProfile",
    {
        "company_name": fields.String(required=True),
        "industry": fields.String(required=True),
        "country": fields.String(required=True),
        "annual_revenue": fields.Float(required=True),
        "employees": fields.Integer(required=True),
        "records_stored": fields.Integer(required=True),
        "coverage_type": fields.String(required=True),
        "signals": fields.Nested(cyber_signals_model, required=True),
    },
)

# Energy Pricing Models
energy_signals_model = energy_ns.model(
    "DigitalSignals",
    {
        "ssl_score": fields.Float(required=True, min=0, max=100),
        "security_headers": fields.Float(required=True, min=0, max=100),
        "governance_disclosure": fields.Float(required=True, min=0, max=100),
        "esg_reporting": fields.Float(required=True, min=0, max=100),
        # Add other signals
    },
)

energy_profile_model = energy_ns.model(
    "EnergyCompanyProfile",
    {
        "company_name": fields.String(required=True),
        "country": fields.String(required=True),
        "segment": fields.String(
            required=True, enum=["upstream", "midstream", "downstream"]
        ),
        "annual_revenue": fields.Float(required=True),
        "employees": fields.Integer(required=True),
        "coverage_type": fields.String(required=True),
        "signals": fields.Nested(energy_signals_model, required=True),
    },
)

# Financial Institutions Models
fi_signals_model = fi_ns.model(
    "FinancialInstitutionSignals",
    {
        "regulatory_disclosures": fields.Float(required=True, min=0, max=100),
        "enforcement_history": fields.Float(required=True, min=0, max=100),
        "board_composition": fields.Float(required=True, min=0, max=100),
        "financial_reporting": fields.Float(required=True, min=0, max=100),
        # Add other signals
    },
)

fi_profile_model = fi_ns.model(
    "FinancialInstitutionProfile",
    {
        "institution_name": fields.String(required=True),
        "institution_type": fields.String(required=True),
        "country": fields.String(required=True),
        "assets_under_management": fields.Float(required=True),
        "employees": fields.Integer(required=True),
        "coverage_type": fields.String(required=True),
        "enforcement_actions_5yr": fields.Integer(required=True),
        "signals": fields.Nested(fi_signals_model, required=True),
    },
)


# ==============================================================================
# Cyber Insurance Endpoints
# ==============================================================================


@cyber_ns.route("/quote")
class CyberQuote(Resource):
    @cyber_ns.expect(cyber_profile_model)
    @cyber_ns.doc("get_cyber_quote")
    def post(self):
        """Generate a cyber insurance quote"""
        try:
            data = request.json
            logger.info(f"Received cyber quote request for: {data.get('company_name')}")

            # Parse coverage type
            coverage_str = data.get("coverage_type", "comprehensive").upper()
            coverage_type = (
                CyberCoverageType[coverage_str]
                if coverage_str in CyberCoverageType.__members__
                else CyberCoverageType.COMPREHENSIVE
            )

            # Create signals object
            signals_data = data.get("signals", {})
            signals = CyberSecuritySignals(**signals_data)

            # Create company profile
            profile = CyberCompanyProfile(
                company_name=data["company_name"],
                industry=IndustryVertical[data.get("industry", "TECHNOLOGY").upper()],
                country=data["country"],
                annual_revenue=data["annual_revenue"],
                employees=data["employees"],
                size_category=CompanySize.SMALL,  # Determine based on employees
                records_stored=data["records_stored"],
                pii_volume=data.get("pii_volume", "medium"),
                phi_handler=data.get("phi_handler", False),
                pci_scope=data.get("pci_scope", False),
                cloud_percentage=data.get("cloud_percentage", 50),
                legacy_systems=data.get("legacy_systems", False),
                bring_your_own_device=data.get("bring_your_own_device", False),
                remote_workforce_pct=data.get("remote_workforce_pct", 30),
                prior_incidents=data.get("prior_incidents", 0),
                cyber_insurance_history=data.get("cyber_insurance_history", 0),
                it_budget_pct=data.get("it_budget_pct", 5.0),
                signals=signals,
            )

            # Calculate pricing
            model = CyberInsurancePricingModel(coverage_type=coverage_type)
            result = model.calculate_premium(profile)

            # Format response
            response = {
                "success": True,
                "company_name": result.company_name,
                "coverage_type": coverage_type.value,
                "composite_score": result.composite_score,
                "risk_tier": result.risk_tier,
                "annual_premium": result.annual_premium,
                "recommended_limit": result.recommended_limit,
                "recommended_retention": result.recommended_retention,
                "breach_probability": result.breach_probability,
                "recommendation": result.recommendation,
                "recommendations": result.recommendations,
                "timestamp": datetime.now().isoformat(),
            }

            logger.info(
                f"Cyber quote generated: {result.company_name} - ${result.annual_premium:,.2f}"
            )
            return response, 200

        except Exception as e:
            logger.error(f"Error generating cyber quote: {str(e)}")
            return {"success": False, "error": str(e)}, 400


@cyber_ns.route("/health")
class CyberHealth(Resource):
    @cyber_ns.doc("cyber_health_check")
    def get(self):
        """Health check for cyber pricing service"""
        return {
            "status": "healthy",
            "service": "cyber-pricing",
            "version": "1.0",
            "timestamp": datetime.now().isoformat(),
        }, 200


# ==============================================================================
# Energy Sector Endpoints
# ==============================================================================


@energy_ns.route("/quote")
class EnergyQuote(Resource):
    @energy_ns.expect(energy_profile_model)
    @energy_ns.doc("get_energy_quote")
    def post(self):
        """Generate an energy sector insurance quote"""
        try:
            data = request.json
            logger.info(
                f"Received energy quote request for: {data.get('company_name')}"
            )

            # Parse segment and coverage
            segment = data.get("segment", "upstream").lower()
            coverage_type = data.get("coverage_type", "property_damage")

            # Create signals
            signals_data = data.get("signals", {})
            signals = DigitalSignals(**signals_data)

            # Create company profile
            profile = EnergyProfile(
                company_name=data["company_name"],
                country=data["country"],
                annual_revenue=data["annual_revenue"],
                employees=data["employees"],
                years_in_operation=data.get("years_in_operation", 10),
                public_company=data.get("public_company", False),
                market_cap=data.get("market_cap", 0),
                production_volume=data.get("production_volume", 0),
                reserves=data.get("reserves", 0),
                international_operations=data.get("international_operations", False),
                prior_incidents_5yr=data.get("prior_incidents_5yr", 0),
                insurance_history_years=data.get("insurance_history_years", 0),
                signals=signals,
            )

            # Get appropriate pricing model
            models = create_energy_models()
            model_key = f"{segment}_{coverage_type}"

            if model_key not in models:
                return {
                    "success": False,
                    "error": f"Invalid segment/coverage: {model_key}",
                }, 400

            model = models[model_key]
            result = model.calculate_premium(profile)

            # Format response
            response = {
                "success": True,
                "company_name": result.company_name,
                "segment": segment,
                "coverage_type": coverage_type,
                "composite_score": result.composite_score,
                "risk_tier": result.risk_tier,
                "annual_premium": result.annual_premium,
                "recommended_limit": result.recommended_limit,
                "recommendation": result.recommendation,
                "timestamp": datetime.now().isoformat(),
            }

            logger.info(
                f"Energy quote generated: {result.company_name} - ${result.annual_premium:,.2f}"
            )
            return response, 200

        except Exception as e:
            logger.error(f"Error generating energy quote: {str(e)}")
            return {"success": False, "error": str(e)}, 400


@energy_ns.route("/health")
class EnergyHealth(Resource):
    @energy_ns.doc("energy_health_check")
    def get(self):
        """Health check for energy pricing service"""
        return {
            "status": "healthy",
            "service": "energy-pricing",
            "version": "1.0",
            "timestamp": datetime.now().isoformat(),
        }, 200


# ==============================================================================
# Financial Institutions Endpoints
# ==============================================================================


@fi_ns.route("/quote")
class FIQuote(Resource):
    @fi_ns.expect(fi_profile_model)
    @fi_ns.doc("get_fi_quote")
    def post(self):
        """Generate a financial institution insurance quote"""
        try:
            data = request.json
            logger.info(
                f"Received FI quote request for: {data.get('institution_name')}"
            )

            # Parse coverage type
            coverage_str = data.get("coverage_type", "DNO").upper()
            coverage_type = (
                FICoverageType[coverage_str]
                if coverage_str in FICoverageType.__members__
                else FICoverageType.DNO
            )

            # Create signals
            signals_data = data.get("signals", {})
            signals = FinancialInstitutionSignals(**signals_data)

            # Create institution profile
            profile = FinancialInstitutionProfile(
                institution_name=data["institution_name"],
                institution_type=FinancialInstitutionType[
                    data.get("institution_type", "COMMERCIAL_BANK").upper()
                ],
                jurisdiction=data.get("jurisdiction", "US_FEDERAL"),
                country=data["country"],
                assets_under_management=data["assets_under_management"],
                annual_revenue=data.get("annual_revenue", 0),
                employees=data["employees"],
                years_in_operation=data.get("years_in_operation", 10),
                public_company=data.get("public_company", False),
                systemically_important=data.get("systemically_important", False),
                regulatory_examinations_clean=data.get(
                    "regulatory_examinations_clean", True
                ),
                enforcement_actions_5yr=data["enforcement_actions_5yr"],
                settlement_amount_5yr=data.get("settlement_amount_5yr", 0),
                active_investigations=data.get("active_investigations", False),
                client_accounts=data.get("client_accounts", 0),
                international_operations=data.get("international_operations", False),
                complex_products=data.get("complex_products", False),
                prior_claims=data.get("prior_claims", 0),
                insurance_history_years=data.get("insurance_history_years", 0),
                signals=signals,
            )

            # Calculate pricing
            model = FinancialInstitutionPricingModel(coverage_type=coverage_type)
            result = model.calculate_premium(profile)

            # Format response
            response = {
                "success": True,
                "institution_name": result.institution_name,
                "coverage_type": coverage_type.value,
                "composite_score": result.composite_score,
                "risk_tier": result.risk_tier,
                "annual_premium": result.annual_premium,
                "recommended_limit": result.recommended_limit,
                "regulatory_risk_probability": result.regulatory_risk_probability,
                "recommendation": result.recommendation,
                "recommendations": result.recommendations,
                "timestamp": datetime.now().isoformat(),
            }

            logger.info(
                f"FI quote generated: {result.institution_name} - ${result.annual_premium:,.2f}"
            )
            return response, 200

        except Exception as e:
            logger.error(f"Error generating FI quote: {str(e)}")
            return {"success": False, "error": str(e)}, 400


@fi_ns.route("/health")
class FIHealth(Resource):
    @fi_ns.doc("fi_health_check")
    def get(self):
        """Health check for financial institutions pricing service"""
        return {
            "status": "healthy",
            "service": "fi-pricing",
            "version": "1.0",
            "timestamp": datetime.now().isoformat(),
        }, 200


# ==============================================================================
# Portfolio Analytics Endpoints
# ==============================================================================


@portfolio_ns.route("/metrics")
class PortfolioMetrics(Resource):
    @portfolio_ns.doc("get_portfolio_metrics")
    def post(self):
        """Calculate portfolio-level metrics"""
        try:
            data = request.json
            logger.info("Received portfolio metrics request")

            # Create portfolio
            portfolio = DSIPortfolioAnalytics()

            # Add policies from request
            for policy_data in data.get("policies", []):
                # This would need actual pricing results
                # For now, return sample response
                pass

            # Calculate metrics
            metrics = portfolio.calculate_portfolio_metrics()

            response = {
                "success": True,
                "metrics": {
                    "total_premium": metrics.total_premium,
                    "policy_count": metrics.policy_count,
                    "tier_distribution": {
                        "tier_1": metrics.tier_1_count,
                        "tier_2": metrics.tier_2_count,
                        "tier_3": metrics.tier_3_count,
                        "tier_4": metrics.tier_4_count,
                        "tier_5": metrics.tier_5_count,
                    },
                    "avg_composite_score": metrics.avg_composite_score,
                    "auto_approved_pct": metrics.auto_approved_pct,
                    "expected_loss_ratio": metrics.expected_loss_ratio,
                },
                "timestamp": datetime.now().isoformat(),
            }

            return response, 200

        except Exception as e:
            logger.error(f"Error calculating portfolio metrics: {str(e)}")
            return {"success": False, "error": str(e)}, 400


@portfolio_ns.route("/health")
class PortfolioHealth(Resource):
    @portfolio_ns.doc("portfolio_health_check")
    def get(self):
        """Health check for portfolio analytics service"""
        return {
            "status": "healthy",
            "service": "portfolio-analytics",
            "version": "1.0",
            "timestamp": datetime.now().isoformat(),
        }, 200


# ==============================================================================
# Root Endpoints
# ==============================================================================


@app.route("/")
def index():
    """API root endpoint"""
    return jsonify(
        {
            "service": "Digital Signal Intelligence API",
            "version": "1.0",
            "status": "operational",
            "documentation": "/docs",
            "endpoints": {
                "cyber": "/api/v1/cyber",
                "energy": "/api/v1/energy",
                "financial": "/api/v1/financial",
                "portfolio": "/api/v1/portfolio",
            },
            "timestamp": datetime.now().isoformat(),
        }
    )


@app.route("/health")
def health():
    """Overall health check"""
    return (
        jsonify(
            {
                "status": "healthy",
                "service": "dsi-api",
                "version": "1.0",
                "models_available": MODELS_AVAILABLE,
                "timestamp": datetime.now().isoformat(),
            }
        ),
        200,
    )


# ==============================================================================
# Error Handlers
# ==============================================================================


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found", "message": str(error)}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({"error": "Internal server error", "message": str(error)}), 500


# ==============================================================================
# Main Entry Point
# ==============================================================================


def main():
    """Main entry point for the API server"""
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("DEBUG", "False").lower() == "true"

    logger.info(f"Starting DSI API server on port {port}")
    logger.info(f"Debug mode: {debug}")
    logger.info(f"Documentation available at: http://localhost:{port}/docs")

    app.run(host="0.0.0.0", port=port, debug=debug)


if __name__ == "__main__":
    main()
