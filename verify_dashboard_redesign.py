import json
import time

print("=== 1. VERIFY BACKEND ROUTE HANDLERS ===")
from app.routes.dashboard import get_dashboard_analytics, get_dashboard_stats
from app.routes.interview import get_ats_candidates

# Test get_dashboard_analytics
t0 = time.time()
analytics = get_dashboard_analytics()
t_elapsed = (time.time() - t0) * 1000
print(f"get_dashboard_analytics() executed in {t_elapsed:.2f}ms")

assert "overview" in analytics, "overview key missing"
assert "matching_analytics" in analytics, "matching_analytics key missing"
assert "skills_distribution" in analytics, "skills_distribution key missing"
assert "interview_analytics" in analytics, "interview_analytics key missing"
assert "voice_screening_analytics" in analytics, "voice_screening_analytics key missing"
assert "evaluation_comparison" in analytics, "evaluation_comparison key missing"
assert "recent_candidates" in analytics, "recent_candidates key missing"
assert "recent_activity" in analytics, "recent_activity key missing"

print("Overview stats:", analytics["overview"])
print("Matching tiers:", analytics["matching_analytics"]["tiers"])
print("Top skills:", [s["skill"] for s in analytics["skills_distribution"]])

# Test get_dashboard_stats
stats = get_dashboard_stats()
assert "total_candidates" in stats, "total_candidates missing"
print("Backwards-compatible stats:", stats)

# Test get_ats_candidates (/interview/ats-status)
ats = get_ats_candidates()
assert "candidates" in ats, "candidates key missing"
print("ATS candidate records count:", len(ats["candidates"]))

print("\n=== 2. VERIFY FRONTEND HTML STRUCTURE ===")
with open("frontend/index.html", "r", encoding="utf-8") as f:
    html = f.read()

assert "cdn.jsdelivr.net/npm/chart.js" in html, "Chart.js script missing"
assert 'data-page="dashboardPage"' in html, "dashboardPage menu item missing"
assert html.find('data-page="dashboardPage"') < html.find('data-page="resumePage"'), "Dashboard is not 1st in sidebar"
assert 'id="matchingChart"' in html, "matchingChart canvas missing"
assert 'id="skillsChart"' in html, "skillsChart canvas missing"
assert 'id="interviewScoreChart"' in html, "interviewScoreChart canvas missing"
assert 'id="voiceRecChart"' in html, "voiceRecChart canvas missing"
assert 'id="dashboardEvalComparison"' in html, "dashboardEvalComparison missing"
assert "pipeline-container" not in html, "Old pipeline container found in HTML"

vs_ids = [
    "vsCandidate", "vsJob", "vsStartBtn", "vsStopBtn", "vsSaveBtn",
    "vsStatusDot", "vsStatusText", "vsTtsEnabled", "vsQuestionBox",
    "vsCurrentQuestion", "vsTranscriptContent", "vsAssessmentPanel",
    "vsAssessmentContent", "vsVisualizerBox"
]
for el_id in vs_ids:
    assert f'id="{el_id}"' in html, f"Missing element ID: {el_id}"

print("Voice Screening layout and element IDs verified intact.")
print("HTML structure verified: Dashboard is #1 item in sidebar, Chart.js included, all chart containers present, generic pipeline removed.")

print("\n=== ALL AUTOMATED CHECKS PASSED SUCCESSFULLY ===")
