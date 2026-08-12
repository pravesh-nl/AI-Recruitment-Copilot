/* ==========================================
   AI Recruitment Copilot
   script.js - Part 1
========================================== */

const API = "http://127.0.0.1:8000";

// ----------------------------
// DOM Elements
// ----------------------------
const resumeInput = document.getElementById("resumeInput");
const browseBtn = document.getElementById("browseBtn");
const uploadBtn = document.getElementById("uploadBtn");

const selectedFiles = document.getElementById("selectedFiles");

const progressFill = document.getElementById("progressFill");
const progressStatus = document.getElementById("progressStatus");

const resumeProcessed = document.getElementById("resumeProcessed");
const parsingAccuracy = document.getElementById("parsingAccuracy");
const profilesCreated = document.getElementById("profilesCreated");

const candidateInfo = document.getElementById("candidateInfo");
const candidateTable = document.getElementById("candidateTable");

const loaderOverlay = document.getElementById("loaderOverlay");

const uploadBox = document.querySelector(".upload-area");



// ----------------------------
// Browse Button
// ----------------------------
browseBtn.addEventListener("click", function () {
    resumeInput.click();
});

resumeInput.addEventListener("change", function () {

    console.log("Files:", resumeInput.files);

    showSelectedFiles(resumeInput.files);

});

// ----------------------------
// File Selection
// ----------------------------


// ----------------------------
// Drag & Drop
// ----------------------------
uploadBox.addEventListener("dragover", (e) => {
    e.preventDefault();
    uploadBox.classList.add("dragging");
});

uploadBox.addEventListener("dragleave", () => {
    uploadBox.classList.remove("dragging");
});

uploadBox.addEventListener("drop", (e) => {

    e.preventDefault();

    uploadBox.classList.remove("dragging");

    resumeInput.files = e.dataTransfer.files;

    showSelectedFiles(resumeInput.files);

});

// ----------------------------
// Show Selected Files
// ----------------------------
function showSelectedFiles(files) {

    selectedFiles.innerHTML = "";

    if (files.length === 0) {

        selectedFiles.innerHTML =
            "<p>No file selected</p>";

        return;
    }

    Array.from(files).forEach((file, index) => {

        const div = document.createElement("div");

        div.className = "file-item";

        div.innerHTML = `
            <i class="fa-solid fa-file-lines"></i>

            <span class="file-name">
                ${file.name}
            </span>

            <button
                type="button"
                class="remove-file-btn"
                title="Remove file"
            >
                <i class="fa-solid fa-xmark"></i>
            </button>
        `;

        const removeBtn =
            div.querySelector(".remove-file-btn");

        removeBtn.addEventListener("click", () => {

            removeSelectedFile(index);

        });

        selectedFiles.appendChild(div);

    });

}
function removeSelectedFile(index) {

    const files = Array.from(resumeInput.files);

    files.splice(index, 1);

    const dataTransfer = new DataTransfer();

    files.forEach(file => {
        dataTransfer.items.add(file);
    });

    resumeInput.files = dataTransfer.files;

    showSelectedFiles(resumeInput.files);

}

// ----------------------------
// Fake Progress Animation
// ----------------------------
function updateProgress(percent, text) {

    progressFill.style.width = percent + "%";

    progressStatus.innerHTML =
        `<strong>${percent}%</strong> - ${text}`;

}
/* ==========================================
   script.js - Part 2
   Upload Resume
========================================== */

