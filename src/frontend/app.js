// Samagra — Evidence-First Procurement Decision Support System
import { PDFDocument } from 'https://cdn.jsdelivr.net/npm/pdf-lib@^1.17.1/dist/pdf-lib.min.js';
import * as mammoth from 'https://cdn.jsdelivr.net/npm/mammoth@1.6.0/mammoth.browser.min.js';

const PRELOADED_SCENARIOS = {
  protective_helmet: {
    title: "Protective Helmets (Clear Specification — Case 1)",
    text: `SAMPLE TENDER EXTRACT – Protective Helmets
Item: Supply of protective helmets for two-wheeler riders (traffic police / field staff)

Technical Specification:
1. Helmets shall conform to IS 4151:2015 (Protective Helmet for Two Wheeler Riders).
2. Each helmet shall bear the BIS Standard Mark (ISI) with valid CM/L licence number.
3. Mandatory under Helmet (Quality Control) Order, 2020 effective 01 June 2021.
4. Supplier to submit copy of valid BIS licence and test reports covering impact absorption, penetration resistance and retention system.`
  },
  power_bank: {
    title: "Power Bank Secondary Cells (Semantic Ambiguity — Case 2)",
    text: `Technical Specification for Procurement of Portable Power Banks:
The secondary lithium cells and batteries incorporated within the power bank assemblies shall strictly conform to applicable Indian Standards for safety of portable sealed secondary cells. Supplier must submit valid BIS Compulsory Registration Scheme (CRS) documentation with valid R-number.`
  },
  industrial_valves: {
    title: "Industrial Valves (False-Friend Non-Existent Standard — Case 3)",
    text: `SAMPLE TENDER EXTRACT – Industrial Valves
Item: Supply of industrial valves for water and high-pressure gas service lines

Specification:
Valves shall conform to “IS 1001 / IS 1002 Industrial Valve – General Requirements” and shall carry BIS ISI Mark.`
  },
  concrete_aggregate: {
    title: "RCC Framed Institutional Building (Audit & Multi-Clause Civil Tender)",
    text: `SAMPLE TENDER EXTRACT – Concrete & Aggregates
Name of Work: Construction of RCC framed structure for institutional building

BOQ Clause 4.2 – Cement
Cement shall be Ordinary Portland Cement 43 Grade conforming to IS 8112:2013 / IS 269:2015 and shall bear BIS Standard Mark (Scheme-I). Manufacturer’s test certificate and ISI licence copy to be submitted.

BOQ Clause 4.3 – Reinforcement Steel
High strength deformed bars conforming to IS 1786:1985 Grade Fe500.

BOQ Clause 4.4 – Coarse & Fine Aggregate
Aggregates shall conform to IS 383:2016. Supplier shall provide ISI mark certificate.

BOQ Clause 4.5 – Concrete
All structural concrete shall be ISI marked as per IS 456:2000. Mix design, cube testing and acceptance criteria shall follow IS 456:2000 and IS 516.`
  }
};

let currentInputMode = "tender";
let selectedFile = null;

function switchInputMode(mode) {
  currentInputMode = mode;
  const tenderBtn = document.getElementById("tab-tender-btn");
  const queryBtn = document.getElementById("tab-query-btn");
  const inputLabel = document.getElementById("input-label");
  const inputText = document.getElementById("input-text");
  const dropzone = document.getElementById("dropzone");

  if (mode === "tender") {
    tenderBtn.classList.add("active");
    queryBtn.classList.remove("active");
    inputLabel.innerText = "Tender Specification Text / BOQ Clauses:";
    inputText.placeholder = "Paste multi-clause tender documents, BOQ specifications, or extract clauses...";
    dropzone.classList.remove("hidden");
  } else {
    queryBtn.classList.add("active");
    tenderBtn.classList.remove("active");
    inputLabel.innerText = "Natural Language Procurement Query:";
    inputText.placeholder = "E.g.: 'Which Indian standard is mandatory for lithium-ion power bank cells under CRS?', 'Is ISI mark applicable on IS 456 concrete?', 'Specify grade and impact quality class for structural steel plates'...";
    dropzone.classList.add("hidden");
  }
}

function loadSampleScenario(key) {
  const scenario = PRELOADED_SCENARIOS[key];
  if (!scenario) return;
  
  switchInputMode("tender");
  document.getElementById("input-text").value = scenario.text;
  selectedFile = null;
  document.getElementById("upload-label-text").innerText = "Attach tender specification document (.txt, .pdf, .docx)";
  
  // Highlight chosen scenario pill
  document.querySelectorAll(".demo-pill").forEach(p => p.classList.remove("selected"));
}

