"""
Example: E-Commerce Product Analysis
=====================================

This example demonstrates how to extend the framework for a different domain.
Shows how to analyze products from an e-commerce platform.
"""
from signals.extractors import (
    DataExtractor, register_extractor
)

from signals.aggregators import (
    DataAggregator, register_aggregator
)

from signals.categorisers import (
    DataCategorizer, register_categorizer
)

from signals.utility import (
    AnalysisPipeline, BatchPipeline
)

from typing import Dict, Any, List
import random

# ============================================================================
# EXTRACTORS: Data Sources
# ============================================================================

@register_extractor
class ShopifyAPIExtractor(DataExtractor):
    """
    Simulates extracting product data from Shopify API.
    """
    
    def __init__(self, store_name: str, product_category: str):
        self.store_name = store_name
        self.product_category = product_category
    
    def extract(self) -> Dict[str, Any]:
        """Simulate API response with product data."""
        # Simulate product data
        num_products = random.randint(50, 200)
        products = []
        
        for i in range(num_products):
            products.append({
                "product_id": f"PROD_{i:04d}",
                "name": f"Product {i}",
                "price": round(random.uniform(10, 500), 2),
                "inventory": random.randint(0, 100),
                "rating": round(random.uniform(3.0, 5.0), 1),
                "num_reviews": random.randint(0, 500),
                "days_since_added": random.randint(1, 365),
                "units_sold": random.randint(0, 1000)
            })
        
        return {
            "store_name": self.store_name,
            "category": self.product_category,
            "products": products,
            "extraction_timestamp": "2024-12-08T10:00:00Z"
        }
    
    def get_source_metadata(self) -> Dict[str, str]:
        return {
            "extractor_type": self.__class__.__name__,
            "source": f"Shopify - {self.store_name}",
            "category": self.product_category
        }


@register_extractor
class CSVFileExtractor(DataExtractor):
    """
    Extract product data from a CSV file.
    """
    
    def __init__(self, file_path: str, store_name: str):
        self.file_path = file_path
        self.store_name = store_name
    
    def extract(self) -> Dict[str, Any]:
        """Simulate reading CSV file."""
        # In reality, you'd use pandas or csv module
        # This is a simulation
        products = [
            {
                "product_id": "CSV_001",
                "name": "Legacy Product 1",
                "price": 29.99,
                "inventory": 45,
                "rating": 4.2,
                "num_reviews": 120,
                "days_since_added": 180,
                "units_sold": 250
            }
            # ... more products
        ]
        
        return {
            "store_name": self.store_name,
            "source_file": self.file_path,
            "products": products
        }


# ============================================================================
# AGGREGATORS: Data Analysis & Transformation
# ============================================================================

