"""
Digital Signal Intelligence - Validation & Backtesting Framework
================================================================

Production framework for validating DSI pricing models against
historical loss experience. Provides statistical evidence that
digital signals predict insurance outcomes.

Author: John Walker
Date: November 2025
Version: 1.0
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from scipy import stats

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ValidationPolicy:
   """Historical policy data for validation"""
   policy_id: str
   company_name: str
   company_domain: str
   inception_date: datetime
   expiry_date: datetime
   coverage_type: str
   line_of_business: str
   industry: str
   country: str
   revenue: float
   employees: int
   premium: float
   limit: float
   deductible: float
   incurred_losses: float
   paid_losses: float
   claim_count: int
   largest_claim: float
   loss_ratio: float = 0.0
   dsi_composite_score: Optional[float] = None
   dsi_signals: Optional[Dict[str, float]] = None
   dsi_risk_tier: Optional[str] = None
   dsi_confidence: Optional[float] = None
   
   def __post_init__(self):
       if self.premium > 0:
           self.loss_ratio = self.incurred_losses / self.premium


@dataclass
class ValidationResult:
   """Results from a validation analysis"""
   analysis_name: str
   analysis_date: datetime
   policies_analyzed: int
   gini_coefficient: float
   c_statistic: float
   kolmogorov_smirnov: float
   quintile_loss_ratios: Dict[str, float]
   quintile_premium_distribution: Dict[str, float]
   quintile_lift: float
   score_lr_correlation: float
   score_lr_p_value: float
   is_monotonic: bool
   monotonicity_violations: int
   dsi_loss_ratio: float
   traditional_loss_ratio: float
   improvement_points: float
   statistical_significance: bool
   confidence_interval_95: Tuple[float, float]
   details: Dict[str, Any] = field(default_factory=dict)


class GiniCalculator:
   """Calculate Gini coefficient for insurance model validation"""
   
   @staticmethod
   def calculate_with_weights(
       predicted_scores: np.ndarray,
       actual_outcomes: np.ndarray,
       weights: np.ndarray
   ) -> float:
       sorted_indices = np.argsort(predicted_scores)
       sorted_outcomes = actual_outcomes[sorted_indices]
       sorted_weights = weights[sorted_indices]
       
       cumulative_outcomes = np.cumsum(sorted_outcomes * sorted_weights)
       cumulative_weights = np.cumsum(sorted_weights)
       
       total_outcome = cumulative_outcomes[-1]
       total_weight = cumulative_weights[-1]
       
       if total_outcome == 0 or total_weight == 0:
           return 0.0
       
       lorenz = cumulative_outcomes / total_outcome
       population = cumulative_weights / total_weight
       auc = np.trapz(lorenz, population)
       gini = 2 * auc - 1
       
       return abs(gini)


class QuintileAnalyzer:
   """Analyze model performance across quintiles"""
   
   @staticmethod
   def analyze(
       scores: np.ndarray,
       loss_ratios: np.ndarray,
       premiums: np.ndarray,
       n_quantiles: int = 5
   ) -> Dict[str, Any]:
       quantile_edges = np.percentile(scores, np.linspace(0, 100, n_quantiles + 1))
       quantile_labels = [f"Q{i+1}" for i in range(n_quantiles)]
       quantile_assignments = np.digitize(scores, quantile_edges[1:-1])
       
       results = {"quantile_count": n_quantiles, "quantiles": {}}
       
       for q in range(n_quantiles):
           mask = quantile_assignments == q
           if not np.any(mask):
               continue
           
           q_label = quantile_labels[q]
           q_scores = scores[mask]
           q_loss_ratios = loss_ratios[mask]
           q_premiums = premiums[mask]
           
           if np.sum(q_premiums) > 0:
               weighted_lr = np.average(q_loss_ratios, weights=q_premiums)
           else:
               weighted_lr = np.mean(q_loss_ratios)
           
           results["quantiles"][q_label] = {
               "count": int(np.sum(mask)),
               "premium_share": float(np.sum(q_premiums) / np.sum(premiums)),
               "avg_score": float(np.mean(q_scores)),
               "weighted_loss_ratio": float(weighted_lr),
           }
       
       if "Q1" in results["quantiles"] and f"Q{n_quantiles}" in results["quantiles"]:
           worst_lr = results["quantiles"]["Q1"]["weighted_loss_ratio"]
           best_lr = results["quantiles"][f"Q{n_quantiles}"]["weighted_loss_ratio"]
           results["lift"] = worst_lr - best_lr
       
       lrs = [results["quantiles"].get(f"Q{i+1}", {}).get("weighted_loss_ratio", 0) 
              for i in range(n_quantiles)]
       violations = sum(1 for i in range(len(lrs)-1) if lrs[i] < lrs[i+1])
       results["monotonicity_violations"] = violations
       results["is_monotonic"] = violations == 0
       
       return results


class CStatisticCalculator:
   """Calculate C-statistic (AUC-ROC) for binary outcomes"""
   
   @staticmethod
   def calculate(
       predicted_scores: np.ndarray,
       binary_outcomes: np.ndarray
   ) -> Tuple[float, float]:
       positives = predicted_scores[binary_outcomes == 1]
       negatives = predicted_scores[binary_outcomes == 0]
       
       n_pos = len(positives)
       n_neg = len(negatives)
       
       if n_pos == 0 or n_neg == 0:
           return 0.5, 0.0
       
       concordant = 0
       for p in positives:
           concordant += np.sum(negatives < p)
           concordant += 0.5 * np.sum(negatives == p)
       
       c_stat = concordant / (n_pos * n_neg)
       se = np.sqrt((c_stat * (1 - c_stat)) / min(n_pos, n_neg))
       
       return c_stat, se


class ValidationFramework:
   """Main validation framework orchestrating all analyses"""
   
   def __init__(self):
       self.gini_calc = GiniCalculator()
       self.quintile_analyzer = QuintileAnalyzer()
       self.c_stat_calc = CStatisticCalculator()
   
   def validate_model(
       self,
       policies: List[ValidationPolicy],
       model_name: str = "DSI Model"
   ) -> ValidationResult:
       scored_policies = [p for p in policies if p.dsi_composite_score is not None]
       
       if len(scored_policies) < 50:
           raise ValueError(f"Insufficient scored policies: {len(scored_policies)}")
       
       scores = np.array([p.dsi_composite_score for p in scored_policies])
       loss_ratios = np.array([p.loss_ratio for p in scored_policies])
       premiums = np.array([p.premium for p in scored_policies])
       had_claim = np.array([1 if p.claim_count > 0 else 0 for p in scored_policies])
       
       gini = self.gini_calc.calculate_with_weights(scores, loss_ratios, premiums)
       c_stat, c_stat_se = self.c_stat_calc.calculate(scores, had_claim)
       quintile_results = self.quintile_analyzer.analyze(scores, loss_ratios, premiums)
       correlation, p_value = stats.spearmanr(scores, loss_ratios)
       
       high_score_mask = scores >= np.median(scores)
       ks_stat, ks_pvalue = stats.ks_2samp(
           loss_ratios[high_score_mask],
           loss_ratios[~high_score_mask]
       )
       
       traditional_lr = np.average(loss_ratios, weights=premiums)
       top_4_quintiles = scores >= np.percentile(scores, 20)
       dsi_lr = np.average(loss_ratios[top_4_quintiles], weights=premiums[top_4_quintiles]) if np.sum(top_4_quintiles) > 0 else traditional_lr
       improvement = (traditional_lr - dsi_lr) * 100
       
       # Bootstrap CI
       n_bootstrap = 500
       bootstrap_improvements = []
       for _ in range(n_bootstrap):
           idx = np.random.choice(len(scores), size=len(scores), replace=True)
           boot_trad = np.average(loss_ratios[idx], weights=premiums[idx])
           boot_top4 = scores[idx] >= np.percentile(scores[idx], 20)
           boot_dsi = np.average(loss_ratios[idx][boot_top4], weights=premiums[idx][boot_top4]) if np.sum(boot_top4) > 0 else boot_trad
           bootstrap_improvements.append((boot_trad - boot_dsi) * 100)
       
       ci_lower, ci_upper = np.percentile(bootstrap_improvements, [2.5, 97.5])
       significant = ci_lower > 0
       
       quintile_lrs = {k: v["weighted_loss_ratio"] for k, v in quintile_results.get("quantiles", {}).items()}
       quintile_premiums = {k: v["premium_share"] for k, v in quintile_results.get("quantiles", {}).items()}
       
       return ValidationResult(
           analysis_name=model_name,
           analysis_date=datetime.now(),
           policies_analyzed=len(scored_policies),
           gini_coefficient=gini,
           c_statistic=c_stat,
           kolmogorov_smirnov=ks_stat,
           quintile_loss_ratios=quintile_lrs,
           quintile_premium_distribution=quintile_premiums,
           quintile_lift=quintile_results.get("lift", 0),
           score_lr_correlation=correlation,
           score_lr_p_value=p_value,
           is_monotonic=quintile_results.get("is_monotonic", False),
           monotonicity_violations=quintile_results.get("monotonicity_violations", 0),
           dsi_loss_ratio=dsi_lr,
           traditional_loss_ratio=traditional_lr,
           improvement_points=improvement,
           statistical_significance=significant,
           confidence_interval_95=(ci_lower, ci_upper),
           details={"quintile_details": quintile_results, "c_stat_se": c_stat_se}
       )
   
   def _interpret_gini(self, gini: float) -> str:
       if gini >= 0.40: return "Excellent"
       elif gini >= 0.30: return "Good"
       elif gini >= 0.20: return "Moderate"
       else: return "Weak"


class RetrospectiveAnalyzer:
   """Analyze historical incidents to demonstrate DSI predictive power"""
   
   def __init__(self):
       self.case_studies = []
   
   def add_case_study(
       self,
       company_name: str,
       incident_date: datetime,
       incident_type: str,
       loss_amount: float,
       pre_incident_signals: Dict[str, float],
       traditional_rating: str,
       narrative: str
   ) -> Dict:
       pre_score = self._calculate_composite(pre_incident_signals)
       
       if pre_score >= 750:
           dsi_recommendation = "Auto-approve preferred"
           would_have_caught = False
       elif pre_score >= 650:
           dsi_recommendation = "Auto-approve standard"
           would_have_caught = False
       elif pre_score >= 500:
           dsi_recommendation = "Manual review required"
           would_have_caught = True
       else:
           dsi_recommendation = "Decline or heavy conditions"
           would_have_caught = True
       
       case = {
           "company_name": company_name,
           "incident_date": incident_date.isoformat(),
           "incident_type": incident_type,
           "loss_amount": loss_amount,
           "pre_incident_score": pre_score,
           "pre_incident_signals": pre_incident_signals,
           "traditional_rating": traditional_rating,
           "dsi_recommendation": dsi_recommendation,
           "would_have_caught": would_have_caught,
           "narrative": narrative,
           "key_warning_signals": self._identify_warnings(pre_incident_signals)
       }
       
       self.case_studies.append(case)
       return case
   
   def _calculate_composite(self, signals: Dict[str, float]) -> float:
       if not signals:
           return 0
       weights = {
           "ssl_certificate": 0.10, "security_headers": 0.10,
           "known_vulnerabilities": 0.25, "patch_discipline": 0.15,
           "governance_disclosure": 0.10, "update_frequency": 0.10,
           "domain_authority": 0.10, "tech_stack_modernity": 0.10
       }
       total_weight = sum(weights.get(s, 0.05) for s in signals)
       weighted_sum = sum(signals[s] * weights.get(s, 0.05) for s in signals)
       return (weighted_sum / total_weight) * 10 if total_weight > 0 else 0
   
   def _identify_warnings(self, signals: Dict[str, float]) -> List[str]:
       warnings = []
       thresholds = {
           "known_vulnerabilities": (60, "Elevated vulnerability exposure"),
           "patch_discipline": (50, "Poor patch management"),
           "security_headers": (50, "Inadequate security headers"),
       }
       for signal, (threshold, message) in thresholds.items():
           if signal in signals and signals[signal] < threshold:
               warnings.append(f"{message} (score: {signals[signal]:.0f})")
       return warnings
   
   def generate_report(self) -> Dict:
       if not self.case_studies:
           return {"error": "No case studies"}
       caught = sum(1 for c in self.case_studies if c["would_have_caught"])
       total_loss = sum(c["loss_amount"] for c in self.case_studies)
       avoidable = sum(c["loss_amount"] for c in self.case_studies if c["would_have_caught"])
       return {
           "summary": {
               "cases": len(self.case_studies),
               "flagged": caught,
               "catch_rate": caught / len(self.case_studies),
               "total_losses": total_loss,
               "avoidable_losses": avoidable
           },
           "case_studies": self.case_studies
       }


class SyntheticDataGenerator:
   """Generate synthetic policy data for testing"""
   
   @staticmethod
   def generate_policies(n_policies: int = 1000) -> List[ValidationPolicy]:
       policies = []
       industries = ["Technology", "Healthcare", "Financial", "Retail"]
       
       for i in range(n_policies):
           true_risk = np.random.beta(2, 5)
           dsi_score = (1 - true_risk) * 1000 + np.random.normal(0, 50)
           dsi_score = np.clip(dsi_score, 100, 950)
           
           claim_prob = 0.15 * (1 + true_risk * 3)
           has_claim = np.random.random() < claim_prob
           loss = np.random.lognormal(10 + true_risk, 1) if has_claim else 0
           premium = np.random.lognormal(11, 0.5)
           
           policies.append(ValidationPolicy(
               policy_id=f"POL-{i+1:05d}",
               company_name=f"Company {i+1}",
               company_domain=f"company{i+1}.com",
               inception_date=datetime.now() - timedelta(days=np.random.randint(365, 1825)),
               expiry_date=datetime.now() - timedelta(days=np.random.randint(0, 365)),
               coverage_type="Cyber",
               line_of_business="Cyber",
               industry=np.random.choice(industries),
               country="United States",
               revenue=np.random.lognormal(17, 1.5),
               employees=int(np.random.lognormal(6, 1.5)),
               premium=premium,
               limit=premium * 100,
               deductible=premium * 0.1,
               incurred_losses=loss,
               paid_losses=loss * 0.8,
               claim_count=1 if has_claim else 0,
               largest_claim=loss,
               dsi_composite_score=dsi_score,
               dsi_risk_tier="Tier 1" if dsi_score >= 750 else "Tier 2" if dsi_score >= 650 else "Tier 3" if dsi_score >= 500 else "Tier 4",
               dsi_confidence=0.85
           ))
       
       return policies


if __name__ == "__main__":
   print("=" * 70)
   print("DSI VALIDATION FRAMEWORK - TEST")
   print("=" * 70)
   
   policies = SyntheticDataGenerator.generate_policies(2000)
   framework = ValidationFramework()
   result = framework.validate_model(policies, "DSI Cyber v1.0")
   
   print(f"\nGini: {result.gini_coefficient:.4f} ({framework._interpret_gini(result.gini_coefficient)})")
   print(f"C-Statistic: {result.c_statistic:.4f}")
   print(f"Quintile Lift: {result.quintile_lift:.2%}")
   print(f"Improvement: {result.improvement_points:.1f} pts")
   print(f"Significant: {result.statistical_significance}")
