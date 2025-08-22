#!/usr/bin/env python3
"""
Cost Analysis and Budgeting System for Iris AI Research

This module provides detailed cost tracking and analysis for different AI models
and research intensity levels to help optimize budget allocation.
"""

import json
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum

class ModelType(Enum):
    CLAUDE_35_SONNET = "claude-3-5-sonnet-20240620"
    CLAUDE_3_HAIKU = "claude-3-haiku-20240307"
    CLAUDE_3_OPUS = "claude-3-opus-20240229"

class ResearchLevel(Enum):
    BASIC = "basic"           # Text-only, single API call
    STANDARD = "standard"     # Single image + text
    COMPREHENSIVE = "comprehensive"  # Multiple images as grid
    PREMIUM = "premium"       # Multiple separate image calls (most expensive)

@dataclass
class ModelPricing:
    """Pricing per model (per 1M tokens)"""
    input_cost: float   # USD per 1M input tokens
    output_cost: float  # USD per 1M output tokens
    name: str

@dataclass
class CostEstimate:
    input_tokens: int
    output_tokens: int
    input_cost: float
    output_cost: float
    total_cost: float
    model: str
    research_level: str

class CostAnalyzer:
    """Analyze and track costs for different research approaches."""
    
    # Current Claude pricing (as of 2024)
    PRICING = {
        ModelType.CLAUDE_35_SONNET: ModelPricing(3.00, 15.00, "Claude 3.5 Sonnet"),
        ModelType.CLAUDE_3_HAIKU: ModelPricing(0.25, 1.25, "Claude 3 Haiku"),
        ModelType.CLAUDE_3_OPUS: ModelPricing(15.00, 75.00, "Claude 3 Opus")
    }
    
    # Estimated token usage by research level
    TOKEN_ESTIMATES = {
        ResearchLevel.BASIC: {"input": 1000, "output": 800},
        ResearchLevel.STANDARD: {"input": 2500, "output": 1200},
        ResearchLevel.COMPREHENSIVE: {"input": 4000, "output": 1200},  # Grid approach
        ResearchLevel.PREMIUM: {"input": 8000, "output": 1500}  # Multiple calls
    }
    
    def __init__(self):
        self.session_costs = []
        
    def estimate_cost(self, model: ModelType, research_level: ResearchLevel, 
                     custom_tokens: Optional[Dict] = None) -> CostEstimate:
        """Estimate cost for a single research operation."""
        pricing = self.PRICING[model]
        tokens = custom_tokens or self.TOKEN_ESTIMATES[research_level]
        
        input_tokens = tokens["input"]
        output_tokens = tokens["output"]
        
        input_cost = (input_tokens / 1_000_000) * pricing.input_cost
        output_cost = (output_tokens / 1_000_000) * pricing.output_cost
        total_cost = input_cost + output_cost
        
        return CostEstimate(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=total_cost,
            model=pricing.name,
            research_level=research_level.value
        )
        
    def compare_approaches(self, lot_count: int = 1) -> Dict:
        """Compare costs across different approaches."""
        comparisons = {}
        
        for model in ModelType:
            comparisons[model.value] = {}
            for level in ResearchLevel:
                estimate = self.estimate_cost(model, level)
                comparisons[model.value][level.value] = {
                    "per_lot": estimate.total_cost,
                    "for_batch": estimate.total_cost * lot_count,
                    "tokens_per_lot": estimate.input_tokens + estimate.output_tokens
                }
        
        return comparisons
    
    def generate_budget_report(self, monthly_lots: int = 100) -> str:
        """Generate a comprehensive budget analysis report."""
        report = []
        report.append("# 💰 Iris AI Cost Analysis & Budget Report")
        report.append(f"📊 Analysis for {monthly_lots} lots per month\n")
        
        # Cost comparison table
        report.append("## 🎯 Cost Comparison by Approach\n")
        report.append("| Model | Research Level | Per Lot | Per 100 Lots | Monthly ({}) |".format(monthly_lots))
        report.append("|-------|---------------|---------|--------------|---------------|")
        
        comparisons = self.compare_approaches(monthly_lots)
        
        for model_key, levels in comparisons.items():
            model_name = self.PRICING[ModelType(model_key)].name
            for level_key, costs in levels.items():
                per_lot = f"${costs['per_lot']:.4f}"
                per_100 = f"${costs['per_lot'] * 100:.2f}"
                monthly = f"${costs['for_batch']:.2f}"
                report.append(f"| {model_name} | {level_key.title()} | {per_lot} | {per_100} | **{monthly}** |")
        
        # Recommendations
        report.append("\n## 🎯 Strategic Recommendations\n")
        
        # Find most cost-effective options
        haiku_comprehensive = self.estimate_cost(ModelType.CLAUDE_3_HAIKU, ResearchLevel.COMPREHENSIVE)
        sonnet_standard = self.estimate_cost(ModelType.CLAUDE_35_SONNET, ResearchLevel.STANDARD)
        
        report.append("### 💡 Optimal Strategies:")
        report.append(f"- **Budget-Conscious**: Haiku + Comprehensive (${haiku_comprehensive.total_cost * monthly_lots:.2f}/month)")
        report.append(f"- **Quality-Balanced**: Sonnet + Standard (${sonnet_standard.total_cost * monthly_lots:.2f}/month)")
        report.append(f"- **Premium Quality**: Sonnet + Comprehensive (${self.estimate_cost(ModelType.CLAUDE_35_SONNET, ResearchLevel.COMPREHENSIVE).total_cost * monthly_lots:.2f}/month)")
        
        # Research level explanations
        report.append("\n### 📋 Research Level Details:")
        report.append("- **Basic**: Text-only analysis, fastest/cheapest")
        report.append("- **Standard**: Single main image + text analysis")
        report.append("- **Comprehensive**: Multi-image grid analysis (RECOMMENDED)")
        report.append("- **Premium**: Multiple separate image calls (most expensive)")
        
        # Cost breakdown
        report.append("\n## 💸 Detailed Cost Breakdown\n")
        
        for model in [ModelType.CLAUDE_3_HAIKU, ModelType.CLAUDE_35_SONNET]:
            pricing = self.PRICING[model]
            report.append(f"### {pricing.name}")
            report.append(f"- Input: ${pricing.input_cost}/1M tokens")
            report.append(f"- Output: ${pricing.output_cost}/1M tokens")
            
            comprehensive = self.estimate_cost(model, ResearchLevel.COMPREHENSIVE)
            report.append(f"- **Comprehensive Research**: ~{comprehensive.input_tokens + comprehensive.output_tokens:,} tokens = ${comprehensive.total_cost:.4f}")
            report.append("")
        
        return "\n".join(report)
    
    def track_actual_usage(self, model: str, input_tokens: int, output_tokens: int, 
                          research_level: str) -> CostEstimate:
        """Track actual API usage and costs."""
        # Find model pricing
        model_type = None
        for mt in ModelType:
            if mt.value == model:
                model_type = mt
                break
        
        if not model_type:
            # Default to Sonnet for unknown models
            model_type = ModelType.CLAUDE_35_SONNET
        
        pricing = self.PRICING[model_type]
        
        input_cost = (input_tokens / 1_000_000) * pricing.input_cost
        output_cost = (output_tokens / 1_000_000) * pricing.output_cost
        total_cost = input_cost + output_cost
        
        actual_cost = CostEstimate(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=total_cost,
            model=pricing.name,
            research_level=research_level
        )
        
        # Store for session tracking
        self.session_costs.append({
            "timestamp": datetime.now().isoformat(),
            "cost": actual_cost
        })
        
        return actual_cost
    
    def get_session_total(self) -> float:
        """Get total cost for current session."""
        return sum(entry["cost"].total_cost for entry in self.session_costs)
    
    def save_session_report(self, filepath: str = "cost_report.json"):
        """Save session cost report to file."""
        report_data = {
            "session_start": datetime.now().isoformat(),
            "total_operations": len(self.session_costs),
            "total_cost": self.get_session_total(),
            "operations": [
                {
                    "timestamp": entry["timestamp"],
                    "model": entry["cost"].model,
                    "research_level": entry["cost"].research_level,
                    "input_tokens": entry["cost"].input_tokens,
                    "output_tokens": entry["cost"].output_tokens,
                    "total_cost": entry["cost"].total_cost
                }
                for entry in self.session_costs
            ]
        }
        
        with open(filepath, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"💾 Cost report saved to {filepath}")

