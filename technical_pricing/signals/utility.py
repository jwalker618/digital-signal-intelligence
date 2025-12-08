
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
# Extractors
# ----------------------------
class DataExtractor(ABC):
    @abstractmethod
    def extract(self) -> List[Dict[str, Any]]:
        raise NotImplementedError

@register_extractor
class APIExtractor(DataExtractor):
    def __init__(self, api_url: str):
        self.api_url = api_url

    def extract(self) -> List[Dict[str, Any]]:
        logging.info(f"Extracting data from API: {self.api_url}")
        # Stub data for demonstration
        return [{"id": 1, "value": 42}, {"id": 2, "value": 99}]

# ----------------------------
# Scorers
# ----------------------------
class DataScorer(ABC):
    @abstractmethod
    def score(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        raise NotImplementedError

@register_scorer
class ThresholdScorer(DataScorer):
    def __init__(self, threshold: int):
        self.threshold = threshold

    def score(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "above_threshold": [
                d for d in data if ("value" in d and d["value"] > self.threshold)
            ],
            "below_threshold": [
                d for d in data if ("value" in d and d["value"] <= self.threshold)
            ],
        }

@register_scorer
class AverageScorer(DataScorer):
    def score(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        values = [d["value"] for d in data if "value" in d]
        return {"average": (sum(values) / len(values)) if values else None}

@register_scorer
class MaxValueScorer(DataScorer):
    def score(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        values = [d["value"] for d in data if "value" in d]
        return {"max_value": (max(values) if values else None)}

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
# Config loader
# ----------------------------
def build_pipeline_from_config(config_path: str) -> ParallelMultiScorerPipeline:
    with open(config_path, "r") as f:
        config = yaml.safe_load(f) or {}

    # Extractor
    extractor_cfg: Dict[str, Any] = config.get("extractor", {})
    extractor_type = extractor_cfg.get("type")
    extractor_params: Dict[str, Any] = extractor_cfg.get("params", {})

    if not extractor_type or extractor_type not in EXTRACTOR_REGISTRY:
        raise KeyError(f"Unknown or missing extractor type: {extractor_type}")

    extractor_cls = EXTRACTOR_REGISTRY[extractor_type]
    extractor = extractor_cls(**extractor_params)

    # Scorers
    scorers: List[DataScorer] = []
    for scorer_cfg in config.get("scorers", []):
        scorer_type = scorer_cfg.get("type")
        params: Dict[str, Any] = scorer_cfg.get("params", {})
        if not scorer_type or scorer_type not in SCORER_REGISTRY:
            raise KeyError(f"Unknown or missing scorer type: {scorer_type}")
        scorer_cls = SCORER_REGISTRY[scorer_type]
        scorers.append(scorer_cls(**params))

    return ParallelMultiScorerPipeline(extractor, scorers)

# ----------------------------
# Usage example
# ----------------------------
if __name__ == "__main__":
    pipeline = build_pipeline_from_config("config.yaml")
    results = pipeline.run()

    for scorer_name, output in results.items():
        print(f"{scorer_name} Results:", output)
