/* ==========================================================
   AI Recruitment Copilot — script.js (Redesigned)
   Backend API: http://127.0.0.1:8000
   All endpoints unchanged. Only UI rendering redesigned.
========================================================== */

const API = "https://ai-driven-smart-hiring-platform-with-2q4r.onrender.com";

/* ----------------------------------------------------------
   STATE
---------------------------------------------------------- */
let deletedJobIds = new Set(); // frontend-only soft delete
let allCandidatesCache = [];   // cached for search filtering

/* ----------------------------------------------------------
   INTERVIEW STATE
---------------------------------------------------------- */
const MAX_REGENS  = 2;           // maximum regenerations per question
const regenCounts = new Map();   // index → count of regenerations used


/* ----------------------------------------------------------
   DOM REFS — Upload Page
---------------------------------------------------------- */
const resumeInput    = document.getElementById("resumeInput");
const browseBtn      = document.getElementById("browseBtn");
const uploadBtn      = document.getElementById("uploadBtn");
const selectedFiles  = document.getElementById("selectedFiles");
const progressFill   = document.getElementById("progressFill");
const progressStatus = document.getElementById("progressStatus");
const resumeProcessed  = document.getElementById("resumeProcessed");
const parsingAccuracy  = document.getElementById("parsingAccuracy");
const profilesCreated  = document.getElementById("profilesCreated");
const candidateInfo    = document.getElementById("candidateInfo");
const candidateTable   = document.getElementById("candidateTable");
const loaderOverlay    = document.getElementById("loaderOverlay");
const uploadBox        = document.querySelector(".upload-drop-zone");

/* ----------------------------------------------------------
   DOM REFS — Job Management Page
---------------------------------------------------------- */
const jobTitleInput       = document.getElementById("jobTitle");
const minExperienceInput  = document.getElementById("minExperience");
const jobSkillsContainer  = document.getElementById("jobSkillsContainer");
const addSkillBtn         = document.getElementById("addSkillBtn");
const createJobBtn        = document.getElementById("createJobBtn");
const jobListingGrid      = document.getElementById("jobListingGrid");
const jobCount            = document.getElementById("jobCount");

/* ----------------------------------------------------------
   DOM REFS — Matching Page
---------------------------------------------------------- */
const jobSelect          = document.getElementById("jobSelect");
const matchCandidatesBtn = document.getElementById("matchCandidatesBtn");
const matchingResults    = document.getElementById("matchingResults");
const selectedJobDetails = document.getElementById("selectedJobDetails");

/* ----------------------------------------------------------
   DOM REFS — Shared Modal (Candidate Profile)
---------------------------------------------------------- */
const modal      = document.getElementById("candidateModal");
const modalBody  = document.getElementById("modalBody");
const closeModal = document.getElementById("closeModal");

/* ----------------------------------------------------------
   DOM REFS — Skill Gap Drawer
---------------------------------------------------------- */
const skillGapDrawer      = document.getElementById("skillGapDrawer");
const drawerCandidateName = document.getElementById("drawerCandidateName");
const drawerCandidateEmail= document.getElementById("drawerCandidateEmail");
const drawerBody          = document.getElementById("drawerBody");
const closeDrawer         = document.getElementById("closeDrawer");

/* ----------------------------------------------------------
   DOM REFS — Interview Page (Question Generator)
---------------------------------------------------------- */
const generateQuestionsBtn = document.getElementById("generateQuestionsBtn");
const generatedQuestions   = document.getElementById("generatedQuestions");

/* ----------------------------------------------------------
   DOM REFS — Interview Page (Simulation)
---------------------------------------------------------- */
const startInterviewBtn  = document.getElementById("startInterviewBtn");
const sendResponseBtn    = document.getElementById("sendResponseBtn");
const endInterviewBtn    = document.getElementById("endInterviewBtn");
const candidateResponse  = document.getElementById("candidateResponse");
const interviewChat      = document.getElementById("interviewChat");

/* ----------------------------------------------------------
   SIMULATION STATE
---------------------------------------------------------- */
let currentSessionId  = null;   // UUID returned by /interview/start
let simulationActive  = false;  // guards the send/end buttons

/* ----------------------------------------------------------
   TOAST
---------------------------------------------------------- */
function showToast(message, isError = false) {
    const toast   = document.getElementById("toast");
    const toastMsg = document.getElementById("toastMessage");
    toast.classList.remove("show", "toast-error");
    toastMsg.textContent = message;
    if (isError) toast.classList.add("toast-error");
    toast.classList.add("show");
    setTimeout(() => toast.classList.remove("show"), 3500);
}

/* ----------------------------------------------------------
   PROGRESS BAR
---------------------------------------------------------- */
function updateProgress(percent, text) {
    progressFill.style.width = percent + "%";
    progressStatus.innerHTML = `<strong>${percent}%</strong> — ${text}`;
}

/* ==========================================================
   SIDEBAR NAVIGATION
========================================================== */
const menuItems = document.querySelectorAll(".menu-item");
const pages     = document.querySelectorAll(".page");

menuItems.forEach(item => {
    item.addEventListener("click", () => {
        menuItems.forEach(i => i.classList.remove("active"));
        pages.forEach(p => p.classList.remove("active-page"));
        item.classList.add("active");
        const pageId = item.dataset.page;
        document.getElementById(pageId).classList.add("active-page");

        // Persist current page in URL hash so reload returns here
        history.replaceState(null, "", `#${pageId}`);

        // Lazy-load page data when navigating
        if (pageId === "matchingPage") {
            loadJobsIntoDropdown();
        } else if (pageId === "dashboardPage") {
            if (typeof loadDashboard === "function") loadDashboard();
        } else if (pageId === "voiceScreeningPage") {
            if (typeof loadVsDropdowns === "function") loadVsDropdowns();
        }
    });
});

/* ==========================================================
   BROWSE + DRAG & DROP
========================================================== */
browseBtn.addEventListener("click", () => resumeInput.click());

resumeInput.addEventListener("change", () => showSelectedFiles(resumeInput.files));

uploadBox.addEventListener("dragover", (e) => {
    e.preventDefault();
    uploadBox.classList.add("dragging");
});

uploadBox.addEventListener("dragleave", () => uploadBox.classList.remove("dragging"));

uploadBox.addEventListener("drop", (e) => {
    e.preventDefault();
    uploadBox.classList.remove("dragging");
    resumeInput.files = e.dataTransfer.files;
    showSelectedFiles(resumeInput.files);
});

/* ----------------------------------------------------------
   Show Selected Files
---------------------------------------------------------- */
function showSelectedFiles(files) {
    selectedFiles.innerHTML = "";
    if (files.length === 0) {
        selectedFiles.innerHTML = `<p class="no-files-text">No file selected</p>`;
        return;
    }
    Array.from(files).forEach((file, index) => {
        const div = document.createElement("div");
        div.className = "file-item";
        div.innerHTML = `
            <i class="fa-solid fa-file-lines"></i>
            <span class="file-name">${file.name}</span>
            <button type="button" class="remove-file-btn" title="Remove file">
                <i class="fa-solid fa-xmark"></i>
            </button>
        `;
        div.querySelector(".remove-file-btn").addEventListener("click", () => removeSelectedFile(index));
        selectedFiles.appendChild(div);
    });
}

function removeSelectedFile(index) {
    const files = Array.from(resumeInput.files);
    files.splice(index, 1);
    const dt = new DataTransfer();
    files.forEach(f => dt.items.add(f));
    resumeInput.files = dt.files;
    showSelectedFiles(resumeInput.files);
}

/* ==========================================================
   UPLOAD RESUMES  —  POST /upload
========================================================== */
uploadBtn.addEventListener("click", async () => {
    const files = resumeInput.files;
    if (files.length === 0) {
        showToast("Please select at least one resume.", true);
        return;
    }

    uploadBtn.disabled = true;
    uploadBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Uploading...`;
    updateProgress(0, "Starting Upload...");

    const formData = new FormData();
    for (const file of files) formData.append("files", file);

    try {
        updateProgress(10, "Uploading Resumes...");
        await delay(300);
        updateProgress(30, "Reading Resumes...");
        await delay(300);
        updateProgress(50, "Parsing Candidate Details...");
        await delay(300);

        const response = await fetch(`${API}/upload`, { method: "POST", body: formData });
        const data     = await response.json();

        if (!response.ok) throw new Error("Upload Failed");

        updateProgress(80, "Saving Profiles...");
        await delay(300);
        updateProgress(100, "Completed ✅");
        await delay(500);

        selectedFiles.innerHTML = "";
        resumeInput.value = "";

        await loadStats();
        await loadLatestCandidate();
        await loadCandidates();

        showToast(`${files.length} resume(s) uploaded successfully!`);

    } catch (err) {
        console.error(err);
        updateProgress(0, "Upload Failed ❌");
        showToast("Upload failed. Is the backend running?", true);
    } finally {
        uploadBtn.disabled = false;
        uploadBtn.innerHTML = `<i class="fa-solid fa-upload"></i> Upload Resumes`;
    }
});

/* ==========================================================
   STATS  —  GET /stats
========================================================== */
async function loadStats() {
    try {
        const res   = await fetch(`${API}/stats`, { cache: "no-store" });
        const stats = await res.json();
        resumeProcessed.textContent  = stats.resume_processed;
        parsingAccuracy.textContent  = stats.parsing_accuracy + "%";
        profilesCreated.textContent  = stats.profiles_created;
    } catch (err) {
        console.error("Stats Error:", err);
    }
}

/* ==========================================================
   LATEST CANDIDATE  —  GET /candidates
========================================================== */
async function loadLatestCandidate() {
    try {
        const res        = await fetch(`${API}/candidates`, { cache: "no-store" });
        const candidates = await res.json();

        if (candidates.length === 0) {
            candidateInfo.innerHTML = `
                <div class="empty-box">
                    <i class="fa-regular fa-folder-open"></i>
                    <p>No resume uploaded yet.</p>
                </div>`;
            return;
        }

        const c      = candidates[0];
        const skills = safeParseJSON(c.skills, []);

        candidateInfo.innerHTML = `
            <div class="candidate-card">
                <p><strong>Name:</strong> ${c.name || "—"}</p>
                <p><strong>Email:</strong> ${c.email || "—"}</p>
                <p><strong>Phone:</strong> ${c.phone || "—"}</p>
                <p><strong>Education:</strong> ${safeParseJSON(c.education, []).join(", ") || "—"}</p>
                <p><strong>Experience:</strong> ${safeParseJSON(c.experience, []).join(", ") || "—"}</p>
                <p class="skills-field">
                    <strong>Skills:</strong>
                    <span class="skills-container">
                        ${skills.length
                            ? skills.map(s => `<span class="skill-card">${s}</span>`).join("")
                            : "—"}
                    </span>
                </p>
                <p><strong>Projects:</strong> ${safeParseJSON(c.projects, []).join(", ") || "—"}</p>
                <p><strong>Certifications:</strong> ${safeParseJSON(c.certifications, []).join(", ") || "—"}</p>
            </div>`;

    } catch (err) {
        console.error("Latest Candidate Error:", err);
    }
}

/* ==========================================================
   CANDIDATES TABLE  —  GET /candidates
========================================================== */
async function loadCandidates() {
    try {
        const response   = await fetch(`${API}/candidates`, { cache: "no-store" });
        const candidates = await response.json();

        // Cache the full list for search
        allCandidatesCache = candidates;

        candidateTable.innerHTML = "";

        if (candidates.length === 0) {
            candidateTable.innerHTML = `<tr><td colspan="5" class="no-data">No candidates available.</td></tr>`;
            renderAllCandidatesTable(candidates);
            return;
        }

        candidates.forEach(candidate => {
            const row = document.createElement("tr");
            row.innerHTML = `
                <td>${candidate.name || "—"}</td>
                <td>${candidate.email || "—"}</td>
                <td>${candidate.phone || "—"}</td>
                <td><span class="status ${getHiringStatusClass(candidate.hiring_status)}">${formatHiringStatus(candidate.hiring_status)}</span></td>
                <td>
                    <button class="view-btn" onclick='showCandidate(${JSON.stringify(candidate)})'>
                        View
                    </button>
                </td>`;
            candidateTable.appendChild(row);
        });

        renderAllCandidatesTable(candidates);

    } catch (err) {
        console.error("Candidates Table Error:", err);
    }
}

/* ----------------------------------------------------------
   Render the Candidates page table (with optional filtered list)
---------------------------------------------------------- */
function renderAllCandidatesTable(candidates) {
    const allTable = document.getElementById("allCandidatesTable");
    const badge    = document.getElementById("candidateCountBadge");
    if (!allTable) return;

    allTable.innerHTML = "";

    if (candidates.length === 0) {
        allTable.innerHTML = `<tr><td colspan="5" class="no-data">No candidates found.</td></tr>`;
        if (badge) badge.textContent = "";
        return;
    }

    candidates.forEach(candidate => {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${candidate.name || "—"}</td>
            <td>${candidate.email || "—"}</td>
            <td>${candidate.phone || "—"}</td>
            <td><span class="status ${getHiringStatusClass(candidate.hiring_status)}">${formatHiringStatus(candidate.hiring_status)}</span></td>
            <td>
                <button class="view-btn" onclick='showCandidate(${JSON.stringify(candidate)})'>
                    View
                </button>
            </td>`;
        allTable.appendChild(row);
    });

    if (badge) badge.textContent = `${candidates.length} candidate${candidates.length !== 1 ? "s" : ""}`;
}

/* ----------------------------------------------------------
   Search / Filter candidates (instant, client-side)
---------------------------------------------------------- */
function filterCandidates(query) {
    const q = query.trim().toLowerCase();
    if (!q) {
        renderAllCandidatesTable(allCandidatesCache);
        return;
    }
    const filtered = allCandidatesCache.filter(c => {
        const name  = (c.name  || "").toLowerCase();
        const email = (c.email || "").toLowerCase();
        return name.includes(q) || email.includes(q);
    });
    renderAllCandidatesTable(filtered);
}

