# Phase V3-6: Release v1.0.0

**Status:** Not Started
**Priority:** High
**Prerequisites:** V3-1 (Test Recovery), V3-4 (Production Extractors)

## Objective

Tag a v1.0.0 release with a clean, production-ready state: all tests passing, documentation current, CI green, Docker image building, and at least a subset of production extractors operational.

## Tasks

1. **All tests passing** — 0 collection errors, 0 failures
2. **CI pipeline green** — Unit, integration, Rust build all pass
3. **Docker image builds** — Dockerfile produces working container
4. **Compile Rust wheel** — `maturin develop` produces installable dsi_core module
5. **Documentation current** — SKILL.md, README.md, builder README all accurate
6. **Changelog** — Document all changes since initial development
7. **Tag release** — `git tag v1.0.0`
8. **Publish Docker image** — Push to GHCR

## Release Checklist

- [ ] All tests pass (`python -m pytest tests/ -v`)
- [ ] Rust compiles (`cargo build --release` in `rust/dsi-core/`)
- [ ] Docker builds (`docker build -t dsi .`)
- [ ] All 7 configs validate (`python -m infrastructure.builder.cli validate coverages/*/config.yaml`)
- [ ] API starts successfully (`uvicorn infrastructure.api.main:app`)
- [ ] E2E pipeline works (submit → score → tier → decision)
- [ ] SKILL.md is current
- [ ] No hardcoded secrets in repository

## Success Criteria

- Tagged v1.0.0 release on main branch
- Docker image available in GHCR
- All CI checks green
- Documentation complete and accurate