uploadBtn.addEventListener("click", async () => {

    const files = resumeInput.files;


    if (files.length === 0) {
        alert("Please select at least one resume.");
        return;
    }
    uploadBtn.disabled = true;
    uploadBtn.innerHTML =
    '<i class="fa-solid fa-spinner fa-spin"></i> Uploading...';
    updateProgress(0, "Starting Upload...");
  

    const formData = new FormData();

    for (const file of files) {
        formData.append("files", file);
    }

    try {

        updateProgress(10, "Uploading Resumes...");
        await new Promise(r => setTimeout(r,300));

        updateProgress(30, "Reading Resumes...");
        await new Promise(r => setTimeout(r,300));

        updateProgress(50, "Parsing Candidate Details...");
        await new Promise(r => setTimeout(r,300));

        const response = await fetch(`${API}/upload`, {
            method: "POST",
            body: formData
        });

        const data = await response.json();

        console.log(data);

        if (!response.ok)
            throw new Error("Upload Failed");

        updateProgress(80, "Saving Profiles...");
        await new Promise(r => setTimeout(r,300));

        updateProgress(100, "Completed ✅");
        await new Promise(r => setTimeout(r,500));

    }
    catch(err){

        console.error(err);

        updateProgress(0,"Upload Failed ❌");

        uploadBtn.disabled=false;

        uploadBtn.innerHTML='<i class="fa-solid fa-upload"></i> Upload Resume';

        return;
    }

   

    selectedFiles.innerHTML = "";
    resumeInput.value = "";

    await new Promise(r=>setTimeout(r,500));

    await loadStats();
    await loadLatestCandidate();
    await loadCandidates();
   
    uploadBtn.disabled = false;
    uploadBtn.innerHTML =
    '<i class="fa-solid fa-upload"></i> Upload Resume';

    

});
/* ==========================================
   script.js - Part 3
   Dashboard Functions
========================================== */

// ----------------------------
// Load Dashboard Stats
// ----------------------------
async function loadStats() {

    try {

        const res = await fetch(`${API}/stats`,{
            cache:"no-store"
        });
        const stats = await res.json();

        resumeProcessed.textContent =
            stats.resume_processed;

        parsingAccuracy.textContent =
            stats.parsing_accuracy + "%";

        profilesCreated.textContent =
            stats.profiles_created;

    }

    catch (err) {

        console.error("Stats Error:", err);

    }

}
// ----------------------------
// Load Latest Candidate
// ----------------------------
async function loadLatestCandidate() {

    try {

        const res = await fetch(`${API}/candidates`, {
            cache: "no-store"
        });

        const candidates = await res.json();

        if (candidates.length === 0) {

            candidateInfo.innerHTML = `
                <div class="empty-state">
                    <i class="fa-regular fa-folder-open"></i>
                    <p>No resume uploaded yet.</p>
                </div>
            `;

            return;
        }

        const c = candidates[0];

        const skills =
            JSON.parse(c.skills || "[]");

        candidateInfo.innerHTML = `

            <div class="candidate-card">

                <p>
                    <strong>Name:</strong>
                    ${c.name || "-"}
                </p>

                <p>
                    <strong>Email:</strong>
                    ${c.email || "-"}
                </p>

                <p>
                    <strong>Phone:</strong>
                    ${c.phone || "-"}
                </p>

                <p>
                    <strong>Education:</strong>
                    ${JSON.parse(
                        c.education || "[]"
                    ).join(", ")}
                </p>

                <p>
                    <strong>Experience:</strong>
                    ${JSON.parse(
                        c.experience || "[]"
                    ).join(", ")}
                </p>

                <p class="skills-field">

                    <strong>Skills:</strong>

                    <span class="skills-container">

                        ${
                            skills.length
                            ? skills.map(skill => `
                                <span class="skill-card">
                                    ${skill}
                                </span>
                            `).join("")
                            : "-"
                        }

                    </span>

                </p>

                <p>
                    <strong>Projects:</strong>
                    ${JSON.parse(
                        c.projects || "[]"
                    ).join(", ")}
                </p>

                <p>
                    <strong>Certifications:</strong>
                    ${JSON.parse(
                        c.certifications || "[]"
                    ).join(", ")}
                </p>

            </div>

        `;

    }

    catch (err) {

        console.error(err);

    }

}

/* ==========================================
   script.js - Part 4
   Candidate Table + Modal + Initial Load
========================================== */

const modal = document.getElementById("candidateModal");
const modalBody = document.getElementById("modalBody");
const closeModal = document.getElementById("closeModal");

// ----------------------------------
// Load Recently Processed Candidates
// ----------------------------------

