/**
 * EcoScan Popup Script
 * Handles the popup UI: scanning, score animation, accordion panels,
 * and rendering the full sustainability report.
 */

// ──────────────────────────────────────────
// DOM Elements
// ──────────────────────────────────────────
const scanBtn = document.getElementById("scan-btn");
const retryBtn = document.getElementById("retry-btn");
const statusEl = document.getElementById("status");
const loadingEl = document.getElementById("loading");
const resultEl = document.getElementById("result");
const errorEl = document.getElementById("error");

// Score elements
const scoreCircle = document.getElementById("score-circle");
const scoreValue = document.getElementById("score-value");
const scoreGrade = document.getElementById("score-grade");
const scoreLabel = document.getElementById("score-label");
const productName = document.getElementById("product-name");
const productBrand = document.getElementById("product-brand");
const categoriesContainer = document.getElementById("categories");

// Material & Certification elements
const materialsList = document.getElementById("materials-list");
const certsList = document.getElementById("certs-list");
const certsCount = document.getElementById("certs-count");

// GWR elements
const gwrLevelBadge = document.getElementById("gwr-level");
const gwrVagueCount = document.getElementById("gwr-vague-count");
const gwrEvidenceCount = document.getElementById("gwr-evidence-count");
const gwrIndexValue = document.getElementById("gwr-index-value");
const gwrPenalty = document.getElementById("gwr-penalty");
const gwrFlagged = document.getElementById("gwr-flagged");
const gwrUnsupported = document.getElementById("gwr-unsupported");

// Loading steps
const stepExtract = document.getElementById("step-extract");
const stepAnalyze = document.getElementById("step-analyze");
const stepScore = document.getElementById("step-score");

// ──────────────────────────────────────────
// UI State Management
// ──────────────────────────────────────────
function showState(state) {
    loadingEl.classList.add("hidden");
    resultEl.classList.add("hidden");
    errorEl.classList.add("hidden");
    statusEl.classList.add("hidden");

    if (state === "loading") {
        loadingEl.classList.remove("hidden");
        scanBtn.disabled = true;
        resetLoadingSteps();
    } else if (state === "result") {
        resultEl.classList.remove("hidden");
        scanBtn.disabled = false;
    } else if (state === "error") {
        errorEl.classList.remove("hidden");
        scanBtn.disabled = false;
    } else {
        statusEl.classList.remove("hidden");
        scanBtn.disabled = false;
    }
}

function resetLoadingSteps() {
    [stepExtract, stepAnalyze, stepScore].forEach((el) => {
        el.classList.remove("active", "done");
    });
    stepExtract.classList.add("active");
}

function advanceLoadingStep(step) {
    if (step === "analyze") {
        stepExtract.classList.remove("active");
        stepExtract.classList.add("done");
        stepAnalyze.classList.add("active");
    } else if (step === "score") {
        stepAnalyze.classList.remove("active");
        stepAnalyze.classList.add("done");
        stepScore.classList.add("active");
    } else if (step === "complete") {
        stepScore.classList.remove("active");
        stepScore.classList.add("done");
    }
}

// ──────────────────────────────────────────
// Score Color & Label
// ──────────────────────────────────────────
function getScoreColor(score) {
    if (score >= 80) return "#10B981";
    if (score >= 65) return "#3B82F6";
    if (score >= 50) return "#F59E0B";
    if (score >= 35) return "#F97316";
    return "#EF4444";
}

function getScoreGradient(score) {
    if (score >= 80) return ["#10B981", "#06B6D4"];
    if (score >= 65) return ["#3B82F6", "#6366F1"];
    if (score >= 50) return ["#F59E0B", "#F97316"];
    if (score >= 35) return ["#F97316", "#EF4444"];
    return ["#EF4444", "#DC2626"];
}

function getScoreLabel(score) {
    if (score >= 80) return "Excellent";
    if (score >= 65) return "Good";
    if (score >= 50) return "Average";
    if (score >= 35) return "Below Average";
    return "Poor";
}

function getCategoryEmoji(name) {
    const n = name.toLowerCase();
    if (n.includes("material")) return "🧵";
    if (n.includes("certif")) return "✅";
    if (n.includes("transparen")) return "🔍";
    if (n.includes("ethic")) return "🤝";
    return "📊";
}

// ──────────────────────────────────────────
// Animated Counter
// ──────────────────────────────────────────
function animateCounter(element, target, duration = 1200) {
    const start = 0;
    const startTime = performance.now();

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        // Ease-out cubic
        const eased = 1 - Math.pow(1 - progress, 3);
        const current = Math.round(start + (target - start) * eased);
        element.textContent = current;
        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }
    requestAnimationFrame(update);
}

