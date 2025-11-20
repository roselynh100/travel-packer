import unittest
import sys
from pathlib import Path

sys.path.insert(1, str(Path(__file__).parent.parent.parent))

from app.models import BoundingBox


class TestBoundingBoxValidation(unittest.TestCase):
    """Test cases for BoundingBox coordinate validation."""

    def test_valid_bounding_box(self):
        """Test that a valid bounding box can be created."""
        bbox = BoundingBox(x_min=10.0, y_min=20.0, x_max=50.0, y_max=80.0)
        self.assertEqual(bbox.x_min, 10.0)
        self.assertEqual(bbox.y_min, 20.0)
        self.assertEqual(bbox.x_max, 50.0)
        self.assertEqual(bbox.y_max, 80.0)

    def test_bounding_box_missing_x_min(self):
        """Test that missing x_min raises ValueError."""
        with self.assertRaises(ValueError) as context:
            BoundingBox(x_min=None, y_min=20.0, x_max=50.0, y_max=80.0)
        self.assertIn("All bounding box coordinates", str(context.exception))

    def test_bounding_box_missing_y_min(self):
        """Test that missing y_min raises ValueError."""
        with self.assertRaises(ValueError) as context:
            BoundingBox(x_min=10.0, y_min=None, x_max=50.0, y_max=80.0)
        self.assertIn("All bounding box coordinates", str(context.exception))

    def test_bounding_box_missing_x_max(self):
        """Test that missing x_max raises ValueError."""
        with self.assertRaises(ValueError) as context:
            BoundingBox(x_min=10.0, y_min=20.0, x_max=None, y_max=80.0)
        self.assertIn("All bounding box coordinates", str(context.exception))

    def test_bounding_box_missing_y_max(self):
        """Test that missing y_max raises ValueError."""
        with self.assertRaises(ValueError) as context:
            BoundingBox(x_min=10.0, y_min=20.0, x_max=50.0, y_max=None)
        self.assertIn("All bounding box coordinates", str(context.exception))

    def test_bounding_box_x_min_equals_x_max(self):
        """Test that x_min equal to x_max raises ValueError."""
        with self.assertRaises(ValueError) as context:
            BoundingBox(x_min=10.0, y_min=20.0, x_max=10.0, y_max=80.0)
        self.assertIn("x_min must be less than x_max", str(context.exception))

    def test_bounding_box_x_min_greater_than_x_max(self):
        """Test that x_min greater than x_max raises ValueError."""
        with self.assertRaises(ValueError) as context:
            BoundingBox(x_min=50.0, y_min=20.0, x_max=10.0, y_max=80.0)
        self.assertIn("x_min must be less than x_max", str(context.exception))

    def test_bounding_box_y_min_equals_y_max(self):
        """Test that y_min equal to y_max raises ValueError."""
        with self.assertRaises(ValueError) as context:
            BoundingBox(x_min=10.0, y_min=20.0, x_max=50.0, y_max=20.0)
        self.assertIn("y_min must be less than y_max", str(context.exception))

    def test_bounding_box_y_min_greater_than_y_max(self):
        """Test that y_min greater than y_max raises ValueError."""
        with self.assertRaises(ValueError) as context:
            BoundingBox(x_min=10.0, y_min=80.0, x_max=50.0, y_max=20.0)
        self.assertIn("y_min must be less than y_max", str(context.exception))

    def test_bounding_box_edge_case_valid(self):
        """Test edge case where coordinates are at boundaries but still valid."""
        # Smallest valid bounding box
        bbox = BoundingBox(x_min=0.0, y_min=0.0, x_max=0.1, y_max=0.1)
        self.assertEqual(bbox.x_min, 0.0)
        self.assertEqual(bbox.y_min, 0.0)
        self.assertEqual(bbox.x_max, 0.1)
        self.assertEqual(bbox.y_max, 0.1)

    def test_bounding_box_negative_coordinates(self):
        """Test that negative coordinates are allowed (if needed for coordinate systems)."""
        bbox = BoundingBox(x_min=-10.0, y_min=-20.0, x_max=10.0, y_max=20.0)
        self.assertEqual(bbox.x_min, -10.0)
        self.assertEqual(bbox.y_min, -20.0)
        self.assertEqual(bbox.x_max, 10.0)
        self.assertEqual(bbox.y_max, 20.0)


if __name__ == '__main__':
    unittest.main()