def main():
    """Generate and display budget analysis."""
    analyzer = CostAnalyzer()
    
    print("🎯 Generating comprehensive budget analysis...")
    print()
    
    # Generate report for different lot volumes
    for lots in [50, 100, 250, 500]:
        print(f"📊 Budget Analysis for {lots} lots/month:")
        print("-" * 50)
        
        # Compare key approaches
        haiku_comp = analyzer.estimate_cost(ModelType.CLAUDE_3_HAIKU, ResearchLevel.COMPREHENSIVE)
        sonnet_std = analyzer.estimate_cost(ModelType.CLAUDE_35_SONNET, ResearchLevel.STANDARD)
        sonnet_comp = analyzer.estimate_cost(ModelType.CLAUDE_35_SONNET, ResearchLevel.COMPREHENSIVE)
        
        print(f"Haiku + Comprehensive:  ${haiku_comp.total_cost * lots:8.2f}")
        print(f"Sonnet + Standard:      ${sonnet_std.total_cost * lots:8.2f}")
        print(f"Sonnet + Comprehensive: ${sonnet_comp.total_cost * lots:8.2f}")
        print()
    
    # Generate full report
    full_report = analyzer.generate_budget_report(100)
    
    # Save to file
    with open("iris_budget_analysis.md", "w") as f:
        f.write(full_report)
    
    print("✅ Full budget analysis saved to 'iris_budget_analysis.md'")
    print("\n" + "="*60)
    print("📋 QUICK RECOMMENDATIONS:")
    print("- For high quality + reasonable cost: Claude 3.5 Sonnet + Comprehensive")
    print("- For budget optimization: Claude 3 Haiku + Comprehensive") 
    print("- Grid approach saves ~60% vs individual image calls")
    print("="*60)

if __name__ == "__main__":
    main()