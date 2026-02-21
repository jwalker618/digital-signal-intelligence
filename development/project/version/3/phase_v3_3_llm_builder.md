# Phase V3-3: LLM Integration for Builder

**Status:** Not Started
**Priority:** Medium
**Prerequisites:** V3-1 (Test Recovery)

## Context

The coverage builder currently uses template-based generation. The `llm_client` parameter is accepted but never called. For complex or novel coverage types, LLM assistance could improve signal selection, weight tuning, and industry-specific query generation.

## Objective

Integrate an LLM client into the builder for enhanced coverage creation:
- Smarter signal selection based on industry analysis
- Industry-specific direct query generation
- Weight recommendation tuning
- Natural language coverage specification parsing

## Tasks

1. **LLM Prompt Templates** — Structured prompts for signal selection, query generation, weight tuning
2. **LLM Client Interface** — Abstract interface supporting multiple providers (OpenAI, Anthropic, local)
3. **Enhanced Industry Analysis** — LLM-augmented risk factor identification
4. **Query Generation** — LLM generates industry-specific direct queries (validated against action rules)
5. **Weight Tuning** — LLM suggests signal weights based on industry analysis
6. **Natural Language Spec** — Parse free-text coverage descriptions into CoverageSpec

## Constraints

- LLM output must be validated against v2.0 schema before use
- score_conditions actions: FLAG | MODIFIER | REFER only (DECLINE tier-level)
- Generated configs must pass validator before being saved
- LLM is advisory — template output is the fallback

## Key Files to Create

- `infrastructure/builder/llm_client.py` — LLM provider interface
- `infrastructure/builder/prompts.py` — Prompt templates
- `infrastructure/builder/llm_analysis.py` — LLM-enhanced analysis

## Success Criteria

- Builder can use LLM for enhanced signal selection and query generation
- LLM output always validated against v2.0 schema
- Graceful fallback to template-based generation when LLM unavailable
- No DECLINE actions in LLM-generated score_conditions
