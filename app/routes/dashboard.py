"""
Dashboard Routes — Milestone 4 Final Redesign
GET /dashboard/analytics — Comprehensive analytics from real DB data (0 LLM calls)
GET /dashboard/stats     — Backwards-compatible summary stats (0 LLM calls)

All metrics are read-only and computed deterministically from SQLite tables:
- candidates
- jobs
- interview_sessions
- voice_screening_sessions
- upload_history
"""

import json
import re
from datetime import datetime
from collections import Counter
from fastapi import APIRouter
from app.database import SessionLocal
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.interview_session import InterviewSession
from app.models.voice_screening_session import VoiceScreeningSession
from app.models.upload_history import UploadHistory
from app.services.voice_screening_service import derive_screening_decision

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)


def _normalize_skill(s: str) -> str:
    if not s:
        return ""
    return re.sub(r"[^a-z0-9+#.\- ]", "", str(s).lower().strip())


def _parse_skills_list(val) -> list:
    """Parse JSON or delimited skills string into a list of normalized skill strings."""
    if not val:
        return []
    if isinstance(val, list):
        items = val
    else:
        try:
            data = json.loads(val)
            if isinstance(data, list):
                items = data
            else:
                items = [data]
        except Exception:
            items = [x.strip() for x in str(val).split(",") if x.strip()]

    result = []
    for item in items:
        if isinstance(item, dict):
            name = item.get("name", "")
            if name:
                result.append(name.strip())
        elif isinstance(item, str) and item.strip():
            result.append(item.strip())
    return result


def _extract_exp_years(exp_val) -> float:
    """Extract experience years from candidate experience field using regex without LLM."""
    if not exp_val:
        return 0.0
    try:
        items = json.loads(exp_val) if isinstance(exp_val, str) and exp_val.strip().startswith("[") else [exp_val]
        text = " ".join(str(i) for i in items).lower()
        match = re.search(r"(\d+(?:\.\d+)?)\s*(?:\+?\s*years?|yrs?)", text)
        if match:
            return float(match.group(1))
        return 1.0 if items else 0.0
    except Exception:
        return 0.0


