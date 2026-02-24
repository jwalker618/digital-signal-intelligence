import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import the actual Base and Models from your codebase
from infrastructure.db.config import Base, DATABASE_URL_SYNC
from infrastructure.db.models import (
    Submission, 
    Quote, 
    ModelVersionRecord,
    SubmissionStatus, 
    QuoteStatus, 
    DecisionType
)

# --- DATASET ---
COMPANIES = [
    {"name": "Cloudflare", "ticker": "NET", "domain": "cloudflare.com", "tier": 1, "premium": 125000, "status": "approve"},
    {"name": "CrowdStrike", "ticker": "CRWD", "domain": "crowdstrike.com", "tier": 1, "premium": 98000, "status": "approve"},
    {"name": "Boeing", "ticker": "BA", "domain": "boeing.com", "tier": 3, "premium": 450000, "status": "refer"},
    {"name": "Petrobras", "ticker": "PBR", "domain": "petrobras.com.br", "tier": 4, "premium": 820000, "status": "refer"},
    {"name": "Pemex", "ticker": "PMX", "domain": "pemex.com", "tier": 5, "premium": 0, "status": "decline"}
]

def seed_data():
    print("--- Initializing DSI Hall of Fame Seeding ---")
    
    engine = create_engine(DATABASE_URL_SYNC)
    SessionLocal = sessionmaker(bind=engine)

    print("Rebuilding perfect database schema from ORM models...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        for co in COMPANIES:
            decision_enum = DecisionType(co['status'])
            print(f"Injecting: {co['name']}")

            # 1. Create Submission WITH configuration string to pass Pydantic validation
            sub = Submission(
                id=uuid.uuid4(),
                submission_id=f"sub_{co['ticker'].lower()}_{uuid.uuid4().hex[:6]}",
                entity_name=co['name'],
                discovered_domain=co['domain'],
                coverage="cyber",
                configuration="cyber_general",  # <--- THE MAGIC FIX
                status=SubmissionStatus.READY
            )
            db.add(sub)
            db.flush() 

            # 2. Create ModelVersionRecord
            mv = ModelVersionRecord(
                id=uuid.uuid4(),
                version_id=f"mv_{uuid.uuid4().hex[:8]}",
                submission_id=sub.id,
                version_number=1,
                final_tier=co['tier'],
                tier_label=f"Tier {co['tier']}",
                decision=decision_enum,
                final_premium=co['premium'],
                signal_conditions=[
                    {"note": "Strong Tech hygiene signal", "action": "modifier", "applied_modifier": -0.05},
                    {"note": f"DSI Primary Analysis: {co['name']}", "action": "flag", "applied_modifier": 0.0}
                ]
            )
            db.add(mv)
            db.flush()

            # 3. Create Final Quote
            quote = Quote(
                id=uuid.uuid4(),
                quote_id=f"Q-{co['ticker']}-001",
                submission_id=sub.id,
                model_version_id=mv.id,
                status=QuoteStatus.READY,
                decision=decision_enum,
                tier=co['tier'],
                tier_label=f"Tier {co['tier']}",
                recommended_premium=co['premium'],
                valid_until=datetime.now(timezone.utc) + timedelta(days=30) # <--- TIMEZONE FIX
            )
            db.add(quote)

        db.commit()
        print("--- All companies seeded successfully ---")
        
    except Exception as e:
        db.rollback()
        print(f"ERROR: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()