/* ----------------------------------------------------------
   Show Candidate Profile Modal
---------------------------------------------------------- */
function showCandidate(candidate) {
    modal.classList.add("open");
    modal.style.display = "flex";
    modalBody.innerHTML = `
        <h2 style="color:var(--primary);margin-bottom:20px;font-size:20px;">
            <i class="fa-solid fa-user" style="margin-right:10px;"></i>Candidate Profile
        </h2>
        <div class="profile-grid">
            <p><strong>Name:</strong> ${candidate.name || "—"}${candidate.name_source ? `<span style="font-size:11px;color:var(--text-muted);margin-left:8px;font-weight:400;">Name Source: ${escapeHTML(candidate.name_source)}</span>` : ""}</p>
            <p><strong>Email:</strong> ${candidate.email || "—"}</p>
            <p><strong>Phone:</strong> ${candidate.phone || "—"}</p>
            <p><strong>Education:</strong> ${safeParseJSON(candidate.education, []).join(", ") || "—"}</p>
            <p><strong>Experience:</strong> ${safeParseJSON(candidate.experience, []).join(", ") || "—"}</p>
            <p><strong>Skills:</strong> ${safeParseJSON(candidate.skills, []).join(", ") || "—"}</p>
            <p><strong>Projects:</strong> ${safeParseJSON(candidate.projects, []).join(", ") || "—"}</p>
            <p><strong>Certifications:</strong> ${safeParseJSON(candidate.certifications, []).join(", ") || "—"}</p>
        </div>
        
        <hr class="divider">
        <h3 style="color:var(--primary);font-size:16px;margin-bottom:10px;"><i class="fa-solid fa-gavel"></i> Recruiter Decision</h3>
        <div style="margin-bottom:15px; font-size:14px;">
            <strong>Current Status:</strong> <span id="modalHiringStatus" class="status ${getHiringStatusClass(candidate.hiring_status)}">${formatHiringStatus(candidate.hiring_status)}</span>
        </div>
        <div style="display:flex; gap:10px;">
            <button type="button" class="btn-primary" onclick="updateHiringStatus(${candidate.id}, 'HIRED')" style="background-color:#10b981; border-color:#10b981;">
                <i class="fa-solid fa-check"></i> Hire Candidate
            </button>
            <button type="button" class="btn-secondary" onclick="updateHiringStatus(${candidate.id}, 'NOT_SELECTED')" style="color:#ef4444; border-color:#ef4444; background:white;">
                <i class="fa-solid fa-xmark"></i> Not Selected
            </button>
        </div>
        `;

}

closeModal.addEventListener("click", () => {
    modal.classList.remove("open");
    modal.style.display = "none";
});

window.addEventListener("click", (e) => {
    if (e.target === modal) {
        modal.classList.remove("open");
        modal.style.display = "none";
    }
});

/* ==========================================================
   SKILL GAP DRAWER — open / close
========================================================== */
closeDrawer.addEventListener("click", closeSkillGapDrawer);

skillGapDrawer.addEventListener("click", (e) => {
    if (e.target === skillGapDrawer) closeSkillGapDrawer();
});

function openSkillGapDrawer() {
    skillGapDrawer.classList.add("open");
    document.body.style.overflow = "hidden";
}

function closeSkillGapDrawer() {
    skillGapDrawer.classList.remove("open");
    document.body.style.overflow = "";
}

/* ==========================================================
   JOB MANAGEMENT — ADD / REMOVE SKILL ROW
========================================================== */
addSkillBtn.addEventListener("click", () => {
    const row = document.createElement("div");
    row.className = "job-skill-row";
    row.innerHTML = `
        <input type="text" class="job-skill-name" placeholder="Skill name (e.g. Python)">
        <select class="job-skill-level">
            <option value="Basic">Basic</option>
            <option value="Intermediate">Intermediate</option>
            <option value="Advanced">Advanced</option>
            <option value="Expert">Expert</option>
        </select>
        <button type="button" class="remove-skill-btn" onclick="removeSkillRow(this)">
            <i class="fa-solid fa-trash"></i>
        </button>`;
    jobSkillsContainer.appendChild(row);
});

function removeSkillRow(button) {
    const rows = jobSkillsContainer.querySelectorAll(".job-skill-row");
    if (rows.length <= 1) {
        showToast("At least one skill is required.", true);
        return;
    }
    button.parentElement.remove();
}

/* ==========================================================
   CREATE JOB  —  POST /jobs
========================================================== */
createJobBtn.addEventListener("click", async () => {
    const title         = jobTitleInput.value.trim();
    const minExperience = parseInt(minExperienceInput.value) || 0;

    if (!title) {
        showToast("Please enter a job title.", true);
        return;
    }

    const skillRows = document.querySelectorAll(".job-skill-row");
    const skills    = [];

    for (const row of skillRows) {
        const name  = row.querySelector(".job-skill-name").value.trim();
        const level = row.querySelector(".job-skill-level").value;
        if (!name) {
            showToast("Please enter all skill names.", true);
            return;
        }
        skills.push({ name, level });
    }

    createJobBtn.disabled = true;
    createJobBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Creating...`;

    try {
        const response = await fetch(`${API}/jobs`, {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body:    JSON.stringify({ title, min_experience: minExperience, skills })
        });

        const data = await response.json();

        if (!response.ok) throw new Error(data.detail || "Failed to create job");

        showToast(`Job "${title}" created successfully!`);

        // Reset form
        jobTitleInput.value   = "";
        minExperienceInput.value = 0;
        jobSkillsContainer.innerHTML = `
            <div class="job-skill-row">
                <input type="text" class="job-skill-name" placeholder="Skill name (e.g. Python)">
                <select class="job-skill-level">
                    <option value="Basic">Basic</option>
                    <option value="Intermediate">Intermediate</option>
                    <option value="Advanced">Advanced</option>
                    <option value="Expert">Expert</option>
                </select>
                <button type="button" class="remove-skill-btn" onclick="removeSkillRow(this)">
                    <i class="fa-solid fa-trash"></i>
                </button>
            </div>`;

        await loadJobListingGrid();
        await loadJobsIntoDropdown();

    } catch (error) {
        console.error("Create Job Error:", error);
        showToast(error.message || "Failed to create job.", true);
    } finally {
        createJobBtn.disabled = false;
        createJobBtn.innerHTML = `<i class="fa-solid fa-briefcase"></i> Create Job`;
    }
});

/* ==========================================================
   LOAD JOB LISTING GRID  —  GET /jobs
   (Used on Job Management Page)
========================================================== */
async function loadJobListingGrid() {
    try {
        const response = await fetch(`${API}/jobs`, { cache: "no-store" });
        const jobs     = await response.json();

        // Filter out soft-deleted jobs
        const visibleJobs = jobs.filter(j => !deletedJobIds.has(j.id));

        // Update count badge
        jobCount.textContent = `${visibleJobs.length} job${visibleJobs.length !== 1 ? "s" : ""}`;

        if (visibleJobs.length === 0) {
            jobListingGrid.innerHTML = `
                <div class="empty-state-full">
                    <i class="fa-solid fa-briefcase"></i>
                    <p>No jobs created yet. Use the form to add your first job posting.</p>
                </div>`;
            return;
        }

        jobListingGrid.innerHTML = "";

        visibleJobs.forEach(job => {
            const skills = Array.isArray(job.skills) ? job.skills : safeParseJSON(job.skills, []);
            const card   = document.createElement("div");
            card.className = "job-listing-card";
            card.id = `job-card-${job.id}`;

            const skillTagsHTML = skills.length
                ? skills.map(s => `
                    <span class="skill-tag">
                        <span class="skill-level-dot level-${s.level ? s.level.toLowerCase() : 'basic'}"></span>
                        ${s.name}
                        <span style="font-weight:400;opacity:.7;font-size:11px;">${s.level || "Basic"}</span>
                    </span>`).join("")
                : `<span style="color:var(--text-muted);font-size:13px;">No skills defined</span>`;

            card.innerHTML = `
                <div class="jlc-top">
                    <div class="jlc-info">
                        <h4>${escapeHTML(job.title)}</h4>
                        <span class="jlc-exp">
                            <i class="fa-solid fa-clock"></i>
                            ${job.min_experience}+ years experience required
                        </span>
                    </div>
                    <div class="jlc-actions">
                        <button class="btn-match-shortcut" onclick="goToMatch(${job.id})">
                            <i class="fa-solid fa-magnifying-glass"></i> Match
                        </button>
                        <button class="btn-danger" onclick="softDeleteJob(${job.id}, '${escapeHTML(job.title)}')">
                            <i class="fa-solid fa-trash"></i>
                        </button>
                    </div>
                </div>
                <div class="jlc-skills">${skillTagsHTML}</div>`;

            jobListingGrid.appendChild(card);
        });

    } catch (err) {
        console.error("Load Job Listing Error:", err);
        jobListingGrid.innerHTML = `<div class="empty-state"><i class="fa-solid fa-triangle-exclamation"></i><p>Failed to load jobs.</p></div>`;
    }
}

/* ----------------------------------------------------------
   Soft Delete Job (frontend-only — no backend DELETE endpoint)
---------------------------------------------------------- */
function softDeleteJob(jobId, title) {
    if (!confirm(`Remove "${title}" from the list?\n\n(This is a local-only action. The job will reappear after page refresh.)`)) return;
    deletedJobIds.add(jobId);
    const card = document.getElementById(`job-card-${jobId}`);
    if (card) {
        card.style.transition = "opacity .3s, transform .3s";
        card.style.opacity    = "0";
        card.style.transform  = "scale(.95)";
        setTimeout(() => card.remove(), 300);
    }
    // Update count
    loadJobListingGrid();
    // Remove from dropdowns
    loadJobsIntoDropdown();
    showToast(`"${title}" removed from view.`);
}

/* ----------------------------------------------------------
   Navigate to matching page with a specific job pre-selected
---------------------------------------------------------- */
function goToMatch(jobId) {
    // Switch page
    menuItems.forEach(i => i.classList.remove("active"));
    pages.forEach(p => p.classList.remove("active-page"));

    const matchMenuItem = document.querySelector('[data-page="matchingPage"]');
    if (matchMenuItem) matchMenuItem.classList.add("active");
    document.getElementById("matchingPage").classList.add("active-page");

    // Load jobs then select this one
    loadJobsIntoDropdown().then(() => {
        jobSelect.value = String(jobId);
        updateSelectedJobDetails(jobId);
    });
}

/* ==========================================================
   LOAD JOBS INTO DROPDOWN  —  GET /jobs
   (Used on Matching Page + Interview Page)
========================================================== */
async function loadJobsIntoDropdown() {
    try {
        const response = await fetch(`${API}/jobs`, { cache: "no-store" });
        const jobs     = await response.json();

        const visibleJobs = jobs.filter(j => !deletedJobIds.has(j.id));

        // Matching page dropdown
        const currentVal = jobSelect.value;
        jobSelect.innerHTML = `<option value="">— Choose a job —</option>`;
        visibleJobs.forEach(job => {
            const opt = document.createElement("option");
            opt.value       = job.id;
            opt.textContent = `${job.title} (${job.min_experience}+ yrs)`;
            jobSelect.appendChild(opt);
        });
        if (currentVal) jobSelect.value = currentVal;

        // Interview Question Generator dropdown
        const interviewJobSel = document.getElementById("interviewJob");
        if (interviewJobSel) {
            const ivCurrentVal = interviewJobSel.value;
            interviewJobSel.innerHTML = `<option value="">Select job</option>`;
            visibleJobs.forEach(job => {
                const opt = document.createElement("option");
                opt.value       = job.id;
                opt.textContent = job.title;
                interviewJobSel.appendChild(opt);
            });
            if (ivCurrentVal) interviewJobSel.value = ivCurrentVal;
        }

        // Interview Simulation Job dropdown
        const simJobSel = document.getElementById("simInterviewJob");
        if (simJobSel) {
            const simCurrentVal = simJobSel.value;
            simJobSel.innerHTML = `<option value="">Select job</option>`;
            visibleJobs.forEach(job => {
                const opt = document.createElement("option");
                opt.value       = job.id;
                opt.textContent = job.title;
                simJobSel.appendChild(opt);
            });
            if (simCurrentVal) simJobSel.value = simCurrentVal;
        }

        return visibleJobs;

    } catch (err) {
        console.error("Load Jobs Dropdown Error:", err);
        return [];
    }
}

/* ----------------------------------------------------------
   Show selected job info banner under controls bar
---------------------------------------------------------- */
function updateSelectedJobDetails(jobId) {
    if (!jobId) {
        selectedJobDetails.style.display = "none";
        return;
    }

    fetch(`${API}/job/${jobId}`, { cache: "no-store" })
        .then(r => r.json())
        .then(job => {
            const skills = Array.isArray(job.skills) ? job.skills : safeParseJSON(job.skills, []);
            const tagsHTML = skills.map(s => `
                <span class="skill-tag">
                    <span class="skill-level-dot level-${(s.level || "basic").toLowerCase()}"></span>
                    ${s.name}
                </span>`).join("");

            selectedJobDetails.innerHTML = `
                <div>
                    <div class="sjd-title">${escapeHTML(job.title)}</div>
                    <div class="sjd-exp"><i class="fa-solid fa-clock"></i> ${job.min_experience}+ years required</div>
                </div>
                ${tagsHTML ? `<div class="sjd-skills">${tagsHTML}</div>` : ""}`;
            selectedJobDetails.style.display = "flex";
        })
        .catch(() => {
            selectedJobDetails.style.display = "none";
        });
}

jobSelect.addEventListener("change", () => {
    updateSelectedJobDetails(jobSelect.value);
});

/* ==========================================================
   MATCH CANDIDATES  —  GET /matching/job/{jobId}
========================================================== */
matchCandidatesBtn.addEventListener("click", async () => {
    const jobId = jobSelect.value;
    if (!jobId) {
        showToast("Please select a job first.", true);
        return;
    }

    matchingResults.innerHTML = `
        <div class="empty-state" style="grid-column:1/-1;padding:80px 20px;">
            <i class="fa-solid fa-spinner fa-spin" style="font-size:28px;color:var(--primary);"></i>
            <p style="font-size:15px;">Finding best candidates...</p>
        </div>`;

    matchCandidatesBtn.disabled = true;
    matchCandidatesBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Matching...`;

    try {
        const response = await fetch(`${API}/matching/job/${jobId}`, { cache: "no-store" });
        const results  = await response.json();

        if (!response.ok) throw new Error(results.detail || "Failed to match candidates");

        displayMatchingResults(results, jobId);

    } catch (error) {
        console.error("Matching Error:", error);
        matchingResults.innerHTML = `
            <div class="empty-state" style="grid-column:1/-1;">
                <i class="fa-solid fa-triangle-exclamation" style="font-size:22px;color:#dc2626;"></i>
                <p>Failed to load candidates. Is the backend running?</p>
            </div>`;
    } finally {
        matchCandidatesBtn.disabled = false;
        matchCandidatesBtn.innerHTML = `<i class="fa-solid fa-magnifying-glass"></i> Find Best Candidates`;
    }
});