// ──────────────────────────────────────────
// Render Score Ring
// ──────────────────────────────────────────
function renderScoreRing(finalScore, grade) {
    const color = getScoreColor(finalScore);
    const [gradStart, gradEnd] = getScoreGradient(finalScore);
    const circumference = 2 * Math.PI * 52;
    const offset = circumference - (finalScore / 100) * circumference;

    // Update gradient colors
    document.getElementById("grad-stop-1").setAttribute("stop-color", gradStart);
    document.getElementById("grad-stop-2").setAttribute("stop-color", gradEnd);

    // Reset and animate the circle
    scoreCircle.style.strokeDasharray = circumference;
    scoreCircle.style.strokeDashoffset = circumference;

    requestAnimationFrame(() => {
        scoreCircle.style.strokeDashoffset = offset;
    });

    // Animate the number
    animateCounter(scoreValue, Math.round(finalScore));
    scoreValue.style.color = color;

    // Update grade badge
    scoreGrade.textContent = grade;
    scoreGrade.style.background = `${color}1F`; // 12% opacity
    scoreGrade.style.color = color;

    // Update label
    scoreLabel.textContent = getScoreLabel(finalScore);
    scoreLabel.style.color = color;
}

// ──────────────────────────────────────────
// Render Category Cards
// ──────────────────────────────────────────
function renderCategories(categoryScores) {
    categoriesContainer.innerHTML = "";

    categoryScores.forEach((cat, index) => {
        const pct = Math.round((cat.score / cat.max_score) * 100);
        const color = getScoreColor(pct);
        const emoji = getCategoryEmoji(cat.category);

        const card = document.createElement("div");
        card.className = "category-card";
        card.style.animationDelay = `${index * 0.1}s`;
        card.innerHTML = `
      <div class="category-header">
        <span class="category-name"><span class="category-emoji">${emoji}</span> ${cat.category}</span>
        <span class="category-score" style="color: ${color}">${Math.round(cat.score)}/${cat.max_score}</span>
      </div>
      <div class="progress-bar">
        <div class="progress-fill" style="width: 0%; background: ${color}"></div>
      </div>
      <p class="category-details">${cat.details}</p>
    `;
        categoriesContainer.appendChild(card);

        // Animate progress bar
        requestAnimationFrame(() => {
            const fill = card.querySelector(".progress-fill");
            fill.style.width = `${pct}%`;
        });
    });
}

// ──────────────────────────────────────────
// Render Materials
// ──────────────────────────────────────────
function renderMaterials(materials) {
    materialsList.innerHTML = "";

    if (!materials || materials.length === 0) {
        materialsList.innerHTML = '<p class="no-materials">No material data extracted.</p>';
        return;
    }

    materials.forEach((mat) => {
        const tier = mat.impact_tier || "low";
        const item = document.createElement("div");
        item.className = "material-item";
        item.innerHTML = `
      <span class="material-tier-dot tier-${tier}"></span>
      <div class="material-info">
        <span class="material-name">${mat.name}</span>
        <span class="material-pct">${mat.percentage != null ? mat.percentage + "%" : "Unknown %"}</span>
      </div>
      <span class="material-tier-label tier-${tier}">${tier}</span>
    `;
        materialsList.appendChild(item);
    });
}

// ──────────────────────────────────────────
// Render Certifications
// ──────────────────────────────────────────
function renderCertifications(certifications) {
    certsList.innerHTML = "";

    if (!certifications || certifications.length === 0) {
        certsList.innerHTML = '<p class="no-certs">No certifications detected.</p>';
        certsCount.textContent = "0";
        return;
    }

    certsCount.textContent = certifications.length.toString();
    const thirdPartyCount = certifications.filter((c) => c.is_third_party).length;

    certifications.forEach((cert) => {
        const iconClass = cert.is_third_party ? "third-party" : "brand-internal";
        const iconEmoji = cert.is_third_party ? "✅" : "⚠️";
        const badgeClass = cert.is_third_party ? "verified" : "unverified";
        const badgeText = cert.is_third_party ? "Verified" : "Brand Label";

        const item = document.createElement("div");
        item.className = "cert-item";
        item.innerHTML = `
      <span class="cert-icon ${iconClass}">${iconEmoji}</span>
      <div class="cert-info">
        <span class="cert-name">${cert.name}</span>
        <span class="cert-standard">${cert.standard}</span>
      </div>
      <span class="cert-badge ${badgeClass}">${badgeText}</span>
    `;
        certsList.appendChild(item);
    });
}

