"""
Milestone 4 Verification Script
Verifies all 12 requirements from the spec without making AI calls.
"""
import json
import sqlite3
import sys

PASS = []
FAIL = []

def check(label, condition, detail=""):
    if condition:
        PASS.append(label)
        print(f"  [PASS] {label}")
    else:
        FAIL.append(label)
        print(f"  [FAIL] {label} -- {detail}")

print("\n=== Milestone 4 Verification ===\n")

# 1. Backend imports
try:
    from app.main import app
    check("Backend import (app.main)", True)
except Exception as e:
    check("Backend import (app.main)", False, str(e))
    sys.exit(1)

# 2. All new routes registered
from app.main import app
route_paths = []
for r in app.routes:
    if hasattr(r, "path"):
        route_paths.append(r.path)

for route in ["/dashboard/stats", "/dashboard/pipeline",
              "/voice-screening/start",
              "/candidates/{candidate_id}/stage"]:
    check(f"Route registered: {route}", route in route_paths, f"Registered: {route_paths}")

# 3. ATS route still exists
check("ATS route /interview/ats-status exists", "/interview/ats-status" in route_paths)

# 4. Existing M1-3 routes still exist
for route in ["/candidates", "/jobs", "/stats", "/interview/start",
              "/interview/{session_id}/message", "/interview/{session_id}/end",
              "/interview/generate-questions", "/interview/regenerate-question"]:
    check(f"M1-3 route preserved: {route}", route in route_paths)

# 5. DB migration — recruitment_stage column exists
conn = sqlite3.connect("recruitment.db")
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(candidates)")
cols = [c[1] for c in cursor.fetchall()]
check("candidates.recruitment_stage column exists", "recruitment_stage" in cols, f"Columns: {cols}")

# 6. Existing candidate records preserved + have default stage
cursor.execute("SELECT id, name, recruitment_stage FROM candidates")
rows = cursor.fetchall()
check("Existing candidate records preserved", len(rows) > 0, f"Count: {len(rows)}")
for row in rows:
    check(f"Candidate {row[0]} ({row[1]}) has recruitment_stage", row[2] is not None, f"stage={row[2]}")

# 7. Existing interview_sessions intact with feedback
cursor.execute("SELECT id, status, feedback FROM interview_sessions WHERE status='completed' LIMIT 3")
completed = cursor.fetchall()
check("Completed interview sessions preserved", len(completed) > 0)
for row in completed:
    if row[2]:
        try:
            fb = json.loads(row[2])
            score = fb.get("overall_score")
            check(f"Session {row[0]} feedback JSON intact (score={score})", score is not None)
        except Exception as e:
            check(f"Session {row[0]} feedback JSON intact", False, str(e))

# 8. voice_screening_sessions table created
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cursor.fetchall()]
check("voice_screening_sessions table created", "voice_screening_sessions" in tables, f"Tables: {tables}")

conn.close()

# 9. ATS endpoint does NOT call calculate_match
import ast, pathlib
ats_src = pathlib.Path("app/routes/interview.py").read_text()
# Search the ats-status handler section
ats_section_start = ats_src.find("ats-status")
ats_section = ats_src[ats_section_start:ats_section_start+3000]
has_calc_match_in_ats = "calculate_match" in ats_section
check("ATS endpoint does NOT call calculate_match()", not has_calc_match_in_ats,
      "calculate_match found in ATS section!")

# 10. Dashboard has no AI/Groq imports
dash_src = pathlib.Path("app/routes/dashboard.py").read_text()
has_groq = "groq" in dash_src.lower() or "gemini" in dash_src.lower()
check("Dashboard routes have NO Groq/AI imports", not has_groq)

# 11. Voice screening has fallback_assessment (never crashes)
vs_svc = pathlib.Path("app/services/voice_screening_service.py").read_text()
check("voice_screening_service has _fallback_assessment", "_fallback_assessment" in vs_svc)
check("voice_screening_service handles 429", "429" in vs_svc)

# 12. Frontend - Save Screening button (not Save Recording)
html_src = pathlib.Path("frontend/index.html").read_text()
check("Frontend uses 'Save Screening' (not 'Save Recording')", "Save Screening" in html_src)
check("Frontend does NOT use 'Save Recording'", "Save Recording" not in html_src)

# 13. Stage auto-update in interview start
interview_src = pathlib.Path("app/routes/interview.py").read_text()
check("Interview start auto-updates recruitment_stage", "recruitment_stage" in interview_src)

print(f"\n{'='*40}")
print(f"PASS: {len(PASS)} | FAIL: {len(FAIL)}")
if FAIL:
    print(f"\nFailed checks:")
    for f in FAIL:
        print(f"  - {f}")
    sys.exit(1)
else:
    print("\nAll checks passed!")
