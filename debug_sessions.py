"""
Verify the fix: simulate what the /candidate/{id}/evaluations endpoint would return
using the actual recommendation derivation logic after the fix.
"""
import sqlite3, json

conn = sqlite3.connect('recruitment.db')
c = conn.cursor()

print("=" * 70)
print("INTERVIEW SESSIONS — what /evaluations endpoint will now return")
print("=" * 70)

c.execute("""
    SELECT id, candidate_id, job_id, status, feedback
    FROM interview_sessions
    ORDER BY candidate_id, created_at DESC
""")

seen = set()
for r in c.fetchall():
    cand_id = r[1]
    if cand_id in seen:
        continue  # only latest per candidate
    seen.add(cand_id)

    sid, cand, job, status, fb_raw = r
    print(f"\nCandidate {cand} | Session {sid} | Status: {status}")

    ai_eval = {
        "score": "N/A",
        "recommendation": "Pending / Not Evaluated",
        "interview_status": "Interview Done" if status == "completed" else
                            ("Interview In Progress" if status == "active" else "Interview Not Done")
    }

    if status == "completed" and fb_raw:
        try:
            fb = json.loads(fb_raw)
            raw_score = fb.get("overall_score", "N/A")
            ai_eval["score"] = raw_score
            stored_rec = fb.get("recommendation", "")
            if stored_rec in ("Recommended", "Not Recommended"):
                ai_eval["recommendation"] = stored_rec
            elif raw_score != "N/A":
                score_f = float(raw_score)
                ai_eval["recommendation"] = "Recommended" if score_f >= 6.0 else "Not Recommended"
            else:
                ai_eval["recommendation"] = "Pending / Not Evaluated"
        except Exception as e:
            print(f"  Parse error: {e}")

    print(f"  interview_status: {ai_eval['interview_status']}")
    print(f"  score:            {ai_eval['score']}")
    print(f"  recommendation:   {ai_eval['recommendation']}")

print()
print("=" * 70)
print("VOICE SCREENING SESSIONS — Screened / Not Screened status")
print("=" * 70)

c.execute("""
    SELECT id, candidate_id, job_id, status, assessment
    FROM voice_screening_sessions
    ORDER BY candidate_id, created_at DESC
""")

seen2 = set()
for r in c.fetchall():
    cand_id = r[1]
    if cand_id in seen2:
        continue
    seen2.add(cand_id)

    sid, cand, job, status, a_raw = r
    print(f"\nCandidate {cand} | Session {sid} | Status: {status}")

    voice_status = "Pending"
    if status == "completed" and a_raw:
        try:
            a = json.loads(a_raw)
            comm = float(a.get("communication_score") or 0)
            overall = float(a.get("overall_score") or 0)
            voice_status = "Screened" if (comm >= 5.5 and overall >= 5.0) else "Not Screened"
            print(f"  comm={comm}, overall={overall}")
        except Exception as e:
            print(f"  Parse error: {e}")

    print(f"  voice_status: {voice_status}")

conn.close()
print("\nVerification complete.")
