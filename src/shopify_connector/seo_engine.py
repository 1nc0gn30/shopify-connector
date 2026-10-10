"""Shopify SEO Listing Auditor & Net Margin Calculator.

Engineered by Neal Frazier Tech (@1nc0gn30) • NullAI Platform.
100% Python Standard Library — Zero External Dependencies.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


def audit_listing(
    title: str,
    description: str = "",
    tags: Optional[List[str]] = None,
    handle: str = "",
    image_alt_texts: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Audit Shopify listing title, tags, description, handle, and alt text for SEO ranking."""
    tags = tags or []
    image_alt_texts = image_alt_texts or []
    
    score = 100
    deductions: List[Dict[str, Any]] = []
    strengths: List[str] = []

    # 1. Title Audit
    title_len = len(title.strip())
    if title_len == 0:
        score -= 40
        deductions.append({"rule": "title_empty", "penalty": 40, "message": "Product title is empty."})
    elif title_len < 30:
        score -= 15
        deductions.append({"rule": "title_too_short", "penalty": 15, "message": f"Title is only {title_len} chars. Target 40–70 characters for optimal Google SERP indexation."})
    elif title_len > 90:
        score -= 10
        deductions.append({"rule": "title_too_long", "penalty": 10, "message": f"Title is {title_len} chars. Titles over 70 chars get truncated on mobile search results."})
    else:
        strengths.append(f"Title length ({title_len} chars) is within the optimal 40–70 character sweet spot.")

    # Keyword separators in title
    if " | " in title or " — " in title or " - " in title:
        strengths.append("Title utilizes clean professional keyword separators for secondary search intent.")

    # 2. Tags Audit
    tag_count = len(tags)
    if tag_count == 0:
        score -= 25
        deductions.append({"rule": "tags_empty", "penalty": 25, "message": "Zero tags defined. Shopify search indexing relies heavily on collection and product tags."})
    elif tag_count < 5:
        score -= 10
        deductions.append({"rule": "tags_sparse", "penalty": 10, "message": f"Only {tag_count} tags defined. Target 8–15 relevant search tags for broad collection filtering."})
    else:
        strengths.append(f"Strong tag coverage with {tag_count} categorized tags.")

    # Multi-word tags check
    multi_word_tags = [t for t in tags if " " in t.strip()]
    if multi_word_tags:
        strengths.append(f"{len(multi_word_tags)} long-tail multi-word tags match specific buyer search intent.")

    # 3. Description Audit
    desc_clean = re.sub(r"<[^>]+>", " ", description).strip()
    word_count = len(desc_clean.split())
    if word_count < 25:
        score -= 15
        deductions.append({"rule": "description_short", "penalty": 15, "message": f"Description is thin ({word_count} words). High-converting listings feature 80–180 words detailing materials, care instructions, and sizing."})
    elif word_count >= 60:
        strengths.append(f"Comprehensive description copy ({word_count} words) with rich semantic depth.")

    # 4. Handle (URL Slug) Audit
    if handle:
        if not re.match(r"^[a-z0-9-]+$", handle):
            score -= 10
            deductions.append({"rule": "handle_invalid_chars", "penalty": 10, "message": "Handle contains uppercase letters or special symbols. Use lowercase alphanumeric with single hyphens."})
        elif "--" in handle:
            score -= 5
            deductions.append({"rule": "handle_double_hyphens", "penalty": 5, "message": "Handle contains consecutive hyphens ('--'). Clean up URL structure for cleaner canonical links."})
        else:
            strengths.append(f"Clean, crawlable URL handle: '/products/{handle}'.")

    # 5. Image Alt Text Audit
    if image_alt_texts:
        missing_alt = [alt for alt in image_alt_texts if not alt.strip()]
        if missing_alt:
            score -= 10
            deductions.append({"rule": "missing_image_alt", "penalty": 10, "message": f"{len(missing_alt)} images are missing descriptive alt text for accessibility and Google Image search."})
        else:
            strengths.append("100% of product images have verified descriptive alt text attributes.")

    score = max(0, min(100, score))

    if score >= 90:
        grade = "A+"
    elif score >= 80:
        grade = "A"
    elif score >= 70:
        grade = "B"
    elif score >= 55:
        grade = "C"
    else:
        grade = "F"

    return {
        "score": score,
        "grade": grade,
        "title_length": title_len,
        "tag_count": tag_count,
        "word_count": word_count,
        "strengths": strengths,
        "deductions": deductions,
        "is_ready_for_publish": score >= 75,
    }


def calculate_margins(
    retail_price: float,
    pod_cost: float,
    shipping_charged: float = 0.0,
    shipping_cost: float = 0.0,
    plan: str = "basic",
    include_ads: bool = False,
) -> Dict[str, Any]:
    """Calculate Shopify fees, payment processing, POD production cost, and net profit margins."""
    retail = max(0.0, float(retail_price))
    pod = max(0.0, float(pod_cost))
    ship_charge = max(0.0, float(shipping_charged))
    ship_cost = max(0.0, float(shipping_cost))

    gross_revenue = retail + ship_charge

    # Shopify Payments rates
    plan_rates = {
        "basic": {"percent": 0.029, "fixed": 0.30},
        "shopify": {"percent": 0.026, "fixed": 0.30},
        "advanced": {"percent": 0.024, "fixed": 0.30},
    }
    rate_info = plan_rates.get(plan.lower(), plan_rates["basic"])

    # Processing Fee
    processing_fee = round((gross_revenue * rate_info["percent"]) + rate_info["fixed"], 2)
    
    # Optional ad conversion fee (e.g. 15% Google/Meta blended CAC)
    ad_spend = round(gross_revenue * 0.15, 2) if include_ads else 0.0

    total_costs = round(pod + ship_cost + processing_fee + ad_spend, 2)
    net_profit = round(gross_revenue - total_costs, 2)
    
    margin_percent = round((net_profit / gross_revenue * 100.0), 1) if gross_revenue > 0 else 0.0

    return {
        "gross_revenue": gross_revenue,
        "retail_price": retail,
        "shipping_charged": ship_charge,
        "pod_production_cost": pod,
        "actual_shipping_cost": ship_cost,
        "shopify_processing_fee": processing_fee,
        "plan_used": plan.title(),
        "processing_rate": f"{rate_info['percent']*100:.1f}% + ${rate_info['fixed']:.2f}",
        "ad_attribution_cost": ad_spend,
        "total_cost": total_costs,
        "net_profit": net_profit,
        "profit_margin_percent": margin_percent,
        "is_profitable": net_profit > 0,
        "recommended_retail_price": round(pod * 2.2, 2) if pod > 0 else retail,
    }
