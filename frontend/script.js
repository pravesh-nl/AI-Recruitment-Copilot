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
    

    Array.from(files).forEach(file => {

        const div = document.createElement("div");

        div.className = "file-item";

        div.innerHTML = `
            <i class="fa-solid fa-file-lines"></i>
            <span>${file.name}</span>
        `;

        selectedFiles.appendChild(div);

    });

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

        const res = await fetch(`${API}/candidates`,{
            cache:"no-store"
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

        candidateInfo.innerHTML = `
            <div class="candidate-card">

                <p><strong>Name:</strong> ${c.name || "-"}</p>

                <p><strong>Email:</strong> ${c.email || "-"}</p>

                <p><strong>Phone:</strong> ${c.phone || "-"}</p>

                <p><strong>Education:</strong> ${JSON.parse(c.education || "[]").join(", ")}</p>

                <p><strong>Experience:</strong> ${JSON.parse(c.experience || "[]").join(", ")}</p>

                <p><strong>Skills:</strong> ${JSON.parse(c.skills || "[]").join(", ")}</p>

                <p><strong>Projects:</strong> ${JSON.parse(c.projects || "[]").join(", ")}</p>

                <p><strong>Certifications:</strong> ${JSON.parse(c.certifications || "[]").join(", ")}</p>

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