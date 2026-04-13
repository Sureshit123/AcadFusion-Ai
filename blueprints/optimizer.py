import io
import pandas as pd
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, send_file
from models.database import db_instance
import random

optimizer_bp = Blueprint('optimizer', __name__)

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
SLOTS = ["09:00-10:00", "10:00-11:00", "11:15-12:15", "12:15-01:15", "02:15-03:15", "03:15-04:15", "04:15-05:15"]

class GreedyOptimizer:
    def __init__(self, raw_grids, max_physical_labs=3):
        self.raw_grids = raw_grids # { '3': grid, ... }
        self.max_physical_labs = max_physical_labs
        self.semesters = list(raw_grids.keys())
        
        # Output structure
        self.optimized_grids = {sem: [[None for _ in range(len(SLOTS))] for _ in range(6)] for sem in self.semesters}
        self.teacher_usage = [[set() for _ in range(len(SLOTS))] for _ in range(6)]
        self.lab_usage = [[0 for _ in range(len(SLOTS))] for _ in range(6)]

    def optimize(self, max_attempts=200):
        self.stats = {"teacher_busy": {}, "lab_room_full": 0, "no_slots": 0}
        self.best_result = None
        self.best_unplaced_count = float('inf')
        self.best_unplaced_items = []

        # Pre-check: Calculate total hours requested for each teacher
        workload = {}
        for sem, grid in self.raw_grids.items():
            for d in range(6):
                for s in range(len(SLOTS)):
                    cell = grid[d][s]
                    if not cell or cell == '-': continue
                    if isinstance(cell, dict):
                        teachers = []
                        if cell.get('type') == 'lab':
                            if cell.get('part') == 2: continue
                            teachers = cell.get('teachers', '').split(', ')
                            if cell.get('b2_teachers'): teachers += cell.get('b2_teachers', '').split(', ')
                            hrs = 2
                        else:
                            teachers = [cell.get('teacher')] if cell.get('teacher') else []
                            hrs = 1
                        
                        for t in set(teachers):
                            if t and t != 'N/A':
                                workload[t] = workload.get(t, 0) + hrs

        for attempt in range(max_attempts):
            result, unplaced = self._attempt_optimize()
            if not unplaced:
                print(f"Optimizer Debug: Solution found on attempt {attempt + 1}")
                return result, None, []
            
            if len(unplaced) < self.best_unplaced_count:
                self.best_unplaced_count = len(unplaced)
                self.best_result = result
                self.best_unplaced_items = unplaced

        # Optimization failed - return best effort
        top_teacher = max(self.stats["teacher_busy"].items(), key=lambda x: x[1], default=("None", 0))
        t_name = top_teacher[0]
        hrs_requested = workload.get(t_name, 0)
        
        diag = f"Optimization reached a limit. Most constrained teacher: '{t_name}' ({hrs_requested} hrs total). "
        
        return self.best_result, diag, self.best_unplaced_items

    def _attempt_optimize(self):
        # Reset trackers
        optimized_grids = {sem: [[None for _ in range(len(SLOTS))] for _ in range(6)] for sem in self.semesters}
        teacher_usage = [[set() for _ in range(len(SLOTS))] for _ in range(6)]
        lab_usage = [[0 for _ in range(len(SLOTS))] for _ in range(6)]
        
        items_to_place = []
        for sem, grid in self.raw_grids.items():
            for d in range(6):
                for s in range(len(SLOTS)):
                    cell = grid[d][s]
                    if not cell or cell == '-': continue
                    if isinstance(cell, dict) and cell.get('type') == 'fixed':
                        optimized_grids[sem][d][s] = cell
                        t = cell.get('teacher')
                        if t and t != 'N/A': teacher_usage[d][s].add(t)
                    else:
                        if isinstance(cell, dict) and cell.get('type') == 'lab' and cell.get('part') == 2:
                            continue
                        item = {"sem": sem, "original_day": d, "original_slot": s}
                        if isinstance(cell, str):
                            item.update({"type": "subject", "name": cell, "teacher": "TBD"})
                        else:
                            item.update(cell)
                        items_to_place.append(item)

        random.shuffle(items_to_place)
        
        unplaced_items = []
        
        # Helper to check availability within THIS attempt's usage
        def _check_free(ts, is_lab, day, slot):
            if day == 5 and slot > 3: return False
            if day == 5 and (slot+1) > 3: return False
            for t in ts:
                if t in teacher_usage[day][slot]:
                    self.stats["teacher_busy"][t] = self.stats["teacher_busy"].get(t, 0) + 1
                    return False
            req = 2 if is_lab and any(i.get('parallel') for i in items_to_place if i.get('name') == lab.get('name')) else 1 # Simple heuristic
            if lab_usage[day][slot] + req > self.max_physical_labs:
                self.stats["lab_room_full"] += 1
                return False
            return True

        # Place Labs
        labs = [i for i in items_to_place if i['type'] == 'lab']
        for lab in labs:
            placed = False
            p_starts = [0, 2, 4, 5]
            days = list(range(6))
            random.shuffle(days)
            t_all = list(set((lab['teachers'].split(', ') if isinstance(lab['teachers'], str) else []) + (lab.get('b2_teachers', '').split(', ') if lab.get('b2_teachers') else [])))
            for d in days:
                for s in p_starts:
                    if optimized_grids[lab['sem']][d][s] is None and optimized_grids[lab['sem']][d][s+1] is None:
                        # Inline check
                        free = True
                        for t in t_all:
                            if t in teacher_usage[d][s] or t in teacher_usage[d][s+1]: free = False; break
                        if d == 5 and (s+1) > 3: free = False
                        if lab_usage[d][s] + (2 if lab.get('parallel') else 1) > self.max_physical_labs: free = False
                        
                        if free:
                            optimized_grids[lab['sem']][d][s] = {**lab, "part": 1}
                            optimized_grids[lab['sem']][d][s+1] = {**lab, "part": 2}
                            for t in t_all:
                                teacher_usage[d][s].add(t)
                                teacher_usage[d][s+1].add(t)
                            rooms = 2 if lab.get('parallel') else 1
                            lab_usage[d][s] += rooms
                            lab_usage[d][s+1] += rooms
                            placed = True; break
                if placed: break
            if not placed: unplaced_items.append(lab)

        # Place Subjects
        subs = [i for i in items_to_place if i['type'] == 'subject']
        for sub in subs:
            placed = False
            for s in range(len(SLOTS)):
                days = list(range(6)); random.shuffle(days)
                for d in days:
                    if optimized_grids[sub['sem']][d][s] is None:
                        t_sub = [sub['teacher']] if sub.get('teacher') else []
                        free = True
                        for t in t_sub:
                            if t in teacher_usage[d][s]: free = False; break
                        if d == 5 and s > 3: free = False
                        
                        if free:
                            optimized_grids[sub['sem']][d][s] = sub
                            for t in t_sub: teacher_usage[d][s].add(t)
                            placed = True; break
                if placed: break
            if not placed: unplaced_items.append(sub)

        return optimized_grids, unplaced_items

    def _is_free(self, teachers, needs_parallel, day, slot, sem, sub_name=None):
        if day == 5 and slot > 3: return False
        if day == 5 and (slot+1) > 3: return False
        
        # Rule: One class of one subject per day per semester
        if sub_name:
            sub_clean = sub_name.split(' ')[0].upper() # Match by first word (e.g. "Maths")
            for s in range(len(SLOTS)):
                existing = self.optimized_grids[sem][day][s]
                if existing and isinstance(existing, dict):
                    ext_name = existing.get('name', '').split(' ')[0].upper()
                    if ext_name == sub_clean:
                        return False

        for t in teachers:
            if t in self.teacher_usage[day][slot]:
                self.stats["teacher_busy"][t] = self.stats["teacher_busy"].get(t, 0) + 1
                return False
        
        required_rooms = 2 if needs_parallel else 1
        if self.lab_usage[day][slot] + required_rooms > self.max_physical_labs:
            self.stats["lab_room_full"] += 1
            return False
            
        return True

    def _place_lab(self, lab):
        potential_starts = [0, 2, 4, 5]
        days = list(range(6))
        random.shuffle(days)
        
        # Collect all teachers involved in a parallel pair
        t_b1 = lab['teachers'].split(', ') if isinstance(lab['teachers'], str) else []
        t_b2 = lab.get('b2_teachers', '').split(', ') if lab.get('b2_teachers') else []
        all_teachers = list(set(t_b1 + t_b2))
        needs_parallel = True if lab.get('parallel') else False
        
        for d in days:
            for s in potential_starts:
                if self.optimized_grids[lab['sem']][d][s] is None and self.optimized_grids[lab['sem']][d][s+1] is None:
                    if self._is_free(all_teachers, needs_parallel, d, s, lab['sem'], lab['name']) and self._is_free(all_teachers, needs_parallel, d, s+1, lab['sem'], lab['name']):
                        self.optimized_grids[lab['sem']][d][s] = {**lab, "part": 1}
                        self.optimized_grids[lab['sem']][d][s+1] = {**lab, "part": 2}
                        for t in all_teachers:
                            self.teacher_usage[d][s].add(t)
                            self.teacher_usage[d][s+1].add(t)
                        rooms = 2 if needs_parallel else 1
                        self.lab_usage[d][s] += rooms
                        self.lab_usage[d][s+1] += rooms
                        return True
        return False

    def _place_subject(self, sub):
        teachers = [sub['teacher']] if sub.get('teacher') else []
        for s in range(len(SLOTS)):
            days = list(range(6))
            random.shuffle(days)
            for d in days:
                if self.optimized_grids[sub['sem']][d][s] is None:
                    if self._is_free(teachers, False, d, s, sub['sem'], sub['name']):
                        self.optimized_grids[sub['sem']][d][s] = sub
                        for t in teachers: self.teacher_usage[d][s].add(t)
                        return True
        return False

