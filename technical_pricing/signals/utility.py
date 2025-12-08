
from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Type

import yaml

# ----------------------------
# Logging
# ----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

# ----------------------------
# Registries
# ----------------------------
EXTRACTOR_REGISTRY: Dict[str, Type["DataExtractor"]] = {}
SCORER_REGISTRY: Dict[str, Type["DataScorer"]] = {}

def register_extractor(cls: Type["DataExtractor"]) -> Type["DataExtractor"]:
    EXTRACTOR_REGISTRY[cls.__name__] = cls
    return cls

def register_scorer(cls: Type["DataScorer"]) -> Type["DataScorer"]:
    SCORER_REGISTRY[cls.__name__] = cls
    return cls

# ----------------------------
# Extractors (stubbed)
# ----------------------------
class DataExtractor(ABC):
    @abstractmethod
    def extract(self) -> Dict[str, Any]:
        raise NotImplementedError

@register_extractor
class EquasisAPIExtractor(DataExtractor):
    """
    simulates an normalised payload for a marine operator:
    {
        "company_name": str,
        "offers_liner_service": bool,
        "vessels": List[{"imo": int, "category": str}]
    }
    """

    def __init__(self, company_name: str, offers_liner_service: bool, fleet_spec: Dict[str, int]):
        self.company_name = company_name
        self.offers_liner_service = offers_liner_service
        self.fleet_spec = fleet_spec # eg. {"container": 60, "bulk": 10}

    def extract(self) -> Dict[str, Any]:
        vessels: List [Dict[str, Any]] = []
        imo_seed  =abs(hash(self.company_name))  % 1000000
        for cat, count in self.fleet_spec.items():
            for i in range(count):
                vessels.append({"imo": imo_seed + i, "category": cat})
        return {
            "company_name": self.company_name,
            "offers_liner_service": self.offers_liner_service,
            "vessels": vessels
        }

# ----------------------------
# Scorers
# ----------------------------
class DataScorer(ABC):
    @abstractmethod
    def score(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        raise NotImplementedError


@register_scorer
class MajorityVesselCategoryScorer(DataScorer):
    def score(self, data: Dict[str, Any]) -> Dict[str, Any]:
        counts: Dict[str, int] = {}
        for v in data.get("vessels", []):
            cat = v.get("category")
            if cat:
                counts[cat] = counts.get(cat, 0) + 1
        if not counts:
            majority = None
        else:
            max_count = max(counts.values())
            max_cats = [c for c, n in counts.items() if n == max_count]
            majority = max_cats[0] if len(max_cats) == 1 else "mixed"
        return {"counts": counts, "majority": majority}

@register_scorer
class FleetSizeScorer(DataScorer):
    def score(self, data: Dict[str, Any]) -> Dict[str, Any]:
        size = len(data.get("vessels", []))
        return {"fleet_size": size}

@register_scorer
class LinerServiceScorer(DataScorer):
    def score(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {"offers_liner_service": bool(data.get("offers_liner_service", False))}

@register_scorer
class CompanyClassifierScorer(DataScorer):
    """
    Implements your classification rules:
      - "major liner": majority == container AND fleet >= 50 AND offers liner service
      - "major tanker": majority == tanker AND fleet >= 30
      - else: "uncategorized" with rationale
    """

    def score(self, data: Dict[str, Any]) -> Dict[str, Any]:
        vessels = data.get("vessels", [])
        fleet_size = len(vessels)
        offers_liner = bool(data.get("offers_liner_service", False))

        counts: Dict[str, int] = {}
        for v in vessels:
            cat = v.get("category")
            if cat:
                counts[cat] = counts.get(cat, 0) + 1
        if not counts:
            majority = None
        else:
            max_count = max(counts.values())
            max_cats = [c for c, n in counts.items() if n == max_count]
            majority = max_cats[0] if len(max_cats) == 1 else "mixed"

        label = "uncategorized"
        reasons: List[str] = []

        if majority == "container" and fleet_size >= 50 and offers_liner:
            label = "major liner"
            reasons += ["container-majority", "fleet >= 50", "offers liner service"]
        elif majority == "tanker" and fleet_size >= 30:
            label = "major tanker"
            reasons += ["tanker-majority", "fleet >= 30"]
        else:
            reasons += [f"majority={majority}", f"fleet={fleet_size}", f"liner_service={offers_liner}"]

        return {
            "company_name": data.get("company_name"),
            "classification": label,
            "features": {
                "majority_category": majority,
                "fleet_size": fleet_size,
                "offers_liner_service": offers_liner,
            },
            "reasons": reasons,
        }      


# ----------------------------
# Parallel pipeline
# ----------------------------
class ParallelMultiScorerPipeline:
    def __init__(self, extractor: DataExtractor, scorers: List[DataScorer], max_workers: int | None = None):
        self.extractor = extractor
        self.scorers = scorers
        self.max_workers = max_workers

    def run(self) -> Dict[str, Dict[str, Any]]:
        data = self.extractor.extract()
        results: Dict[str, Dict[str, Any]] = {}

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_scorer: Dict[Any, str] = {
                executor.submit(self._run_scorer, scorer, data): scorer.__class__.__name__
                for scorer in self.scorers
            }

            for future in as_completed(future_to_scorer.keys()):
                scorer_name = future_to_scorer[future]
                try:
                    results[scorer_name] = future.result()
                except Exception as e:
                    logging.exception(f"Scorer {scorer_name} failed: {e}")
                    results[scorer_name] = {"error": str(e)}

        return results

    def _run_scorer(self, scorer: DataScorer, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        scorer_name = scorer.__class__.__name__
        start_time = time.perf_counter()
        logging.info(f"Starting scorer: {scorer_name}")

        output = scorer.score(data)

        duration = time.perf_counter() - start_time
        logging.info(f"Finished scorer: {scorer_name} in {duration:.3f}s")

        return {
            "scorer": scorer_name,
            "params": vars(scorer),  # e.g., {"threshold": 50}
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "duration_sec": round(duration, 3),
            "output": output,
        }


# ----------------------------
# Demo: three companies
# ----------------------------
companies = [
    EquasisAPIExtractor(
        company_name="Atlas Container Lines",
        offers_liner_service=True,
        fleet_spec={"container": 60, "bulk": 10},
    ),
    EquasisAPIExtractor(
        company_name="Marina Tankers Ltd",
        offers_liner_service=False,
        fleet_spec={"tanker": 35, "container": 2},
    ),
    EquasisAPIExtractor(
        company_name="Ocean Mix Shipping",
        offers_liner_service=False,
        fleet_spec={"container": 20, "tanker": 25, "bulk": 5},
    ),
]

scorers = [
    MajorityVesselCategoryScorer(),
    FleetSizeScorer(),
    LinerServiceScorer(),
    CompanyClassifierScorer(),
]

all_results = []
for extractor in companies:
    pipeline = ParallelMultiScorerPipeline(extractor, scorers)
    results = pipeline.run()
    all_results.append(results)

# Human-readable summary
summary = []
for res in all_results:
    company_name = res["CompanyClassifierScorer"]["output"]["company_name"]
    classification = res["CompanyClassifierScorer"]["output"]["classification"]
    features = res["CompanyClassifierScorer"]["output"]["features"]
    summary.append({
        "company": company_name,
        "classification": classification,
        "majority_category": features["majority_category"],
        "fleet_size": features["fleet_size"],
        "offers_liner_service": features["offers_liner_service"],
    })

print("\n=== Classification Summary ===")
for row in summary:
    print(row)
