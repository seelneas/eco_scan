/**
 * EcoScan Background Service Worker (Phase 7 — Streaming, Privacy)
 * Manages communication between the content script, popup, and the FastAPI backend.
 * Supports both batch and streaming analysis modes.
 */

const API_BASE_URL = "http://localhost:8000/api/v1";
const CACHE_TTL_MS = 24 * 60 * 60 * 1000; // 24 hours

// ──────────────────────────────────────────
// Privacy: Data Anonymization
// ──────────────────────────────────────────

/**
 * Get or create a persistent anonymous user identifier.
 * Stored in chrome.storage.local.
 */
async function getAnonymousUserId() {
    return new Promise((resolve) => {
        chrome.storage.local.get("anonymous_id", (result) => {
            if (result.anonymous_id) {
                resolve(result.anonymous_id);
            } else {
                const newId = crypto.randomUUID();
                chrome.storage.local.set({ anonymous_id: newId }, () => {
                    resolve(newId);
                });
            }
        });
    });
}

/**
 * Hash a string using SHA-256 for secure identifiers.
 */
async function hashString(str) {
    const encoder = new TextEncoder();
    const data = encoder.encode(str);
    const hashBuffer = await crypto.subtle.digest("SHA-256", data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('').slice(0, 32);
}

async function anonymizeProductData(data) {
    // Strip query parameters from URLs to reduce tracking
    let cleanUrl = data.product_url;
    try {
        const url = new URL(data.product_url);
        // Keep path for product identification, strip tracking params
        const trackingParams = [
            "ref", "utm_source", "utm_medium", "utm_campaign",
            "utm_content", "utm_term", "tag", "linkCode",
            "pd_rd_r", "pd_rd_w", "pd_rd_wg", "pf_rd_p",
            "pf_rd_r", "qid", "sr", "dib", "dib_tag",
            "sprefix", "crid", "content-id", "rnid",
        ];
        trackingParams.forEach((p) => url.searchParams.delete(p));
        cleanUrl = url.toString();
    } catch (e) {
        // URL parse failed, use original
    }

    // Strip potential PII from text
    let cleanText = data.product_text || "";
    cleanText = cleanText.replace(
        /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g,
        "[EMAIL_REDACTED]"
    );
    cleanText = cleanText.replace(
        /\b(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b/g,
        "[PHONE_REDACTED]"
    );

    // Provide a hashed user identifier for anonymous analytics
    const rawId = await getAnonymousUserId();
    const userHash = await hashString(rawId);

    return {
        product_url: cleanUrl,
        product_text: cleanText,
        brand_name: data.brand_name || null,
        user_id_hash: userHash,
    };
}

// ──────────────────────────────────────────
// Cache Management (chrome.storage.local)
// ──────────────────────────────────────────
async function getCachedResult(url) {
    return new Promise((resolve) => {
        const key = `ecoscan_${btoa(url).slice(0, 50)}`;
        chrome.storage.local.get(key, (result) => {
            const cached = result[key];
            if (cached && Date.now() - cached.timestamp < CACHE_TTL_MS) {
                resolve(cached.data);
            } else {
                resolve(null);
            }
        });
    });
}

async function setCachedResult(url, data) {
    const key = `ecoscan_${btoa(url).slice(0, 50)}`;
    chrome.storage.local.set({
        [key]: {
            data: data,
            timestamp: Date.now(),
        },
    });
}

// ──────────────────────────────────────────
// API Communication: Batch Mode
// ──────────────────────────────────────────
async function analyzeProduct(productData) {
    // Check local cache first
    const cached = await getCachedResult(productData.product_url);
    if (cached) {
        console.log("[EcoScan] Local cache hit for:", productData.product_url);
        return cached;
    }

    // Anonymize before sending
    const cleanData = await anonymizeProductData(productData);

    console.log("[EcoScan] Sending to API:", cleanData.product_url);

    try {
        const response = await fetch(`${API_BASE_URL}/analyze`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                // API key would go here when configured:
                // "X-API-Key": await getApiKey(),
            },
            body: JSON.stringify(cleanData),
        });

        if (response.status === 429) {
            const detail = await response.json();
            return {
                success: false,
                product_url: productData.product_url,
                error: `Rate limit reached. Try again in ${detail.detail?.retry_after_seconds || 60} seconds.`,
            };
        }

        if (!response.ok) {
            throw new Error(`API returned ${response.status}`);
        }

        const result = await response.json();

        // Cache successful results
        if (result.success) {
            await setCachedResult(productData.product_url, result);
        }

        return result;
    } catch (error) {
        console.error("[EcoScan] API Error:", error);
        return {
            success: false,
            product_url: productData.product_url,
            error: `Connection failed: ${error.message}. Is the backend running?`,
        };
    }
}