@register_aggregator
class InventoryAggregator(DataAggregator):
    """
    Analyzes inventory levels and stock health.
    """
    
    def aggregate(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        products = raw_data.get("products", [])
        
        total_inventory = sum(p.get("inventory", 0) for p in products)
        out_of_stock = len([p for p in products if p.get("inventory", 0) == 0])
        low_stock = len([p for p in products if 0 < p.get("inventory", 0) <= 10])
        
        inventory_values = [p.get("inventory", 0) for p in products if p.get("inventory", 0) > 0]
        avg_inventory = sum(inventory_values) / len(inventory_values) if inventory_values else 0
        
        return {
            "store_name": raw_data.get("store_name"),
            "total_products": len(products),
            "total_inventory_units": total_inventory,
            "average_inventory_per_product": round(avg_inventory, 1),
            "out_of_stock_count": out_of_stock,
            "low_stock_count": low_stock,
            "out_of_stock_percentage": round(out_of_stock / len(products) * 100, 1) if products else 0
        }


@register_aggregator
class RevenueAggregator(DataAggregator):
    """
    Calculates revenue metrics and sales performance.
    """
    
    def aggregate(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        products = raw_data.get("products", [])
        
        # Calculate total revenue (price * units_sold)
        total_revenue = sum(
            p.get("price", 0) * p.get("units_sold", 0) 
            for p in products
        )
        
        # Average order value
        total_units = sum(p.get("units_sold", 0) for p in products)
        avg_price = sum(p.get("price", 0) for p in products) / len(products) if products else 0
        
        # Top performers
        products_by_revenue = sorted(
            products,
            key=lambda p: p.get("price", 0) * p.get("units_sold", 0),
            reverse=True
        )
        top_5_revenue = sum(
            p.get("price", 0) * p.get("units_sold", 0)
            for p in products_by_revenue[:5]
        )
        
        return {
            "store_name": raw_data.get("store_name"),
            "total_revenue": round(total_revenue, 2),
            "total_units_sold": total_units,
            "average_product_price": round(avg_price, 2),
            "top_5_products_revenue": round(top_5_revenue, 2),
            "top_5_concentration": round(top_5_revenue / total_revenue * 100, 1) if total_revenue > 0 else 0
        }


@register_aggregator
class CustomerSatisfactionAggregator(DataAggregator):
    """
    Analyzes customer ratings and review engagement.
    """
    
    def aggregate(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        products = raw_data.get("products", [])
        
        # Rating analysis
        ratings = [p.get("rating", 0) for p in products if p.get("rating", 0) > 0]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0
        
        high_rated = len([r for r in ratings if r >= 4.5])
        low_rated = len([r for r in ratings if r < 3.5])
        
        # Review engagement
        total_reviews = sum(p.get("num_reviews", 0) for p in products)
        products_with_reviews = len([p for p in products if p.get("num_reviews", 0) > 0])
        
        return {
            "store_name": raw_data.get("store_name"),
            "average_rating": round(avg_rating, 2),
            "highly_rated_count": high_rated,
            "poorly_rated_count": low_rated,
            "total_reviews": total_reviews,
            "products_with_reviews": products_with_reviews,
            "review_coverage": round(products_with_reviews / len(products) * 100, 1) if products else 0
        }


@register_aggregator
class ProductFreshnessAggregator(DataAggregator):
    """
    Analyzes product catalog freshness and turnover.
    """
    
    def aggregate(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        products = raw_data.get("products", [])
        
        days_list = [p.get("days_since_added", 0) for p in products]
        avg_days = sum(days_list) / len(days_list) if days_list else 0
        
        new_products = len([d for d in days_list if d <= 30])
        old_products = len([d for d in days_list if d > 180])
        
        return {
            "store_name": raw_data.get("store_name"),
            "average_product_age_days": round(avg_days, 0),
            "new_products_30days": new_products,
            "old_products_180days": old_products,
            "catalog_freshness_score": round((new_products / len(products)) * 100, 1) if products else 0
        }


# ============================================================================
# CATEGORIZERS: Classification & Scoring
# ============================================================================

@register_categorizer
class StoreSizeCategorizer(DataCategorizer):
    """
    Categorizes store by catalog size.
    """
    
    def __init__(self, small_threshold: int = 50, medium_threshold: int = 150):
        self.small_threshold = small_threshold
        self.medium_threshold = medium_threshold
    
    def categorize(self, aggregated_data: Dict[str, Any]) -> Dict[str, Any]:
        catalog_size = aggregated_data.get("total_products", 0)
        
        if catalog_size < self.small_threshold:
            category = "boutique"
        elif catalog_size < self.medium_threshold:
            category = "medium"
        else:
            category = "large_catalog"
        
        return {
            "store_name": aggregated_data.get("store_name"),
            "size_category": category,
            "catalog_size": catalog_size
        }


@register_categorizer
class InventoryHealthScorer(DataCategorizer):
    """
    Scores inventory management health.
    """
    
    def __init__(self, critical_oos_threshold: float = 15.0):
        self.critical_oos_threshold = critical_oos_threshold
    
    def categorize(self, aggregated_data: Dict[str, Any]) -> Dict[str, Any]:
        oos_percentage = aggregated_data.get("out_of_stock_percentage", 0)
        low_stock = aggregated_data.get("low_stock_count", 0)
        total_products = aggregated_data.get("total_products", 1)
        
        # Calculate score (0-100)
        score = 100
        
        # Penalize for out of stock
        score -= min(40, oos_percentage * 2)
        
        # Penalize for low stock issues
        low_stock_percentage = (low_stock / total_products) * 100
        score -= min(20, low_stock_percentage)
        
        score = max(0, score)
        
        if score >= 80:
            health = "excellent"
        elif score >= 60:
            health = "good"
        elif score >= 40:
            health = "needs_attention"
        else:
            health = "critical"
        
        return {
            "store_name": aggregated_data.get("store_name"),
            "inventory_health": health,
            "inventory_score": round(score, 1),
            "out_of_stock_percentage": oos_percentage,
            "recommendation": self._get_recommendation(health, oos_percentage)
        }
    
    def _get_recommendation(self, health: str, oos_pct: float) -> str:
        if health == "critical":
            return "Immediate restocking required - significant revenue loss"
        elif health == "needs_attention":
            return "Review reorder points and safety stock levels"
        elif health == "good":
            return "Monitor low-stock items closely"
        else:
            return "Inventory management performing well"


@register_categorizer
class RevenuePerformanceCategorizer(DataCategorizer):
    """
    Categorizes store by revenue performance.
    """
    
    def __init__(self, high_revenue_threshold: float = 50000):
        self.high_revenue_threshold = high_revenue_threshold
    
    def categorize(self, aggregated_data: Dict[str, Any]) -> Dict[str, Any]:
        total_revenue = aggregated_data.get("total_revenue", 0)
        top_5_concentration = aggregated_data.get("top_5_concentration", 0)
        
        # Revenue tier
        if total_revenue >= self.high_revenue_threshold:
            revenue_tier = "high_performer"
        elif total_revenue >= self.high_revenue_threshold * 0.5:
            revenue_tier = "moderate_performer"
        else:
            revenue_tier = "growth_stage"
        
        # Revenue concentration risk
        if top_5_concentration > 60:
            concentration_risk = "high"
            concentration_note = "Revenue highly concentrated in few products"
        elif top_5_concentration > 40:
            concentration_risk = "moderate"
            concentration_note = "Some revenue concentration"
        else:
            concentration_risk = "low"
            concentration_note = "Well-diversified revenue"
        
        return {
            "store_name": aggregated_data.get("store_name"),
            "revenue_tier": revenue_tier,
            "total_revenue": total_revenue,
            "concentration_risk": concentration_risk,
            "top_5_concentration_pct": top_5_concentration,
            "assessment": concentration_note
        }


@register_categorizer
class CustomerExperienceScorer(DataCategorizer):
    """
    Scores overall customer experience based on ratings and reviews.
    """
    
    def categorize(self, aggregated_data: Dict[str, Any]) -> Dict[str, Any]:
        avg_rating = aggregated_data.get("average_rating", 0)
        review_coverage = aggregated_data.get("review_coverage", 0)
        poorly_rated = aggregated_data.get("poorly_rated_count", 0)
        total_products = aggregated_data.get("total_products", 1)
        
        # Rating score (0-50 points)
        rating_score = (avg_rating / 5.0) * 50
        
        # Review engagement score (0-30 points)
        engagement_score = min(30, (review_coverage / 100) * 30)
        
        # Quality score (0-20 points) - penalize poor ratings
        poor_rating_pct = (poorly_rated / total_products) * 100
        quality_score = max(0, 20 - poor_rating_pct)
        
        total_score = rating_score + engagement_score + quality_score
        
        if total_score >= 80:
            experience = "excellent"
        elif total_score >= 60:
            experience = "good"
        elif total_score >= 40:
            experience = "fair"
        else:
            experience = "needs_improvement"
        
        return {
            "store_name": aggregated_data.get("store_name"),
            "customer_experience": experience,
            "experience_score": round(total_score, 1),
            "average_rating": avg_rating,
            "review_coverage_pct": review_coverage,
            "action_items": self._get_action_items(experience, avg_rating, review_coverage)
        }
    
    def _get_action_items(self, experience: str, rating: float, coverage: float) -> List[str]:
        actions = []
        
        if rating < 4.0:
            actions.append("Improve product quality and customer service")
        if coverage < 30:
            actions.append("Encourage more customer reviews")
        if experience in ["fair", "needs_improvement"]:
            actions.append("Conduct customer satisfaction survey")
        
        return actions if actions else ["Maintain current standards"]


# ============================================================================
# DEMO
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("E-COMMERCE STORE ANALYSIS")
    print("="*80)
    
    # Create test stores
    stores = [
        ShopifyAPIExtractor(store_name="TechGadgets Pro", product_category="Electronics"),
        ShopifyAPIExtractor(store_name="Fashion Forward", product_category="Apparel"),
        ShopifyAPIExtractor(store_name="Home Essentials", product_category="Home & Garden"),
    ]
    
    # Define analysis pipeline
    aggregators = [
        InventoryAggregator(),
        RevenueAggregator(),
        CustomerSatisfactionAggregator(),
        ProductFreshnessAggregator(),
    ]
    
    categorizers = [
        StoreSizeCategorizer(small_threshold=50, medium_threshold=150),
        InventoryHealthScorer(critical_oos_threshold=15.0),
        RevenuePerformanceCategorizer(high_revenue_threshold=50000),
        CustomerExperienceScorer(),
    ]
    
    # Run batch analysis
    batch = BatchPipeline(
        extractors=stores,
        aggregators=aggregators,
        categorizers=categorizers,
        max_workers=4
    )
    
    results = batch.run()
    
    # Display summary
    print("\n" + "="*80)
    print("STORE PERFORMANCE SUMMARY")
    print("="*80)
    
    for result in results:
        metadata = result["pipeline_metadata"]
        cat_results = result["categorization_results"]
        
        print(f"\n{metadata['company_name']}")
        print("-" * 40)
        
        # Size
        size_data = cat_results.get("StoreSizeCategorizer", {}).get("output", {})
        print(f"  Catalog: {size_data.get('size_category', 'N/A')} ({size_data.get('catalog_size', 0)} products)")
        
        # Inventory Health
        inv_data = cat_results.get("InventoryHealthScorer", {}).get("output", {})
        print(f"  Inventory Health: {inv_data.get('inventory_health', 'N/A').upper()} (Score: {inv_data.get('inventory_score', 0)}/100)")
        print(f"    → {inv_data.get('recommendation', 'N/A')}")
        
        # Revenue
        rev_data = cat_results.get("RevenuePerformanceCategorizer", {}).get("output", {})
        print(f"  Revenue: ${rev_data.get('total_revenue', 0):,.2f} ({rev_data.get('revenue_tier', 'N/A')})")
        print(f"    → Concentration Risk: {rev_data.get('concentration_risk', 'N/A').upper()}")
        
        # Customer Experience
        exp_data = cat_results.get("CustomerExperienceScorer", {}).get("output", {})
        print(f"  Customer Experience: {exp_data.get('customer_experience', 'N/A').upper()} (Score: {exp_data.get('experience_score', 0)}/100)")
        print(f"    → Avg Rating: {exp_data.get('average_rating', 0)}/5.0")
        
    print("\n" + "="*80)
    print("Analysis complete!")
    print("="*80 + "\n")
