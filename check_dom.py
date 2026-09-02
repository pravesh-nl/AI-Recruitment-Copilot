import pathlib, re

html = pathlib.Path('frontend/index.html').read_text(encoding='utf-8')
js = pathlib.Path('frontend/script.js').read_text(encoding='utf-8')
css = pathlib.Path('frontend/style.css').read_text(encoding='utf-8')

# Verify sections are inside main
main_match = re.search(r'<main[^>]*>(.*?)</main>', html, re.DOTALL)
assert main_match, '<main> not found!'
main_content = main_match.group(1)

for section_id in ['resumePage', 'candidatesPage', 'jobsPage', 'matchingPage', 'interviewPage', 'dashboardPage', 'voiceScreeningPage']:
    assert f'id="{section_id}"' in main_content, f'{section_id} is NOT inside <main>!'
    print(f'Verified: {section_id} is inside <main>')

# Verify Voice Screening controls exist in HTML
for vs_el in ['vsCandidate', 'vsJob', 'vsStartBtn', 'vsStopBtn', 'vsSaveBtn', 'vsStatusDot', 'vsStatusText', 'vsTtsEnabled', 'vsCurrentQuestion', 'vsTranscriptContent', 'vsAssessmentPanel']:
    assert f'id="{vs_el}"' in html, f'Missing ID: {vs_el}'
    print(f'Verified element ID: {vs_el}')

print('\nALL FRONTEND DOM & STRUCTURE CHECKS PASSED!')