@router.get("/analytics")
def get_dashboard_analytics():
    """
    Return comprehensive, real project analytics computed strictly from the SQLite database.
    Zero external AI calls. Fast, deterministic, and safe.
    """
    db = SessionLocal()
    try:
        candidates = db.query(Candidate).all()
        jobs = db.query(Job).all()
        interviews = db.query(InterviewSession).all()
        voice_screenings = db.query(VoiceScreeningSession).all()

        total_candidates = len(candidates)
        total_jobs = len(jobs)
        total_interviews = len(interviews)
        total_voice_screenings = len(voice_screenings)

        # -------------------------------------------------------------
        # 1. Interview Sessions Analytics
        # -------------------------------------------------------------
        completed_interviews = [s for s in interviews if s.status == "completed"]
        active_interviews = [s for s in interviews if s.status == "active"]
        
        interview_scores = []
        interview_modes = Counter()
        score_buckets = {"0-2": 0, "2-4": 0, "4-6": 0, "6-8": 0, "8-10": 0}

        for session in interviews:
            interview_modes[session.interview_mode or "technical"] += 1
            if session.feedback:
                try:
                    fb = json.loads(session.feedback)
                    score = fb.get("overall_score")
                    if score is not None and isinstance(score, (int, float)):
                        sc_val = float(score)
                        interview_scores.append(sc_val)
                        if sc_val <= 2.0:
                            score_buckets["0-2"] += 1
                        elif sc_val <= 4.0:
                            score_buckets["2-4"] += 1
                        elif sc_val <= 6.0:
                            score_buckets["4-6"] += 1
                        elif sc_val <= 8.0:
                            score_buckets["6-8"] += 1
                        else:
                            score_buckets["8-10"] += 1
                except Exception:
                    pass

        avg_interview_score = (
            round(sum(interview_scores) / len(interview_scores), 1)
            if interview_scores else None
        )

        # -------------------------------------------------------------
        # 2. Voice Screening Analytics
        #    Screened / Not Screened decision derived deterministically:
        #      SCREENED     = communication_score >= 5.5 AND overall_score >= 5.0
        #      NOT SCREENED = communication_score <  5.5 OR  overall_score <  5.0
        # -------------------------------------------------------------
        completed_voice = [s for s in voice_screenings if s.status == "completed"]
        active_voice = [s for s in voice_screenings if s.status == "active"]

        vs_overall_scores = []
        vs_comm_scores = []
        vs_tech_scores = []
        # New: Screened / Not Screened counts (replaces old Recommended/Consider/Not Recommended)
        vs_decisions = {"Screened": 0, "Not Screened": 0}
        # Map: candidate_id -> voice screening decision for completed sessions
        candidate_vs_decision = {}

        for vs in voice_screenings:
            if vs.assessment and vs.status == "completed":
                try:
                    a = json.loads(vs.assessment)
                    ov = a.get("overall_score")
                    cm = a.get("communication_score")
                    tc = a.get("technical_score")
                    if ov is not None and isinstance(ov, (int, float)) and float(ov) > 0:
                        vs_overall_scores.append(float(ov))
                    if cm is not None and isinstance(cm, (int, float)) and float(cm) > 0:
                        vs_comm_scores.append(float(cm))
                    if tc is not None and isinstance(tc, (int, float)) and float(tc) > 0:
                        vs_tech_scores.append(float(tc))

                    # Deterministic Screened / Not Screened decision
                    decision = derive_screening_decision(a)
                    vs_decisions[decision] += 1
                    # Store per-candidate decision (latest completed session wins)
                    candidate_vs_decision[vs.candidate_id] = decision
                except Exception:
                    pass

        avg_vs_score = (
            round(sum(vs_overall_scores) / len(vs_overall_scores), 1)
            if vs_overall_scores else None
        )
        avg_comm_score = (
            round(sum(vs_comm_scores) / len(vs_comm_scores), 1)
            if vs_comm_scores else None
        )
        avg_tech_score = (
            round(sum(vs_tech_scores) / len(vs_tech_scores), 1)
            if vs_tech_scores else None
        )

        # Screening rate: % of completed screenings that resulted in Screened
        total_completed_vs = len(completed_voice)
        screened_count = vs_decisions["Screened"]
        screening_rate = (
            round(screened_count / total_completed_vs * 100, 1)
            if total_completed_vs > 0 else None
        )

        # -------------------------------------------------------------
        # 3. Top Extracted Candidate Skills (from Real Resumes)
        # -------------------------------------------------------------
        skill_counter = Counter()
        for cand in candidates:
            cand_skills = _parse_skills_list(cand.skills)
            for sk in cand_skills:
                norm = sk.strip()
                if norm and len(norm) > 1:
                    # Clean up composite strings like "Python C++ C"
                    if "  " in norm:
                        subparts = [p.strip() for p in norm.split("  ") if p.strip()]
                        for sp in subparts:
                            skill_counter[sp] += 1
                    else:
                        skill_counter[norm] += 1

        top_skills = [
            {"skill": name, "count": count}
            for name, count in skill_counter.most_common(8)
        ]

        # -------------------------------------------------------------
        # 4. ATS / Matching Analytics (Local Deterministic — 0 LLM Calls)
        # -------------------------------------------------------------
        match_tiers = {
            "Excellent (85-100%)": 0,
            "Strong (70-84%)": 0,
            "Moderate (50-69%)": 0,
            "Low (<50%)": 0
        }
        job_match_summaries = []
        total_evaluations = 0

        if candidates and jobs:
            for job in jobs:
                j_skills = [_normalize_skill(s) for s in _parse_skills_list(job.skills)]
                j_min_exp = job.min_experience or 0
                job_scores = []

                for cand in candidates:
                    c_skills_set = {_normalize_skill(s) for s in _parse_skills_list(cand.skills)}
                    c_exp = _extract_exp_years(cand.experience)

                    matched_skills_count = sum(1 for js in j_skills if js and js in c_skills_set)
                    skill_score = (matched_skills_count / len(j_skills) * 80) if j_skills else 80
                    exp_score = 20 if j_min_exp <= 0 or c_exp >= j_min_exp else (c_exp / j_min_exp * 20)
                    score = round(min(100, max(0, skill_score + exp_score)))

                    job_scores.append(score)
                    total_evaluations += 1

                    if score >= 85:
                        match_tiers["Excellent (85-100%)"] += 1
                    elif score >= 70:
                        match_tiers["Strong (70-84%)"] += 1
                    elif score >= 50:
                        match_tiers["Moderate (50-69%)"] += 1
                    else:
                        match_tiers["Low (<50%)"] += 1

                avg_job_match = round(sum(job_scores) / len(job_scores)) if job_scores else 0
                job_match_summaries.append({
                    "job_id": job.id,
                    "job_title": job.title,
                    "candidate_count": len(candidates),
                    "avg_match": avg_job_match
                })

        # -------------------------------------------------------------
        # 5. Recent Candidates
        # -------------------------------------------------------------
        sorted_candidates = sorted(
            candidates,
            key=lambda c: c.uploaded_at if c.uploaded_at else datetime.min,
            reverse=True
        )

        candidate_iv_done = {
            s.candidate_id for s in completed_interviews
        }
        # Set of candidate_ids with a completed voice screening session
        candidate_vs_done_ids = {v.candidate_id for v in completed_voice}

        recent_candidates = []
        for cand in sorted_candidates[:5]:
            skills_preview = _parse_skills_list(cand.skills)[:4]
            # Determine accurate voice status: Screened / Not Screened / Pending
            if cand.id in candidate_vs_decision:
                voice_status = candidate_vs_decision[cand.id]  # "Screened" or "Not Screened"
            elif cand.id in candidate_vs_done_ids:
                voice_status = "Not Screened"  # completed but no parseable assessment
            else:
                voice_status = "Pending"
            recent_candidates.append({
                "id": cand.id,
                "name": cand.name or "Unnamed Candidate",
                "email": cand.email or "No email provided",
                "skills": skills_preview,
                "uploaded_at": cand.uploaded_at.strftime("%b %d, %Y") if cand.uploaded_at else "Recently",
                "interview_completed": cand.id in candidate_iv_done,
                "voice_completed": cand.id in candidate_vs_done_ids,  # backwards compat
                "voice_status": voice_status  # new: "Screened" / "Not Screened" / "Pending"
            })

        # -------------------------------------------------------------
        # 6. Recent System Activity Timeline (Real DB Timestamps)
        # -------------------------------------------------------------
        activities = []

        for cand in candidates:
            if cand.uploaded_at:
                activities.append({
                    "timestamp": cand.uploaded_at,
                    "formatted_time": cand.uploaded_at.strftime("%b %d, %H:%M"),
                    "type": "resume_upload",
                    "icon": "fa-file-arrow-up",
                    "color": "#ea580c",
                    "title": "Resume Processed",
                    "description": f"Extracted profile for {cand.name or 'Candidate'}"
                })

        for job in jobs:
            if job.created_at:
                activities.append({
                    "timestamp": job.created_at,
                    "formatted_time": job.created_at.strftime("%b %d, %H:%M"),
                    "type": "job_created",
                    "icon": "fa-briefcase",
                    "color": "#6366f1",
                    "title": "Job Role Created",
                    "description": f"Active role: {job.title}"
                })

        for session in interviews:
            t = session.updated_at or session.created_at
            if t and session.status == "completed":
                activities.append({
                    "timestamp": t,
                    "formatted_time": t.strftime("%b %d, %H:%M"),
                    "type": "interview_completed",
                    "icon": "fa-comments",
                    "color": "#10b981",
                    "title": "AI Interview Completed",
                    "description": f"{session.interview_mode.capitalize()} mode session completed"
                })

        for vs in voice_screenings:
            t = vs.updated_at or vs.created_at
            if t and vs.status == "completed":
                # Include the screening decision in the activity description
                decision = candidate_vs_decision.get(vs.candidate_id, "Not Screened")
                decision_text = f"Status: {decision}"
                activities.append({
                    "timestamp": t,
                    "formatted_time": t.strftime("%b %d, %H:%M"),
                    "type": "voice_screening_completed",
                    "icon": "fa-microphone-lines",
                    "color": "#8b5cf6" if decision == "Screened" else "#ef4444",
                    "title": "Voice Screening Completed",
                    "description": f"Preliminary screening assessment · {decision_text}"
                })

        # Sort activities descending by real timestamp
        activities.sort(key=lambda a: a["timestamp"], reverse=True)
        # Drop raw datetime before JSON serialization
        recent_activity_list = [
            {k: v for k, v in a.items() if k != "timestamp"}
            for a in activities[:7]
        ]

        return {
            "overview": {
                "total_candidates": total_candidates,
                "total_jobs": total_jobs,
                "total_interviews": total_interviews,
                "completed_interviews": len(completed_interviews),
                "active_interviews": len(active_interviews),
                "avg_interview_score": avg_interview_score,
                "total_voice_screenings": total_voice_screenings,
                "completed_voice_screenings": len(completed_voice),
                "active_voice_screenings": len(active_voice),
                "avg_voice_score": avg_vs_score,
                "avg_communication_score": avg_comm_score,
                "avg_technical_score": avg_tech_score
            },
            "skills_distribution": top_skills,
            "matching_analytics": {
                "has_data": bool(candidates and jobs),
                "tiers": match_tiers,
                "job_matches": job_match_summaries,
                "total_evaluations": total_evaluations
            },
            "interview_analytics": {
                "status": {
                    "completed": len(completed_interviews),
                    "active": len(active_interviews)
                },
                "score_buckets": score_buckets,
                "modes": dict(interview_modes),
                "total_evaluated": len(interview_scores)
            },
            "voice_screening_analytics": {
                "status": {
                    "completed": len(completed_voice),
                    "active": len(active_voice)
                },
                "decisions": vs_decisions,
                "screening_rate": screening_rate,
                "scores": {
                    "overall": avg_vs_score,
                    "communication": avg_comm_score,
                    "technical": avg_tech_score
                },
                "total_evaluated": len(vs_overall_scores)
            },
            "evaluation_comparison": {
                "ai_interview": {
                    "title": "AI Interview Assistant",
                    "role": "In-Depth Technical & Behavioral Interview",
                    "format": "Interactive AI simulated chat conversation",
                    "total_sessions": total_interviews,
                    "completed_sessions": len(completed_interviews),
                    "avg_score": f"{avg_interview_score} / 10" if avg_interview_score is not None else "N/A"
                },
                "voice_screening": {
                    "title": "Voice Screening",
                    "role": "Preliminary Screening & Spoken Communication",
                    "format": "Browser speech-to-text voice interaction",
                    "total_sessions": total_voice_screenings,
                    "completed_sessions": len(completed_voice),
                    "avg_score": f"{avg_vs_score} / 10" if avg_vs_score is not None else "N/A"
                }
            },
            "recent_candidates": recent_candidates,
            "recent_activity": recent_activity_list
        }

    except Exception as e:
        return {
            "error": str(e),
            "overview": {
                "total_candidates": 0,
                "total_jobs": 0,
                "total_interviews": 0,
                "completed_interviews": 0,
                "active_interviews": 0,
                "avg_interview_score": None,
                "total_voice_screenings": 0,
                "completed_voice_screenings": 0,
                "active_voice_screenings": 0,
                "avg_voice_score": None,
                "avg_communication_score": None,
                "avg_technical_score": None
            },
            "skills_distribution": [],
            "matching_analytics": {
                "has_data": False,
                "tiers": {},
                "job_matches": [],
                "total_evaluations": 0
            },
            "interview_analytics": {
                "status": {"completed": 0, "active": 0},
                "score_buckets": {},
                "modes": {},
                "total_evaluated": 0
            },
            "voice_screening_analytics": {
                "status": {"completed": 0, "active": 0},
                "decisions": {"Screened": 0, "Not Screened": 0},
                "screening_rate": None,
                "scores": {"overall": None, "communication": None, "technical": None},
                "total_evaluated": 0
            },
            "evaluation_comparison": {
                "ai_interview": {
                    "title": "AI Interview Assistant",
                    "role": "In-Depth Technical & Behavioral Interview",
                    "format": "Interactive AI simulated chat conversation",
                    "total_sessions": 0,
                    "completed_sessions": 0,
                    "avg_score": "N/A"
                },
                "voice_screening": {
                    "title": "Voice Screening",
                    "role": "Preliminary Screening & Spoken Communication",
                    "format": "Browser speech-to-text voice interaction",
                    "total_sessions": 0,
                    "completed_sessions": 0,
                    "avg_score": "N/A"
                }
            },
            "recent_candidates": [],
            "recent_activity": []
        }
    finally:
        db.close()


@router.get("/stats")
def get_dashboard_stats():
    """
    Backwards-compatible summary stats endpoint using real data.
    """
    data = get_dashboard_analytics()
    overview = data.get("overview", {})
    vs_recs = data.get("voice_screening_analytics", {}).get("recommendations", {})
    return {
        "total_candidates": overview.get("total_candidates", 0),
        "total_jobs": overview.get("total_jobs", 0),
        "total_interviews": overview.get("total_interviews", 0),
        "completed_interviews": overview.get("completed_interviews", 0),
        "active_interviews": overview.get("active_interviews", 0),
        "average_interview_score": overview.get("avg_interview_score"),
        "total_voice_screenings": overview.get("total_voice_screenings", 0),
        "completed_voice_screenings": overview.get("completed_voice_screenings", 0),
        "avg_voice_score": overview.get("avg_voice_score"),
        "voice_decisions": data.get("voice_screening_analytics", {}).get("decisions", {}),
        "screening_rate": data.get("voice_screening_analytics", {}).get("screening_rate")
    }