/* ----------------------------------------------------------
   Display Matching Results
---------------------------------------------------------- */
function displayMatchingResults(results, jobId) {
    if (!results.length) {
        matchingResults.innerHTML = `
            <div class="empty-state" style="grid-column:1/-1;padding:80px 20px;">
                <i class="fa-solid fa-users-slash" style="font-size:36px;color:var(--border-strong);"></i>
                <p>No candidates found in the database. Upload some resumes first.</p>
            </div>`;
        return;
    }

    matchingResults.innerHTML = "";

    results.forEach(candidate => {
        const score     = candidate.match_score;
        const level     = (candidate.match_level || "").toLowerCase();
        const tierClass = score >= 75 ? "high" : score >= 50 ? "medium" : "low";

        // Badge class from level string
        let badgeClass = "good";
        if (level.includes("excellent")) badgeClass = "excellent";
        else if (level.includes("good"))     badgeClass = "good";
        else if (level.includes("moderate")) badgeClass = "moderate";
        else if (level.includes("low"))      badgeClass = "low";

        const card = document.createElement("div");
        card.className = "matching-card";
        card.innerHTML = `
            <div class="score-strip ${tierClass}"></div>

            <div class="mc-header">
                <div>
                    <h3>${escapeHTML(candidate.candidate_name || "—")}</h3>
                    <p class="mc-email">
                        <i class="fa-solid fa-envelope"></i>
                        ${escapeHTML(candidate.email || "—")}
                    </p>
                </div>
                <div class="score-circle ${tierClass}">
                    <span>${score}</span>
                    <span class="score-label">score</span>
                </div>
            </div>

            <div class="mc-body" style="justify-content: space-between; align-items: center;">
                <div style="display:flex; flex-direction:column; gap:8px;">
                    <span class="mc-exp">
                        <i class="fa-solid fa-briefcase"></i>
                        ${candidate.candidate_experience} yrs experience
                    </span>
                    <span class="status ${getHiringStatusClass(candidate.hiring_status)}" style="font-size:11px; padding:4px 8px; border-radius:4px; border:1px solid currentColor;">
                        ${formatHiringStatus(candidate.hiring_status)}
                    </span>
                </div>
                <span class="match-level-badge ${badgeClass}">
                    ${escapeHTML(candidate.match_level || "—")}
                </span>
            </div>

            <button
                class="view-match-btn"
                onclick="viewMatchDetails(${candidate.candidate_id}, ${jobId})"
            >
                <i class="fa-solid fa-chart-bar"></i>
                View Skill Gap Analysis
            </button>`;

        matchingResults.appendChild(card);
    });
}

/* ==========================================================
   SKILL GAP ANALYSIS  —  GET /matching/skill-gap/{jobId}/{candidateId}
========================================================== */
async function viewMatchDetails(candidateId, jobId) {
    // Show drawer with loading state
    drawerCandidateName.textContent  = "Loading...";
    drawerCandidateEmail.textContent = "";
    drawerBody.innerHTML = `
        <div class="empty-state" style="padding:80px 20px;">
            <i class="fa-solid fa-spinner fa-spin" style="font-size:28px;color:white;"></i>
        </div>`;
    openSkillGapDrawer();

    try {
        const response = await fetch(
            `${API}/matching/skill-gap/${jobId}/${candidateId}`,
            { cache: "no-store" }
        );
        const data = await response.json();

        if (!response.ok) throw new Error(data.detail || "Failed to load details");

        renderSkillGapDrawer(data);

    } catch (error) {
        console.error("Skill Gap Error:", error);
        drawerBody.innerHTML = `
            <div class="empty-state" style="padding:80px 20px;">
                <i class="fa-solid fa-triangle-exclamation" style="font-size:28px;color:#f87171;"></i>
                <p>Unable to load skill gap details.</p>
            </div>`;
    }
}

/* ----------------------------------------------------------
   Render Skill Gap Drawer Content
---------------------------------------------------------- */
function renderSkillGapDrawer(data) {
    // Header
    drawerCandidateName.textContent  = data.candidate_name  || "Candidate";
    drawerCandidateEmail.textContent = data.email           || "";

    const score     = data.match_score || 0;
    const tierClass = score >= 75 ? "high" : score >= 50 ? "medium" : "low";

    // Summary strip
    const matchedCount = (data.matched_skills  || []).length;
    const missingCount = (data.missing_skills  || []).length;
    const totalCount   = matchedCount + missingCount;

    let summaryHTML = `
        <div class="drawer-summary">
            <div class="drawer-stat">
                <span class="ds-value" style="color:var(--${tierClass === 'high' ? 'green' : tierClass === 'medium' ? 'yellow' : 'red'})">${score}%</span>
                <span class="ds-label">Match Score</span>
            </div>
            <div class="drawer-stat">
                <span class="ds-value" style="color:var(--green)">${matchedCount}</span>
                <span class="ds-label">Matched Skills</span>
            </div>
            <div class="drawer-stat">
                <span class="ds-value" style="color:var(--red)">${missingCount}</span>
                <span class="ds-label">Missing Skills</span>
            </div>
        </div>`;

    // Matched Skills
    let matchedHTML = "";
    (data.matched_skills || []).forEach(skill => {
        const isLevelMatch = skill.level_match;
        matchedHTML += `
            <div class="skill-match-row ${isLevelMatch ? "skill-good" : "skill-warning"}">
                <span class="smr-name">${escapeHTML(skill.name)}</span>
                <span class="smr-tag smr-required">Req: ${skill.required_level}</span>
                <span class="smr-tag smr-candidate">Has: ${skill.candidate_level}</span>
                <span class="smr-status">${isLevelMatch ? "✓ Match" : "⚠ Gap"}</span>
            </div>`;
    });

    // Missing Skills
    let missingHTML = "";
    (data.missing_skills || []).forEach(skill => {
        missingHTML += `
            <div class="skill-match-row skill-missing">
                <span class="smr-name">${escapeHTML(skill.name)}</span>
                <span class="smr-tag smr-required">Req: ${skill.required_level}</span>
                <span class="smr-tag" style="background:#fee2e2;color:#dc2626;">Not Found</span>
                <span class="smr-status">❌ Missing</span>
            </div>`;
    });

    // Experience
    const expGap     = (data.candidate_experience || 0) < (data.required_experience || 0);
    const expValClass = expGap ? "exp-status-warn" : "exp-status-good";
    const expStatus   = expGap ? "⚠ Gap" : "✓ Met";

    const experienceHTML = `
        <div class="experience-comparison">
            <div class="exp-box">
                <span class="exp-value">${data.candidate_experience}</span>
                <span class="exp-label">Candidate Years</span>
            </div>
            <div class="exp-box">
                <span class="exp-value">${data.required_experience}</span>
                <span class="exp-label">Required Years</span>
            </div>
            <div class="exp-box">
                <span class="exp-value ${expValClass}">${expStatus}</span>
                <span class="exp-label">Experience Status</span>
            </div>
        </div>`;

    // Recommendations
    const recommendations = (data.skill_gap && data.skill_gap.recommendations) || [];
    let recommendHTML = "";
    if (recommendations.length > 0) {
        recommendHTML = `
            <div class="drawer-section">
                <div class="drawer-section-title">
                    <i class="fa-solid fa-lightbulb"></i>
                    Skill Gap Recommendations
                </div>
                <ul class="recommendations-list">
                    ${recommendations.map(r => `
                        <li>
                            <i class="fa-solid fa-arrow-right"></i>
                            ${escapeHTML(r)}
                        </li>`).join("")}
                </ul>
            </div>`;
    }

    // Compose final drawer body
    drawerBody.innerHTML = `
        ${summaryHTML}

        <div class="drawer-section">
            <div class="drawer-section-title">
                <i class="fa-solid fa-code"></i>
                Skill Matching (${matchedCount} of ${totalCount} skills matched)
            </div>
            ${matchedHTML || '<p style="color:var(--text-muted);font-size:13px;">No skills matched.</p>'}
        </div>

        ${missingCount > 0 ? `
        <div class="drawer-section">
            <div class="drawer-section-title">
                <i class="fa-solid fa-circle-xmark" style="color:var(--red);"></i>
                Missing Skills
            </div>
            ${missingHTML}
        </div>` : ""}

        <div class="drawer-section">
            <div class="drawer-section-title">
                <i class="fa-solid fa-briefcase"></i>
                Experience Analysis
            </div>
            ${experienceHTML}
        </div>

        ${recommendHTML}`;
}

