import sys
import os
from unittest.mock import MagicMock

# Mock Flask and other dependencies
sys.modules['flask'] = MagicMock()
sys.modules['models.database'] = MagicMock()
sys.modules['pandas'] = MagicMock()
sys.modules['openpyxl'] = MagicMock()

# Import the GreedyOptimizer
# We need to add the project root to sys.path
sys.path.append(os.getcwd())

from blueprints.optimizer import GreedyOptimizer

SLOTS = ["09:00-10:00", "10:00-11:00", "11:15-12:15", "12:15-01:15", "02:15-03:15", "03:15-04:15", "04:15-05:15"]

def test_compactness_and_no_repeat():
    # Mock raw grids for one semester
    raw_grids = {
        '3': [[None for _ in range(7)] for _ in range(6)]
    }
    
    # 3 subjects, 2 credits each = 6 classes
    # Add items
    for i in range(2):
        raw_grids['3'][0][i] = {"type": "subject", "name": f"Sub{i}", "teacher": f"T{i}"}
    
    # Create optimizer
    optimizer = GreedyOptimizer(raw_grids)
    
    # FORCE a clash in slot 1 for all teachers
    # We need to reach into the internal state to simulate this
    # OR we can just mock it in _attempt_optimize if we were testing just that.
    # But let's just see if _refine_and_fill works.
    
    # Directly test _refine_and_fill
    test_grid = {
        '3': [[None for _ in range(7)] for _ in range(6)]
    }
    test_grid['3'][0][0] = {"name": "Class A"}
    test_grid['3'][0][3] = {"name": "Class B"} # Gaps at 1 and 2
    
    refined = optimizer._refine_and_fill(test_grid)
    row_0 = refined['3'][0]
    
    print("\nRefined Row 0 (Manual Test):")
    print(" | ".join([ (s['name'] if s else "-") for s in row_0 ]))
    
    if row_0[1] and row_0[1]['type'] == 'productive':
        print("SUCCESS: Gap at slot 1 filled.")
    else:
        print("FAILED: Gap at slot 1 NOT filled.")

    # Test _already_has_subject
    day_slots = [
        {"name": "Math 101"},
        None,
        {"name": "Physics"}
    ]
    print("\nSubject Repetition Test:")
    if optimizer._already_has_subject(day_slots, "Math"):
        print("SUCCESS: Math detected in Math 101.")
    else:
        print("FAILED: Math NOT detected in Math 101.")
    
    if not optimizer._already_has_subject(day_slots, "Chemistry"):
        print("SUCCESS: Chemistry not detected.")
    else:
        print("FAILED: Chemistry detected.")

if __name__ == "__main__":
    test_compactness_and_no_repeat()
