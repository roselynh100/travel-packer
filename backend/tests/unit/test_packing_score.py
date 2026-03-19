import datetime
import sys
import unittest
from pathlib import Path
from typing import Dict, List
from unittest.mock import patch

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.models import (
    Activity,
    Airline,
    BagType,
    BoundingBox,
    CVResult,
    Dimensions,
    Item,
    Location,
    RecommendedItem,
    RemovalRecommendation,
    Trip,
)
from app.state.db import items_store, recommendations_store
from machine_learning.generator import baseline_list_algorithm
from machine_learning.packing_score import get_user_packing_score


class TestScoringFullCoverage(unittest.TestCase):
    test_results = []
    # This dictionary bridges the gap between IDs and Names for the Mock
    rec_id_to_name_map = {}

    def setUp(self):
        items_store.clear()
        recommendations_store.clear()
        self.rec_id_to_name_map.clear()
        self.default_loc = Location(
            city="Toronto", country="Canada", airport_code="YYZ"
        )
        self.base_date = datetime.datetime(2026, 3, 17)

    def _create_cv(self, name: str) -> CVResult:
        return CVResult(
            item_name=name,
            confidence_score=0.99,
            bounding_boxes=[BoundingBox(x_min=0, y_min=0, x_max=10, y_max=10)],
            dimensions=Dimensions(length=20, width=20, height=5),
        )

    def dynamic_generator_mock(self, trip):
        """Mock generator that uses our local map to find item names by ID."""
        recs = []
        for rid in trip.recommendations:
            rec_obj = recommendations_store.get(rid)
            # Only 'pack' status recommendations are part of the baseline list
            if rec_obj and rec_obj.status == "pack":
                name = self.rec_id_to_name_map.get(rid, "Unknown Item")
                recs.append(RecommendedItem(item_name=name))
        return recs

    def _setup_scenario(
        self,
        match_ratio: float,  # % of recommended items packed
        extra_qty: int,  # Items packed NOT on the list
        weight_kg: float,
        vol_cm3: float,
        removal_recs: List[dict],  # [{"status": "remove"/"swap", "accepted": bool}]
    ):
        trip = Trip(
            origin_details=self.default_loc,
            destination_details=self.default_loc,
            start_date=self.base_date,
            end_date=self.base_date + datetime.timedelta(days=4),
            doing_laundry=False,
            bag_type=BagType.checked,
            airline=Airline.air_canada,
            activities=[Activity.work],
            highest_temp=20,
            lowest_temp=10,
            precipitation_percentage=0.1,
        )

        # 1. Setup 'Pack' recommendations
        golden_recs = baseline_list_algorithm(trip)
        trip_rec_ids = []
        trip_item_ids = []

        num_to_pack = int(len(golden_recs) * match_ratio)

        for i, rec_item in enumerate(golden_recs):
            rec = RemovalRecommendation(status="pack", is_accepted=True)
            # Store the ID -> Name relationship in our local test map
            self.rec_id_to_name_map[rec.recommendation_id] = rec_item.item_name

            recommendations_store[rec.recommendation_id] = rec
            trip_rec_ids.append(rec.recommendation_id)

            if i < num_to_pack:
                item = Item(
                    quantity=1,
                    cv_result=self._create_cv(rec_item.item_name),
                    recommendation=rec.recommendation_id,
                )
                items_store[item.item_id] = item
                trip_item_ids.append(item.item_id)

        # 2. Setup Manual Extras (Unlinked)
        for _ in range(extra_qty):
            item = Item(
                quantity=1, cv_result=self._create_cv("Extra"), recommendation=None
            )
            items_store[item.item_id] = item
            trip_item_ids.append(item.item_id)

        # 3. Setup Correction Recommendations (For Delta)
        for r_data in removal_recs:
            r_rec = RemovalRecommendation(
                status=r_data["status"], is_accepted=r_data["accepted"]
            )
            r_rec.__dict__["type"] = "RemovalRecommendation"
            recommendations_store[r_rec.recommendation_id] = r_rec
            trip_rec_ids.append(r_rec.recommendation_id)

        trip.items = trip_item_ids
        trip.recommendations = trip_rec_ids
        trip.total_items_weight = weight_kg
        trip.total_items_volume = vol_cm3

        with patch(
            "machine_learning.packing_score.baseline_list_algorithm",
            side_effect=self.dynamic_generator_mock,
        ):
            score = get_user_packing_score(trip)

        # Generate Parameter Description for the table
        removals_desc = "None"
        if removal_recs:
            acc = sum(1 for r in removal_recs if r["accepted"])
            removals_desc = f"{acc}/{len(removal_recs)} Acc"

        self.test_results.append(
            {
                "Match": f"{int(match_ratio*100)}%",
                "Extras": extra_qty,
                "Weight": f"{weight_kg}kg",
                "Vol": f"{int(vol_cm3/1000)}k",
                "Removals": removals_desc,
                "Score": round(score, 2),
            }
        )

    def test_parameter_coverage(self):
        # --- HIGH RANGE (80 - 100) ---
        # Case 1: THE BEST POSSIBLE SCORE
        self._setup_scenario(
            1.0, 0, 18.4, 60000, [{"status": "swap", "accepted": True}]
        )

        # Case 2: THE "GOOD ENOUGH" (100% Match, at the 23kg limit)
        self._setup_scenario(1.0, 0, 23.0, 75000, [])

        # --- MID RANGE (40 - 70) ---
        # Case 3: THE FORGETFUL MINIMALIST (Packs only 20% of list, but very light bag)
        # S_list = 20. S_weight = 100. S_vol = 100.
        # Math: (0.5 * 20) + 25 + 25 = 60.0
        self._setup_scenario(0.2, 0, 5.0, 10000, [])

        # Case 4: THE MANUAL HOARDER (100% Match, but 40 UNLINKED EXTRAS)
        # Penalty: 10 * (40/10 recs) = -40. S_list = 60.
        # Math: (0.5 * 60) + 25 + 25 = 80.0 (Drops lower if weight increases)
        self._setup_scenario(1.0, 40, 22.0, 70000, [])

        # Case 5: THE STUBBORN ROGUE (0% Match, Packs 20 items AI didn't ask for)
        # S_list = 0. S_weight = 100. S_vol = 100. Delta = -5 (Rejected 1 removal).
        # Math: 0 + 25 + 25 - 5 = 45.0
        self._setup_scenario(
            0.0, 20, 15.0, 40000, [{"status": "remove", "accepted": False}]
        )

        # --- LOW RANGE (0 - 30) ---
        # Case 6: THE DISASTER (20% Match, 30kg Weight, Rejected Advice)
        # S_list = 20. S_weight = 20. S_vol = 20. Delta = -5.
        # Math: (0.5 * 20) + (0.25 * 20) + (0.25 * 20) - 5 = 10 + 5 + 5 - 5 = 15.0
        self._setup_scenario(
            0.2, 0, 30.0, 90000, [{"status": "remove", "accepted": False}]
        )

        # Case 7: TOTAL SYSTEMS FAILURE (0% Match, 40kg Weight, 120k Vol, Delta -10)
        # Everything is 0 or negative.
        self._setup_scenario(
            0.0, 50, 40.0, 120000, [{"status": "remove", "accepted": False}] * 5
        )

    @classmethod
    def tearDownClass(cls):
        print("\n" + "=" * 95)
        print(f"{'FULL PARAMETER SCORING ANALYSIS (Weight Limit: 23kg)':^95}")
        print("=" * 95)
        header = f"{'Match %':<8} | {'Extras':<7} | {'Weight':<8} | {'Vol':<6} | {'Removals':<12} | {'Score':<8}"
        print(header)
        print("-" * len(header))
        for res in cls.test_results:
            print(
                f"{res['Match']:<8} | {res['Extras']:<7} | {res['Weight']:<8} | {res['Vol']:<6} | {res['Removals']:<12} | {res['Score']:<8}"
            )
        print("=" * 95 + "\n")


if __name__ == "__main__":
    unittest.main()