@optimizer_bp.route('/optimizer')
def index():
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    return render_template('timetable/optimizer.html', days=DAYS, slots=SLOTS)

@optimizer_bp.route('/api/optimize_excel', methods=['POST'])
def optimize_excel():
    if 'file' not in request.files: return jsonify({'error': 'No file uploaded'}), 400
    file = request.files['file']
    
    try:
        xl = pd.ExcelFile(file)
        raw_grids = {}
        sem_sheets = [s for s in xl.sheet_names if s.startswith('Semester_') or s.lower().startswith('sem')]
        
        if not sem_sheets:
            print("Optimizer Debug: No semester sheets found.")
            return jsonify({'error': 'No valid "Semester_X" sheets found in the Excel file.'}), 400

        for sheet in sem_sheets:
            try:
                sem = sheet.split('_')[1] if '_' in sheet else sheet.replace('Semester', '').replace('Sem', '').strip()
                df = pd.read_excel(file, sheet_name=sheet)
                if df.empty or len(df.columns) < 2: continue
                grid = [[None for _ in range(len(SLOTS))] for _ in range(6)]
                for r_idx, row in df.iterrows():
                    if r_idx >= 6: break
                    s_map = 0
                    for c_idx in range(1, len(df.columns)):
                        if s_map >= len(SLOTS): break
                        col_name = str(df.columns[c_idx]).upper()
                        if col_name in ['RECESS', 'LUNCH', 'BREAK']: continue
                        val = row.iloc[c_idx]
                        if pd.isna(val) or str(val).strip() in ['-', '', 'nan']: 
                            grid[r_idx][s_map] = None
                        else:
                            grid[r_idx][s_map] = parse_cell_string(str(val))
                        s_map += 1
                raw_grids[sem] = grid
            except Exception as sheet_err:
                print(f"Optimizer Debug: Error parsing sheet {sheet}: {sheet_err}")
                continue

        if not raw_grids:
            print("Optimizer Debug: raw_grids is empty after parsing.")
            return jsonify({'error': 'Failed to extract any valid data.'}), 400
            
        opt = GreedyOptimizer(raw_grids)
        opt_grids, err, unplaced = opt.optimize()
        
        return jsonify({
            'success': True, 
            'grids': opt_grids, 
            'error': err,
            'unplaced': unplaced
        })
    except Exception as e:
        print(f"Excel Optimizer Error: {e}")
        return jsonify({'error': f"Excel Error: {str(e)}"}), 500

