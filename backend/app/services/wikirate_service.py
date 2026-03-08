"""
EcoScan Wikirate Service
Integrates with Wikirate.org to fetch real-world ESG data and sustainability metrics.
Used to replace hardcoded estimates with community-verified facts.
"""

import logging
import httpx
from typing import Optional, Dict, Any, List
from app.core.config import get_settings

logger = logging.getLogger("ecoscan.wikirate")
settings = get_settings()

class WikirateService:
    """
    Service to fetch corporate sustainability data from Wikirate.org.
    Uses the Card API (e.g., CompanyName+MetricName.json).
    """

    BASE_URL = "https://wikirate.org"

    def __init__(self):
        self.api_key = settings.WIKIRATE_API_KEY
        # Use a browser-like user agent to avoid 403s on public endpoints
        self.headers = {
            "User-Agent": "EcoScan-Sustainability-Agent/1.0 (https://ecoscan.ai; team@ecoscan.ai)",
            "Accept": "application/json",
        }
        if self.api_key:
            self.headers["X-API-Key"] = self.api_key

    async def search_company(self, name: str) -> Optional[str]:
        """
        Find the canonical Wikirate card name for a given company.
        """
        try:
            # We use the search endpoint or filter companies
            url = f"{self.BASE_URL}/Company.json"
            params = {"filter[name]": name, "limit": 1}
            
            async with httpx.AsyncClient(headers=self.headers, timeout=10.0) as client:
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    cards = data.get("cards", [])
                    if cards:
                        # Return the name of the first match
                        return cards[0].get("name")
        except Exception as e:
            logger.error(f"Error searching company on Wikirate: {e}")
        return None

    async def get_metric_answer(self, company_name: str, metric_name: str) -> Optional[Dict[str, Any]]:
        """
        Fetch the latest answer for a specific metric for a company.
        Wikirate structure: Company+Metric.json
        """
        try:
            # Wikirate uses a '+' to join company and metric names for the specific "Answer" card
            card_path = f"{company_name}+{metric_name}".replace(" ", "_")
            url = f"{self.BASE_URL}/{card_path}.json"
            
            async with httpx.AsyncClient(headers=self.headers, timeout=10.0) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    # Wikirate card JSON usually has the value in a specific field
                    return data
        except Exception as e:
            logger.debug(f"Metric {metric_name} not found for {company_name}")
        return None

    async def fetch_sustainability_profile(self, company_name: str) -> Dict[str, Any]:
        """
        Aggregates multiple key metrics to form a real-world score.
        """
        canonical_name = await self.search_company(company_name)
        if not canonical_name:
            return {"found": False, "company": company_name}

        # Curated list of high-value Wikirate metrics
        # Note: These names must match Wikirate metric card names exactly
        metrics_to_fetch = {
            "transparency": "Fashion_Transparency_Index_Score",
            "emissions": "Greenhouse_Gas_Emissions_Scope_1_2",
            "water": "Water_Consumption",
            "gri": "Reporting_according_to_GRI_Standards",
            "waste": "Waste_Recycled_Percentage"
        }

        results = {"found": True, "canonical_name": canonical_name, "metrics": {}}
        
        for key, metric in metrics_to_fetch.items():
            answer = await self.get_metric_answer(canonical_name, metric)
            if answer:
                # Basic extraction of the value
                results["metrics"][key] = {
                    "value": answer.get("value"),
                    "year": answer.get("year"),
                    "metric_name": metric
                }

        return results

# Singleton instance
wikirate = WikirateService()