/* ==========================================================
   INTERVIEW QUESTIONS  —  POST /interview/generate-questions
========================================================== */
generateQuestionsBtn.addEventListener("click", async () => {
    const jobId       = document.getElementById("interviewJob").value;
    const questionType = document.getElementById("questionType").value;

    if (!jobId) {
        showToast("Please select a job position.", true);
        return;
    }

    generatedQuestions.innerHTML = `
        <div class="empty-state">
            <i class="fa-solid fa-spinner fa-spin" style="font-size:22px;color:var(--primary);"></i>
            <p>AI is generating questions...</p>
        </div>`;

    generateQuestionsBtn.disabled = true;
    generateQuestionsBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Generating...`;

    try {
        const response = await fetch(`${API}/interview/generate-questions`, {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body:    JSON.stringify({
                job_id:        parseInt(jobId),
                question_type: questionType
            })
        });

        const data = await response.json();

        if (!response.ok) throw new Error(data.detail || "Failed to generate questions.");

        displayGeneratedQuestions(data.questions, parseInt(jobId), questionType);

    } catch (error) {
        console.error("Interview Question Error:", error);
        generatedQuestions.innerHTML = `
            <div class="empty-state">
                <i class="fa-solid fa-triangle-exclamation" style="color:#dc2626;"></i>
                <p>${escapeHTML(error.message) || "Failed to generate questions. Is the backend running?"}</p>
            </div>`;
        showToast(error.message || "Failed to generate questions.", true);
    } finally {
        generateQuestionsBtn.disabled = false;
        generateQuestionsBtn.innerHTML = `<i class="fa-solid fa-wand-magic-sparkles"></i> Generate Questions`;
    }
});

function displayGeneratedQuestions(questions, jobId, questionType) {
    // questions is already an array from the API
    if (!Array.isArray(questions) || questions.length === 0) {
        generatedQuestions.innerHTML = `
            <div class="empty-state">
                <i class="fa-solid fa-triangle-exclamation" style="color:#dc2626;"></i>
                <p>No questions were generated. Please try again.</p>
            </div>`;
        return;
    }

    // Reset per-question regeneration counters for this new set
    regenCounts.clear();

    generatedQuestions.innerHTML = "";

    questions.forEach((question, index) => {
        regenCounts.set(index, 0);

        const card = document.createElement("div");
        card.className = "question-card";
        card.id = `question-card-${index}`;
        card.dataset.jobId        = jobId;
        card.dataset.questionType = questionType;

        card.innerHTML = `
            <div class="question-number">${index + 1}</div>
            <div class="question-body">
                <div class="question-text">${escapeHTML(question)}</div>
                <button
                    class="btn-regenerate"
                    id="regen-btn-${index}"
                    title="Regenerate this question (${MAX_REGENS - 0} remaining)"
                    onclick="regenerateSingleQuestion(${index})"
                >
                    <i class="fa-solid fa-rotate"></i>
                    Regenerate <span class="regen-count-label">(${MAX_REGENS} left)</span>
                </button>
            </div>`;
        generatedQuestions.appendChild(card);
    });
}

async function regenerateSingleQuestion(index) {
    const card = document.getElementById(`question-card-${index}`);
    if (!card) return;

    const jobId        = parseInt(card.dataset.jobId);
    const questionType = card.dataset.questionType;
    const regenBtn     = document.getElementById(`regen-btn-${index}`);
    const textEl       = card.querySelector(".question-text");

    // Guard: enforce max regenerations
    const currentCount = regenCounts.get(index) || 0;
    if (currentCount >= MAX_REGENS) return;

    // Loading state
    regenBtn.disabled = true;
    regenBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Regenerating...`;
    textEl.style.opacity = "0.4";
    textEl.style.transition = "opacity 0.2s";

    const currentQuestion = textEl.textContent.trim();

    try {
        const response = await fetch(`${API}/interview/regenerate-question`, {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body:    JSON.stringify({
                job_id:        jobId,
                question_type: questionType,
                question:      currentQuestion
            })
        });

        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Failed to regenerate question.");

        // Replace only this question's text
        textEl.textContent = data.question.trim();
        textEl.style.opacity = "1";

        // Increment and persist the counter for this question
        const newCount = currentCount + 1;
        regenCounts.set(index, newCount);

        const remaining = MAX_REGENS - newCount;

        if (newCount >= MAX_REGENS) {
            // Lock the button permanently
            regenBtn.disabled = true;
            regenBtn.innerHTML = `<i class="fa-solid fa-ban"></i> Regeneration limit reached`;
            regenBtn.classList.add("btn-regenerate--exhausted");
        } else {
            regenBtn.disabled = false;
            regenBtn.innerHTML = `
                <i class="fa-solid fa-rotate"></i>
                Regenerate <span class="regen-count-label">(${remaining} left)</span>`;
            regenBtn.title = `Regenerate this question (${remaining} remaining)`;
        }

        showToast(`Question ${index + 1} regenerated.`);

    } catch (error) {
        console.error("Regenerate Error:", error);
        textEl.style.opacity = "1";

        const remaining = MAX_REGENS - currentCount;
        regenBtn.disabled = false;
        regenBtn.innerHTML = `
            <i class="fa-solid fa-rotate"></i>
            Regenerate <span class="regen-count-label">(${remaining} left)</span>`;

        showToast(error.message || "Failed to regenerate question.", true);
    }
}

/* ==========================================================
   INITIAL PAGE LOAD
========================================================== */
window.addEventListener("DOMContentLoaded", () => {
    // Wire candidate search input immediately (no API needed)
    const searchInput = document.getElementById("candidateSearchInput");
    if (searchInput) {
        searchInput.addEventListener("input", () => filterCandidates(searchInput.value));
    }

    // Restore the active page from URL hash (survives Live Server auto-reloads)
    const hash = window.location.hash.replace("#", ""); // e.g. "jobsPage"
    const targetPage = hash ? document.getElementById(hash) : null;
    const targetMenuItem = hash
        ? document.querySelector(`[data-page="${hash}"]`)
        : null;

    if (targetPage && targetMenuItem) {
        // Deactivate defaults
        pages.forEach(p => p.classList.remove("active-page"));
        menuItems.forEach(i => i.classList.remove("active"));
        // Activate the saved page
        targetPage.classList.add("active-page");
        targetMenuItem.classList.add("active");

        // Lazy-load if needed
        if (hash === "matchingPage") loadJobsIntoDropdown();
        if (hash === "dashboardPage") {
            if (typeof loadDashboard === "function") loadDashboard();
        }
        if (hash === "voiceScreeningPage") {
            loadVsDropdowns();
        }
    }

    // Load dynamic data asynchronously in parallel after UI is painted.
    // Using Promise.all so all requests fire simultaneously instead of awaiting each one.
    Promise.all([
        loadStats(),
        loadLatestCandidate(),
        loadCandidates(),
        loadJobListingGrid(),
        loadJobsIntoDropdown(),
        loadCandidatesIntoSimDropdown(),
        loadAtsCandidates()
    ]).catch(err => console.error("Startup parallel load error:", err));
});

/* ==========================================================
   UTILITIES
========================================================== */
function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function safeParseJSON(value, fallback) {
    try {
        if (Array.isArray(value)) return value;
        return JSON.parse(value || "null") || fallback;
    } catch {
        return fallback;
    }
}

function escapeHTML(str) {
    if (!str) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

/* ==========================================================
   AI INTERVIEW SIMULATION
========================================================== */

/* ----------------------------------------------------------
   Load candidates into the simulation Candidate dropdown
---------------------------------------------------------- */
async function loadCandidatesIntoSimDropdown() {
    const sel = document.getElementById("interviewCandidate");
    if (!sel) return;
    try {
        const res        = await fetch(`${API}/candidates`, { cache: "no-store" });
        const candidates = await res.json();

        const currentVal = sel.value;
        sel.innerHTML = `<option value="">Select candidate</option>`;
        candidates.forEach(c => {
            const opt = document.createElement("option");
            opt.value       = c.id;
            opt.textContent = c.name || `Candidate #${c.id}`;
            sel.appendChild(opt);
        });
        if (currentVal) sel.value = currentVal;
    } catch (err) {
        console.error("Load Candidates Sim Dropdown Error:", err);
    }
}

/* ----------------------------------------------------------
   Start Interview  —  POST /interview/start
---------------------------------------------------------- */
startInterviewBtn.addEventListener("click", async () => {
    const candidateId   = document.getElementById("interviewCandidate").value;
    const jobId         = document.getElementById("simInterviewJob").value;
    const interviewMode = document.getElementById("interviewMode").value;

    if (!candidateId) { showToast("Please select a candidate.", true); return; }
    if (!jobId)       { showToast("Please select a job position.", true); return; }
    if (!interviewMode) { showToast("Please select an interview mode.", true); return; }

    startInterviewBtn.disabled = true;
    startInterviewBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Starting...`;

    // Clear and show loading in chat
    interviewChat.innerHTML = `
        <div class="chat-empty">
            <i class="fa-solid fa-spinner fa-spin" style="font-size:28px;color:var(--primary);"></i>
            <p>Connecting to AI Interviewer...</p>
        </div>`;

    try {
        const response = await fetch(`${API}/interview/start`, {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body:    JSON.stringify({
                candidate_id:   parseInt(candidateId),
                job_id:         parseInt(jobId),
                interview_mode: interviewMode
            })
        });

        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Failed to start interview.");

        // Store session and activate chat
        currentSessionId = data.session_id;
        simulationActive = true;

        interviewChat.innerHTML = "";
        appendChatMessage("ai", data.initial_message);

        // Enable input controls
        candidateResponse.disabled = false;
        sendResponseBtn.disabled   = false;
        endInterviewBtn.disabled   = false;
        candidateResponse.focus();

        // Disable start controls to prevent double-start
        document.getElementById("interviewCandidate").disabled = true;
        document.getElementById("simInterviewJob").disabled    = true;
        document.getElementById("interviewMode").disabled      = true;
        startInterviewBtn.innerHTML = `<i class="fa-solid fa-circle-check"></i> In Progress`;
        
        await loadAtsCandidates();

    } catch (error) {
        console.error("Start Interview Error:", error);
        const isUnavailable = error.message && (
            error.message.toLowerCase().includes("unavailable") ||
            error.message.toLowerCase().includes("rate limit") ||
            error.message.toLowerCase().includes("authentication") ||
            error.message.toLowerCase().includes("try again")
        );
        const displayMsg = isUnavailable
            ? error.message
            : (error.message || "Failed to start interview. Is the backend running?");
        interviewChat.innerHTML = `
            <div class="chat-empty">
                <i class="fa-solid fa-triangle-exclamation" style="color:#dc2626;font-size:28px;"></i>
                <p>${escapeHTML(displayMsg)}</p>
            </div>`;
        showToast(displayMsg, true);
        startInterviewBtn.disabled = false;
        startInterviewBtn.innerHTML = `<i class="fa-solid fa-play"></i> Start Interview`;
    }
});

/* ----------------------------------------------------------
   Send message  —  POST /interview/{session_id}/message
---------------------------------------------------------- */
sendResponseBtn.addEventListener("click", sendSimMessage);

candidateResponse.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !sendResponseBtn.disabled) sendSimMessage();
});

async function sendSimMessage() {
    const message = candidateResponse.value.trim();
    if (!message)           return;
    if (!simulationActive)  return;
    if (!currentSessionId)  return;

    // Show user bubble immediately
    appendChatMessage("user", message);
    candidateResponse.value    = "";
    sendResponseBtn.disabled   = true;
    candidateResponse.disabled = true;

    // Show AI typing indicator
    const typingId = appendAiTyping();

    try {
        const response = await fetch(`${API}/interview/${currentSessionId}/message`, {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body:    JSON.stringify({ message })
        });

        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Failed to send message.");

        // Replace typing indicator with real AI response
        const typingEl = document.getElementById(typingId);
        if (typingEl) typingEl.remove();
        appendChatMessage("ai", data.ai_response);

    } catch (error) {
        console.error("Send Message Error:", error);
        const typingEl = document.getElementById(typingId);
        if (typingEl) typingEl.remove();
        const isUnavailable = error.message && (
            error.message.toLowerCase().includes("unavailable") ||
            error.message.toLowerCase().includes("rate limit") ||
            error.message.toLowerCase().includes("try again")
        );
        const errMsg = isUnavailable
            ? error.message
            : "⚠️ AI service temporarily unavailable. Please try again.";
        appendChatMessage("ai", errMsg);
        showToast(error.message || "Failed to get AI response.", true);
    } finally {
        sendResponseBtn.disabled   = false;
        candidateResponse.disabled = false;
        candidateResponse.focus();
    }
}

/* ----------------------------------------------------------
   End Interview  —  POST /interview/{session_id}/end
---------------------------------------------------------- */
endInterviewBtn.addEventListener("click", async () => {
    if (!currentSessionId) return;

    endInterviewBtn.disabled   = true;
    sendResponseBtn.disabled   = true;
    candidateResponse.disabled = true;
    endInterviewBtn.innerHTML  = `<i class="fa-solid fa-spinner fa-spin"></i> Ending...`;

    try {
        const response = await fetch(`${API}/interview/${currentSessionId}/end`, {
            method:  "POST",
            headers: { "Content-Type": "application/json" }
        });

        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Failed to end interview.");

        simulationActive = false;
        
        // Ensure inputs are permanently disabled until reset
        sendResponseBtn.disabled   = true;
        candidateResponse.disabled = true;
        endInterviewBtn.style.display = "none"; // Hide end button to prevent confusion
        
        showSimSummary(data.summary);
        showToast("Interview ended. Summary generated.");
        
        await loadAtsCandidates();

    } catch (error) {
        console.error("End Interview Error:", error);
        const isUnavailable = error.message && (
            error.message.toLowerCase().includes("unavailable") ||
            error.message.toLowerCase().includes("rate limit") ||
            error.message.toLowerCase().includes("try again")
        );
        const errMsg = isUnavailable
            ? error.message
            : (error.message || "Failed to end the interview.");
        showToast(errMsg, true);
        endInterviewBtn.disabled = false;
        endInterviewBtn.innerHTML = `<i class="fa-solid fa-flag-checkered"></i> End`;
    }
});

/* ----------------------------------------------------------
   Helper: append a chat bubble (role: "ai" | "user")
---------------------------------------------------------- */
function appendChatMessage(role, text) {
    const div = document.createElement("div");
    div.className = `chat-message ${role}`;

    const prefix = role === "ai"
        ? `<span class="chat-role-label"><i class="fa-solid fa-robot"></i> NovaAI</span>`
        : `<span class="chat-role-label"><i class="fa-solid fa-user"></i> You</span>`;

    div.innerHTML = `${prefix}<p>${escapeHTML(text)}</p>`;
    interviewChat.appendChild(div);
    interviewChat.scrollTop = interviewChat.scrollHeight;
}

/* ----------------------------------------------------------
   Helper: append AI typing indicator, return its DOM id
---------------------------------------------------------- */
function appendAiTyping() {
    const id  = `typing-${Date.now()}`;
    const div = document.createElement("div");
    div.className = "chat-message ai chat-typing";
    div.id = id;
    div.innerHTML = `
        <span class="chat-role-label"><i class="fa-solid fa-robot"></i> NovaAI</span>
        <p class="typing-dots"><span></span><span></span><span></span></p>`;
    interviewChat.appendChild(div);
    interviewChat.scrollTop = interviewChat.scrollHeight;
    return id;
}

/* ----------------------------------------------------------
   Helper: display the interview summary card (Structured JSON)
---------------------------------------------------------- */
function showSimSummary(summary) {
    let summaryData = summary;
    if (typeof summary === "string") {
        try {
            summaryData = JSON.parse(summary);
        } catch (e) {
            summaryData = {
                overall_score: "N/A",
                skill_ratings: [],
                strengths: [],
                areas_for_improvement: [],
                overall_feedback: summary
            };
        }
    }

    const overallScore = summaryData.overall_score || "N/A";
    const skillRatings = Array.isArray(summaryData.skill_ratings) ? summaryData.skill_ratings : [];
    const strengths = Array.isArray(summaryData.strengths) ? summaryData.strengths : [];
    const improvements = Array.isArray(summaryData.areas_for_improvement) ? summaryData.areas_for_improvement : [];
    const overallFeedback = summaryData.overall_feedback || "No feedback available.";

    let skillsHtml = "";
    if (skillRatings.length > 0) {
        skillsHtml = skillRatings.map(s => `
            <div class="feedback-skill-row">
                <span class="fs-name">${escapeHTML(s.skill)}</span>
                <span class="fs-score">${s.score} / 10</span>
            </div>
        `).join("");
    } else {
        skillsHtml = "<p style='color:var(--text-muted);font-size:13px;'>No skill ratings available.</p>";
    }

    let strengthsHtml = strengths.length > 0
        ? `<ul class="feedback-list">${strengths.map(s => `<li>${escapeHTML(s)}</li>`).join("")}</ul>`
        : "<p style='color:var(--text-muted);font-size:13px;'>None specified.</p>";

    let improvementsHtml = improvements.length > 0
        ? `<ul class="feedback-list">${improvements.map(i => `<li>${escapeHTML(i)}</li>`).join("")}</ul>`
        : "<p style='color:var(--text-muted);font-size:13px;'>None specified.</p>";

    const summaryDiv = document.createElement("div");
    summaryDiv.className = "sim-summary-card";
    summaryDiv.innerHTML = `
        <div class="sim-summary-header">
            <i class="fa-solid fa-clipboard-check"></i> Interview Feedback
        </div>
        
        <div class="feedback-section">
            <div class="feedback-overall-score">
                <span class="fos-label">Overall Score</span>
                <span class="fos-value">${overallScore} <span style="font-size:16px;opacity:0.7">/ 10</span></span>
            </div>
        </div>

        <div class="feedback-section">
            <h4 class="feedback-section-title">Skill Ratings</h4>
            ${skillsHtml}
        </div>

        <div class="feedback-section">
            <h4 class="feedback-section-title">Strengths</h4>
            ${strengthsHtml}
        </div>

        <div class="feedback-section">
            <h4 class="feedback-section-title">Areas for Improvement</h4>
            ${improvementsHtml}
        </div>

        <div class="feedback-section">
            <h4 class="feedback-section-title">Overall Feedback</h4>
            <p class="sim-summary-text">${escapeHTML(overallFeedback)}</p>
        </div>

        <button class="btn-primary sim-restart-btn" style="margin-top:20px;" onclick="resetSimulation()">
            <i class="fa-solid fa-rotate-left"></i> Start New Interview
        </button>`;
    
    interviewChat.appendChild(summaryDiv);
    interviewChat.scrollTop = interviewChat.scrollHeight;
}

/* ----------------------------------------------------------
   Reset simulation state (Start New Interview)
---------------------------------------------------------- */
function resetSimulation() {
    currentSessionId = null;
    simulationActive = false;

    // Re-enable controls
    document.getElementById("interviewCandidate").disabled = false;
    document.getElementById("simInterviewJob").disabled    = false;
    document.getElementById("interviewMode").disabled      = false;
    startInterviewBtn.disabled = false;
    startInterviewBtn.innerHTML = `<i class="fa-solid fa-play"></i> Start Interview`;

    sendResponseBtn.disabled   = true;
    endInterviewBtn.disabled   = true;
    endInterviewBtn.style.display = ""; // Reset display
    candidateResponse.disabled = true;
    candidateResponse.value    = "";
    endInterviewBtn.innerHTML  = `<i class="fa-solid fa-flag-checkered"></i> End`;

    interviewChat.innerHTML = `
        <div class="chat-empty">
            <i class="fa-solid fa-comments"></i>
            <p>Start an interview to begin the AI-simulated conversation.</p>
        </div>`;
}

/* ==========================================================
   ATS INTEGRATION (MILESTONE 3)
========================================================== */
async function loadAtsCandidates() {
    const atsList = document.getElementById("atsCandidates");
    if (!atsList) return;

    try {
        const response = await fetch(`${API}/interview/ats-status`, { cache: "no-store" });

        // Only parse + render if request succeeded
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: Failed to load ATS status`);
        }

        const data = await response.json();
        const candidates = data.candidates || [];

        // Clear container ONLY after we have confirmed data
        atsList.innerHTML = "";

        if (candidates.length === 0) {
            atsList.innerHTML = `
                <div class="ats-row">
                    <div class="ats-candidate"><strong>No candidates in database</strong></div>
                    <span class="status-badge" style="background:#f1f5f9;color:#64748b;padding:4px 10px;border-radius:12px;font-size:12px;font-weight:500;">—</span>
                </div>`;
            return;
        }

        candidates.forEach(c => {
            const row = document.createElement("div");
            row.className = "ats-row";

            let statusText = c.status || "Not scheduled";
            let badgeStyle = "background:#f1f5f9;color:#64748b;"; // Not scheduled (default)
            if (statusText === "Interview in progress") {
                badgeStyle = "background:#dbeafe;color:#1e40af;";
            } else if (statusText === "Completed") {
                badgeStyle = "background:#dcfce7;color:#166534;";
            }

            const matchInfo = (c.match_percentage !== undefined && c.match_percentage !== null)
                ? `${c.match_percentage}% match &middot; ${escapeHTML(c.job_title)}`
                : escapeHTML(c.job_title);

            row.innerHTML = `
                <div class="ats-candidate">
                    <strong>${escapeHTML(c.candidate_name)}</strong>
                    <div class="ats-match-info" style="font-size:13px;color:#64748b;margin-top:2px;">
                        ${matchInfo}
                    </div>
                </div>
                <span class="status-badge" style="${badgeStyle} padding:4px 10px;border-radius:12px;font-size:12px;font-weight:500;">
                    ${escapeHTML(statusText)}
                </span>
            `;
            atsList.appendChild(row);
        });

    } catch (err) {
        console.error("ATS load failed:", err);
        // Preserve whatever is already in the container — do NOT replace with blank.
        // Only add an error notice if the container is empty / still shows the loading spinner.
        const hasRealContent = atsList.querySelectorAll(".ats-row:not(#ats-loading-row)").length > 0;
        if (!hasRealContent) {
            atsList.innerHTML = `
                <div class="ats-row" style="color:#dc2626;">
                    <div class="ats-candidate">
                        <i class="fa-solid fa-triangle-exclamation" style="margin-right:6px;"></i>
                        Unable to load ATS status. Is the backend running?
                    </div>
                </div>`;
        }
    }
}


