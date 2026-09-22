// Samagra — Evidence-First Procurement Decision Support System

/* ============================================================
   PRELOADED DEMONSTRATION SCENARIOS
   ============================================================ */

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


/* ============================================================
   APPLICATION STATE
   ============================================================ */

let currentInputMode = "tender";
let selectedFile = null;


/* ============================================================
   INPUT MODE
   ============================================================ */

function switchInputMode(mode) {
  currentInputMode = mode;

  const tenderBtn = document.getElementById("tab-tender-btn");
  const queryBtn = document.getElementById("tab-query-btn");
  const inputLabel = document.getElementById("input-label");
  const inputText = document.getElementById("input-text");
  const dropzone = document.getElementById("dropzone");

  if (mode === "tender") {
    tenderBtn?.classList.add("active");
    queryBtn?.classList.remove("active");

    if (inputLabel) {
      inputLabel.innerText = "Tender Specification Text / BOQ Clauses:";
    }

    if (inputText) {
      inputText.placeholder =
        "Paste multi-clause tender documents, BOQ specifications, or extract clauses...";
    }

    dropzone?.classList.remove("hidden");
  } else {
    queryBtn?.classList.add("active");
    tenderBtn?.classList.remove("active");

    if (inputLabel) {
      inputLabel.innerText = "Natural Language Procurement Query:";
    }

    if (inputText) {
      inputText.placeholder =
        "E.g.: Which Indian standard is mandatory for lithium-ion power bank cells under CRS?";
    }

    dropzone?.classList.add("hidden");
  }
}


/* ============================================================
   DEMO SCENARIOS
   ============================================================ */

function loadSampleScenario(key) {
  const scenario = PRELOADED_SCENARIOS[key];

  if (!scenario) {
    console.warn(`Unknown demonstration scenario: ${key}`);
    return;
  }

  switchInputMode("tender");

  const inputText = document.getElementById("input-text");
  const uploadLabel = document.getElementById("upload-label-text");

  if (inputText) {
    inputText.value = scenario.text;
  }

  selectedFile = null;

  if (uploadLabel) {
    uploadLabel.innerText =
      "Attach tender specification document (.txt, .pdf, .docx)";
  }

  document
    .querySelectorAll(".demo-pill")
    .forEach((p) => p.classList.remove("selected"));
}


/* ============================================================
   FILE HANDLING
   ============================================================ */

async function handleFileSelect(event) {
  const file = event.target.files?.[0];

  if (!file) {
    return;
  }

  selectedFile = file;

  const uploadLabel = document.getElementById("upload-label-text");

  if (uploadLabel) {
    uploadLabel.innerText =
      `Processing: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
  }

  try {
    const validTypes = [
      "text/plain",
      "application/pdf",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ];

    const validExtension = /\.(txt|pdf|docx)$/i.test(file.name);

    if (!validTypes.includes(file.type) && !validExtension) {
      throw new Error(
        "Unsupported file type. Please upload .txt, .pdf, or .docx."
      );
    }

    let extractedText = "";

    if (
      file.type === "text/plain" ||
      /\.txt$/i.test(file.name)
    ) {
      extractedText = await file.text();
    } else if (
      file.type === "application/pdf" ||
      /\.pdf$/i.test(file.name)
    ) {
      extractedText = await extractTextFromPDF(file);
    } else if (
      file.type ===
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document" ||
      /\.docx$/i.test(file.name)
    ) {
      extractedText = await extractTextFromDOCX(file);
    }

    if (!extractedText.trim()) {
      throw new Error(
        "No extractable text was found in the document."
      );
    }

    const inputText = document.getElementById("input-text");

    if (inputText) {
      inputText.value = extractedText;
    }

    if (uploadLabel) {
      uploadLabel.innerText =
        `Attached: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
    }
  } catch (err) {
    console.error("File extraction error:", err);

    alert(`Error processing file: ${err.message}`);

    if (uploadLabel) {
      uploadLabel.innerText =
        "Attach tender specification document (.txt, .pdf, .docx)";
    }

    selectedFile = null;

    const fileInput = document.getElementById("file-upload");

    if (fileInput) {
      fileInput.value = "";
    }
  }
}


