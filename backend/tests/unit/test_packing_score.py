import datetime
import sys
import unittest
from pathlib import Path
from typing import Dict, List

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.models import (
    Airline,
    BagType,
    BoundingBox,
    CVResult,
    Dimensions,
    Item,
    Location,
    RemovalRecommendation,
    Trip,
)
from app.state.db import items_store, recommendations_store
from machine_learning.packing_score import get_user_packing_score


class TestPackingScoringExpanded(unittest.TestCase):
    test_results = []

    def setUp(self):
        items_store.clear()
        recommendations_store.clear()
        self.default_loc = Location(
            city="Toronto", country="Canada", airport_code="YYZ"
        )
        self.base_date = datetime.datetime(2026, 2, 14)

    def _create_cv(self, name: str) -> CVResult:
        return CVResult(
            item_name=name,
            confidence_score=0.95,
            bounding_boxes=[BoundingBox(x_min=0, y_min=0, x_max=10, y_max=10)],
            dimensions=Dimensions(length=20, width=20, height=10),
        )

    def _setup_scenario(
        self,
        scenario_name: str,
        packed_items: List[
            dict
        ],  # [{"name": str, "qty": int, "weight": float, "vol": float, "linked": bool}]
        recs_list: List[dict],  # [{"name": str, "accepted": bool}]
        total_weight: float,
        total_volume: float,
    ) -> Trip:
        name_to_rec_id = {}
        trip_item_ids = []
        trip_rec_ids = []

        # 1. Setup Recommendations
        for r_data in recs_list:
            rec = RemovalRecommendation(status="pack", is_accepted=r_data["accepted"])
            rec.__dict__["item_name"] = r_data["name"]
            recommendations_store[rec.recommendation_id] = rec
            trip_rec_ids.append(rec.recommendation_id)
            name_to_rec_id[r_data["name"]] = rec.recommendation_id

        # 2. Setup Items
        for i_data in packed_items:
            r_id = name_to_rec_id.get(i_data["name"]) if i_data.get("linked") else None
            item = Item(
                quantity=i_data["qty"],
                cv_result=self._create_cv(i_data["name"]),
                recommendation=r_id,
                weight_kg=i_data.get("weight", 0.5),
                estimated_volume_cm3=i_data.get("vol", 1000.0),
            )
            items_store[item.item_id] = item
            trip_item_ids.append(item.item_id)

        # 3. Trip Configuration (Regular + Checked = 23kg limit)
        trip = Trip(
            origin_details=self.default_loc,
            destination_details=self.default_loc,
            start_date=self.base_date,
            end_date=self.base_date + datetime.timedelta(days=10),
            doing_laundry=True,
            bag_type=BagType.checked,
            airline=Airline.air_canada,
            items=trip_item_ids,
            recommendations=trip_rec_ids,
            total_items_weight=total_weight,
            total_items_volume=total_volume,
        )

        score = get_user_packing_score(trip)

        self.test_results.append(
            {
                "Scenario": scenario_name,
                "Weight": f"{total_weight}/{trip.limit_kg}kg",
                "Volume": f"{int(total_volume)}/75k",
                "Score": round(score, 2),
            }
        )
        return trip

    def test_expanded_scenarios(self):
        # --- Scenario A: The Ultimate Optimized Pro ---
        # Usage: 18.4kg / 23kg = 80% (Safe Zone Max)
        # Volume: 60,000 / 75,000 = 80% (Safe Zone Max)
        # Recommendation Match: 100%
        # Acceptance Rate: 100% (Delta = +5.0)
        # Expected Score: 100.0 (Clipped from 105.0)

        self._setup_scenario(
            "Ultimate Optimized Pro",
            packed_items=[
                {
                    "name": "Laptop",
                    "qty": 1,
                    "weight": 2.5,
                    "vol": 2000,
                    "linked": True,
                },
                {
                    "name": "Winter Coat",
                    "qty": 1,
                    "weight": 3.0,
                    "vol": 15000,
                    "linked": True,
                },
                {"name": "Boots", "qty": 1, "weight": 2.5, "vol": 8000, "linked": True},
                {
                    "name": "Jeans",
                    "qty": 4,
                    "weight": 4.0,
                    "vol": 15000,
                    "linked": True,
                },
                {
                    "name": "T-shirt",
                    "qty": 8,
                    "weight": 6.4,
                    "vol": 20000,
                    "linked": True,
                },
            ],
            recs_list=[
                {"name": "Laptop", "accepted": True},
                {"name": "Winter Coat", "accepted": True},
                {"name": "Boots", "accepted": True},
                {"name": "Jeans", "accepted": True},
                {"name": "Jeans", "accepted": True},
                {"name": "Jeans", "accepted": True},
                {"name": "Jeans", "accepted": True},
                {"name": "T-shirt", "accepted": True},
                {"name": "T-shirt", "accepted": True},
                {"name": "T-shirt", "accepted": True},
                {"name": "T-shirt", "accepted": True},
                {"name": "T-shirt", "accepted": True},
                {"name": "T-shirt", "accepted": True},
                {"name": "T-shirt", "accepted": True},
                {"name": "T-shirt", "accepted": True},
            ],
            total_weight=18.4,  # Exactly 80% of 23kg
            total_volume=60000.0,  # Exactly 80% of 75k
        )

        # --- Scenario B: The 'Danger Zone' Packer ---
        # Usage: 95% (Between 0.8 and 1.0)
        # Should see a slight drop in score compared to the Pro.
        self._setup_scenario(
            "Danger Zone (95%)",
            packed_items=[{"name": "Heavy Gear", "qty": 1, "linked": True}],
            recs_list=[{"name": "Heavy Gear", "accepted": True}],
            total_weight=21.85,  # 95% of 23kg
            total_volume=71250.0,  # 95% of 75k
        )

        # --- Scenario C: The Volume Buster ---
        # Under weight, but over volume (too many fluffy sweaters).
        self._setup_scenario(
            "Volume Violation",
            packed_items=[{"name": "Pillow", "qty": 4, "linked": True}],
            recs_list=[{"name": "Pillow", "accepted": True}] * 4,
            total_weight=10.0,
            total_volume=85000.0,  # Limit is 75k
        )

        # --- Scenario D: Total Rebel Chaos ---
        # Exceeds weight, volume, and ignored all recommendations.
        self._setup_scenario(
            "Chaos Rebel",
            packed_items=[{"name": "Random Box", "qty": 5, "linked": False}],
            recs_list=[{"name": "Essential Kit", "accepted": False}],
            total_weight=28.0,
            total_volume=90000.0,
        )

    @classmethod
    def tearDownClass(cls):
        print("\n" + "=" * 70)
        print(f"{'ADVANCED SCORING SUMMARY (Limit: 23kg / 75k Vol)':^70}")
        print("=" * 70)
        header = f"{'Scenario':<20} | {'Weight':<12} | {'Volume':<12} | {'Score':<8}"
        print(header)
        print("-" * len(header))
        for res in cls.test_results:
            print(
                f"{res['Scenario']:<20} | {res['Weight']:<12} | {res['Volume']:<12} | {res['Score']:<8}"
            )
        print("=" * 70 + "\n")


if __name__ == "__main__":
    unittest.main()