/* ==========================================================
   MILESTONE 4 — DASHBOARD CONTROLLER (REAL PROJECT DATA ONLY)
   GET /dashboard/analytics — 100% DB-only, 0 external AI calls
========================================================== */

let dbCharts = {
    matching: null,
    skills: null,
    interview: null,
    voice: null
};

async function loadDashboard() {
    const strip = document.getElementById("dbQuickStrip");
    if (!strip) return;

    if (!strip.children.length || strip.querySelector(".db-strip-loading")) {
        strip.innerHTML = `<div class="db-strip-loading"><i class="fa-solid fa-spinner fa-spin"></i> Loading live analytics...</div>`;
    }

    const refreshBtn = document.getElementById("refreshDashboardBtn");
    if (refreshBtn) {
        const icon = refreshBtn.querySelector("i");
        if (icon) icon.classList.add("fa-spin");
    }

    try {
        const res = await fetch(`${API}/dashboard/analytics`, { cache: "no-store" });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        // 1. Render Quick Stats Strip
        renderQuickStrip(data.overview || {});

        // 2. Render Charts (ATS Matching & Skills)
        renderMatchingChart(data.matching_analytics || {}, data.overview?.total_jobs || 0);
        renderSkillsChart(data.skills_distribution || [], data.overview?.total_candidates || 0);

        // 3. Render Evaluation Charts (AI Interview & Voice Screening)
        renderInterviewChart(data.interview_analytics || {}, data.overview?.avg_interview_score);
        renderVoiceChart(data.voice_screening_analytics || {}, data.overview?.avg_voice_score);

        // 4. Render Evaluation Method Comparison
        renderEvaluationComparison(data.evaluation_comparison || {});

        // 5. Render Recent Candidates Table
        renderRecentCandidates(data.recent_candidates || []);

        // 6. Render Hiring Decisions
        renderHiringDecisions(data.hiring_decisions?.list || []);

        // 7. Update Timestamp
        const lastUpdated = document.getElementById("dbLastUpdated");
        if (lastUpdated) {
            const now = new Date();
            const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            lastUpdated.innerHTML = `<i class="fa-regular fa-clock"></i> Updated at ${timeStr}`;
        }

    } catch (err) {
        console.error("Dashboard loading error:", err);
        strip.innerHTML = `<div class="db-strip-loading" style="color:var(--red)"><i class="fa-solid fa-triangle-exclamation"></i> Unable to load analytics. Is the backend running?</div>`;
    } finally {
        if (refreshBtn) {
            const icon = refreshBtn.querySelector("i");
            if (icon) icon.classList.remove("fa-spin");
        }
    }
}

function renderQuickStrip(ov) {
    const strip = document.getElementById("dbQuickStrip");
    if (!strip) return;

    const avgIvScore = ov.avg_interview_score !== null && ov.avg_interview_score !== undefined
        ? `${ov.avg_interview_score}/10`
        : "N/A";

    const avgVsScore = ov.avg_voice_score !== null && ov.avg_voice_score !== undefined
        ? `${ov.avg_voice_score}/10`
        : "N/A";

    strip.innerHTML = `
        <div class="db-stat-item">
            <div class="db-stat-icon icon-blue">
                <i class="fa-solid fa-users"></i>
            </div>
            <div class="db-stat-content">
                <span class="db-stat-val">${ov.total_candidates ?? 0}</span>
                <span class="db-stat-lbl">Candidates</span>
                <span class="db-stat-sub">Parsed profiles</span>
            </div>
        </div>

        <div class="db-stat-item">
            <div class="db-stat-icon icon-orange">
                <i class="fa-solid fa-briefcase"></i>
            </div>
            <div class="db-stat-content">
                <span class="db-stat-val">${ov.total_jobs ?? 0}</span>
                <span class="db-stat-lbl">Job Roles</span>
                <span class="db-stat-sub">Active postings</span>
            </div>
        </div>

        <div class="db-stat-item">
            <div class="db-stat-icon icon-green">
                <i class="fa-solid fa-comments"></i>
            </div>
            <div class="db-stat-content">
                <span class="db-stat-val">${ov.completed_interviews ?? 0}</span>
                <span class="db-stat-lbl">AI Interviews</span>
                <span class="db-stat-sub">${ov.total_interviews ?? 0} total sessions</span>
            </div>
        </div>

        <div class="db-stat-item">
            <div class="db-stat-icon icon-purple">
                <i class="fa-solid fa-microphone-lines"></i>
            </div>
            <div class="db-stat-content">
                <span class="db-stat-val">${ov.completed_voice_screenings ?? 0}</span>
                <span class="db-stat-lbl">Voice Screenings</span>
                <span class="db-stat-sub">${ov.total_voice_screenings ?? 0} total sessions</span>
            </div>
        </div>

        <div class="db-stat-item">
            <div class="db-stat-icon icon-amber">
                <i class="fa-solid fa-star"></i>
            </div>
            <div class="db-stat-content">
                <span class="db-stat-val">${avgIvScore}</span>
                <span class="db-stat-lbl">Avg Interview</span>
                <span class="db-stat-sub">Detailed chat score</span>
            </div>
        </div>

        <div class="db-stat-item">
            <div class="db-stat-icon icon-teal">
                <i class="fa-solid fa-waveform-lines"></i>
            </div>
            <div class="db-stat-content">
                <span class="db-stat-val">${avgVsScore}</span>
                <span class="db-stat-lbl">Avg Voice Score</span>
                <span class="db-stat-sub">Preliminary screen</span>
            </div>
        </div>
    `;
}

function renderMatchingChart(matching, totalJobs) {
    const canvas = document.getElementById("matchingChart");
    const footer = document.getElementById("matchingSummaryText");
    if (!canvas) return;

    const tiers = matching.tiers || {};
    const labels = Object.keys(tiers);
    const data = Object.values(tiers);
    const hasData = data.some(v => v > 0);

    if (footer) {
        footer.innerHTML = `<span><strong>${matching.total_evaluations || 0}</strong> match evaluations</span><span>across <strong>${totalJobs}</strong> active job roles</span>`;
    }

    if (dbCharts.matching) {
        dbCharts.matching.destroy();
        dbCharts.matching = null;
    }

    if (typeof Chart === "undefined" || !hasData) {
        canvas.parentElement.innerHTML = `<div class="db-strip-loading"><i class="fa-solid fa-circle-info"></i> No candidate matching evaluations yet. Create jobs and upload candidates to populate.</div>`;
        return;
    }

    const ctx = canvas.getContext("2d");
    dbCharts.matching = new Chart(ctx, {
        type: "doughnut",
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: [
                    "#10b981", // Excellent (green)
                    "#3b82f6", // Strong (blue)
                    "#f59e0b", // Moderate (amber)
                    "#cbd5e1"  // Low (slate)
                ],
                borderWidth: 2,
                borderColor: "#ffffff"
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: "right",
                    labels: { boxWidth: 12, font: { size: 11, family: "Inter" }, color: "#475569" }
                },
                tooltip: {
                    callbacks: {
                        label: (item) => ` ${item.label}: ${item.raw} candidates`
                    }
                }
            },
            cutout: "68%"
        }
    });
}

function renderSkillsChart(skillsList, totalCandidates) {
    const canvas = document.getElementById("skillsChart");
    const footer = document.getElementById("skillsSummaryText");
    if (!canvas) return;

    if (footer) {
        footer.innerHTML = `<span>Real skills extracted from <strong>${totalCandidates}</strong> resumes</span><span>Top ${skillsList.length} skills shown</span>`;
    }

    if (dbCharts.skills) {
        dbCharts.skills.destroy();
        dbCharts.skills = null;
    }

    if (typeof Chart === "undefined" || !skillsList.length) {
        canvas.parentElement.innerHTML = `<div class="db-strip-loading"><i class="fa-solid fa-circle-info"></i> No skills extracted yet. Upload candidate resumes to view skill distribution.</div>`;
        return;
    }

    const labels = skillsList.map(s => s.skill);
    const data = skillsList.map(s => s.count);

    const ctx = canvas.getContext("2d");
    dbCharts.skills = new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                label: "Candidates with Skill",
                data: data,
                backgroundColor: "#ea580c",
                borderRadius: 4,
                maxBarThickness: 18
            }]
        },
        options: {
            indexAxis: "y",
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (item) => ` ${item.raw} candidate${item.raw !== 1 ? 's' : ''}`
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: { precision: 0, font: { size: 10, family: "Inter" }, color: "#64748b" },
                    grid: { color: "#f1f5f9" }
                },
                y: {
                    ticks: { font: { size: 11, family: "Inter", weight: 500 }, color: "#334155" },
                    grid: { display: false }
                }
            }
        }
    });
}

function renderInterviewChart(interviewData, avgScore) {
    const canvas = document.getElementById("interviewScoreChart");
    const footer = document.getElementById("interviewSummaryText");
    if (!canvas) return;

    const buckets = interviewData.score_buckets || {};
    const labels = ["0–2", "2.1–4", "4.1–6", "6.1–8", "8.1–10"];
    const data = [
        buckets["0-2"] || 0,
        buckets["2-4"] || 0,
        buckets["4-6"] || 0,
        buckets["6-8"] || 0,
        buckets["8-10"] || 0
    ];
    const totalDone = interviewData.status?.completed || 0;

    if (footer) {
        footer.innerHTML = `<span><strong>${totalDone}</strong> completed sessions</span><span>Avg score: <strong>${avgScore !== null && avgScore !== undefined ? avgScore + '/10' : 'N/A'}</strong></span>`;
    }

    if (dbCharts.interview) {
        dbCharts.interview.destroy();
        dbCharts.interview = null;
    }

    if (typeof Chart === "undefined" || !data.some(v => v > 0)) {
        canvas.parentElement.innerHTML = `<div class="db-strip-loading"><i class="fa-solid fa-circle-info"></i> No completed AI interview evaluations yet. Conduct an interview to populate.</div>`;
        return;
    }

    const ctx = canvas.getContext("2d");
    dbCharts.interview = new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                label: "Interviews in Score Range",
                data: data,
                backgroundColor: "#059669",
                borderRadius: 4,
                maxBarThickness: 28
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        title: (items) => `Score Range: ${items[0].label} / 10`,
                        label: (item) => ` ${item.raw} session${item.raw !== 1 ? 's' : ''}`
                    }
                }
            },
            scales: {
                x: {
                    ticks: { font: { size: 11, family: "Inter" }, color: "#64748b" },
                    grid: { display: false }
                },
                y: {
                    beginAtZero: true,
                    ticks: { precision: 0, font: { size: 10, family: "Inter" }, color: "#64748b" },
                    grid: { color: "#f1f5f9" }
                }
            }
        }
    });
}

