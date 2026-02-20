# DSI API Documentation

This directory contains documentation for the DSI API.

## Overview

The DSI API provides endpoints for:

1. **Submissions** - Create and manage insurance submissions
2. **Quotes** - Generate and retrieve pricing quotes
3. **Referrals** - Manage underwriter referral workflow
4. **Analytics** - Access portfolio analytics and performance metrics

## API Reference

### Authentication

All API requests require authentication via API key:

```http
Authorization: Bearer <api_key>
```

### Endpoints

See individual documentation files:

- [Submissions API](./submissions.md)
- [Quotes API](./quotes.md)
- [Referrals API](./referrals.md)
- [Analytics API](./analytics.md)

## OpenAPI Specification

The full OpenAPI specification is available at `/openapi.json` when the API server is running.

## Rate Limits

- Standard tier: 100 requests/minute
- Premium tier: 1000 requests/minute

## Error Handling

All errors return a standard JSON format:

```json
{
    "error": {
        "code": "error_code",
        "message": "Human readable message",
        "details": {}
    }
}
```