// ──────────────────────────────────────────
// Render Greenwashing Risk
// ──────────────────────────────────────────
function renderGWR(greenwashingReport) {
    const gwr = greenwashingReport;
    const riskLevel = gwr.risk_level || "medium";

    // Badge
    gwrLevelBadge.textContent = riskLevel.toUpperCase();
    gwrLevelBadge.className = `gwr-badge risk-${riskLevel}`;

    // Stats
    gwrVagueCount.textContent = gwr.vague_claims_count || 0;
    gwrEvidenceCount.textContent = gwr.verifiable_evidence_count || 0;
    gwrIndexValue.textContent = gwr.gwr_index || 0;

    // Penalty
    if (gwr.penalty_percent > 0) {
        gwrPenalty.textContent = `⚠️ Score reduced by ${gwr.penalty_percent}% due to greenwashing risk`;
        gwrPenalty.style.display = "block";
    } else {
        gwrPenalty.style.display = "none";
    }

    // Flagged terms
    gwrFlagged.innerHTML = "";
    if (gwr.flagged_terms && gwr.flagged_terms.length > 0) {
        gwr.flagged_terms.forEach((term) => {
            const risk = term.greenwashing_risk || "medium";
            const tag = document.createElement("div");
            tag.className = `flagged-term risk-${risk}`;
            tag.innerHTML = `
        <strong>"${term.word}"</strong>
        <span class="flag-reason">${term.reason}</span>
      `;
            gwrFlagged.appendChild(tag);
        });
    } else {
        gwrFlagged.innerHTML = '<p class="no-flags">✅ No vague claims detected.</p>';
    }

    // Unsupported claims
    gwrUnsupported.innerHTML = "";
    if (gwr.unsupported_claims && gwr.unsupported_claims.length > 0) {
        const unsupportedHeader = document.createElement("p");
        unsupportedHeader.style.cssText = "font-size:11px;font-weight:600;color:#EF4444;margin-bottom:6px;";
        unsupportedHeader.textContent = "⛔ Unsupported Claims:";
        gwrUnsupported.appendChild(unsupportedHeader);

        gwr.unsupported_claims.forEach((claim) => {
            const el = document.createElement("div");
            el.className = "unsupported-claim";
            el.innerHTML = `
        <strong>"${claim.claim}"</strong>
        <span>${claim.evidence}</span>
      `;
            gwrUnsupported.appendChild(el);
        });
    }
}

// ──────────────────────────────────────────
// Master Render Function
// ──────────────────────────────────────────
function renderScore(scoring) {
    const {
        final_score,
        grade,
        category_scores,
        greenwashing_report,
        llm_analysis,
    } = scoring;

    // Product info
    productName.textContent = llm_analysis.product.name || "Unknown Product";
    productBrand.textContent = llm_analysis.product.brand
        ? `by ${llm_analysis.product.brand}`
        : "";

    // Score ring
    renderScoreRing(final_score, grade);

    // Category breakdown
    renderCategories(category_scores);

    // Materials
    renderMaterials(llm_analysis.materials);

    // Certifications
    renderCertifications(llm_analysis.certifications);

    // Greenwashing report
    renderGWR(greenwashing_report);

    showState("result");
}

// ──────────────────────────────────────────
// Accordion Logic
// ──────────────────────────────────────────
function initAccordions() {
    const triggers = document.querySelectorAll(".accordion-trigger");

    triggers.forEach((trigger) => {
        const targetId = trigger.getAttribute("data-target");
        const panel = document.getElementById(targetId);
        const isExpanded = panel.classList.contains("expanded");

        trigger.setAttribute("aria-expanded", isExpanded ? "true" : "false");

        trigger.addEventListener("click", () => {
            const expanded = trigger.getAttribute("aria-expanded") === "true";
            trigger.setAttribute("aria-expanded", !expanded);
            panel.classList.toggle("expanded");
        });
    });
}

// ──────────────────────────────────────────
// Scan Action
// ──────────────────────────────────────────
function triggerScan() {
    showState("loading");

    // Step 1: Get product data from content script
    advanceLoadingStep("analyze");

    chrome.runtime.sendMessage({ action: "GET_PRODUCT_DATA" }, (productData) => {
        if (!productData || !productData.has_data) {
            document.getElementById("error-message").textContent =
                "No product data found. Visit a product page on a supported site and try again.";
            showState("error");
            return;
        }

        // Step 2: Send to backend
        advanceLoadingStep("score");

        chrome.runtime.sendMessage(
            { action: "ANALYZE_PRODUCT", data: productData },
            (result) => {
                advanceLoadingStep("complete");

                setTimeout(() => {
                    if (result && result.success) {
                        renderScore(result.scoring);
                    } else {
                        document.getElementById("error-message").textContent =
                            result?.error || "Analysis failed. Make sure the backend server is running.";
                        showState("error");
                    }
                }, 400);
            }
        );
    });
}

scanBtn.addEventListener("click", triggerScan);
retryBtn.addEventListener("click", triggerScan);

// ──────────────────────────────────────────
// Initialize
// ──────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
    initAccordions();
    showState("idle");
});