async function loadCandidates() {

    try {

        const response = await fetch(`${API}/candidates`,{
            cache:"no-store"
        });

        const candidates = await response.json();

        candidateTable.innerHTML = "";

        if (candidates.length === 0) {

            candidateTable.innerHTML = `
                <tr>
                    <td colspan="5">
                        <div class="empty-table">
                            <i class="fa-regular fa-folder-open"></i>
                            <p>No candidates available.</p>
                        </div>
                    </td>
                </tr>
            `;

            return;
        }

        candidates.forEach((candidate) => {

            const row = document.createElement("tr");

            row.innerHTML = `

                <td>${candidate.name || "-"}</td>

                <td>${candidate.email || "-"}</td>

                <td>${candidate.phone || "-"}</td>

                <td>
                    <span class="status processed">
                        Processed
                    </span>
                </td>

                <td>

                    <button
                        class="view-btn"
                        onclick='showCandidate(${JSON.stringify(candidate)})'
                    >
                        View
                    </button>

                </td>

            `;

            candidateTable.appendChild(row);

        });

    }

    catch (err) {

        console.error("Candidate Load Error:", err);

    }

}


// ----------------------------------
// Show Candidate Profile
// ----------------------------------

function showCandidate(candidate) {

    modal.style.display = "flex";

    modalBody.innerHTML = `

        <div class="profile-grid">

            <p><strong>Name:</strong> ${candidate.name || "-"}</p>

            <p><strong>Email:</strong> ${candidate.email || "-"}</p>

            <p><strong>Phone:</strong> ${candidate.phone || "-"}</p>

            <p><strong>Education:</strong> ${JSON.parse(candidate.education || "[]").join(", ")}</p>

            <p><strong>Experience:</strong> ${JSON.parse(candidate.experience || "[]").join(", ")}</p>

            <p><strong>Skills:</strong> ${JSON.parse(candidate.skills || "[]").join(", ")}</p>

            <p><strong>Projects:</strong> ${JSON.parse(candidate.projects || "[]").join(", ")}</p>

            <p><strong>Certifications:</strong> ${JSON.parse(candidate.certifications || "[]").join(", ")}</p>

        </div>

    `;

}


// ----------------------------------
// Close Modal
// ----------------------------------

closeModal.onclick = function () {

    modal.style.display = "none";

};

window.onclick = function (event) {

    if (event.target === modal) {

        modal.style.display = "none";

    }

};


// ----------------------------------
// Initial Page Load
// ----------------------------------

window.addEventListener("DOMContentLoaded", () => {

    loadStats();

    loadLatestCandidate();

    loadCandidates();

});
/* ============================================================
   MILESTONE 2 - JOB POSTING & CANDIDATE MATCHING
============================================================ */

// ------------------------------------------------------------
// DOM Elements
// ------------------------------------------------------------

const jobTitleInput =
    document.getElementById("jobTitle");

const minExperienceInput =
    document.getElementById("minExperience");

const jobSkillsContainer =
    document.getElementById("jobSkillsContainer");

const addSkillBtn =
    document.getElementById("addSkillBtn");

const createJobBtn =
    document.getElementById("createJobBtn");

const jobSelect =
    document.getElementById("jobSelect");

const matchCandidatesBtn =
    document.getElementById("matchCandidatesBtn");

const matchingResults =
    document.getElementById("matchingResults");


// ============================================================
// ADD SKILL ROW
// ============================================================

addSkillBtn.addEventListener("click", () => {

    const row = document.createElement("div");

    row.className = "job-skill-row";

    row.innerHTML = `

        <input
            type="text"
            class="job-skill-name"
            placeholder="Skill name"
        >

        <select class="job-skill-level">

            <option value="Basic">
                Basic
            </option>

            <option value="Intermediate">
                Intermediate
            </option>

            <option value="Advanced">
                Advanced
            </option>

            <option value="Expert">
                Expert
            </option>

        </select>

        <button
            type="button"
            class="remove-skill-btn"
            onclick="removeSkillRow(this)"
        >

            <i class="fa-solid fa-trash"></i>

        </button>

    `;

    jobSkillsContainer.appendChild(row);

});


// ============================================================
// REMOVE SKILL ROW
// ============================================================

function removeSkillRow(button) {

    const rows =
        jobSkillsContainer.querySelectorAll(
            ".job-skill-row"
        );

    if (rows.length <= 1) {

        alert("At least one skill is required.");

        return;
    }

    button.parentElement.remove();
}


// ============================================================
// CREATE JOB
// ============================================================

