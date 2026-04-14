import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.chart import BarChart, Reference
import io
import json

def classify_grade(total, internal=0, external=0):
    """Categorizes marks into grades."""
    try:
        total = int(total)
        internal = int(internal)
        external = int(external)
    except:
        return "Fail"
        
    # Rule: 50 < internal <= 100 is always PASS
    if 50 < internal <= 100:
        pass
    # Rule: internal <= 50 and external < 18 is FAIL
    elif internal <= 50 and external < 18:
        return "Fail"
    
    if total >= 91: return "Outstanding / Excellent"
    if total >= 81: return "Very Good"
    if total >= 71: return "Good"
    if total >= 61: return "Above Average"
    if total >= 51: return "Average"
    if total >= 41: return "Pass"
    return "Fail"

def generate_excel_report(results):
    """
    Takes a list of student result dictionaries and generates a multi-sheet Excel file.
    Returns: BytesIO object containing the Excel file data.
    """
    with open('last_results_dump.json', 'w') as f:
        json.dump(results, f, indent=4)
        
    valid_results = [r for r in results if r.get('status') in ['Pass', 'Fail']]
    failed_skipped_results = [r for r in results if r.get('status') not in ['Pass']]

    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Sheet 1: All Students
        if results:
            # 1. Collect all unique subject codes/names from valid results
            all_subjects_meta = {} # code -> name
            for r in results:
                if r.get('status') in ['Pass', 'Fail']:
                    for sub_code, sub_data in r.get('subjects', {}).items():
                        if sub_code not in all_subjects_meta or not all_subjects_meta[sub_code]:
                            all_subjects_meta[sub_code] = sub_data.get('name', '')
            
            all_subject_codes = sorted(list(all_subjects_meta.keys()))
            
            df_all = []
            for i, r in enumerate(results):
                res_status = r.get('status')
                
                row = {
                    'SL.No': i + 1,
                    'USN': r.get('usn'),
                    'NAME': r.get('name') if r.get('name') and r.get('name') != "Unknown" else res_status,
                }
                
                backlog_count = 0
                for sub_code in all_subject_codes:
                    if res_status in ['Pass', 'Fail']:
                        sub_data = r.get('subjects', {}).get(sub_code)
                        if sub_data:
                            row[f'{sub_code}_INT'] = sub_data.get('internal', 0)
                            row[f'{sub_code}_EXT'] = sub_data.get('external', 0)
                            row[f'{sub_code}_TOT'] = sub_data.get('total', 0)
                            
                            # Uniformly map PT flags
                            raw_res = sub_data.get('result', '').upper()
                            if raw_res in ['P', 'PASS']: res_flag = 'P'
                            elif raw_res in ['F', 'FAIL']: res_flag = 'F'
                            elif raw_res in ['A', 'ABSENT']: res_flag = 'A'
                            else: res_flag = raw_res
                            
                            row[f'{sub_code}_PT'] = res_flag
                            if res_flag in ['F', 'A']:
                                backlog_count += 1
                        else:
                            row[f'{sub_code}_INT'] = '-'
                            row[f'{sub_code}_EXT'] = '-'
                            row[f'{sub_code}_TOT'] = '-'
                            row[f'{sub_code}_PT'] = '-'
                    else:
                        row[f'{sub_code}_INT'] = '-'
                        row[f'{sub_code}_EXT'] = '-'
                        row[f'{sub_code}_TOT'] = '-'
                        row[f'{sub_code}_PT'] = '-'
                
                row['Grand Total'] = r.get('total_marks', 0) if res_status in ['Pass', 'Fail'] else '-'
                row['No.of B/L'] = backlog_count if res_status in ['Pass', 'Fail'] else '-'
                df_all.append(row)
            
            df = pd.DataFrame(df_all)
            df.to_excel(writer, sheet_name='All Students', index=False)
            
            worksheet = writer.sheets['All Students']
            
            # Insert a top row to build our custom merged headers
            worksheet.insert_rows(1)
            
            # Static columns vertical merge (SL.No, USN, NAME)
            for col_idx, col_name in enumerate(['SL.No', 'USN', 'NAME'], 1):
                worksheet.cell(row=1, column=col_idx, value=col_name)
                worksheet.cell(row=2, column=col_idx, value='') # Clear the leftover pandas flat header
                worksheet.merge_cells(start_row=1, start_column=col_idx, end_row=2, end_column=col_idx)
                
            # Dynamic Subject Headers
            current_col = 4
            for sub_code in all_subject_codes:
                sub_name = all_subjects_meta.get(sub_code, "")
                header_text = f"{sub_code} - {sub_name}" if sub_name else sub_code
                worksheet.cell(row=1, column=current_col, value=header_text)
                worksheet.merge_cells(start_row=1, start_column=current_col, end_row=1, end_column=current_col + 3)
                
                # Rewrite the 2nd row headers gracefully
                worksheet.cell(row=2, column=current_col, value='INT')
                worksheet.cell(row=2, column=current_col+1, value='EXT')
                worksheet.cell(row=2, column=current_col+2, value='TOT')
                worksheet.cell(row=2, column=current_col+3, value='PT')
                
                current_col += 4
                
            # Summary columns vertical merge (Grand Total, No.of B/L)
            for sum_idx, sum_name in enumerate(['Grand Total', 'No.of B/L'], current_col):
                worksheet.cell(row=1, column=sum_idx, value=sum_name)
                worksheet.cell(row=2, column=sum_idx, value='')
                worksheet.merge_cells(start_row=1, start_column=sum_idx, end_row=2, end_column=sum_idx)

            # Styling
            yellow_fill = PatternFill(start_color='FFFFFF00', end_color='FFFFFF00', fill_type='solid')
            thin_border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
            header_font = Font(bold=True)
            
            max_col = worksheet.max_column
            
            # Apply iteration across the newly formatted worksheet
            for row_idx, row in enumerate(worksheet.iter_rows(min_row=1, max_row=worksheet.max_row, min_col=1, max_col=max_col), start=1):
                for cell in row:
                    cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=False)
                    cell.border = thin_border
                    
                if row_idx in [1, 2]:
                    for cell in row:
                        cell.font = header_font
                        cell.fill = PatternFill(start_color='FFF2CC', end_color='FFF2CC', fill_type='solid')
                else:
                    bl_cell_value = row[-1].value
                    if isinstance(bl_cell_value, (int, float)) and bl_cell_value > 0:
                        for cell in row:
                            cell.fill = yellow_fill
                            
            # Auto-adjust column widths roughly
            worksheet.column_dimensions['B'].width = 15 # USN
            worksheet.column_dimensions['C'].width = 25 # Name
            
        else:
            pd.DataFrame(columns=['USN', 'Message']).to_excel(writer, sheet_name='All Students', index=False)

        # Sheet 2: Subject-wise Pass % (MOVED TO 2nd)
        if valid_results:
            subject_stats = {}
            grade_ranges = [
                "Outstanding / Excellent", "Very Good", "Good", 
                "Above Average", "Average"
            ]
            
            for r in valid_results:
                for sub_code, sub_data in r.get('subjects', {}).items():
                    if sub_code not in subject_stats:
                        subject_stats[sub_code] = {
                            'Name': sub_data.get('name', ''),
                            'Appeared': 0, 
                            'Passed': 0,
                            'Outstanding / Excellent': 0,
                            'Very Good': 0,
                            'Good': 0,
                            'Above Average': 0,
                            'Average': 0,
                            'Pass': 0,
                            'Fail': 0
                        }
                    
                    subject_stats[sub_code]['Appeared'] += 1
                    res_flag = sub_data.get('result', '').upper()
                    if res_flag in ['P', 'PASS']:
                        subject_stats[sub_code]['Passed'] += 1
                    
                    # Grade breakdown
                    grade = classify_grade(sub_data.get('total', 0), sub_data.get('internal', 0), sub_data.get('external', 0))
                    if grade in subject_stats[sub_code]:
                        subject_stats[sub_code][grade] += 1
            
            pass_percents = []
            for sub_code, stats in subject_stats.items():
                p_percent = round((stats['Passed'] / stats['Appeared']) * 100, 2) if stats['Appeared'] > 0 else 0
                row = {
                    'Subject Code': sub_code,
                    'Subject Name': stats['Name'],
                    'Appeared': stats['Appeared'],
                    'Passed': stats['Passed'],
                }
                # Add grade columns
                for gr in grade_ranges:
                    row[gr] = stats[gr]
                
                # Move Pass Percentage to the end
                row['Pass Percentage'] = p_percent
                pass_percents.append(row)
            
            df_subs = pd.DataFrame(pass_percents)
            if not df_subs.empty:
                # Sort by Passed students in decreasing order
                df_subs = df_subs.sort_values(by='Passed', ascending=False)
                df_subs.to_excel(writer, sheet_name='Subject-wise Pass %', index=False)
                
                # Create Visualization
                ws = writer.sheets['Subject-wise Pass %']
                chart = BarChart()
                chart.type = "col"
                chart.style = 10
                chart.title = "Appeared vs Passed Students per Subject"
                chart.y_axis.title = 'Total Students'
                chart.x_axis.title = 'Subject Code'
                
                # Reference data: Appeared (3) and Passed (4) columns
                data = Reference(ws, min_col=3, min_row=1, max_row=len(df_subs)+1, max_col=4)
                # Reference categories: Subject Code column (1st column)
                cats = Reference(ws, min_col=1, min_row=2, max_row=len(df_subs)+1)
                
                chart.add_data(data, titles_from_data=True)
                chart.set_categories(cats)
                # Keep legend enabled to distinguish between Appeared and Passed
                
                # Add chart to the sheet (Column O)
                ws.add_chart(chart, "O2")
            else:
                pd.DataFrame(columns=['Subject Code']).to_excel(writer, sheet_name='Subject-wise Pass %', index=False)
        else:
             pd.DataFrame(columns=['Subject Code']).to_excel(writer, sheet_name='Subject-wise Pass %', index=False)

        # Sheet 3: Top 5 Toppers (MOVED TO 3rd)
        if valid_results:
            try:
                # We need to compute total marks and percentage natively here since they aren't uniquely extracted dynamically
                flat_data = []
                for r in valid_results:
                    percentage = round((r.get('total_marks', 0) / r.get('max_marks', 1)) * 100, 2) if r.get('max_marks') else 0
                    flat_data.append({
                        'USN': r.get('usn'),
                        'Name': r.get('name'),
                        'Total Marks': r.get('total_marks', 0),
                        'Percentage': percentage
                    })
                df_toppers = pd.DataFrame(flat_data).sort_values(by=['Total Marks'], ascending=[False]).head(5)
                df_toppers.to_excel(writer, sheet_name='Top 5 Toppers', index=False)
            except Exception as e:
                pd.DataFrame([{'Error': str(e)}]).to_excel(writer, sheet_name='Top 5 Toppers', index=False)
        else:
            pd.DataFrame(columns=['USN', 'Name']).to_excel(writer, sheet_name='Top 5 Toppers', index=False)

        # Sheet 4: Failed / Skipped Students (Replaced purely with Backlog summary)
        if valid_results:
            failed_students = []
            for r in valid_results:
                bl_count = sum(1 for s in r.get('subjects', {}).values() if s.get('result', '').upper() in ['F', 'A', 'FAIL', 'ABSENT'])
                if bl_count > 0:
                    failed_students.append({
                        'USN': r.get('usn'),
                        'Name': r.get('name', 'N/A'),
                        'No.of B/L': bl_count
                    })
            if failed_students:
                pd.DataFrame(failed_students).to_excel(writer, sheet_name='Failed & Skipped', index=False)
            else:
                 pd.DataFrame([{'Message': "No Backlogs Found!"}]).to_excel(writer, sheet_name='Failed & Skipped', index=False)
        else:
            pd.DataFrame(columns=['USN', 'Status']).to_excel(writer, sheet_name='Failed & Skipped', index=False)
    
    output.seek(0)
    return output