/* ============================================================
   PDF EXTRACTION
   Lazy-loaded so a CDN failure does NOT kill the entire UI.
   ============================================================ */

async function extractTextFromPDF(file) {
  let pdfjsLib;

  try {
    pdfjsLib = await import(
      "https://cdn.jsdelivr.net/npm/pdfjs-dist@4.10.38/build/pdf.min.mjs"
    );
  } catch (err) {
    throw new Error(
      "PDF extraction library could not be loaded. Check your internet connection."
    );
  }

  pdfjsLib.GlobalWorkerOptions.workerSrc =
    "https://cdn.jsdelivr.net/npm/pdfjs-dist@4.10.38/build/pdf.worker.min.mjs";

  const arrayBuffer = await file.arrayBuffer();

  const loadingTask = pdfjsLib.getDocument({
    data: new Uint8Array(arrayBuffer)
  });

  const pdf = await loadingTask.promise;

  const pages = [];

  for (
    let pageNumber = 1;
    pageNumber <= pdf.numPages;
    pageNumber++
  ) {
    const page = await pdf.getPage(pageNumber);
    const content = await page.getTextContent();

    const pageText = content.items
      .map((item) => item.str || "")
      .join(" ")
      .replace(/\s+/g, " ")
      .trim();

    if (pageText) {
      pages.push(`[Page ${pageNumber}]\n${pageText}`);
    }
  }

  return pages.join("\n\n");
}


/* ============================================================
   DOCX EXTRACTION
   Lazy-loaded for the same reason as PDF extraction.
   ============================================================ */

async function extractTextFromDOCX(file) {
  let mammoth;

  try {
    mammoth = await import(
      "https://cdn.jsdelivr.net/npm/mammoth@1.6.0/mammoth.browser.min.js"
    );
  } catch (err) {
    throw new Error(
      "DOCX extraction library could not be loaded. Check your internet connection."
    );
  }

  const arrayBuffer = await file.arrayBuffer();

  const result = await mammoth.extractRawText({
    arrayBuffer
  });

  return result.value || "";
}


/* ============================================================
   CLEAR INPUT
   ============================================================ */

function clearInput() {
  const inputText = document.getElementById("input-text");
  const fileUpload = document.getElementById("file-upload");
  const uploadLabel = document.getElementById("upload-label-text");
  const statsBar = document.getElementById("summary-stats-bar");
  const resultsContainer = document.getElementById(
    "results-cards-container"
  );

  if (inputText) {
    inputText.value = "";
  }

  selectedFile = null;

  if (fileUpload) {
    fileUpload.value = "";
  }

  if (uploadLabel) {
    uploadLabel.innerText =
      "Attach tender specification document (.txt, .pdf, .docx)";
  }

  resetTrace();

  statsBar?.classList.add("hidden");

  if (resultsContainer) {
    resultsContainer.innerHTML = `
      <div class="empty-state" id="empty-state">
        <div class="empty-state-icon">🏛️</div>
        <h3>Evidence-First Procurement Decision Support</h3>
        <p>
          Select a demonstration scenario or paste a procurement
          specification to generate the evidence trail.
        </p>
      </div>
    `;
  }
}


/* ============================================================
   TRACE UI
   ============================================================ */

function resetTrace() {
  const badge = document.getElementById("trace-status-badge");

  if (badge) {
    badge.innerText = "Awaiting Input";
    badge.className = "trace-status";
  }

  document.querySelectorAll(".trace-item").forEach((item) => {
    item.className = "trace-item idle";
  });
}


function updateTraceStep(stepIdx, statusClass, text) {
  const items = document.querySelectorAll(".trace-item");

  if (items[stepIdx]) {
    items[stepIdx].className = `trace-item ${statusClass}`;

    if (text) {
      items[stepIdx].innerText = text;
    }
  }
}


/* ============================================================
   ANALYSIS
   ============================================================ */