function renderVoiceChart(voiceData, avgScore) {
    const canvas = document.getElementById("voiceRecChart");
    const footer = document.getElementById("voiceSummaryText");
    if (!canvas) return;

    // Use new decisions field (Screened / Not Screened)
    const decisions = voiceData.decisions || {};
    const screened    = decisions["Screened"]    || 0;
    const notScreened = decisions["Not Screened"] || 0;
    const labels = ["Screened", "Not Screened"];
    const data   = [screened, notScreened];
    const hasData = data.some(v => v > 0);

    const totalCompleted = voiceData.status?.completed || 0;
    const commScore = voiceData.scores?.communication;
    const screeningRate = voiceData.screening_rate;

    if (footer) {
        const rateStr  = screeningRate !== null && screeningRate !== undefined ? `${screeningRate}%` : 'N/A';
        const commStr  = commScore !== null && commScore !== undefined ? `${commScore}/10` : 'N/A';
        footer.innerHTML =
            `<span><strong>${totalCompleted}</strong> completed</span>` +
            `<span>Screened: <strong>${screened}</strong> &nbsp;|&nbsp; Not Screened: <strong>${notScreened}</strong></span>` +
            `<span>Rate: <strong>${rateStr}</strong></span>` +
            `<span>Avg Comm: <strong>${commStr}</strong></span>`;
    }

    if (dbCharts.voice) {
        dbCharts.voice.destroy();
        dbCharts.voice = null;
    }

    if (typeof Chart === "undefined" || !hasData) {
        canvas.parentElement.innerHTML = `<div class="db-strip-loading"><i class="fa-solid fa-circle-info"></i> No completed voice screenings yet. Conduct a preliminary voice screening to view results.</div>`;
        return;
    }

    const ctx = canvas.getContext("2d");
    dbCharts.voice = new Chart(ctx, {
        type: "doughnut",
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: [
                    "#10b981", // Screened (green)
                    "#ef4444"  // Not Screened (red)
                ],
                borderWidth: 2,
                borderColor: "#ffffff"
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: "right",
                    labels: { boxWidth: 12, font: { size: 11, family: "Inter" }, color: "#475569" }
                },
                tooltip: {
                    callbacks: {
                        label: (item) => ` ${item.label}: ${item.raw} screening${item.raw !== 1 ? 's' : ''}`
                    }
                }
            },
            cutout: "68%"
        }
    });
}

function renderEvaluationComparison(comp) {
    const el = document.getElementById("dashboardEvalComparison");
    if (!el) return;

    const iv = comp.ai_interview || { title: "AI Interview Assistant", total_sessions: 0, completed_sessions: 0, avg_score: "N/A" };
    const vs = comp.voice_screening || { title: "Voice Screening", total_sessions: 0, completed_sessions: 0, avg_score: "N/A" };

    el.innerHTML = `
        <div class="eval-comparison-grid">
            <!-- Method A: AI Interview Assistant -->
            <div class="eval-method-box">
                <div class="eval-method-header">
                    <div class="eval-method-icon eval-icon-interview">
                        <i class="fa-solid fa-comments"></i>
                    </div>
                    <div class="eval-method-titles">
                        <h4>${iv.title}</h4>
                        <span>Deep Technical &amp; Behavioral Chat Simulation</span>
                    </div>
                </div>

                <div class="eval-method-stats">
                    <div>
                        <div class="eval-stat-num">${iv.total_sessions}</div>
                        <div class="eval-stat-lbl">Sessions</div>
                    </div>
                    <div>
                        <div class="eval-stat-num" style="color:#059669">${iv.completed_sessions}</div>
                        <div class="eval-stat-lbl">Completed</div>
                    </div>
                    <div>
                        <div class="eval-stat-num" style="color:#d97706">${iv.avg_score}</div>
                        <div class="eval-stat-lbl">Avg Score</div>
                    </div>
                </div>

                <div class="eval-method-desc">
                    Generates customized technical/behavioral questions, assesses multi-turn response depth, and produces granular skill ratings.
                </div>
            </div>

            <!-- VS Badge -->
            <div class="eval-vs-badge">VS</div>

            <!-- Method B: Voice Screening -->
            <div class="eval-method-box">
                <div class="eval-method-header">
                    <div class="eval-method-icon eval-icon-voice">
                        <i class="fa-solid fa-microphone-lines"></i>
                    </div>
                    <div class="eval-method-titles">
                        <h4>${vs.title}</h4>
                        <span>Preliminary Voice &amp; Spoken Fit Screening</span>
                    </div>
                </div>

                <div class="eval-method-stats">
                    <div>
                        <div class="eval-stat-num">${vs.total_sessions}</div>
                        <div class="eval-stat-lbl">Sessions</div>
                    </div>
                    <div>
                        <div class="eval-stat-num" style="color:#7c3aed">${vs.completed_sessions}</div>
                        <div class="eval-stat-lbl">Completed</div>
                    </div>
                    <div>
                        <div class="eval-stat-num" style="color:#0d9488">${vs.avg_score}</div>
                        <div class="eval-stat-lbl">Avg Score</div>
                    </div>
                </div>

                <div class="eval-method-desc">
                    Browser speech-to-text screening focusing on verbal fluency, spoken communication, basic domain familiarity, and fast preliminary fit.
                </div>
            </div>
        </div>
        <p style="font-size:11px; color:var(--text-muted); margin-top:12px; line-height:1.5;">
            <i class="fa-solid fa-circle-info" style="color:var(--primary); margin-right:4px;"></i>
            <strong>Independent Evaluation Mechanisms</strong>: Voice Screening and AI Interview Assistant measure different dimensions. The platform maintains separate assessments so recruiters have comprehensive, multi-angle visibility into each candidate.
        </p>
    `;
}

function renderRecentCandidates(candidates) {
    const wrap = document.getElementById("recentCandidatesWrapper");
    if (!wrap) return;

    if (!candidates.length) {
        wrap.innerHTML = `<div class="db-strip-loading"><i class="fa-solid fa-users"></i> No candidates in the database yet.</div>`;
        return;
    }

    const rows = candidates.map(c => {
        const skillsHtml = (c.skills || []).map(s => `<span class="db-skill-pill">${s}</span>`).join("") || `<span style="font-size:11px;color:var(--text-muted)">No skills listed</span>`;
        const ivBadge = c.interview_completed
            ? `<span class="db-badge-done" title="AI Interview Completed"><i class="fa-solid fa-check"></i> Interviewed</span>`
            : `<span class="db-badge-pending">Pending</span>`;

        // Use voice_status field for accurate Screened / Not Screened / Pending display
        const voiceStatus = c.voice_status || (c.voice_completed ? "Screened" : "Pending");
        let vsBadge;
        if (voiceStatus === "Screened") {
            vsBadge = `<span class="db-badge-done" style="background:#f0fdf4;color:#16a34a;border:1px solid #bbf7d0" title="Voice Screening: Screened"><i class="fa-solid fa-check"></i> Screened</span>`;
        } else if (voiceStatus === "Not Screened") {
            vsBadge = `<span class="db-badge-done" style="background:#fef2f2;color:#dc2626;border:1px solid #fecaca" title="Voice Screening: Not Screened"><i class="fa-solid fa-xmark"></i> Not Screened</span>`;
        } else {
            vsBadge = `<span class="db-badge-pending">Pending</span>`;
        }

        return `
            <tr>
                <td>
                    <div class="db-cand-name">${c.name}</div>
                    <div class="db-cand-email">${c.email}</div>
                </td>
                <td>${skillsHtml}</td>
                <td>
                    <div style="display:flex;flex-direction:column;gap:4px;">
                        <div><small style="color:var(--text-muted);font-size:10px">AI Chat:</small> ${ivBadge}</div>
                        <div><small style="color:var(--text-muted);font-size:10px">Voice:</small> ${vsBadge}</div>
                    </div>
                </td>
            </tr>
        `;
    }).join("");

    wrap.innerHTML = `
        <table class="db-table-compact">
            <thead>
                <tr>
                    <th>Candidate</th>
                    <th>Extracted Skills</th>
                    <th>Evaluation Status</th>
                </tr>
            </thead>
            <tbody>
                ${rows}
            </tbody>
        </table>
    `;
}

function renderHiringDecisions(decisions) {
    const wrap = document.getElementById("hiringDecisionsWrapper");
    if (!wrap) return;

    if (!decisions.length) {
        wrap.innerHTML = `<div class="db-strip-loading"><i class="fa-solid fa-gavel"></i> No hiring decisions made yet.</div>`;
        return;
    }

    const itemsHtml = decisions.map(d => {
        let icon = "fa-clock";
        let color = "#6b7280";
        if (d.hiring_status === "HIRED") { icon = "fa-check"; color = "#10b981"; }
        else if (d.hiring_status === "NOT_SELECTED") { icon = "fa-xmark"; color = "#ef4444"; }
        else if (d.hiring_status === "IN_PROGRESS") { icon = "fa-spinner"; color = "#3b82f6"; }
        else if (d.hiring_status === "NOT_EVALUATED") { icon = "fa-circle-question"; color = "#8b5cf6"; }

        return `
        <div class="db-activity-row">
            <div class="db-act-icon" style="background:${color}18; color:${color}">
                <i class="fa-solid ${icon}"></i>
            </div>
            <div class="db-act-body">
                <div class="db-act-title">${d.name}</div>
                <div class="db-act-desc">${formatHiringStatus(d.hiring_status)}</div>
            </div>
            <div class="db-act-time"></div>
        </div>
        `;
    }).join("");

    wrap.innerHTML = `<div class="db-timeline">${itemsHtml}</div>`;
}

function getHiringStatusClass(status) {
    if (status === "HIRED") return "processed"; // Green-ish
    if (status === "NOT_SELECTED") return "error"; // Red-ish
    if (status === "IN_PROGRESS") return "pending"; // Blue/Yellow
    return "pending";
}

function formatHiringStatus(status) {
    if (!status) return "In Progress";
    if (status === "HIRED") return "Hired";
    if (status === "NOT_SELECTED") return "Not Selected";
    if (status === "IN_PROGRESS") return "In Progress";
    if (status === "NOT_EVALUATED") return "Pending";
    return status.replace(/_/g, " ");
}

async function updateHiringStatus(candidateId, status) {
    try {
        const res = await fetch(`${API}/candidates/${candidateId}/hiring-status`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ status })
        });
        if (!res.ok) {
            const data = await res.json();
            throw new Error(data.detail || "Failed to update status");
        }
        
        // Update modal UI instantly
        const modalStatusEl = document.getElementById("modalHiringStatus");
        if (modalStatusEl) {
            modalStatusEl.className = "status " + getHiringStatusClass(status);
            modalStatusEl.textContent = formatHiringStatus(status);
        }
        
        showToast("Hiring status updated to " + formatHiringStatus(status));
        
        // Refresh tables in background
        loadCandidates();
    } catch (err) {
        showToast(err.message, true);
    }
}


/* ==========================================================
   MILESTONE 4 — VOICE SCREENING
   Browser Web Speech API (SpeechRecognition + SpeechSynthesis)
   No audio files stored. Transcript saved to DB via backend API.
   Feature completely isolated: failure never affects M1-3.
========================================================== */

let vsSessionId            = null;
let vsActive               = false;
let vsRecognition          = null;
let vsTtsEnabled           = true;
let vsAccumulatedTranscript = "";  // accumulated answer text across multiple recognition sessions
let vsRecording            = false; // true while mic is actively capturing
let vsSubmitting           = false; // prevents double-submission

/* ----------------------------------------------------------
   Init — wire up VS button events
---------------------------------------------------------- */
function initVoiceScreening() {
    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    const warning = document.getElementById("vsBrowserWarning");
    if (!SpeechRec && warning) {
        warning.style.display = "flex";
    }

    const ttsChk = document.getElementById("vsTtsEnabled");
    if (ttsChk) ttsChk.addEventListener("change", () => { vsTtsEnabled = ttsChk.checked; });

    const startBtn = document.getElementById("vsStartBtn");
    const stopBtn  = document.getElementById("vsStopBtn");
    const saveBtn  = document.getElementById("vsSaveBtn");

    if (startBtn) startBtn.addEventListener("click", startVoiceScreening);
    if (stopBtn)  stopBtn.addEventListener("click",  vsToggleRecording);
    if (saveBtn)  saveBtn.addEventListener("click",  saveVoiceScreening);

    // Submit Answer button — sends the accumulated transcript to the AI
    const submitAnswerBtn = document.getElementById("vsSubmitAnswerBtn");
    if (submitAnswerBtn) submitAnswerBtn.addEventListener("click", vsSubmitAnswer);
}

/* ----------------------------------------------------------
   Status indicator helper
---------------------------------------------------------- */
function setVsStatus(statusKey, text) {
    const dot    = document.getElementById("vsStatusDot");
    const textEl = document.getElementById("vsStatusText");
    const visualizer = document.getElementById("vsVisualizerBox");
    if (dot)    dot.className = `vs-status-dot ${statusKey ? "vs-status-" + statusKey : ""}`;
    if (textEl) textEl.textContent = text;
    if (visualizer) {
        const waveText = visualizer.querySelector(".vs-wave-status-text");
        if (statusKey === "recording") {
            visualizer.classList.add("vs-visualizer-active");
            if (waveText) waveText.textContent = "Listening to voice input...";
        } else if (statusKey === "processing") {
            visualizer.classList.add("vs-visualizer-active");
            if (waveText) waveText.textContent = "AI Processing speech...";
        } else {
            visualizer.classList.remove("vs-visualizer-active");
            if (waveText) waveText.textContent = "Audio Engine Ready";
        }
    }
}