def parse_cell_string(s):
    if '(' not in s: return {"type": "fixed", "name": s, "teacher": "N/A"}
    
    # Handle parallel labs: "React (B1: T1) & ML (B2: T2)"
    if ' & ' in s:
        try:
            parts = s.split(' & ')
            # Part 1: B1
            sub1 = parts[0].split('(')[0].strip()
            rest1 = parts[0].split('(')[1].replace(')', '')
            teachers1 = rest1.split(': ')[1]
            # Part 2: B2
            sub2 = parts[1].split('(')[0].strip()
            rest2 = parts[1].split('(')[1].replace(')', '')
            teachers2 = rest2.split(': ')[1]
            return {"type": "lab", "name": sub1, "batch": "B1", "teachers": teachers1, 
                    "parallel": sub2, "b2_teachers": teachers2}
        except: pass

    # Default Lab/Subject
    try:
        name = s.split('(')[0].strip()
        rest = s.split('(')[1].replace(')', '')
        if ': ' in rest: # Lab
            batch = rest.split(': ')[0]
            teachers = rest.split(': ')[1]
            return {"type": "lab", "name": name, "batch": batch, "teachers": teachers}
        else: # Subject
            return {"type": "subject", "name": name, "teacher": rest}
    except: return {"type": "fixed", "name": s, "teacher": "N/A"}