async function handleFileSelect(event) {
  const file = event.target.files[0];
  if (!file) return;

  selectedFile = file;
  document.getElementById("upload-label-text").innerText = `Processing: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;

  try {
    const validTypes = ['text/plain', 'application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
    if (!validTypes.includes(file.type) && !file.name.match(/\.(txt|pdf|docx)$/i)) {
      throw new Error("Unsupported file type. Please upload .txt, .pdf, or .docx.");
    }

    let extractedText = "";
    if (file.type === 'text/plain' || file.name.endsWith('.txt')) {
      extractedText = await file.text();
    }
    else if (file.type === 'application/pdf' || file.name.endsWith('.pdf')) {
      extractedText = await extractTextFromPDF(file);
    }
    else if (file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' || file.name.endsWith('.docx')) {
      extractedText = await extractTextFromDOCX(file);
    }

    document.getElementById("input-text").value = extractedText;
    document.getElementById("upload-label-text").innerText = `Attached: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
  } catch (err) {
    alert(`Error processing file: ${err.message}`);
    document.getElementById("upload-label-text").innerText = "Attach tender specification document (.txt, .pdf, .docx)";
    selectedFile = null;
  }
}
async function extractTextFromPDF(file) {
  const arrayBuffer = await file.arrayBuffer();
  const pdfDoc = await PDFDocument.load(arrayBuffer);
  let text = "";
  for (let i = 0; i < pdfDoc.getPageCount(); i++) {
    const page = pdfDoc.getPage(i);
    const content = await page.getTextContent();
    text += content.items.map(item => item.str).join(" ") + "\n";
  }
  return text;
}

async function extractTextFromDOCX(file) {
  const arrayBuffer = await file.arrayBuffer();
  const result = await mammoth.extractRawText({ arrayBuffer });
  return result.value;
}

function clearInput() {
  document.getElementById("input-text").value = "";
  selectedFile = null;
  document.getElementById("file-upload").value = "";
  document.getElementById("upload-label-text").innerText = "Attach tender specification document (.txt, .pdf, .docx)";
  resetTrace();
  document.getElementById("summary-stats-bar").classList.add("hidden");
  document.getElementById("results-cards-container").innerHTML = `
    <div class="empty-state" id="empty-state">
      <div class="empty-state-icon">🏛️</div>
      <h3>Evidence-First Procurement Decision Support</h3>
      <p>Select a demonstration scenario from the left panel or paste a procurement specification to generate the complete statutory audit trail.</p>
    </div>
  `;
}

function resetTrace() {
  const badge = document.getElementById("trace-status-badge");
  badge.innerText = "Awaiting Input";
  badge.className = "trace-status";
  
  const items = document.querySelectorAll(".trace-item");
  items.forEach(it => {
    it.className = "trace-item idle";
  });
}

function updateTraceStep(stepIdx, statusClass, text) {
  const items = document.querySelectorAll(".trace-item");
  if (items[stepIdx]) {
    items[stepIdx].className = `trace-item ${statusClass}`;
    if (text) items[stepIdx].innerText = text;
  }
}

