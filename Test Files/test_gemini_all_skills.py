from app.services.gemini_skill_service import analyze_all_skills


candidate_data = {
    "skills": [
        "Python",
        "HTML",
        "JavaScript"
    ],

    "education": [
        "B.Tech Computer Science"
    ],

    "experience": [
        "Developed web applications"
    ],

    "projects": [
        "Built a responsive portfolio website using HTML and JavaScript"
    ],

    "certifications": []
}


required_skills = [
    "Python",
    "CSS",
    "JavaScript",
    "SQL"
]


result = analyze_all_skills(
    required_skills,
    candidate_data
)


print("\n===== ALL SKILL ANALYSIS =====")

for skill in result:
    print(skill)