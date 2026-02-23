import uuid
import json
from datetime import datetime
# Import 'text' to fix the error you received
from sqlalchemy import text
from infrastructure.db.config import session_scope

# --- DATASET ---
COMPANIES = [
    {"name": "Cloudflare", "ticker": "NET", "domain": "cloudflare.com", "tier": 1, "premium": 125000, "status": "approve"},
    {"name": "CrowdStrike", "ticker": "CRWD", "domain": "crowdstrike.com", "tier": 1, "premium": 98000, "status": "approve"},
    {"name": "Boeing", "ticker": "BA", "domain": "boeing.com", "tier": 3, "premium": 450000, "status": "refer"},
    {"name": "Petrobras", "ticker": "PBR", "domain": "petrobras.com.br", "tier": 4, "premium": 820000, "status": "refer"},
    {"name": "Klarna", "ticker": "KLAR", "domain": "klarna.com", "tier": 2, "premium": 210000, "status": "approve"},
    {"name": "Shopify", "ticker": "SHOP", "domain": "shopify.com", "tier": 1, "premium": 115000, "status": "approve"},
    {"name": "Pemex", "ticker": "PMX", "domain": "pemex.com", "tier": 5, "premium": 0, "status": "decline"},
    {"name": "Beazley", "ticker": "BEZ", "domain": "beazley.com", "tier": 2, "premium": 185000, "status": "approve"},
    {"name": "Markel", "ticker": "MKL", "domain": "markel.com", "tier": 2, "premium": 195000, "status": "approve"},
    {"name": "Palo Alto Networks", "ticker": "PANW", "domain": "paloaltonetworks.com", "tier": 1, "premium": 105000, "status": "approve"},
    {"name": "Rolls-Royce", "ticker": "RR", "domain": "rolls-royce.com", "tier": 3, "premium": 310000, "status": "refer"},
    {"name": "Caterpillar", "ticker": "CAT", "domain": "caterpillar.com", "tier": 2, "premium": 240000, "status": "approve"},
    {"name": "Atlassian", "ticker": "TEAM", "domain": "atlassian.com", "tier": 1, "premium": 88000, "status": "approve"}
]

def seed_data():
    print("--- Initializing DSI Hall of Fame Seeding ---")
    
    with session_scope() as session:
        # 1. Clear existing data using explicit text() wrappers
        print("Cleaning old records...")
        session.execute(text("DELETE FROM model_versions"))
        session.execute(text("DELETE FROM submissions"))
        
        for co in COMPANIES:
            sub_id = f"sub_{co['ticker'].lower()}_{uuid.uuid4().hex[:6]}"
            print(f"Injecting: {co['name']} -> {sub_id}")

            # 2. Insert Submission
            sub_query = text("""
                INSERT INTO submissions (id, entity_name, discovered_domain, coverage, status, created_at) 
                VALUES (:id, :name, :domain, :cov, :status, :now)
            """)
            session.execute(sub_query, {
                "id": sub_id, 
                "name": co['name'], 
                "domain": co['domain'], 
                "cov": "cyber", 
                "status": co['status'], 
                "now": datetime.utcnow()
            })

            # 3. Insert Model Version (The linked pricing result)
            signals = [
                {"note": "Strong Tech hygiene signal", "action": "modifier", "applied_modifier": -0.05},
                {"note": f"DSI Primary Analysis: {co['name']}", "action": "flag", "applied_modifier": 0.0}
            ]
            
            mv_query = text("""
                INSERT INTO model_versions (id, submission_id, final_tier, tier_label, final_premium, decision, signal_conditions, created_at) 
                VALUES (:id, :sub_id, :tier, :label, :prem, :dec, :sigs, :now)
            """)
            session.execute(mv_query, {
                "id": f"mv_{uuid.uuid4().hex[:8]}",
                "sub_id": sub_id,
                "tier": co['tier'],
                "label": f"Tier {co['tier']}",
                "prem": co['premium'],
                "dec": co['status'],
                "sigs": json.dumps(signals),
                "now": datetime.utcnow()
            })
        
        print("--- All companies seeded successfully ---")

if __name__ == "__main__":
    try:
        seed_data()
    except Exception as e:
        print(f"ERROR: {e}")