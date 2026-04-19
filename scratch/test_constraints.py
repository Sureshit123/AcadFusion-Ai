import unittest
import sys
import os

# Add parent directory to path to import blueprints
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock the database before importing blueprint
from unittest.mock import MagicMock
sys.modules['models.database'] = MagicMock()

from blueprints.timetable import DepartmentCycleGenerator, SLOTS

class TestTeacherBreaks(unittest.TestCase):
    def setUp(self):
        # Minimal semesters_data
        self.semesters_data = {
            '3': {
                'subjects': [{'name': 'Sub1', 'teacher': 'T1', 'credits': 3}],
                'labs': [],
                'fixed': []
            }
        }
        self.gen = DepartmentCycleGenerator('odd', self.semesters_data, 3)

    def test_subject_subject_no_gap(self):
        # Mark T1 busy with a subject at Slot 0
        self.gen.mark_busy(['T1'], 'subject', 0, 0)
        
        # Try to place another subject at Slot 1 (Should fail - No gap)
        self.assertFalse(self.gen.is_resource_free(['T1'], 'subject', 0, 1))

    def test_subject_subject_with_gap(self):
        # Mark T1 busy with a subject at Slot 0
        self.gen.mark_busy(['T1'], 'subject', 0, 0)
        
        # Slot 1 is empty (Gap)
        # Try to place another subject at Slot 2 (Should succeed)
        self.assertTrue(self.gen.is_resource_free(['T1'], 'subject', 0, 2))

    def test_subject_lab_subject_no_gap(self):
        # Mark T1 busy with a subject at Slot 0
        self.gen.mark_busy(['T1'], 'subject', 0, 0)
        
        # Mark T1 busy with a lab at Slot 1 and 2
        self.gen.mark_busy(['T1'], 'lab', 0, 1)
        self.gen.mark_busy(['T1'], 'lab', 0, 2)
        
        # Try to place another subject at Slot 3 (Should fail - Lab is not a gap)
        self.assertFalse(self.gen.is_resource_free(['T1'], 'subject', 0, 3))

    def test_subject_fixed_subject_gap(self):
        # Mark T1 busy with a subject at Slot 0
        self.gen.mark_busy(['T1'], 'subject', 0, 0)
        
        # Mark T1 busy with a fixed slot at Slot 1
        self.gen.mark_busy(['T1'], 'fixed', 0, 1)
        
        # Try to place another subject at Slot 2 (Should succeed - Fixed is a gap)
        self.assertTrue(self.gen.is_resource_free(['T1'], 'subject', 0, 2))

    def test_lab_lab_no_gap_ok(self):
        # Mark T1 busy with a lab at Slot 0-1
        self.gen.mark_busy(['T1'], 'lab', 0, 0)
        self.gen.mark_busy(['T1'], 'lab', 0, 1)
        
        # Labs don't need gaps between them (according to logic)
        # Try to place another lab at Slot 2-3 (is_resource_free only checks slot availability for labs)
        self.assertTrue(self.gen.is_resource_free(['T1'], 'lab', 0, 2))

    def test_forward_backward_check(self):
        # Mark T1 busy with a subject at Slot 4
        self.gen.mark_busy(['T1'], 'subject', 0, 4)
        
        # Try to place subject at Slot 3 (Should fail)
        self.assertFalse(self.gen.is_resource_free(['T1'], 'subject', 0, 3))
        
        # Try to place subject at Slot 2 (Should succeed if Slot 3 is empty)
        self.assertTrue(self.gen.is_resource_free(['T1'], 'subject', 0, 2))

if __name__ == '__main__':
    unittest.main()
