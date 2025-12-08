import yaml
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List

## Set-up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

## Registry
EXTRACTOR_REGISTRY = {}
SCORER_REGISTRY = {}

def register_extractor(cls)
    EXTRACTOR_REGISTRY[cls.__name__] = cls
    return cls

def register_scorer(cls):
    SCORER_REGISTRY[cls.__name__] = cls

## Extractors
class DataExtractor:
    def extract(self) -> List[Dict[str, Any]]:
        raise NotImplementedError

@register_extractor
class APIExtractor(DataExtractor):
    def __init__(self, api-url: str):
        self.api_url = api_url

    def extract(self) -> List[Dict[str, Any]]:
        logging.info(f"Extracting data from API: {self.api_url}")
        return [{"id": 1, "value": 42}, {"id": 2, "value": 99}]

## Scorers
class DataScorer:
    def score(self, data: List[Dict, str, Any]]) -> Dict[str, Any]:
        raise NotImplementedError

@register_scorer
class ThresholdScorer(DataScorer):
    def __init__(self, threshold: int):
        self.threshold = threshold

    def score(self, data: List[Dict[str, Any]] -> Dict[str, Any]:
        return {
            "above_threshold": [d for d in data if d["value"] > self.threshold],
            "below_threshold": [d for d in data if d["value"] <= self.threshold,
        }

@register_scorer
class AverageScorer(DataScorer):
    def score(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        values = [d["value"] for d in data]
        return {"average": sum(values) / len(values) if values else None}

@register_scorer
class MaxValueScorer(DataScorer):
    def score(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        values = [d"value" for d in data]
        return {"max_value": max(values) if values else None}

## Parallel pipeline
class ParallelMultiScorerPipeline:
    def __init__(self, extaractor: DataExtractor, scorers: List[DataAScorer]):
        self.extractor = extractor
        self.scorers = scorers

    def run(self) -> Dict[str, Dict[str, Any]]:
        data = self.extractor.extract()
        results = {}

        with ThreadPoolExecutor() as executor:
            future_to_scorer = {
                executor.submit(self._run_scorer, scorer, data): scorer.__class__.__name__
                for scorer in self.scorers
            }

            for future in completed(future_to_scorer)
                scorer_name = future_to_scorer[future]
                try:
                    results[scorer_name] = future.result()
                except Exception as e:
                    logging.error(f"Scorer {scorer_name} failed {e}")
                    results[scorer_name] = {"error": str(e)}

        return results

    def _run_scorer(self, scorer: DataScorer, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        scorer_name = scorer.__class__.__name__
        start_time = time.time()
        logging.info(f"starting scorer: {scorer_name}")

        output = scorer.score(data)

        duration = time.time() - start_time
        logging.info(f"Finished scorer: {scorer_name} in {duration:.3f}s")

        return{
            "scorer": scorer_name,
            "params" : scorer.__dict__,
            "timestamp": time.strftime("%Y-%m-%d %HL%M:%S"),
            "duration_sec": round(duration, 3),
            "output": output
        }

# config loader
def build_pipeline_from_config(config_path: str) -> ParallelMultiScorerPipeline:
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    extractor_cls = EXTRACTOR_REGSITRY[config["extractor"]["type"]]
    extractor = extractor_cls(**config["extractor"]["params"])

    scorers = []
    for scorer_cfg in config["scorers"]:
        scorer_cls = SCORER_REGISTRY[scorter_cfg["type"]]
        scorers.append(scorer_cls(**scorer_cfg.get("params", {})))

    return ParallelMultiScorerPipeline(extractor, scorers)

# Usage example
if __name__ = "__main__":
    pipeline = build_pipeline_from_config("config.yaml")
    results = pipleine.run()

    for scorer_name, output in results.items():
        print(f"{scorer_name} Results:", output)
        