async function handleAnalyzeSubmit(event) {
  event.preventDefault();
  const text = document.getElementById("input-text").value.trim();
  if (!text && !selectedFile) {
    alert("Please provide specification text or attach a document.");
    return;
  }

  const analyzeBtn = document.getElementById("analyze-btn");
  const spinner = document.getElementById("loading-spinner");
  const btnText = analyzeBtn.querySelector(".btn-text");

  analyzeBtn.disabled = true;
  spinner.classList.remove("hidden");
  btnText.innerText = "Auditing Specifications...";

  const traceBadge = document.getElementById("trace-status-badge");
  traceBadge.innerText = "Executing Statutory Audit Pipeline...";
  traceBadge.className = "trace-status";

  updateTraceStep(0, "active", "1. Document & Clause Extraction ✓");
  updateTraceStep(1, "active", "2. Exact + BM25 + BGE-M3 Retrieval ✓");
  updateTraceStep(2, "active", "3. RRF Rank Fusion & Candidate Ranking ✓");
  updateTraceStep(3, "active", "4. Statutory Lifecycle & Trap Check ✓");

  try {
    let response;
    if (selectedFile) {
      const formData = new FormData();
      formData.append("text", document.getElementById("input-text").value);
      formData.append("document_title", selectedFile.name);
      response = await fetch("/api/recommend", {
        method: "POST",
        body: formData,
      });
    } else {
      response = await fetch("/api/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: text,
          document_title: currentInputMode === "query" ? "Natural Language Officer Query" : "Tender Specification"
        }),
      });
    }

    if (!response.ok) {
      throw new Error(`Server returned error status: ${response.status}`);
    }

    const data = await response.json();
    updateTraceStep(4, "active", "5. Regulatory & Mandatory QCO Check ✓");
    updateTraceStep(5, "active", "6. Evidence Dossier Generated ✓");

    traceBadge.innerText = "Audit Complete";
    traceBadge.classList.add("active");

    renderResults(data);
  } catch (err) {
    console.error("Audit error:", err);
    traceBadge.innerText = "Audit Failed";
    traceBadge.classList.add("review-needed");
    alert("Failed to process specification: " + err.message);
  } finally {
    analyzeBtn.disabled = false;
    spinner.classList.add("hidden");
    btnText.innerText = "Audit & Verify Standards";
  }
}
function renderResults(result) {
  // Update stats bar
  const statsBar = document.getElementById("summary-stats-bar");
  statsBar.classList.remove("hidden");
  
  document.getElementById("stat-total").innerText = result.total_clauses;
  document.getElementById("stat-clear").innerText = result.clear_count;
  document.getElementById("stat-ambiguous").innerText = result.ambiguous_count;
  document.getElementById("stat-review").innerText = result.human_review_count;

  const container = document.getElementById("results-cards-container");
  container.innerHTML = "";

  if (!result.cards || result.cards.length === 0) {
    container.innerHTML = `<div class="empty-state"><p>No valid requirement clauses extracted.</p></div>`;
    return;
  }

  result.cards.forEach((card, idx) => {
    const cardEl = document.createElement("div");
    cardEl.className = "audit-card";

    // Determine badge styling
    let badgeClass = "badge-verified";
    let badgeLabel = "VERIFIED APPLICABLE";
    
    if (card.recommendation_status === "HUMAN_REVIEW_REQUIRED" || card.recommendation_status === "FALSE_FRIEND_REJECTED") {
      badgeClass = "badge-danger";
      badgeLabel = "HUMAN REVIEW REQUIRED";
    } else if (card.recommendation_status === "CODE_OF_PRACTICE_WARNING") {
      badgeClass = "badge-warning";
      badgeLabel = "CODE OF PRACTICE (NOT PRODUCT)";
    } else if (card.recommendation_status === "SUPERSEDED") {
      badgeClass = "badge-warning";
      badgeLabel = "SUPERSEDED EDITION";
    } else if (card.ai_trace.ai_invoked) {
      badgeClass = "badge-ai";
      badgeLabel = card.ai_trace.status_label;
    }

    // Related standards tags
    let alliedHtml = "";
    const rels = card.related_standards || {};
    
    if (rels.test_methods && rels.test_methods.length > 0) {
      alliedHtml += `<div><span style="font-size:0.75rem; font-weight:600; color:#0284c7;">Test Methods:</span> ` +
        rels.test_methods.map(r => `<span class="std-tag std-tag-test" title="${r.note || ''}">${r.standard}</span>`).join(" ") + `</div>`;
    }
    if (rels.safety_standards && rels.safety_standards.length > 0) {
      alliedHtml += `<div style="margin-top:4px;"><span style="font-size:0.75rem; font-weight:600; color:#dc2626;">Safety Standards:</span> ` +
        rels.safety_standards.map(r => `<span class="std-tag std-tag-safety" title="${r.note || ''}">${r.standard}</span>`).join(" ") + `</div>`;
    }
    if (rels.normative_references && rels.normative_references.length > 0) {
      alliedHtml += `<div style="margin-top:4px;"><span style="font-size:0.75rem; font-weight:600; color:#16a34a;">Normative References:</span> ` +
        rels.normative_references.map(r => `<span class="std-tag std-tag-normative" title="${r.note || ''}">${r.standard}</span>`).join(" ") + `</div>`;
    }
    if (rels.superseded && rels.superseded.length > 0) {
      alliedHtml += `<div style="margin-top:4px;"><span style="font-size:0.75rem; font-weight:600; color:#b45309;">Lifecycle Relation:</span> ` +
        rels.superseded.map(r => `<span class="std-tag" title="${r.note || ''}">${r.standard} (${r.type})</span>`).join(" ") + `</div>`;
    }
    if (!alliedHtml) {
      alliedHtml = `<span style="font-size:0.8rem; color:#64748b;">No direct allied standard relationships indexed.</span>`;
    }

    // Traps tags
    let trapsHtml = "";
    if (card.traps_detected && card.traps_detected.length > 0) {
      trapsHtml = card.traps_detected.map(t => `<span class="badge-danger" style="font-size:0.7rem; padding:2px 6px; border-radius:3px; margin-right:4px;">⚠ ${t}</span>`).join("");
    }

    cardEl.innerHTML = `
      <!-- Card Header -->
      <div class="card-top-bar">
        <div class="card-title-group">
          <h4>${card.recommended_standard_id || "DEFECT / UNVERIFIED STANDARD"}</h4>
          <div class="card-subtitle">${card.standard_title || "Unverified specification reference"}</div>
        </div>
        <div style="text-align:right;">
          <span class="status-badge ${badgeClass}">${badgeLabel}</span>
          <div style="margin-top:4px; font-size:0.75rem; font-weight:600; color:#475569;">${card.ai_trace.status_label}</div>
        </div>
      </div>

      <!-- Traps banner if detected -->
      ${trapsHtml ? `<div style="margin-top:-4px;">${trapsHtml}</div>` : ""}

      <!-- Verbatim Requirement Citation -->
      <div class="citation-box">
        <div class="citation-meta">Source Requirement: ${card.section || 'Specification Clause'} (Page ${card.page || 1})</div>
        <div class="citation-quote">"${card.extracted_requirement}"</div>
      </div>

      <!-- Evidence Breakdown Grid -->
      <div class="evidence-grid">
        <!-- Panel 1: Applicability Verification -->
        <div class="evidence-subpanel">
          <div class="subpanel-header">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
            Applicability & Scope Verification
          </div>
          <ul class="check-list">
            ${card.applicability_checks.map(c => `<li>${c}</li>`).join("")}
          </ul>
        </div>

        <!-- Panel 2: Regulatory & Certification Mandate -->
        <div class="evidence-subpanel">
          <div class="subpanel-header">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
            Regulatory Mandate & Certification Scheme
          </div>
          <ul class="check-list">
            <li><strong>Scheme:</strong> ${card.regulatory_check.certification_scheme || "NOT DETERMINED"}</li>
            <li><strong>Mandatory Status:</strong> ${card.regulatory_check.mandatory || "NOT DETERMINED"}</li>
            <li><strong>Statutory Order:</strong> ${card.regulatory_check.qco_order || "NOT DETERMINED"}</li>
            <li><strong>Ministry / Date:</strong> ${card.regulatory_check.ministry || "NOT DETERMINED"} ${card.regulatory_check.effective_date ? `(Eff: ${card.regulatory_check.effective_date})` : ""}</li>
          </ul>
        </div>

        <!-- Panel 3: Lifecycle, Version & Amendments -->
        <div class="evidence-subpanel">
          <div class="subpanel-header">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
            Version, Amendments & Lifecycle
          </div>
          <ul class="check-list">
            <li><strong>Current Indexed Record:</strong> ${card.version_info.indexed_record || "NOT DETERMINED"}</li>
            <li><strong>Superseded:</strong> ${card.version_info.is_superseded ? `YES (Superseded by ${card.version_info.superseded_by})` : "NO (Active Standard)"}</li>
            <li><strong>Amendments:</strong> ${card.version_info.amendment || "Standard baseline edition"}</li>
            <li><strong>Revision History:</strong> ${card.version_info.amendment_history || "Active edition in BIS catalogue."}</li>
          </ul>
        </div>

        <!-- Panel 4: Allied & Related Standards -->
        <div class="evidence-subpanel">
          <div class="subpanel-header">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="18" cy="5" r="3"></circle><circle cx="6" cy="12" r="3"></circle><circle cx="18" cy="19" r="3"></circle><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line></svg>
            Allied Standards (Test / Safety / Normative)
          </div>
          <div class="tag-list" style="margin-top:4px;">
            ${alliedHtml}
          </div>
        </div>
      </div>

      <!-- Executive Dossier Callout for Superior Authorities & Public Safety -->
      <div class="dossier-callout">
        <div class="dossier-title">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
          Executive Dossier for Superior Authorities & Public Safety Rationale
        </div>
        <div class="safety-mandate">
          ${card.public_safety_rationale}
        </div>
        <div class="dossier-text">
          ${card.superior_authority_audit_context}
        </div>
        ${card.ai_trace.reasoning_explanation ? `
          <div style="margin-top:4px; font-size:0.8rem; background:#ffffff; border:1px solid #cbd5e1; padding:8px 10px; border-radius:4px;">
            <strong>Decision-Support Explanation:</strong> ${card.ai_trace.reasoning_explanation}
          </div>
        ` : ""}
      </div>

      <!-- Trace Milestones Steps -->
      <div class="card-trace-steps">
        ${card.trace_milestones.map(m => `<span class="card-step-badge">${m}</span>`).join("")}
      </div>
    `;

    container.appendChild(cardEl);
  });
}

