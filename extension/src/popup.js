/**
 * EcoScan Popup Script
 * Handles the popup UI: scanning, score animation, accordion panels,
 * feedback form, and rendering the full sustainability report.
 */

// ──────────────────────────────────────────
// DOM Elements
// ──────────────────────────────────────────
const scanBtn = document.getElementById("scan-btn");
const retryBtn = document.getElementById("retry-btn");
const closeBtn = document.getElementById("close-btn");
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

// Brand Reputation elements
const brandSection = document.getElementById("brand-section");
const brandOverallGrade = document.getElementById("brand-overall-grade");
const brandStatsGrid = document.getElementById("brand-stats-grid");
const brandProductsCount = document.getElementById("brand-products-count");

// Alternatives elements
const alternativesSection = document.getElementById("alternatives-section");
const alternativesList = document.getElementById("alternatives-list");
const altsCount = document.getElementById("alts-count");

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

// Feedback elements
const feedbackToggle = document.getElementById("feedback-toggle");
const feedbackBtn = document.getElementById("feedback-btn");
const feedbackForm = document.getElementById("feedback-form");
const feedbackType = document.getElementById("feedback-type");
const feedbackText = document.getElementById("feedback-text");
const feedbackCancel = document.getElementById("feedback-cancel");
const feedbackSubmit = document.getElementById("feedback-submit");
const feedbackSuccess = document.getElementById("feedback-success");

// Loading steps
const stepExtract = document.getElementById("step-extract");
const stepAnalyze = document.getElementById("step-analyze");
const stepScore = document.getElementById("step-score");

// Track current analysis for feedback context
let currentAnalysis = null;

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

    document.getElementById("grad-stop-1").setAttribute("stop-color", gradStart);
    document.getElementById("grad-stop-2").setAttribute("stop-color", gradEnd);

    scoreCircle.style.strokeDasharray = circumference;
    scoreCircle.style.strokeDashoffset = circumference;

    requestAnimationFrame(() => {
        scoreCircle.style.strokeDashoffset = offset;
    });

    animateCounter(scoreValue, Math.round(finalScore));
    scoreValue.style.color = color;

    scoreGrade.textContent = grade;
    scoreGrade.style.background = `${color}1F`;
    scoreGrade.style.color = color;

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

    gwrLevelBadge.textContent = riskLevel.toUpperCase();
    gwrLevelBadge.className = `gwr-badge risk-${riskLevel}`;

    gwrVagueCount.textContent = gwr.vague_claims_count || 0;
    gwrEvidenceCount.textContent = gwr.verifiable_evidence_count || 0;
    gwrIndexValue.textContent = gwr.gwr_index || 0;

    if (gwr.penalty_percent > 0) {
        gwrPenalty.textContent = `⚠️ Score reduced by ${gwr.penalty_percent}% due to greenwashing risk`;
        gwrPenalty.style.display = "block";
    } else {
        gwrPenalty.style.display = "none";
    }

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
// Render Brand Profile
// ──────────────────────────────────────────
function renderBrandProfile(brand) {
    if (!brand) {
        brandSection.classList.add("hidden");
        return;
    }

    brandSection.classList.remove("hidden");
    brandOverallGrade.textContent = brand.overall_grade || "—";
    brandProductsCount.textContent = `${brand.total_products_scanned || 0} products analyzed in our community`;

    const color = getScoreColor(brand.average_score);
    brandOverallGrade.style.background = `${color}1F`;
    brandOverallGrade.style.color = color;

    brandStatsGrid.innerHTML = `
        <div class="brand-stat-card">
            <span class="brand-stat-label">Avg. Score</span>
            <span class="brand-stat-value" style="color: ${color}">${Math.round(brand.average_score)}/100</span>
        </div>
        <div class="brand-stat-card">
            <span class="brand-stat-label">Risk Level</span>
            <span class="brand-stat-value">${brand.overall_risk_level.toUpperCase()}</span>
        </div>
        <div class="brand-stat-card">
            <span class="brand-stat-label">Ethical Focus</span>
            <span class="brand-stat-value">${Math.round(brand.average_ethics_score)}/20</span>
        </div>
        <div class="brand-stat-card">
            <span class="brand-stat-label">Best Finding</span>
            <span class="brand-stat-value">${Math.round(brand.best_product_score)}/100</span>
        </div>
    `;
}