// ──────────────────────────────────────────
// API Communication: Streaming Mode (SSE)
// ──────────────────────────────────────────
async function analyzeProductStreaming(productData, sendProgress) {
    // Check local cache first
    const cached = await getCachedResult(productData.product_url);
    if (cached) {
        console.log("[EcoScan] Local cache hit (stream mode):", productData.product_url);
        sendProgress({ type: "stage", data: { stage: "complete", message: "Loaded from cache!" } });
        return cached;
    }

    // Anonymize before sending
    const cleanData = await anonymizeProductData(productData);

    console.log("[EcoScan] Starting streaming analysis:", cleanData.product_url);

    try {
        const response = await fetch(`${API_BASE_URL}/analyze/stream`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(cleanData),
        });

        if (response.status === 429) {
            return {
                success: false,
                error: "Rate limit reached. Try again later.",
            };
        }

        if (!response.ok) {
            throw new Error(`API returned ${response.status}`);
        }

        // Read SSE stream
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        let finalResult = null;

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });

            // Parse SSE events from buffer
            const events = buffer.split("\n\n");
            buffer = events.pop(); // Keep incomplete event in buffer

            for (const event of events) {
                if (!event.trim()) continue;

                const lines = event.trim().split("\n");
                let eventType = "";
                let eventData = "";

                for (const line of lines) {
                    if (line.startsWith("event: ")) {
                        eventType = line.slice(7);
                    } else if (line.startsWith("data: ")) {
                        eventData = line.slice(6);
                    }
                }

                if (!eventType || !eventData) continue;

                try {
                    const parsed = JSON.parse(eventData);

                    // Forward progress events to popup
                    sendProgress({ type: eventType, data: parsed });

                    if (eventType === "result") {
                        finalResult = parsed;
                    }
                } catch (e) {
                    console.warn("[EcoScan] Failed to parse SSE event:", e);
                }
            }
        }

        // Cache the final result
        if (finalResult && finalResult.success) {
            await setCachedResult(productData.product_url, finalResult);
        }

        return finalResult || { success: false, error: "Stream ended without result." };

    } catch (error) {
        console.error("[EcoScan] Stream Error:", error);
        return {
            success: false,
            error: `Streaming failed: ${error.message}. Is the backend running?`,
        };
    }
}

// ──────────────────────────────────────────
// Message Handlers
// ──────────────────────────────────────────
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === "PRODUCT_DETECTED") {
        chrome.action.setBadgeText({ text: "🌿", tabId: sender.tab.id });
        chrome.action.setBadgeBackgroundColor({
            color: "#10B981",
            tabId: sender.tab.id,
        });
    }

    if (message.action === "ANALYZE_PRODUCT") {
        // Batch mode (existing behavior)
        analyzeProduct(message.data).then((result) => {
            sendResponse(result);
        });
        return true;
    }

    if (message.action === "ANALYZE_PRODUCT_STREAM") {
        // Streaming mode (Phase 7)
        // Use a port for bidirectional communication
        const port = chrome.runtime.connect({ name: "stream_analysis" });

        analyzeProductStreaming(message.data, (progress) => {
            // Send progress updates back to popup via the same message channel
            // Since we can't use sendResponse multiple times, use runtime messaging
            chrome.runtime.sendMessage({
                action: "STREAM_PROGRESS",
                data: progress,
            });
        }).then((result) => {
            sendResponse(result);
        });
        return true;
    }

    if (message.action === "GET_PRODUCT_DATA") {
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            const activeTab = tabs[0];
            if (!activeTab || !activeTab.id || activeTab.url.startsWith("chrome://")) {
                sendResponse({ has_data: false, error: "Cannot scan this page." });
                return;
            }

            chrome.tabs.sendMessage(
                activeTab.id,
                { action: "EXTRACT_PRODUCT" },
                (response) => {
                    if (chrome.runtime.lastError) {
                        console.warn("[EcoScan] Content script not found:", chrome.runtime.lastError.message);
                        sendResponse({ has_data: false, error: "Content script not active. Refresh the page." });
                    } else {
                        sendResponse(response);
                    }
                }
            );
        });
        return true;
    }

    if (message.action === "SUBMIT_FEEDBACK") {
        // Send feedback to backend
        getAnonymousUserId().then(rawId => hashString(rawId)).then(userHash => {
            const feedbackData = {
                ...message.data,
                user_id_hash: message.data.user_id_hash || userHash
            };

            fetch(`${API_BASE_URL}/feedback`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(feedbackData),
            })
                .then((r) => r.json())
                .then((res) => sendResponse(res))
                .catch((err) => sendResponse({ success: false, error: err.message }));
        });
        return true;
    }
});