/* ----------------------------------------------------------
   Populate dropdowns with candidates and jobs
---------------------------------------------------------- */
async function loadVsDropdowns() {
    const vsCandSel = document.getElementById("vsCandidate");
    const vsJobSel  = document.getElementById("vsJob");
    if (!vsCandSel || !vsJobSel) return;

    try {
        const [cRes, jRes] = await Promise.all([
            fetch(`${API}/candidates`, { cache: "no-store" }).catch(() => ({ ok: false })),
            fetch(`${API}/jobs`,       { cache: "no-store" }).catch(() => ({ ok: false }))
        ]);
        const candidates = cRes.ok ? await cRes.json() : [];
        const jobs       = jRes.ok ? await jRes.json() : [];

        const prevCand = vsCandSel.value;
        const prevJob  = vsJobSel.value;

        vsCandSel.innerHTML = `<option value="">Select candidate</option>`;
        if (candidates.length === 0 && !cRes.ok) {
            const errOpt = document.createElement("option");
            errOpt.value = "";
            errOpt.textContent = "⚠️ Unable to load candidates (backend unavailable)";
            vsCandSel.appendChild(errOpt);
        } else {
            candidates.forEach(c => {
                const o = document.createElement("option");
                o.value = c.id;
                o.textContent = c.name || `Candidate #${c.id}`;
                vsCandSel.appendChild(o);
            });
        }
        if (prevCand) vsCandSel.value = prevCand;

        vsJobSel.innerHTML = `<option value="">Select job</option>`;
        if (jobs.length === 0 && !jRes.ok) {
            const errOpt = document.createElement("option");
            errOpt.value = "";
            errOpt.textContent = "⚠️ Unable to load jobs (backend unavailable)";
            vsJobSel.appendChild(errOpt);
        } else {
            jobs.forEach(j => {
                const o = document.createElement("option");
                o.value = j.id;
                o.textContent = j.title;
                vsJobSel.appendChild(o);
            });
        }
        if (prevJob) vsJobSel.value = prevJob;

    } catch (err) {
        console.error("VS dropdown error:", err);
    }
}

