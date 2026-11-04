import re
import os

designs = [
    ('01_overview.html', 'Overview / Dashboard'),
    ('02_student_directory.html', 'Student Directory'),
    ('03_student_profile.html', 'Student Profile'),
    ('04_support_cases.html', 'Support Cases & Interventions'),
    ('05_warning_review.html', 'Early-Warning Review'),
    ('06_reports_analytics.html', 'Reports & Analytics'),
    ('07_data_import.html', 'Data Import & Quality'),
]

for fname, label in designs:
    p = os.path.join('reference_designs', fname)
    with open(p, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Extract any headline classes
    headlines = re.findall(r'<[^>]*class="[^"]*(?:headline-[a-z]+)[^"]*"[^>]*>(.*?)</[^>]+>', html, re.DOTALL)
    clean_headlines = [re.sub(r'<[^>]+>', '', h).strip() for h in headlines if re.sub(r'<[^>]+>', '', h).strip()][:5]
    
    # Extract buttons
    buttons = re.findall(r'<button[^>]*>(.*?)</button>', html, re.DOTALL)
    clean_buttons = [re.sub(r'<[^>]+>', '', b).strip() for b in buttons if re.sub(r'<[^>]+>', '', b).strip()][:6]
    
    # Extract inputs/selects
    inputs = len(re.findall(r'<input', html))
    selects = len(re.findall(r'<select', html))
    
    print(f"=== {fname} ({label}) ===")
    print(f"  Headlines: {clean_headlines}")
    print(f"  Key Buttons: {clean_buttons}")
    print(f"  Inputs: {inputs}, Selects: {selects}")