createJobBtn.addEventListener(
    "click",
    async () => {

        const title =
            jobTitleInput.value.trim();

        const minExperience =
            parseInt(
                minExperienceInput.value
            ) || 0;


        if (!title) {

            alert("Please enter a job title.");

            return;
        }


        const skillRows =
            document.querySelectorAll(
                ".job-skill-row"
            );


        const skills = [];


        for (const row of skillRows) {

            const name =
                row.querySelector(
                    ".job-skill-name"
                ).value.trim();

            const level =
                row.querySelector(
                    ".job-skill-level"
                ).value;


            if (!name) {

                alert(
                    "Please enter all skill names."
                );

                return;
            }


            skills.push({

                name: name,

                level: level

            });

        }


        createJobBtn.disabled = true;

        createJobBtn.innerHTML =
            '<i class="fa-solid fa-spinner fa-spin"></i> Creating...';


        try {

            const response =
                await fetch(
                    `${API}/jobs`,
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body: JSON.stringify({

                            title: title,

                            min_experience:
                                minExperience,

                            skills: skills

                        })
                    }
                );


            const data =
                await response.json();


            if (!response.ok) {

                throw new Error(
                    data.detail ||
                    "Failed to create job"
                );
            }


            alert(
                "Job created successfully!"
            );


            // Clear form

            jobTitleInput.value = "";

            minExperienceInput.value = 0;


            jobSkillsContainer.innerHTML = `

                <div class="job-skill-row">

                    <input
                        type="text"
                        class="job-skill-name"
                        placeholder="Skill name"
                    >

                    <select
                        class="job-skill-level"
                    >

                        <option value="Basic">
                            Basic
                        </option>

                        <option value="Intermediate">
                            Intermediate
                        </option>

                        <option value="Advanced">
                            Advanced
                        </option>

                        <option value="Expert">
                            Expert
                        </option>

                    </select>

                    <button
                        type="button"
                        class="remove-skill-btn"
                        onclick="removeSkillRow(this)"
                    >

                        <i class="fa-solid fa-trash"></i>

                    </button>

                </div>

            `;


            await loadJobs();


            // Automatically select newly created job

            jobSelect.value =
                data.job_id;


        }

        catch (error) {

            console.error(
                "Create Job Error:",
                error
            );

            alert(
                error.message ||
                "Failed to create job."
            );

        }

        finally {

            createJobBtn.disabled = false;

            createJobBtn.innerHTML =
                '<i class="fa-solid fa-briefcase"></i> Create Job';

        }

    }
);


// ============================================================
// LOAD JOBS
// ============================================================

async function loadJobs() {

    try {

        const response =
            await fetch(
                `${API}/jobs`,
                {
                    cache: "no-store"
                }
            );


        const jobs =
            await response.json();


        jobSelect.innerHTML = `

            <option value="">
                Select a job
            </option>

        `;


        jobs.forEach(job => {

            const option =
                document.createElement("option");

            option.value =
                job.id;

            option.textContent =
                `${job.title} (${job.min_experience}+ years)`;

            jobSelect.appendChild(option);

        });

    }

    catch (error) {

        console.error(
            "Load Jobs Error:",
            error
        );

    }
}


// ============================================================
// MATCH CANDIDATES
// ============================================================

matchCandidatesBtn.addEventListener(
    "click",
    async () => {

        const jobId =
            jobSelect.value;


        if (!jobId) {

            alert(
                "Please select a job first."
            );

            return;
        }


        matchingResults.innerHTML = `

            <div class="empty-state">

                <i class="fa-solid fa-spinner fa-spin"></i>

                <p>
                    Matching candidates...
                </p>

            </div>

        `;


        try {

            const response =
                await fetch(
                    `${API}/matching/job/${jobId}`,
                    {
                        cache: "no-store"
                    }
                );


            const results =
                await response.json();


            if (!response.ok) {

                throw new Error(
                    results.detail ||
                    "Failed to match candidates"
                );
            }


            displayMatchingResults(
                results,
                jobId
            );

        }

        catch (error) {

            console.error(
                "Matching Error:",
                error
            );


            matchingResults.innerHTML = `

                <div class="empty-state">

                    <i class="fa-solid fa-triangle-exclamation"></i>

                    <p>
                        Failed to load matching candidates.
                    </p>

                </div>

            `;

        }

    }
);


// ============================================================
// DISPLAY MATCHING RESULTS
// ============================================================

