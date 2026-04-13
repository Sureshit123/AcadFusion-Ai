import traceback
from processor import generate_excel_report

results = [
    {
        'usn':'123',
        'name':'abc',
        'status':'Pass',
        'subjects': {'CS1': {'internal':10, 'external':20, 'total':30, 'result':'P'}},
        'total_marks':30,
        'max_marks':100
    }
]
try:
    generate_excel_report(results)
    print('SUCCESS')
except Exception as e:
    print('ERROR:')
    traceback.print_exc()
