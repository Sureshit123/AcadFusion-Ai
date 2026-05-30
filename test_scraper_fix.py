#!/usr/bin/env python
from scraper import parse_vtu_html

with open('latest_result.html', 'r', encoding='utf-8') as f:
    html = f.read()

result = parse_vtu_html('2BL21IS034', html)
print(f'Student Name: {result["name"]}')
print(f'USN: {result["usn"]}')
print(f'Status: {result["status"]}')
print(f'Total Marks: {result["total_marks"]}')
print(f'Number of Subjects: {len(result["subjects"])}')
print(f'\nFirst Subject: {list(result["subjects"].items())[0] if result["subjects"] else "None"}')