async function handleAnalyzeSubmit(event) {
  event.preventDefault();

  const inputText = document.getElementById("input-text");
  const text = inputText?.value.trim() || "";

  if (!text) {
    alert("Please provide specification text or attach a document.");
    return;
  }

  const analyzeBtn = document.getElementById("analyze-btn");
  const spinner = document.getElementById("loading-spinner");
  const btnText = analyzeBtn?.querySelector(".btn-text");

  if (analyzeBtn) {
    analyzeBtn.disabled = true;
  }

  spinner?.classList.remove("hidden");

  if (btnText) {
    btnText.innerText = "Analyzing Specifications...";
  }

  const traceBadge = document.getElementById("trace-status-badge");

  if (traceBadge) {
    traceBadge.innerText = "Executing Evidence-First Pipeline...";
    traceBadge.className = "trace-status";
  }

  updateTraceStep(
    0,
    "active",
    "1. Document & Clause Extraction ✓"
  );

  updateTraceStep(
    1,
    "active",
    "2. Exact + BM25 + BGE-M3 Retrieval ✓"
  );

  updateTraceStep(
    2,
    "active",
    "3. RRF Rank Fusion & Candidate Ranking ✓"
  );

  updateTraceStep(
    3,
    "active",
    "4. Applicability & Version Verification ✓"
  );

  try {
    const response = await fetch("/api/recommend", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        text,
        document_title:
          selectedFile?.name ||
          (currentInputMode === "query"
            ? "Natural Language Officer Query"
            : "Tender Specification")
      })
    });

    if (!response.ok) {
      let detail = `Server returned error status: ${response.status}`;

      try {
        const errorData = await response.json();

        if (errorData?.detail) {
          detail = errorData.detail;
        }
      } catch (_) {
        // Keep default HTTP error message.
      }

      throw new Error(detail);
    }

    const data = await response.json();

    updateTraceStep(
      4,
      "active",
      "5. Regulatory & Certification Check ✓"
    );

    updateTraceStep(
      5,
      "active",
      "6. Evidence Trail Generated ✓"
    );

    if (traceBadge) {
      traceBadge.innerText = "Analysis Complete";
      traceBadge.classList.add("active");
    }

    renderResults(data);
  } catch (err) {
    console.error("Analysis error:", err);

    if (traceBadge) {
      traceBadge.innerText = "Analysis Failed";
      traceBadge.className = "trace-status review-needed";
    }

    alert("Failed to process specification: " + err.message);
  } finally {
    if (analyzeBtn) {
      analyzeBtn.disabled = false;
    }

    spinner?.classList.add("hidden");

    if (btnText) {
      btnText.innerText = "Audit & Verify Standards";
    }
  }
}


/* ============================================================
   HTML ESCAPING
   ============================================================ */

function escapeHtml(value) {
  if (value === null || value === undefined) {
    return "";
  }

  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}


/* ============================================================
   RESULT RENDERING
   ============================================================ */