function displayMatchingResults(
    results,
    jobId
) {

    if (!results.length) {

        matchingResults.innerHTML = `

            <div class="empty-state">

                <i class="fa-solid fa-users"></i>

                <p>
                    No candidates available.
                </p>

            </div>

        `;

        return;
    }


    matchingResults.innerHTML = "";


    results.forEach(candidate => {

        const card =
            document.createElement("div");

        card.className =
            "matching-card";


        const score =
            candidate.match_score;


        card.innerHTML = `

            <div class="candidate-header">

                <div>

                    <h3>${candidate.candidate_name || "-"}</h3>

                    <p>
                        <i class="fa-solid fa-envelope"></i>
                        ${candidate.email || "-"}
                    </p>

                </div>

                <div class="score-badge">
                    ${score}%
                </div>

            </div>

            <div class="candidate-body">

                <p>
                    <i class="fa-solid fa-briefcase"></i>
                    <strong>Experience:</strong>
                    ${candidate.candidate_experience} Years
                </p>

                <span class="match-level">
                    ${candidate.match_level}
                </span>

            </div>

            <button
                class="view-match-btn"
                onclick="viewMatchDetails(
                    ${candidate.candidate_id},
                    ${jobId}
                )"
            >
                <i class="fa-solid fa-eye"></i>
                View Details
            </button>

        `;

        matchingResults.appendChild(card);

    });

}


// ============================================================
// VIEW MATCH DETAILS
// ============================================================

async function viewMatchDetails(candidateId, jobId) {

    try {

        const response = await fetch(
            `${API}/matching/skill-gap/${jobId}/${candidateId}`,
            {
                cache: "no-store"
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail || "Failed to load details"
            );
        }

        // -----------------------------------------
        // Open Modal
        // -----------------------------------------

        modal.style.display = "flex";


        // -----------------------------------------
        // Skill Matching HTML
        // -----------------------------------------

        let skillsHTML = "";

        // Matched skills
        data.matched_skills.forEach(skill => {

            const isLevelMatch = skill.level_match;

            skillsHTML += `
                <div class="skill-match-row
                    ${isLevelMatch ? "skill-good" : "skill-warning"}">

                    <strong>
                        ${skill.name}
                    </strong>

                    <span>
                        Required:
                        <b>${skill.required_level}</b>
                    </span>

                    <span>
                        Candidate:
                        <b>${skill.candidate_level}</b>
                    </span>

                    <span class="skill-status">
                        ${isLevelMatch
                            ? "✓ Level Match"
                            : "⚠ Level Gap"}
                    </span>

                </div>
            `;

        });


        // -----------------------------------------
        // Missing Skills
        // -----------------------------------------

        data.missing_skills.forEach(skill => {

            skillsHTML += `
                <div class="skill-match-row skill-missing">

                    <strong>
                        ${skill.name}
                    </strong>

                    <span>
                        Required:
                        <b>${skill.required_level}</b>
                    </span>

                    <span>
                        Candidate:
                        <b>Not Found</b>
                    </span>

                    <span class="skill-status">
                        ❌ Missing
                    </span>

                </div>
            `;

        });


        // -----------------------------------------
        // Experience Analysis
        // -----------------------------------------

        const experienceGap =
            data.candidate_experience <
            data.required_experience;

        const experienceHTML = `

            <div class="experience-analysis">

                <h3>
                    <i class="fa-solid fa-briefcase"></i>
                    Experience Analysis
                </h3>

                <div class="experience-box">

                    <div>
                        <span>Candidate Experience</span>
                        <strong>
                            ${data.candidate_experience} years
                        </strong>
                    </div>

                    <div>
                        <span>Required Experience</span>
                        <strong>
                            ${data.required_experience} years
                        </strong>
                    </div>

                    <div>
                        <span>Status</span>

                        <strong class="${
                            experienceGap
                                ? "experience-warning"
                                : "experience-good"
                        }">

                            ${
                                experienceGap
                                    ? "⚠ Experience Gap"
                                    : "✓ Requirement Met"
                            }

                        </strong>

                    </div>

                </div>

            </div>
        `;


        // -----------------------------------------
        // Recommendations
        // -----------------------------------------

        const recommendations =
            data.skill_gap?.recommendations || [];

        let recommendationHTML = "";

        if (recommendations.length > 0) {

            recommendationHTML = `

                <div class="recommendation-section">

                    <h3>
                        <i class="fa-solid fa-lightbulb"></i>
                        Skill Gap Recommendations
                    </h3>

                    <ul>

                        ${recommendations
                            .map(item => `
                                <li>${item}</li>
                            `)
                            .join("")
                        }

                    </ul>

                </div>

            `;

        }


        // -----------------------------------------
        // Final Modal
        // -----------------------------------------

        modalBody.innerHTML = `

            <div class="match-summary">

                <div class="profile-grid">

                    <p>
                        <strong>Name:</strong>
                        ${data.candidate_name || "-"}
                    </p>

                    <p>
                        <strong>Email:</strong>
                        ${data.email || "-"}
                    </p>

                    <p>
                        <strong>Match Score:</strong>
                        <span class="modal-score">
                            ${data.match_score}%
                        </span>
                    </p>

                    <p>
                        <strong>Match Level:</strong>
                        ${data.match_level}
                    </p>

                </div>

            </div>


            <div class="modal-section">

                <h3>
                    <i class="fa-solid fa-code"></i>
                    Skill Matching
                </h3>

                <div class="skill-matching-list">

                    ${skillsHTML}

                </div>

            </div>


            ${experienceHTML}


            ${recommendationHTML}

        `;

    }

    catch (error) {

        console.error(
            "Match Details Error:",
            error
        );

        alert(
            error.message ||
            "Unable to load candidate details."
        );

    }
}