// ──────────────────────────────────────────
// Render Alternatives
// ──────────────────────────────────────────
function renderAlternatives(alternatives, currentScore) {
    if (!alternatives || alternatives.length === 0) {
        alternativesSection.classList.add("hidden");
        return;
    }

    alternativesSection.classList.remove("hidden");
    altsCount.textContent = alternatives.length;
    alternativesList.innerHTML = "";

    alternatives.forEach((alt) => {
        const improvement = Math.round(alt.score - currentScore);
        const item = document.createElement("a");
        item.href = alt.url;
        item.target = "_blank";
        item.className = "alternative-item";
        item.innerHTML = `
            <div class="alt-header">
                <span class="alt-name">${alt.name}</span>
                <span class="alt-score-badge">${Math.round(alt.score)}</span>
            </div>
            <div class="alt-meta">
                <span class="alt-brand">${alt.brand}</span>
                ${improvement > 0 ? `<span class="alt-improvement">+${improvement} points better</span>` : ""}
            </div>
        `;
        alternativesList.appendChild(item);
    });
}

// ──────────────────────────────────────────
// Master Render Function
// ──────────────────────────────────────────
function renderScore(result) {
    console.log("[EcoScan Popup] Starting result render:", result);
    const { scoring, brand_profile, alternatives } = result;

    if (!scoring) {
        console.error("[EcoScan Popup] Error: Scoring data is missing from response.");
        return;
    }

    const {
        final_score,
        grade,
        category_scores,
        greenwashing_report,
        llm_analysis,
    } = scoring;

    // Product info
    try {
        productName.textContent = llm_analysis.product.name || "Unknown Product";
        productBrand.textContent = llm_analysis.product.brand
            ? `by ${llm_analysis.product.brand}`
            : "";
    } catch (e) { console.warn("Render failed: Product Info", e); }

    // Brand Profile
    try { renderBrandProfile(brand_profile); } catch (e) { console.warn("Render failed: Brand Profile", e); }

    // Score ring
    try { renderScoreRing(final_score, grade); } catch (e) { console.warn("Render failed: Score Ring", e); }

    // Category breakdown
    try { renderCategories(category_scores); } catch (e) { console.warn("Render failed: Categories", e); }

    // Materials
    try { renderMaterials(llm_analysis.materials); } catch (e) { console.warn("Render failed: Materials", e); }

    // Certifications
    try { renderCertifications(llm_analysis.certifications); } catch (e) { console.warn("Render failed: Certifications", e); }

    // Greenwashing report
    try { renderGWR(greenwashing_report); } catch (e) { console.warn("Render failed: Greenwashing", e); }

    // Alternatives
    try { renderAlternatives(alternatives, final_score); } catch (e) { console.warn("Render failed: Alternatives", e); }

    // Store context for feedback
    try {
        currentAnalysis = {
            product_url: result.product_url || window.location.href,
            score: final_score,
        };
        resetFeedback();
    } catch (e) { console.warn("Failed to set feedback context", e); }

    showState("result");
    console.log("[EcoScan Popup] Render complete.");
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
// Scan Action (Phase 7: Streaming Support)
// ──────────────────────────────────────────
let streamProgressListener = null;

function triggerScan() {
    showState("loading");
    advanceLoadingStep("analyze");

    // Clean up any previous stream listener
    if (streamProgressListener) {
        chrome.runtime.onMessage.removeListener(streamProgressListener);
        streamProgressListener = null;
    }

    chrome.runtime.sendMessage({ action: "GET_PRODUCT_DATA" }, (productData) => {
        if (!productData || !productData.has_data) {
            console.warn("[EcoScan] Data extraction failed:", productData?.error);
            document.getElementById("error-message").textContent =
                productData?.error || "No product data found. Visit a product page on a supported site and try again.";
            showState("error");
            return;
        }

        // Set up listener for streaming progress updates
        streamProgressListener = (message) => {
            if (message.action === "STREAM_PROGRESS" && message.data) {
                handleStreamProgress(message.data);
            }
        };
        chrome.runtime.onMessage.addListener(streamProgressListener);

        // Use streaming analysis with batch fallback
        chrome.runtime.sendMessage(
            { action: "ANALYZE_PRODUCT_STREAM", data: productData },
            (result) => {
                // Clean up listener
                if (streamProgressListener) {
                    chrome.runtime.onMessage.removeListener(streamProgressListener);
                    streamProgressListener = null;
                }

                if (result && result.success) {
                    advanceLoadingStep("complete");
                    setTimeout(() => renderScore(result), 300);
                } else if (result && result.error && result.error.includes("Streaming failed")) {
                    // Fallback to batch mode
                    console.log("[EcoScan] Streaming failed, falling back to batch mode");
                    advanceLoadingStep("score");
                    chrome.runtime.sendMessage(
                        { action: "ANALYZE_PRODUCT", data: productData },
                        (batchResult) => {
                            advanceLoadingStep("complete");
                            setTimeout(() => {
                                if (batchResult && batchResult.success) {
                                    renderScore(batchResult);
                                } else {
                                    document.getElementById("error-message").textContent =
                                        batchResult?.error || "Analysis failed. Make sure the backend server is running.";
                                    showState("error");
                                }
                            }, 400);
                        }
                    );
                } else {
                    document.getElementById("error-message").textContent =
                        result?.error || "Analysis failed. Make sure the backend server is running.";
                    showState("error");
                }
            }
        );
    });
}

function handleStreamProgress(event) {
    const { type, data } = event;

    if (type === "stage") {
        switch (data.stage) {
            case "extracting":
                resetLoadingSteps();
                stepExtract.classList.add("active");
                break;
            case "analyzing":
                advanceLoadingStep("analyze");
                break;
            case "scoring":
                advanceLoadingStep("score");
                break;
            case "complete":
                advanceLoadingStep("complete");
                break;
        }
        // Update loading title if there's a message
        const loadingTitle = document.querySelector(".loading-title");
        if (loadingTitle && data.message) {
            loadingTitle.textContent = data.message;
        }
    } else if (type === "chunk") {
        // Show live progress indicator (chars received)
        const loadingTitle = document.querySelector(".loading-title");
        if (loadingTitle && data.total_length) {
            loadingTitle.textContent = `Analyzing... (${data.total_length} chars received)`;
        }
    }
}

scanBtn.addEventListener("click", triggerScan);
retryBtn.addEventListener("click", triggerScan);

// ──────────────────────────────────────────
// Feedback Logic (3-state: toggle → form → success)
// ──────────────────────────────────────────

function resetFeedback() {
    feedbackToggle.classList.remove("hidden");
    feedbackForm.classList.add("hidden");
    feedbackSuccess.classList.add("hidden");
    feedbackText.value = "";
    feedbackType.selectedIndex = 0;
    feedbackSubmit.disabled = false;
    feedbackSubmit.textContent = "Send Feedback";
}

// State 1 → State 2: Show the form
feedbackBtn.addEventListener("click", () => {
    feedbackToggle.classList.add("hidden");
    feedbackForm.classList.remove("hidden");
    feedbackText.focus();
});

// State 2 → State 1: Cancel
feedbackCancel.addEventListener("click", () => {
    resetFeedback();
});

// State 2 → State 3: Submit
feedbackSubmit.addEventListener("click", () => {
    const message = feedbackText.value.trim();
    if (!message) {
        feedbackText.style.borderColor = "#EF4444";
        feedbackText.placeholder = "Please describe the issue before sending...";
        return;
    }
    feedbackText.style.borderColor = "";

    if (!currentAnalysis) return;

    feedbackSubmit.disabled = true;
    feedbackSubmit.textContent = "Sending...";

    const payload = {
        product_url: currentAnalysis.product_url,
        feedback_type: feedbackType.value,
        message: message,
        expected_score: null,
        user_id_hash: "anonymous_user",
    };

    chrome.runtime.sendMessage({ action: "SUBMIT_FEEDBACK", data: payload }, (response) => {
        if (response && response.success) {
            // Show success
            feedbackForm.classList.add("hidden");
            feedbackSuccess.classList.remove("hidden");

            // Auto-reset after 4 seconds
            setTimeout(() => {
                resetFeedback();
            }, 4000);
        } else {
            feedbackSubmit.disabled = false;
            feedbackSubmit.textContent = "Retry";
            feedbackText.value = message;
            // Show inline error
            const errorMsg = document.createElement("p");
            errorMsg.className = "feedback-error";
            errorMsg.textContent = "Failed to send. Check your connection and try again.";
            if (!feedbackForm.querySelector(".feedback-error")) {
                feedbackForm.appendChild(errorMsg);
            }
        }
    });
});

// ──────────────────────────────────────────
// Initialize
// ──────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
    initAccordions();
    showState("idle");

    // Close button handler
    if (closeBtn) {
        closeBtn.addEventListener("click", () => {
            window.close();
        });
    }
});