/* ----------------------------------------------------------
   Start screening — POST /voice-screening/start
---------------------------------------------------------- */
async function startVoiceScreening() {
    const candidateId = document.getElementById("vsCandidate")?.value;
    const jobId       = document.getElementById("vsJob")?.value;

    if (!candidateId) { showToast("Please select a candidate.", true); return; }
    if (!jobId)       { showToast("Please select a job position.", true); return; }

    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRec) {
        showToast("Voice recognition is not supported in this browser. Please use Chrome or Edge.", true);
        return;
    }

    const startBtn = document.getElementById("vsStartBtn");
    if (startBtn) { startBtn.disabled = true; startBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Connecting...`; }
    setVsStatus("processing", "Connecting to AI...");

    try {
        const res = await fetch(`${API}/voice-screening/start`, {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body:    JSON.stringify({ candidate_id: parseInt(candidateId), job_id: parseInt(jobId) })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Failed to start screening");

        vsSessionId = data.session_id;
        vsActive    = true;

        // Reset answer accumulator for fresh session
        vsAccumulatedTranscript = "";
        vsRecording             = false;
        vsSubmitting            = false;

        // Update control state
        if (startBtn) { startBtn.disabled = true; startBtn.innerHTML = `<i class="fa-solid fa-circle-check"></i> In Progress`; }
        const stopBtn = document.getElementById("vsStopBtn");
        if (stopBtn) { stopBtn.disabled = false; stopBtn.innerHTML = `<i class="fa-solid fa-stop"></i> Stop Recording`; }
        document.getElementById("vsCandidate").disabled = true;
        document.getElementById("vsJob").disabled = true;

        // Display first question
        vsSetCurrentQuestion(data.first_question);
        vsAppendTranscript("ai", data.first_question);

        // Speak it if TTS enabled, then start listening
        vsRecording = true;
        if (vsTtsEnabled) {
            vsSpeak(data.first_question, () => { if (vsActive && vsRecording) vsStartListening(); });
        } else {
            vsStartListening();
        }

        vsUpdateAnswerControls();
        setVsStatus("recording", "Listening...");
        showToast(`Voice screening started for ${data.candidate_name}.`);

    } catch (err) {
        console.error("VS start error:", err);
        showToast(err.message || "Failed to start voice screening.", true);
        setVsStatus("", "Ready");
        if (startBtn) { startBtn.disabled = false; startBtn.innerHTML = `<i class="fa-solid fa-microphone"></i> Start Screening`; }
    }
}

/* ----------------------------------------------------------
   Start browser SpeechRecognition for one capture session.

   KEY DESIGN (fix for auto-submit on pause):
   - recognition.onend does NOT submit the answer.
   - It only appends captured text to vsAccumulatedTranscript and
     restarts recognition so the candidate can keep speaking.
   - The answer is only sent to the backend when the candidate
     explicitly clicks "Submit Answer" (vsSubmitAnswer).
   - A natural 2-3 second pause just restarts the recogniser;
     no submission occurs.
   - Stops permanently on microphone-denied error.
---------------------------------------------------------- */
function vsStartListening() {
    if (!vsActive || !vsRecording) return;

    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRec) return;

    // Abort any previous recogniser before creating a new one
    if (vsRecognition) {
        try { vsRecognition.abort(); } catch (e) {}
        vsRecognition = null;
    }

    vsRecognition = new SpeechRec();
    vsRecognition.lang            = "en-US";
    vsRecognition.continuous      = false;  // browser still stops after ~2-3 s of silence
    vsRecognition.interimResults  = true;

    // Local text captured in this recognition session (not yet appended to accumulator)
    let sessionFinal   = "";
    let sessionInterim = "";

    vsRecognition.onstart = () => {
        setVsStatus("recording", "Listening... Speak now.");
    };

    vsRecognition.onresult = (event) => {
        sessionInterim = "";
        for (let i = event.resultIndex; i < event.results.length; i++) {
            if (event.results[i].isFinal) {
                sessionFinal += event.results[i][0].transcript;
            } else {
                sessionInterim += event.results[i][0].transcript;
            }
        }

        // Show accumulated + current session final + current interim
        const interimEl = document.getElementById("vsInterimText");
        if (interimEl) {
            const displayText = (vsAccumulatedTranscript + sessionFinal + sessionInterim).trim();
            interimEl.textContent = displayText ? `"${displayText}..."` : "";
        }

        vsUpdateAnswerControls();
    };

    vsRecognition.onend = () => {
        // ── IMPORTANT: onend is NOT a submission trigger ──
        // The browser stopped capturing (pause, silence, tab focus change).
        // We accumulate the text captured so far and restart automatically.

        if (sessionFinal.trim()) {
            if (vsAccumulatedTranscript && !vsAccumulatedTranscript.endsWith(" ")) {
                vsAccumulatedTranscript += " ";
            }
            vsAccumulatedTranscript += sessionFinal.trim();
            sessionFinal = "";
        }

        // Show accumulated text in interim display
        const interimEl = document.getElementById("vsInterimText");
        if (interimEl) {
            interimEl.textContent = vsAccumulatedTranscript
                ? `"${vsAccumulatedTranscript}..."`
                : "";
        }

        vsUpdateAnswerControls();

        // Restart recognition so candidate can keep speaking
        if (vsActive && vsRecording) {
            setVsStatus("recording", "Paused — listening again...");
            setTimeout(() => {
                if (vsActive && vsRecording) vsStartListening();
            }, 400);
        }
    };

    vsRecognition.onerror = (event) => {
        console.warn("SpeechRecognition error:", event.error);
        if (event.error === "not-allowed" || event.error === "service-not-allowed") {
            showToast("Microphone access denied. Please allow microphone in browser settings.", true);
            setVsStatus("", "Microphone denied");
            vsActive    = false;
            vsRecording = false;
            vsUpdateAnswerControls();
            const stopBtn = document.getElementById("vsStopBtn");
            const saveBtn = document.getElementById("vsSaveBtn");
            if (stopBtn) { stopBtn.disabled = true; stopBtn.innerHTML = `<i class="fa-solid fa-stop"></i> Stop Recording`; }
            if (saveBtn && vsSessionId) saveBtn.disabled = false;
        } else if (event.error === "no-speech") {
            // Natural — browser stopped because no sound; restart quietly
            if (vsActive && vsRecording) {
                setTimeout(() => { if (vsActive && vsRecording) vsStartListening(); }, 600);
            }
        } else if (event.error === "network") {
            showToast("Network error during speech recognition. Retrying...", true);
            setTimeout(() => { if (vsActive && vsRecording) vsStartListening(); }, 2500);
        } else if (event.error === "aborted") {
            // Intentional abort (e.g. when candidate clicks Stop Recording) — ignore
        } else {
            setTimeout(() => { if (vsActive && vsRecording) vsStartListening(); }, 2000);
        }
    };

    try {
        vsRecognition.start();
    } catch (startErr) {
        console.warn("SpeechRecognition.start() error:", startErr);
        setTimeout(() => { if (vsActive && vsRecording) vsStartListening(); }, 1500);
    }
}

/* ----------------------------------------------------------
   Toggle mic on/off without ending the session or submitting.
   "Stop Recording" pauses capture; "Resume Recording" restarts.
---------------------------------------------------------- */
function vsToggleRecording() {
    if (!vsActive) return;

    const stopBtn = document.getElementById("vsStopBtn");

    if (vsRecording) {
        // PAUSE recording — stop mic, keep accumulated text, do NOT submit
        vsRecording = false;
        if (vsRecognition) {
            try { vsRecognition.abort(); } catch (e) {}
            vsRecognition = null;
        }
        setVsStatus("recording", "Recording paused — click to resume.");
        if (stopBtn) stopBtn.innerHTML = `<i class="fa-solid fa-microphone"></i> Resume Recording`;
        vsUpdateAnswerControls();
    } else {
        // RESUME recording
        vsRecording = true;
        setVsStatus("recording", "Listening... Speak now.");
        if (stopBtn) stopBtn.innerHTML = `<i class="fa-solid fa-stop"></i> Stop Recording`;
        vsUpdateAnswerControls();
        vsStartListening();
    }
}

/* ----------------------------------------------------------
   Update Submit Answer button state based on accumulated transcript.
---------------------------------------------------------- */
function vsUpdateAnswerControls() {
    const submitBtn = document.getElementById("vsSubmitAnswerBtn");
    if (!submitBtn) return;
    const hasText = vsAccumulatedTranscript.trim().length > 0;
    submitBtn.disabled = !hasText || vsSubmitting || !vsActive;
}

/* ----------------------------------------------------------
   Explicitly submit the accumulated answer to the backend.
   This is the ONLY path that sends the answer — never automatic.
---------------------------------------------------------- */
async function vsSubmitAnswer() {
    const answer = vsAccumulatedTranscript.trim();
    if (!answer) {
        showToast("No speech captured yet. Please speak your answer first.", true);
        return;
    }
    if (!vsSessionId || !vsActive) return;
    if (vsSubmitting) return;  // prevent double-click

    vsSubmitting = true;
    vsUpdateAnswerControls();

    // Stop mic while AI is processing
    vsRecording = false;
    if (vsRecognition) {
        try { vsRecognition.abort(); } catch (e) {}
        vsRecognition = null;
    }

    // Clear interim display
    const interimEl = document.getElementById("vsInterimText");
    if (interimEl) interimEl.textContent = "";

    // Snapshot and reset accumulator for next answer
    const answerToSend = answer;
    vsAccumulatedTranscript = "";

    // Append the answer to the transcript panel
    vsAppendTranscript("candidate", answerToSend);
    setVsStatus("processing", "Processing response...");

    const stopBtn = document.getElementById("vsStopBtn");
    if (stopBtn) { stopBtn.disabled = true; stopBtn.innerHTML = `<i class="fa-solid fa-stop"></i> Stop Recording`; }

    await vsSendResponse(answerToSend);

    vsSubmitting = false;
    if (stopBtn && vsActive) { stopBtn.disabled = false; }
    vsUpdateAnswerControls();
}

/* ----------------------------------------------------------
   Send candidate transcript to backend — POST /voice-screening/{id}/respond
---------------------------------------------------------- */
async function vsSendResponse(spokenText) {
    if (!vsSessionId || !vsActive) return;

    try {
        const res = await fetch(`${API}/voice-screening/${vsSessionId}/respond`, {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body:    JSON.stringify({ transcript: spokenText })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Failed to get next question");

        const nextQ = data.next_question;
        vsSetCurrentQuestion(nextQ);
        vsAppendTranscript("ai", nextQ);

        // After AI responds, re-enable recording so candidate can answer next question
        vsRecording = true;
        const stopBtn = document.getElementById("vsStopBtn");
        if (stopBtn) { stopBtn.disabled = false; stopBtn.innerHTML = `<i class="fa-solid fa-stop"></i> Stop Recording`; }

        // Speak next question, then resume listening
        if (vsTtsEnabled) {
            vsSpeak(nextQ, () => { if (vsActive && vsRecording) vsStartListening(); });
        } else {
            if (vsActive && vsRecording) vsStartListening();
        }
        setVsStatus("recording", "Listening...");

    } catch (err) {
        console.error("VS respond error:", err);
        showToast(err.message || "AI failed to generate next question. Try submitting again.", true);
        setVsStatus("recording", "Error — try submitting again or stop recording.");
        // Re-enable recording on error so candidate can retry
        vsRecording = true;
        const stopBtn = document.getElementById("vsStopBtn");
        if (stopBtn) { stopBtn.disabled = false; stopBtn.innerHTML = `<i class="fa-solid fa-stop"></i> Stop Recording`; }
        vsUpdateAnswerControls();
    }
}

/* ----------------------------------------------------------
   Browser TTS — SpeechSynthesis
---------------------------------------------------------- */
function vsSpeak(text, onEndCallback) {
    if (!window.speechSynthesis) {
        // TTS not available — just continue
        if (onEndCallback) onEndCallback();
        return;
    }
    window.speechSynthesis.cancel(); // Stop any currently playing
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "en-US";
    utterance.rate = 0.95;
    utterance.pitch = 1.0;
    if (onEndCallback) utterance.onend = onEndCallback;
    utterance.onerror = () => { if (onEndCallback) onEndCallback(); }; // Continue even if TTS errors
    window.speechSynthesis.speak(utterance);
}

/* ----------------------------------------------------------
   Stop screening
---------------------------------------------------------- */
function stopVoiceScreening() {
    vsActive     = false;
    vsRecording  = false;
    vsSubmitting = false;

    if (vsRecognition) {
        try { vsRecognition.abort(); } catch (e) {}
        vsRecognition = null;
    }
    if (window.speechSynthesis) window.speechSynthesis.cancel();

    const stopBtn       = document.getElementById("vsStopBtn");
    const saveBtn       = document.getElementById("vsSaveBtn");
    const submitAnswBtn = document.getElementById("vsSubmitAnswerBtn");
    if (stopBtn) { stopBtn.disabled = true; stopBtn.innerHTML = `<i class="fa-solid fa-stop"></i> Stop Recording`; }
    if (saveBtn) saveBtn.disabled = false;
    if (submitAnswBtn) submitAnswBtn.disabled = true;

    // Clear interim
    const interimEl = document.getElementById("vsInterimText");
    if (interimEl) interimEl.textContent = "";

    setVsStatus("", "Stopped — click Save Screening to generate assessment");
    showToast("Screening stopped. Click 'Save Screening' to generate the assessment.");
}

/* ----------------------------------------------------------
   Save screening — POST /voice-screening/{id}/end
   Generates AI assessment and persists to DB.
---------------------------------------------------------- */
async function saveVoiceScreening() {
    if (!vsSessionId) {
        showToast("No active screening session to save.", true);
        return;
    }

    const saveBtn = document.getElementById("vsSaveBtn");
    if (saveBtn) { saveBtn.disabled = true; saveBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Generating Assessment...`; }
    setVsStatus("processing", "Generating assessment...");

    try {
        const res = await fetch(`${API}/voice-screening/${vsSessionId}/end`, {
            method:  "POST",
            headers: { "Content-Type": "application/json" }
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Failed to end screening");

        setVsStatus("", "Completed");
        vsDisplayAssessment(data.assessment);

        if (saveBtn) { saveBtn.innerHTML = `<i class="fa-solid fa-check"></i> Saved`; }
        showToast("Screening saved and assessment generated.");

    } catch (err) {
        console.error("VS save error:", err);
        showToast(err.message || "Failed to save screening.", true);
        setVsStatus("", "Save failed");
        if (saveBtn) { saveBtn.disabled = false; saveBtn.innerHTML = `<i class="fa-solid fa-floppy-disk"></i> Save Screening`; }
    }
}

/* ----------------------------------------------------------
   Helpers — transcript display
---------------------------------------------------------- */
function vsSetCurrentQuestion(question) {
    const el = document.getElementById("vsCurrentQuestion");
    if (el) el.textContent = question;
}

function vsAppendTranscript(role, content) {
    const container = document.getElementById("vsTranscriptContent");
    if (!container) return;

    // Remove placeholder on first real entry
    const ph = container.querySelector(".vs-placeholder");
    if (ph) ph.remove();

    // Ensure interim element stays at the bottom
    let interimEl = document.getElementById("vsInterimText");
    if (interimEl) interimEl.remove();

    const div = document.createElement("div");
    div.className = `vs-transcript-turn vs-turn-${role}`;
    div.innerHTML = `
        <span class="vs-turn-role">
            ${role === "ai"
                ? '<i class="fa-solid fa-robot"></i> NovaAI'
                : '<i class="fa-solid fa-user"></i> Candidate'}
        </span>
        <p>${escapeHTML(content)}</p>`;
    container.appendChild(div);

    // Re-append interim element
    interimEl = document.createElement("p");
    interimEl.id = "vsInterimText";
    interimEl.className = "vs-interim";
    container.appendChild(interimEl);

    container.scrollTop = container.scrollHeight;
}

/* ----------------------------------------------------------
   Render assessment panel after save
---------------------------------------------------------- */
function vsDisplayAssessment(assessment) {
    const panel   = document.getElementById("vsAssessmentPanel");
    const content = document.getElementById("vsAssessmentContent");
    if (!panel || !content) return;

    if (!assessment) { panel.style.display = "none"; return; }

    const ov   = assessment.overall_score       ?? "N/A";
    const comm = assessment.communication_score ?? "N/A";
    const tech = assessment.technical_score     ?? "N/A";
    const rec  = assessment.recommendation      || "Needs Further Evaluation";
    const fb   = assessment.overall_feedback    || "No feedback generated.";
    const str  = Array.isArray(assessment.strengths)              ? assessment.strengths              : [];
    const imp  = Array.isArray(assessment.areas_for_improvement)  ? assessment.areas_for_improvement  : [];

    // Deterministic Screened / Not Screened decision — same threshold as backend:
    //   SCREENED     = communication_score >= 5.5 AND overall_score >= 5.0
    //   NOT SCREENED = communication_score <  5.5 OR  overall_score <  5.0
    const commNum    = typeof comm === "number" ? comm : parseFloat(comm) || 0;
    const overallNum = typeof ov   === "number" ? ov   : parseFloat(ov)   || 0;
    const isScreened = (commNum >= 5.5 && overallNum >= 5.0) && !assessment.error;
    const screeningDecision = isScreened ? "SCREENED" : "NOT SCREENED";

    let recClass = "rec-consider";
    const recLow = rec.toLowerCase();
    if (recLow.includes("strong"))  recClass = "rec-strong";
    else if (recLow.includes("needs")) recClass = "rec-needs";

    content.innerHTML = `
        <!-- ═══ PRELIMINARY SCREENING RESULT BANNER ═══ -->
        <div style="
            display:flex; align-items:center; gap:14px;
            padding:18px 20px; border-radius:10px; margin-bottom:20px;
            background:${isScreened ? '#f0fdf4' : '#fef2f2'};
            border:2px solid ${isScreened ? '#16a34a' : '#dc2626'};
        ">
            <div style="
                width:48px; height:48px; border-radius:50%;
                background:${isScreened ? '#16a34a' : '#dc2626'};
                display:flex; align-items:center; justify-content:center;
                flex-shrink:0;
            ">
                <i class="fa-solid ${isScreened ? 'fa-check' : 'fa-xmark'}" style="color:#fff;font-size:20px;"></i>
            </div>
            <div style="flex:1;">
                <div style="font-size:11px;font-weight:600;color:var(--text-muted);text-transform:uppercase;letter-spacing:.06em;margin-bottom:2px;">Preliminary Voice Screening Result</div>
                <div style="font-size:20px;font-weight:800;color:${isScreened ? '#16a34a' : '#dc2626'};letter-spacing:.01em;">
                    ${isScreened ? '✓ SCREENED' : '✕ NOT SCREENED'}
                </div>
                <div style="font-size:11px;color:var(--text-muted);margin-top:2px;">
                    ${isScreened
                        ? 'Candidate meets the preliminary communication & professional suitability threshold.'
                        : 'Candidate did not meet the preliminary communication & suitability threshold.'}
                </div>
            </div>
            <div style="text-align:right;flex-shrink:0;">
                <div style="font-size:10px;color:var(--text-muted);margin-bottom:2px;">Threshold</div>
                <div style="font-size:11px;font-weight:600;color:var(--text-muted);">Comm ≥ 5.5 &amp; Overall ≥ 5.0</div>
            </div>
        </div>

        <!-- ═══ SCORE CARDS ═══ -->
        <div class="vs-assessment-scores">
            <div class="vs-score-card">
                <div class="vs-score-val">${ov}</div>
                <div class="vs-score-lbl">Overall</div>
                <div class="vs-score-max">/ 10</div>
            </div>
            <div class="vs-score-card">
                <div class="vs-score-val">${comm}</div>
                <div class="vs-score-lbl">Communication</div>
                <div class="vs-score-max">/ 10</div>
            </div>
            <div class="vs-score-card">
                <div class="vs-score-val">${tech}</div>
                <div class="vs-score-lbl">Domain Familiarity</div>
                <div class="vs-score-max">/ 10</div>
            </div>
            <div class="vs-recommendation ${recClass}">
                <i class="fa-solid fa-medal"></i>
                <span>${escapeHTML(rec)}</span>
                <small>AI recommendation · recruiter makes final decision</small>
            </div>
        </div>

        ${(str.length || imp.length) ? `
        <div class="vs-eval-2col">
            <div class="vs-assessment-section">
                <h4 class="vs-section-title"><i class="fa-solid fa-circle-check" style="color:#10b981"></i> Strengths</h4>
                ${str.length ? `<ul class="vs-list">${str.map(s => `<li>${escapeHTML(s)}</li>`).join("")}</ul>` : `<p class="vs-feedback-text" style="color:var(--text-muted);">None noted.</p>`}
            </div>
            <div class="vs-assessment-section">
                <h4 class="vs-section-title"><i class="fa-solid fa-circle-arrow-up" style="color:#f59e0b"></i> Areas for Improvement</h4>
                ${imp.length ? `<ul class="vs-list">${imp.map(i => `<li>${escapeHTML(i)}</li>`).join("")}</ul>` : `<p class="vs-feedback-text" style="color:var(--text-muted);">None noted.</p>`}
            </div>
        </div>` : ""}

        <div class="vs-assessment-section" style="margin-top:12px;">
            <h4 class="vs-section-title"><i class="fa-solid fa-comment-dots" style="color:var(--primary);"></i> Preliminary Assessment Summary</h4>
            <p class="vs-feedback-text">${escapeHTML(fb)}</p>
        </div>

        ${(assessment.answer_naturalness && assessment.answer_naturalness !== "Unable to Analyze") ? `
        <div class="vs-assessment-section" style="margin-top:14px;padding:14px 16px;border-radius:8px;background:var(--surface-alt,#f8f9fb);border:1px solid var(--border,#e5e7eb);">
            <h4 class="vs-section-title" style="margin-bottom:8px;">
                <i class="fa-solid fa-magnifying-glass" style="color:#7c3aed;"></i>
                Answer Naturalness
            </h4>
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
                <span style="
                    display:inline-block;padding:3px 12px;border-radius:20px;font-size:12px;font-weight:700;letter-spacing:.03em;
                    ${assessment.answer_naturalness === 'Natural'
                        ? 'background:#dcfce7;color:#15803d;'
                        : assessment.answer_naturalness === 'Possibly Scripted'
                        ? 'background:#fef9c3;color:#854d0e;'
                        : 'background:#fee2e2;color:#991b1b;'}
                ">${escapeHTML(assessment.answer_naturalness)}</span>
            </div>
            <p class="vs-feedback-text" style="margin-bottom:6px;">${escapeHTML(assessment.naturalness_feedback || "")}</p>
            <p style="font-size:10px;color:var(--text-muted);font-style:italic;margin:0;">
                <i class="fa-solid fa-circle-info"></i>
                This is an observational indicator only — not a guaranteed AI-generation detector.
                It does not affect the Screened / Not Screened decision.
            </p>
        </div>` : ""}

        ${assessment.error ? `
        <div class="vs-error-note">
            <i class="fa-solid fa-triangle-exclamation"></i>
            Note: Assessment may be incomplete — AI encountered an error. Transcript is preserved.
        </div>` : ""}

        <div style="margin-top:20px;display:flex;gap:10px;">
            <button class="btn-secondary" onclick="vsReset()">
                <i class="fa-solid fa-rotate-left"></i> Start New Screening
            </button>
        </div>
    `;

    panel.style.display = "block";
    panel.scrollIntoView({ behavior: "smooth" });
}

/* ----------------------------------------------------------
   Reset voice screening state
---------------------------------------------------------- */
function vsReset() {
    vsSessionId             = null;
    vsActive                = false;
    vsRecording             = false;
    vsSubmitting            = false;
    vsAccumulatedTranscript = "";

    if (vsRecognition) { try { vsRecognition.abort(); } catch(e) {} vsRecognition = null; }
    if (window.speechSynthesis) window.speechSynthesis.cancel();

    const startBtn      = document.getElementById("vsStartBtn");
    const stopBtn       = document.getElementById("vsStopBtn");
    const saveBtn       = document.getElementById("vsSaveBtn");
    const submitAnswBtn = document.getElementById("vsSubmitAnswerBtn");

    if (startBtn) { startBtn.disabled = false; startBtn.innerHTML = `<i class="fa-solid fa-microphone"></i> Start Screening`; }
    if (stopBtn)  { stopBtn.disabled = true; stopBtn.innerHTML = `<i class="fa-solid fa-stop"></i> Stop Recording`; }
    if (saveBtn)  { saveBtn.disabled = true; saveBtn.innerHTML = `<i class="fa-solid fa-floppy-disk"></i> Save Screening`; }
    if (submitAnswBtn) submitAnswBtn.disabled = true;

    const candSel = document.getElementById("vsCandidate");
    const jobSel  = document.getElementById("vsJob");
    if (candSel) candSel.disabled = false;
    if (jobSel)  jobSel.disabled  = false;

    vsSetCurrentQuestion("Start the screening to receive your first question.");

    const tc = document.getElementById("vsTranscriptContent");
    if (tc) tc.innerHTML = `<p class="vs-placeholder">Your spoken responses and AI questions will appear here...</p>`;

    const ap = document.getElementById("vsAssessmentPanel");
    if (ap) ap.style.display = "none";

    setVsStatus("", "Ready");
}


/* ==========================================================
   MILESTONE 4 — NAVIGATION & INITIALIZATION WIRING
========================================================== */

window.addEventListener("DOMContentLoaded", () => {
    // Init voice screening button handlers (wires Submit Answer, Stop Recording toggle, etc.)
    if (typeof initVoiceScreening === "function") {
        initVoiceScreening();
    }

    // Refresh Dashboard button
    const refreshBtn = document.getElementById("refreshDashboardBtn");
    if (refreshBtn) {
        refreshBtn.addEventListener("click", () => {
            loadDashboard();
            showToast("Dashboard analytics refreshed");
        });
    }

    // Hash navigation support on page reload
    const currentHash = window.location.hash.replace("#", "");
    if (currentHash && document.getElementById(currentHash)) {
        const targetMenu = document.querySelector(`[data-page="${currentHash}"]`);
        if (targetMenu) targetMenu.click();
    } else {
        // Default to Dashboard — defer so the UI paints before the API request fires
        setTimeout(() => { if (typeof loadDashboard === "function") loadDashboard(); }, 0);
    }
    // NOTE: loadVsDropdowns() is called lazily when the user navigates to voiceScreeningPage
    // (the menu item listener is already wired in the sidebar navigation block above)
});