// ============================================================
// INITIAL LOAD
// ============================================================

window.addEventListener(
    "DOMContentLoaded",
    () => {

        loadJobs();

    }
);
// ==========================
// Sidebar Navigation
// ==========================

const menuItems = document.querySelectorAll(".menu li");
const pages = document.querySelectorAll(".page");

menuItems.forEach(item => {

    item.addEventListener("click", () => {

        // Remove active sidebar
        menuItems.forEach(i => i.classList.remove("active"));

        // Hide all pages
        pages.forEach(page => page.classList.remove("active-page"));

        // Activate clicked menu
        item.classList.add("active");

        // Show selected page
        const pageId = item.dataset.page;
        document.getElementById(pageId).classList.add("active-page");

    });

});
const generateQuestionsBtn =
    document.getElementById("generateQuestionsBtn");

const generatedQuestions =
    document.getElementById("generatedQuestions");

    // ============================================================
// MILESTONE 3 - GENERATE INTERVIEW QUESTIONS
// ============================================================

generateQuestionsBtn.addEventListener("click", async () => {

    const jobTitle = document.getElementById("interviewJob").value.trim();

    const questionType =
        document.getElementById("questionType").value;

    if (!jobTitle) {

        alert("Please enter a job title.");

        return;
    }

    // Show loading state

    generatedQuestions.innerHTML = `
        <div class="empty-state">

            <i class="fa-solid fa-spinner fa-spin"></i>

            <p>
                Gemini is generating interview questions...
            </p>

        </div>
    `;

    generateQuestionsBtn.disabled = true;

    generateQuestionsBtn.innerHTML = `
        <i class="fa-solid fa-spinner fa-spin"></i>
        Generating...
    `;


    try {

        const response = await fetch(
            `${API}/interview/generate-questions`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    job_title: jobTitle,
                    question_type: questionType
                })
            }
        );


        const data = await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Failed to generate questions."
            );

        }


        displayGeneratedQuestions(data.questions);

    }

    catch (error) {

        console.error(
            "Interview Question Error:",
            error
        );

        generatedQuestions.innerHTML = `
            <div class="empty-state">

                <i class="fa-solid fa-triangle-exclamation"></i>

                <p>
                    Failed to generate questions.
                </p>

            </div>
        `;

    }

    finally {

        generateQuestionsBtn.disabled = false;

        generateQuestionsBtn.innerHTML = `
            <i class="fa-solid fa-wand-magic-sparkles"></i>
            Generate Questions
        `;

    }

});
function displayGeneratedQuestions(questions) {

    const lines = questions
        .split("\n")
        .map(line => line.trim())
        .filter(line => line.length > 0);


    generatedQuestions.innerHTML = "";


    lines.forEach((question, index) => {

        const card = document.createElement("div");

        card.className = "question-card";


        card.innerHTML = `
            <div class="question-number">
                ${index + 1}
            </div>

            <div class="question-text">
                ${question.replace(
                    /^\d+[\.\)]\s*/,
                    ""
                )}
            </div>
        `;


        generatedQuestions.appendChild(card);

    });

}