function renderResults(result) {
  const statsBar = document.getElementById("summary-stats-bar");

  if (statsBar) {
    statsBar.classList.remove("hidden");
  }

  const totalEl = document.getElementById("stat-total");
  const clearEl = document.getElementById("stat-clear");
  const ambiguousEl = document.getElementById("stat-ambiguous");
  const reviewEl = document.getElementById("stat-review");

  if (totalEl) {
    totalEl.innerText = result.total_clauses ?? 0;
  }

  if (clearEl) {
    clearEl.innerText = result.clear_count ?? 0;
  }

  if (ambiguousEl) {
    ambiguousEl.innerText = result.ambiguous_count ?? 0;
  }

  if (reviewEl) {
    reviewEl.innerText = result.human_review_count ?? 0;
  }

  const container = document.getElementById(
    "results-cards-container"
  );

  if (!container) {
    return;
  }

  container.innerHTML = "";

  if (!result.cards || result.cards.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <p>No valid requirement clauses extracted.</p>
      </div>
    `;

    return;
  }

  result.cards.forEach((card) => {
    const cardEl = document.createElement("div");
    cardEl.className = "audit-card";

    const status =
      card.recommendation_status || "HUMAN_REVIEW_REQUIRED";

    let badgeClass = "badge-verified";
    let badgeLabel = "VERIFIED APPLICABLE";

    if (status === "HUMAN_REVIEW_REQUIRED") {
      badgeClass = "badge-danger";
      badgeLabel = "HUMAN REVIEW REQUIRED";
    } else if (status === "FALSE_FRIEND_REJECTED") {
      badgeClass = "badge-danger";
      badgeLabel = "STANDARD REJECTED";
    } else if (status === "CODE_OF_PRACTICE_WARNING") {
      badgeClass = "badge-warning";
      badgeLabel = "CODE OF PRACTICE";
    } else if (status === "SUPERSEDED") {
      badgeClass = "badge-warning";
      badgeLabel = "SUPERSEDED EDITION";
    } else if (card.ai_trace?.ai_invoked) {
      badgeClass = "badge-ai";
      badgeLabel =
        card.ai_trace.status_label || "AI ESCALATION";
    }

    const rels = card.related_standards || {};
    let alliedHtml = "";

    if (rels.test_methods?.length) {
      alliedHtml += `
        <div>
          <span class="related-label">Test Methods:</span>
          ${rels.test_methods
            .map(
              (r) =>
                `<span class="std-tag std-tag-test" title="${escapeHtml(
                  r.note || ""
                )}">${escapeHtml(r.standard)}</span>`
            )
            .join(" ")}
        </div>
      `;
    }

    if (rels.safety_standards?.length) {
      alliedHtml += `
        <div style="margin-top:4px;">
          <span class="related-label">Safety Standards:</span>
          ${rels.safety_standards
            .map(
              (r) =>
                `<span class="std-tag std-tag-safety" title="${escapeHtml(
                  r.note || ""
                )}">${escapeHtml(r.standard)}</span>`
            )
            .join(" ")}
        </div>
      `;
    }

    if (rels.normative_references?.length) {
      alliedHtml += `
        <div style="margin-top:4px;">
          <span class="related-label">Normative References:</span>
          ${rels.normative_references
            .map(
              (r) =>
                `<span class="std-tag std-tag-normative" title="${escapeHtml(
                  r.note || ""
                )}">${escapeHtml(r.standard)}</span>`
            )
            .join(" ")}
        </div>
      `;
    }

    if (rels.superseded?.length) {
      alliedHtml += `
        <div style="margin-top:4px;">
          <span class="related-label">Lifecycle Relation:</span>
          ${rels.superseded
            .map(
              (r) =>
                `<span class="std-tag" title="${escapeHtml(
                  r.note || ""
                )}">
                  ${escapeHtml(r.standard)}
                  (${escapeHtml(r.type || "")})
                </span>`
            )
            .join(" ")}
        </div>
      `;
    }

    if (!alliedHtml) {
      alliedHtml = `
        <span style="font-size:0.8rem;color:#64748b;">
          No direct allied standard relationships indexed.
        </span>
      `;
    }

    const aiTrace = card.ai_trace || {};
    const versionInfo = card.version_info || {};
    const regulatory = card.regulatory_check || {};

    const aiExplanation = aiTrace.reasoning_explanation
      ? `
        <div class="decision-explanation">
          <strong>Decision-Support Explanation:</strong>
          ${escapeHtml(aiTrace.reasoning_explanation)}
        </div>
      `
      : "";

    const traceMilestones = Array.isArray(card.trace_milestones)
      ? card.trace_milestones
      : [];

    cardEl.innerHTML = `
      <div class="card-top-bar">
        <div class="card-title-group">
          <h4>
            ${escapeHtml(
              card.recommended_standard_id ||
                "UNVERIFIED STANDARD"
            )}
          </h4>

          <div class="card-subtitle">
            ${escapeHtml(
              card.standard_title ||
                "No sufficiently supported standard was identified."
            )}
          </div>
        </div>

        <div style="text-align:right;">
          <span class="status-badge ${badgeClass}">
            ${escapeHtml(badgeLabel)}
          </span>

          <div style="
            margin-top:4px;
            font-size:0.75rem;
            font-weight:600;
            color:#475569;
          ">
            ${escapeHtml(
              aiTrace.status_label || "AI NOT INVOKED"
            )}
          </div>
        </div>
      </div>

      <div class="citation-box">
        <div class="citation-meta">
          Source Requirement:
          ${escapeHtml(
            card.section || "Specification Clause"
          )}
          ${
            card.page
              ? `(Page ${escapeHtml(card.page)})`
              : ""
          }
        </div>

        <div class="citation-quote">
          "${escapeHtml(
            card.extracted_requirement || ""
          )}"
        </div>
      </div>

      <div class="evidence-grid">

        <div class="evidence-subpanel">
          <div class="subpanel-header">
            Applicability & Scope Verification
          </div>

          <ul class="check-list">
            ${
              card.applicability_checks?.length
                ? card.applicability_checks
                    .map(
                      (c) =>
                        `<li>${escapeHtml(c)}</li>`
                    )
                    .join("")
                : "<li>NOT DETERMINED</li>"
            }
          </ul>
        </div>

        <div class="evidence-subpanel">
          <div class="subpanel-header">
            Regulatory & Certification
          </div>

          <ul class="check-list">
            <li>
              <strong>Scheme:</strong>
              ${escapeHtml(
                regulatory.certification_scheme ||
                  "NOT DETERMINED"
              )}
            </li>

            <li>
              <strong>Mandatory:</strong>
              ${escapeHtml(
                regulatory.mandatory === true
                  ? "MANDATORY"
                  : regulatory.mandatory === false
                  ? "NON-MANDATORY"
                  : "NOT DETERMINED"
              )}
            </li>

            <li>
              <strong>Order:</strong>
              ${escapeHtml(
                regulatory.qco_order ||
                  "NOT DETERMINED"
              )}
            </li>

            <li>
              <strong>Ministry / Date:</strong>
              ${escapeHtml(
                regulatory.ministry ||
                  "NOT DETERMINED"
              )}
              ${
                regulatory.effective_date
                  ? ` (${escapeHtml(
                      regulatory.effective_date
                    )})`
                  : ""
              }
            </li>
          </ul>
        </div>

        <div class="evidence-subpanel">
          <div class="subpanel-header">
            Version, Amendments & Lifecycle
          </div>

          <ul class="check-list">
            <li>
              <strong>Indexed Record:</strong>
              ${escapeHtml(
                versionInfo.indexed_record ||
                  "NOT DETERMINED"
              )}
            </li>

            <li>
              <strong>Superseded:</strong>
              ${
                versionInfo.is_superseded
                  ? `YES — Superseded by ${escapeHtml(
                      versionInfo.superseded_by ||
                        "NOT DETERMINED"
                    )}`
                  : "NO / NOT INDICATED"
              }
            </li>

            <li>
              <strong>Amendments:</strong>
              ${escapeHtml(
                versionInfo.amendment ||
                  "NOT DETERMINED"
              )}
            </li>

            <li>
              <strong>Revision History:</strong>
              ${escapeHtml(
                versionInfo.amendment_history ||
                  "NOT DETERMINED"
              )}
            </li>
          </ul>
        </div>

        <div class="evidence-subpanel">
          <div class="subpanel-header">
            Allied Standards
          </div>

          <div class="tag-list" style="margin-top:4px;">
            ${alliedHtml}
          </div>
        </div>

      </div>

      ${
        aiExplanation
          ? `
            <div class="decision-support-callout">
              ${aiExplanation}
            </div>
          `
          : ""
      }

      <div class="card-trace-steps">
        ${
          traceMilestones.length
            ? traceMilestones
                .map(
                  (m) =>
                    `<span class="card-step-badge">${escapeHtml(
                      m
                    )}</span>`
                )
                .join("")
            : ""
        }
      </div>
    `;

    container.appendChild(cardEl);
  });
}


/* ============================================================
   INLINE HTML HANDLERS
   Keep these because the existing HTML may use onclick /
   onchange / onsubmit attributes.
   ============================================================ */

window.switchInputMode = switchInputMode;
window.loadSampleScenario = loadSampleScenario;
window.handleFileSelect = handleFileSelect;
window.clearInput = clearInput;
window.handleAnalyzeSubmit = handleAnalyzeSubmit;
window.resetTrace = resetTrace;