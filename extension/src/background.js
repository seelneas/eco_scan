/**
 * EcoScan Background Service Worker
 * Manages communication between the content script, popup, and the FastAPI backend.
 */

const API_BASE_URL = "http://localhost:8000/api/v1";
const CACHE_TTL_MS = 24 * 60 * 60 * 1000; // 24 hours

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
// API Communication
// ──────────────────────────────────────────
async function analyzeProduct(productData) {
    // Check cache first
    const cached = await getCachedResult(productData.product_url);
    if (cached) {
        console.log("[EcoScan] Cache hit for:", productData.product_url);
        return cached;
    }

    console.log("[EcoScan] Sending to API:", productData.product_url);

    try {
        const response = await fetch(`${API_BASE_URL}/analyze`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                product_url: productData.product_url,
                product_text: productData.product_text,
                brand_name: productData.brand_name || null,
            }),
        });

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
// Message Handlers
// ──────────────────────────────────────────

// Listen for product detection from content script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === "PRODUCT_DETECTED") {
        // Update the extension badge to indicate a product was found
        chrome.action.setBadgeText({ text: "🌿", tabId: sender.tab.id });
        chrome.action.setBadgeBackgroundColor({
            color: "#10B981",
            tabId: sender.tab.id,
        });
    }

    if (message.action === "ANALYZE_PRODUCT") {
        // Triggered by the popup when user clicks "Scan"
        analyzeProduct(message.data).then((result) => {
            sendResponse(result);
        });
        return true; // Keep channel open for async response
    }

    if (message.action === "GET_PRODUCT_DATA") {
        // Popup asks the content script for product data
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            if (tabs[0]) {
                chrome.tabs.sendMessage(
                    tabs[0].id,
                    { action: "EXTRACT_PRODUCT" },
                    (response) => {
                        sendResponse(response);
                    }
                );
            }
        });
        return true;
    }
});
