"""V6/Stage-6 — deepened-parsing tests for hiring.py + sentiment.py extractors."""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Hiring
# ---------------------------------------------------------------------------


def test_greenhouse_deepened_parsing(monkeypatch):
    from signal_architecture.signals.extractors.production import hiring
    from signal_architecture.signals.extractors.production.hiring import GreenhouseScraper
    sample = {
        "jobs": [
            {"departments": [{"name": "Engineering"}],
             "offices": [{"name": "San Francisco"}],
             "location": {"name": "Remote, US"}},
            {"departments": [{"name": "Engineering"}],
             "offices": [{"name": "San Francisco"}],
             "location": {"name": "San Francisco, CA"}},
            {"departments": [{"name": "Sales"}],
             "offices": [{"name": "New York"}],
             "location": {"name": "New York, NY"}},
        ],
    }
    monkeypatch.setattr(hiring, "_json", lambda url, **kw: sample)
    monkeypatch.delenv("DSI_DISABLE_GREENHOUSE", raising=False)
    r = GreenhouseScraper().extract("example.com")
    d = r.data
    assert d["open_jobs"] == 3
    assert ("Engineering", 2) in d["department_top"]
    assert ("San Francisco", 2) in d["office_top"]
    assert d["remote_job_count"] == 1


def test_lever_deepened_parsing(monkeypatch):
    from signal_architecture.signals.extractors.production import hiring
    from signal_architecture.signals.extractors.production.hiring import LeverScraper
    sample = [
        {"categories": {"team": "Engineering", "commitment": "Full-time",
                        "location": "Remote"}},
        {"categories": {"team": "Engineering", "commitment": "Contract",
                        "location": "London"}},
        {"categories": {"team": "Sales", "commitment": "Full-time",
                        "location": "New York"}},
    ]
    monkeypatch.setattr(hiring, "_json", lambda url, **kw: sample)
    monkeypatch.delenv("DSI_DISABLE_LEVER", raising=False)
    r = LeverScraper().extract("example.com")
    d = r.data
    assert d["open_jobs"] == 3
    assert ("Engineering", 2) in d["team_top"]
    assert ("Full-time", 2) in d["commitment_top"]
    assert d["remote_job_count"] == 1


def test_ashby_deepened_parsing(monkeypatch):
    from signal_architecture.signals.extractors.production import hiring
    from signal_architecture.signals.extractors.production.hiring import AshbyScraper
    sample = {
        "jobs": [
            {"department": "Engineering", "location": "Remote US",
             "employmentType": "FullTime"},
            {"department": "Engineering", "location": "NYC",
             "employmentType": "FullTime"},
            {"department": "Marketing", "location": "Remote EMEA",
             "employmentType": "Contract"},
        ],
    }
    monkeypatch.setattr(hiring, "_json", lambda url, **kw: sample)
    monkeypatch.delenv("DSI_DISABLE_ASHBY", raising=False)
    r = AshbyScraper().extract("example.com")
    d = r.data
    assert d["open_jobs"] == 3
    assert ("Engineering", 2) in d["department_top"]
    assert ("FullTime", 2) in d["employment_type_top"]
    assert d["remote_job_count"] == 2


def test_google_jobs_deepened_parsing(monkeypatch):
    from signal_architecture.signals.extractors.production import hiring
    from signal_architecture.signals.extractors.production.hiring import GoogleJobsExtractor
    sample = {
        "jobs_results": [
            {"company_name": "Acme Inc", "via": "via LinkedIn",
             "detected_extensions": {"schedule_type": "Full-time"}},
            {"company_name": "Acme Inc", "via": "via Indeed",
             "detected_extensions": {"schedule_type": "Full-time"}},
            {"company_name": "Other Corp", "via": "via LinkedIn",
             "detected_extensions": {"schedule_type": "Contract"}},
        ],
    }
    monkeypatch.setattr(hiring, "_json", lambda url, **kw: sample)
    monkeypatch.setenv("SERPAPI_API_KEY", "dummy")
    monkeypatch.delenv("DSI_DISABLE_GOOGLE_JOBS", raising=False)
    r = GoogleJobsExtractor().extract("example.com")
    d = r.data
    assert d["result_count"] == 3
    assert ("Acme Inc", 2) in d["company_top"]
    assert ("Full-time", 2) in d["employment_top"]
    assert ("via LinkedIn", 2) in d["via_top"]


# ---------------------------------------------------------------------------
# Sentiment
# ---------------------------------------------------------------------------


def test_bbb_deepened_parsing(monkeypatch):
    from signal_architecture.signals.extractors.production import sentiment
    from signal_architecture.signals.extractors.production.sentiment import BBBScraper
    sample_html = '''
    <html>example.com listed. Rating: A+<span>. A+<span>. BBB Accredited Business.
    Complaint count: 3 complaints. complaint submitted.</html>
    '''
    monkeypatch.setattr(sentiment, "_fetch_html", lambda url, **kw: sample_html)
    monkeypatch.delenv("DSI_DISABLE_BBB", raising=False)
    r = BBBScraper().extract("example.com")
    d = r.data
    assert d["listed_on_bbb"] is True
    assert d["accredited_mention_count"] == 1
    assert d["complaint_keyword_count"] >= 3


def test_glassdoor_deepened_parsing(monkeypatch):
    from signal_architecture.signals.extractors.production import sentiment
    from signal_architecture.signals.extractors.production.sentiment import GlassdoorScraper
    sample_html = '''
    <html>example.com page. "rating":"4.2", "reviews_count":"1250".
    <a href="/Interview/foo">Interviews</a>
    <a href="/Interview/bar">Interviews</a>
    <a href="/Salaries/baz">Salaries</a>
    Employer Response included. Employer Response included twice.</html>
    '''
    monkeypatch.setattr(sentiment, "_fetch_html", lambda url, **kw: sample_html)
    monkeypatch.delenv("DSI_DISABLE_GLASSDOOR", raising=False)
    r = GlassdoorScraper().extract("example.com")
    d = r.data
    assert d["listed_on_glassdoor"] is True
    assert d["rating"] == 4.2
    assert d["review_count"] == 1250
    assert d["interview_link_count"] == 2
    assert d["salary_link_count"] == 1
    assert d["employer_response_count"] == 2