@optimizer_bp.route('/api/optimize_text', methods=['POST'])
def optimize_text():
    try:
        data = request.json
        text = data.get('text', '')
        if not text.strip(): return jsonify({'error': 'Empty text'}), 400
        raw_grids = {}
        
        current_sem = "Unknown"
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        
        for line in lines:
            # 1. Detect Semester Header
            if 'Semester' in line or 'Sem' in line:
                import re
                m = re.search(r'(?:Semester|Sem)\s*(\d+)', line, re.I)
                if m: current_sem = m.group(1)
                continue
            
            # 2. Skip Table Header Day/Time
            if 'Day/Time' in line or '09:00' in line: continue
            
            # 3. Parse Row: "Monday MATHS OS RECESS OOPS DDCO LUNCH..."
            # This is complex because spaces are used both as delimiters and in names
            # We try to find Days first
            day_found = None
            for d in DAYS:
                if line.startswith(d):
                    day_found = d
                    line = line[len(d):].strip()
                    break
            
            if not day_found: continue
            
            # Simplified heuristic: Split by large gaps or known keywords
            items = []
            # Remove keywords like RECESS/LUNCH/BREAK
            clean_line = line.replace('RECESS', ' | ').replace('LUNCH', ' | ').replace('-', ' | ')
            # Split by '|' or double spaces
            raw_items = [i.strip() for i in clean_line.split('|') if i.strip()]
            
            # Assign to slots (assuming standard sequence)
            d_idx = DAYS.index(day_found)
            if current_sem not in raw_grids:
                raw_grids[current_sem] = [[None for _ in range(len(SLOTS))] for _ in range(6)]
            
            s_idx = 0
            for item in raw_items:
                if s_idx >= len(SLOTS): break
                # Extract Subject/Teacher
                # Heuristic: "MATHS M. Y Dhange" -> Subject=MATHS, Teacher=rest
                parts = item.split(' ', 1)
                name = parts[0]
                teacher = parts[1] if len(parts) > 1 else "TBD"
                
                raw_grids[current_sem][d_idx][s_idx] = {"type": "subject", "name": name, "teacher": teacher}
                s_idx += 1
            
        if not raw_grids:
             return jsonify({'error': 'Could not parse any structured data. Please check the format.'}), 400

        opt = GreedyOptimizer(raw_grids)
        opt_grids, err, unplaced = opt.optimize()
        
        return jsonify({
            'success': True, 
            'grids': opt_grids, 
            'error': err,
            'unplaced': unplaced
        })
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500
