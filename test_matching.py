import json

from app.database import SessionLocal
from app.models.candidate import Candidate
from app.models.job import Job
from app.services.matching import (
    calculate_match,
    generate_skill_gap
)
from app.services.matching import calculate_match


db = SessionLocal()

try:

    # --------------------------------------------------------
    # Get latest job
    # --------------------------------------------------------

    job = (
        db.query(Job)
        .order_by(Job.id.desc())
        .first()
    )

    if not job:
        print("No job found in database.")
        exit()

    print("\n==============================")
    print("JOB")
    print("==============================")

    print("Title:", job.title)
    print("Required Experience:", job.min_experience)
    print("Skills:", job.skills)

    # --------------------------------------------------------
    # Get candidates
    # --------------------------------------------------------

    candidates = (
        db.query(Candidate)
        .order_by(Candidate.id.asc())
        .all()
    )

    if not candidates:
        print("\nNo candidates found.")
        exit()

    # --------------------------------------------------------
    # Calculate matches
    # --------------------------------------------------------

    results = []

    for candidate in candidates:

        result = calculate_match(
            candidate,
            job
        )
        gap = generate_skill_gap(result)

        print("\nSkill Gap Analysis:")

        print("Has Skill Gap:", gap["has_skill_gap"])

        print("Missing Skills:")
        for skill in gap["missing_skills"]:
            print("-", skill["name"])

        print("Recommendations:")
        for recommendation in gap["recommendations"]:
            print("-", recommendation)

        results.append(result)

    # --------------------------------------------------------
    # Sort highest first
    # --------------------------------------------------------

    results.sort(
        key=lambda x: x["match_score"],
        reverse=True
    )

    # --------------------------------------------------------
    # Display
    # --------------------------------------------------------

    print("\n==============================")
    print("MATCHING RESULTS")
    print("==============================")

    for result in results:

        print("\n--------------------------------")
        print("Candidate:", result["candidate_name"])
        print("Score:", result["match_score"])
        print("Level:", result["match_level"])
        print(
            "Experience:",
            result["candidate_experience"],
            "/ Required:",
            result["required_experience"]
        )

        print("\nMatched Skills:")

        for skill in result["matched_skills"]:

            print(
                " ",
                skill["name"],
                "| Status:",
                skill.get("status"),
                "| Level:",
                skill.get("candidate_level"),
                "| Confidence:",
                skill.get("confidence")
            )

        print("\nMissing Skills:")

        for skill in result["missing_skills"]:

            print(
                " ",
                skill["name"],
                "| Required:",
                skill["required_level"],
                "| Status:",
                skill.get("status")
            )

finally:

    db.close()