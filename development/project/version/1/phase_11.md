# Phase 11: Production API

## Purpose
Expose the full DSI model as a production‑grade API with authentication, routing, and middleware.

## Key Deliverables
- FastAPI implementation
- Auth modules (JWT + API key)
- 32 documented API endpoints
- Middleware for logging, tracing, and error handling

## Implementation Summary
This phase wraps the DSI engine in a secure, scalable API layer. It includes authentication, request validation, routing, and documentation.

 Add async extractor support (future enhancement)

## Detailed Plan

Complete production-grade API for full model interaction.

### 11.1 API Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      DSI API GATEWAY                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Authentication │ Rate Limiting │ Logging │ Monitoring          │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    REST ENDPOINTS                        │   │
│  │                                                          │   │
│  │  /api/v1/submissions     POST, GET                       │   │
│  │  /api/v1/quotes          POST, GET, PATCH                │   │
│  │  /api/v1/referrals       GET, PATCH                      │   │
│  │  /api/v1/discovery       POST                            │   │
│  │  /api/v1/portfolio       GET                             │   │
│  │  /api/v1/analytics       GET                             │   │
│  │  /api/v1/config          GET, POST (admin)               │   │
│  │  /api/v1/health          GET                             │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    ASYNC JOBS                            │   │
│  │                                                          │   │
│  │  /api/v1/jobs            POST (long-running)             │   │
│  │  /api/v1/jobs/{id}       GET (status)                    │   │
│  │  /api/v1/webhooks        POST (callbacks)                │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    WEBSOCKET                             │   │
│  │                                                          │   │
│  │  /ws/submissions/{id}    Real-time status updates        │   │
│  │  /ws/portfolio           Live portfolio feed             │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 11.2 Core Endpoints

```python
# Submission endpoints
@router.post("/api/v1/submissions")
async def create_submission(
    request: SubmissionRequest,
    background_tasks: BackgroundTasks
) -> SubmissionResponse:
    """
    Create new submission and trigger pricing.

    Request:
    {
        "entity_name": "Acme Corp",
        "domain_hint": "acme.com",
        "coverage": "cyber",
        "submission_data": {
            "tiv": 10000000,
            "revenue": 50000000
        },
        "direct_query_responses": {
            "bankruptcy_filed": false
        }
    }

    Response:
    {
        "submission_id": "sub_abc123",
        "status": "processing",
        "estimated_completion": "2024-01-15T10:30:00Z"
    }
    """
    pass

@router.get("/api/v1/quotes/{quote_id}")
async def get_quote(quote_id: str) -> QuoteResponse:
    """
    Retrieve quote details.

    Response:
    {
        "quote_id": "quo_xyz789",
        "submission_id": "sub_abc123",
        "status": "ready",
        "composite_score": 742,
        "tier": 2,
        "tier_label": "STANDARD",
        "decision": "approve",
        "premium_options": {
            "1000000": 12500,
            "2000000": 18750,
            "5000000": 31250
        },
        "recommended_premium": 18750,
        "discovery": {
            "domain": "acme.com",
            "confidence": "high"
        },
        "signal_summary": {...},
        "valid_until": "2024-02-15T00:00:00Z"
    }
    """
    pass

@router.patch("/api/v1/referrals/{referral_id}")
async def process_referral(
    referral_id: str,
    decision: ReferralDecision
) -> QuoteResponse:
    """
    Process a referral decision.

    Request:
    {
        "decision": "approve",  # approve, decline, modify
        "adjustments": {
            "tier_override": 3,
            "premium_adjustment": 1.15
        },
        "notes": ["Manual review completed"]
    }
    """
    pass

# Multi-coverage endpoint
@router.post("/api/v1/submissions/multi")
async def create_multi_coverage_submission(
    request: MultiCoverageRequest
) -> MultiSubmissionResponse:
    """Create submission across multiple coverages/locales"""
    pass

# Analytics endpoints
@router.get("/api/v1/analytics/portfolio")
async def get_portfolio_analytics(
    coverage: str = None,
    period: str = "mtd"
) -> PortfolioAnalytics:
    """Get portfolio-level analytics"""
    pass
```

### 11.3 Authentication & Security

```python
# JWT-based authentication
@router.post("/api/v1/auth/token")
async def create_token(credentials: Credentials) -> TokenResponse:
    """Issue JWT token"""
    pass

# API key authentication for system integrations
@router.post("/api/v1/auth/api-key")
async def validate_api_key(api_key: str) -> ValidationResponse:
    """Validate API key"""
    pass

# Role-based access control
class Permission(Enum):
    SUBMIT = "submit"           # Create submissions
    QUOTE = "quote"             # View quotes
    REFERRAL = "referral"       # Process referrals
    ANALYTICS = "analytics"     # View analytics
    ADMIN = "admin"             # Admin operations

@requires_permission(Permission.REFERRAL)
async def process_referral(...):
    pass
```

### 11.4 Rate Limiting & Quotas

```yaml
rate_limits:
  default:
    requests_per_minute: 60
    requests_per_day: 10000

  by_endpoint:
    /api/v1/submissions:
      requests_per_minute: 30
    /api/v1/discovery:
      requests_per_minute: 20

  by_tier:
    standard:
      requests_per_minute: 60
    premium:
      requests_per_minute: 300
    enterprise:
      requests_per_minute: 1000

quotas:
  submissions_per_month: 1000
  api_calls_per_month: 100000
```

### 11.5 Implementation Tasks

| Task | File | Status |
|-|-|-|
| Set up FastAPI application | `api/main.py` | ✅ Complete |
| Create submission endpoints | `api/routes/submissions.py` | ✅ Complete |
| Create quote endpoints | `api/routes/quotes.py` | ✅ Complete |
| Create referral endpoints | `api/routes/referrals.py` | ✅ Complete |
| Create analytics endpoints | `api/routes/analytics.py` | ✅ Complete |
| Implement authentication | `api/auth/` | ✅ Complete |
| Add rate limiting | `api/middleware/` | ✅ Complete |
| Add request logging | `api/middleware/` | ✅ Complete |
| Create OpenAPI documentation | FastAPI auto-generated | ✅ Complete |
| Add API tests | `tests/api/` | ✅ Complete |
| Create Docker configuration | `deploy/docker-compose.yml` | ✅ Complete |
