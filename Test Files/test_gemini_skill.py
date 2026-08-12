from app.services.gemini_skill_service import analyze_skill_evidence


candidate_data = {
    "skills": [
        "Python",
        "JavaScript",
        "HTML",
        "CSS"
    ],
    "education": [
        "B.Tech Computer Science"
    ],

    "experience": [
        "Software development internship"
    ],

    "projects": [
        "Built a machine learning model for customer churn prediction using Python."
    ],

    "certifications": []
}


result = analyze_skill_evidence(
    "CSS",
    candidate_data
)

print("\n===== SKILL ANALYSIS =====")
print(result)