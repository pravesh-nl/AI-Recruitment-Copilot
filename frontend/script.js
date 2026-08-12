/* ==========================================================
   AI Recruitment Copilot — script.js (Redesigned)
   Backend API: http://127.0.0.1:8000
   All endpoints unchanged. Only UI rendering redesigned.
========================================================== */

const API = "http://127.0.0.1:8000";

/* ----------------------------------------------------------
   STATE
---------------------------------------------------------- */
let deletedJobIds = new Set(); // frontend-only soft delete
let allCandidatesCache = [];   // cached for search filtering

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
   DOM REFS — Interview Page
---------------------------------------------------------- */
const generateQuestionsBtn = document.getElementById("generateQuestionsBtn");
const generatedQuestions   = document.getElementById("generatedQuestions");

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

        // Lazy-load matching page jobs when navigating there
        if (pageId === "matchingPage") {
            loadJobsIntoDropdown();
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
                <td><span class="status processed">Processed</span></td>
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
            <td><span class="status processed">Processed</span></td>
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
            <p><strong>Name:</strong> ${candidate.name || "—"}</p>
            <p><strong>Email:</strong> ${candidate.email || "—"}</p>
            <p><strong>Phone:</strong> ${candidate.phone || "—"}</p>
            <p><strong>Education:</strong> ${safeParseJSON(candidate.education, []).join(", ") || "—"}</p>
            <p><strong>Experience:</strong> ${safeParseJSON(candidate.experience, []).join(", ") || "—"}</p>
            <p><strong>Skills:</strong> ${safeParseJSON(candidate.skills, []).join(", ") || "—"}</p>
            <p><strong>Projects:</strong> ${safeParseJSON(candidate.projects, []).join(", ") || "—"}</p>
            <p><strong>Certifications:</strong> ${safeParseJSON(candidate.certifications, []).join(", ") || "—"}</p>
        </div>`;
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

        // Interview page dropdown
        const interviewJobSel = document.getElementById("interviewJob");
        if (interviewJobSel) {
            const ivCurrentVal = interviewJobSel.value;
            interviewJobSel.innerHTML = `<option value="">Select job</option>`;
            visibleJobs.forEach(job => {
                const opt = document.createElement("option");
                opt.value       = job.title;
                opt.textContent = job.title;
                interviewJobSel.appendChild(opt);
            });
            if (ivCurrentVal) interviewJobSel.value = ivCurrentVal;
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

            <div class="mc-body">
                <span class="mc-exp">
                    <i class="fa-solid fa-briefcase"></i>
                    ${candidate.candidate_experience} yrs experience
                </span>
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
    const jobTitle    = document.getElementById("interviewJob").value.trim();
    const questionType = document.getElementById("questionType").value;

    if (!jobTitle) {
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
            body:    JSON.stringify({ job_title: jobTitle, question_type: questionType })
        });

        const data = await response.json();

        if (!response.ok) throw new Error(data.detail || "Failed to generate questions.");

        displayGeneratedQuestions(data.questions);

    } catch (error) {
        console.error("Interview Question Error:", error);
        generatedQuestions.innerHTML = `
            <div class="empty-state">
                <i class="fa-solid fa-triangle-exclamation" style="color:#dc2626;"></i>
                <p>Failed to generate questions.</p>
            </div>`;
    } finally {
        generateQuestionsBtn.disabled = false;
        generateQuestionsBtn.innerHTML = `<i class="fa-solid fa-wand-magic-sparkles"></i> Generate Questions`;
    }
});

function displayGeneratedQuestions(questions) {
    const lines = questions
        .split("\n")
        .map(l => l.trim())
        .filter(l => l.length > 0);

    generatedQuestions.innerHTML = "";
    lines.forEach((question, index) => {
        const card = document.createElement("div");
        card.className = "question-card";
        card.innerHTML = `
            <div class="question-number">${index + 1}</div>
            <div class="question-text">${escapeHTML(question.replace(/^\d+[.)]\s*/, ""))}</div>`;
        generatedQuestions.appendChild(card);
    });
}

/* ==========================================================
   INITIAL PAGE LOAD
========================================================== */
window.addEventListener("DOMContentLoaded", async () => {
    await loadStats();
    await loadLatestCandidate();
    await loadCandidates();
    await loadJobListingGrid();
    await loadJobsIntoDropdown();

    // Wire candidate search input
    const searchInput = document.getElementById("candidateSearchInput");
    if (searchInput) {
        searchInput.addEventListener("input", () => filterCandidates(searchInput.value));
    }
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