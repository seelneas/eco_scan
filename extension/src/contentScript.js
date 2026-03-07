/**
 * EcoScan Content Script
 * Extracts product information from e-commerce pages.
 * Supports: Amazon, Walmart, Patagonia, H&M, Zara, Target, Etsy, Nordstrom.
 */

// ──────────────────────────────────────────
// Platform-Specific DOM Extractors
// ──────────────────────────────────────────
const EXTRACTORS = {
    "amazon.com": {
        name: () =>
            document.getElementById("productTitle")?.textContent?.trim() || null,
        brand: () =>
            document.getElementById("bylineInfo")?.textContent?.replace(/^(Brand:|Visit the|by)\s*/i, "").trim() ||
            document.querySelector("#brand")?.textContent?.trim() ||
            null,
        description: () => {
            const parts = [];
            // Feature bullets
            const bullets = document.querySelectorAll("#feature-bullets .a-list-item");
            if (bullets.length) {
                parts.push(Array.from(bullets).map((li) => li.textContent.trim()).join("\n"));
            }
            // Product description
            const desc = document.getElementById("productDescription");
            if (desc) parts.push(desc.textContent.trim());
            // A+ content
            const aPlus = document.querySelector("#aplus_feature_div, #aplusProductDescription");
            if (aPlus) parts.push(aPlus.textContent.trim().slice(0, 2000));
            return parts.join("\n") || null;
        },
        materials: () => {
            let text = "";
            // Technical details table
            const rows = document.querySelectorAll(
                "#productDetails_techSpec_section_1 tr, #detailBullets_feature_div .a-list-item, #productDetails_detailBullets_sections1 tr"
            );
            rows.forEach((row) => {
                const content = row.textContent.toLowerCase();
                if (content.includes("material") || content.includes("fabric") || content.includes("composition") || content.includes("fiber")) {
                    text += row.textContent.trim() + "\n";
                }
            });
            // Product information section
            const infoSections = document.querySelectorAll(".a-section .a-spacing-small");
            infoSections.forEach((sec) => {
                const content = sec.textContent.toLowerCase();
                if (content.includes("material") || content.includes("fabric")) {
                    text += sec.textContent.trim() + "\n";
                }
            });
            return text || null;
        },
    },

    "walmart.com": {
        name: () =>
            document.querySelector("[itemprop='name'], h1.prod-ProductTitle")?.textContent?.trim() || null,
        brand: () =>
            document.querySelector("[itemprop='brand'], .prod-brandName a")?.textContent?.trim() || null,
        description: () => {
            const desc = document.querySelector("[data-testid='product-description'], .about-product-description, .dangerous-html");
            return desc?.textContent?.trim() || null;
        },
        materials: () => {
            const spec = document.querySelector(".product-specifications, .specifications-list");
            if (!spec) return null;
            let text = "";
            const rows = spec.querySelectorAll("tr, .spec-row");
            rows.forEach((row) => {
                const content = row.textContent.toLowerCase();
                if (content.includes("material") || content.includes("fabric") || content.includes("composition")) {
                    text += row.textContent.trim() + "\n";
                }
            });
            return text || null;
        },
    },

    "patagonia.com": {
        name: () =>
            document.querySelector("h1.product-hero__title, h1[class*='product'], h1")?.textContent?.trim() || null,
        brand: () => "Patagonia",
        description: () => {
            const parts = [];
            const desc = document.querySelector(".product-description, [class*='product-description'], [class*='pdp-description']");
            if (desc) parts.push(desc.textContent.trim());
            // Features section
            const features = document.querySelector("[class*='features'], [class*='specs']");
            if (features) parts.push(features.textContent.trim());
            return parts.join("\n") || null;
        },
        materials: () => {
            const details = document.querySelector(".product-details, [class*='materials'], [class*='fabric']");
            return details?.textContent?.trim() || null;
        },
    },

    "hm.com": {
        name: () =>
            document.querySelector("h1.product-item-headline, h1[class*='ProductName']")?.textContent?.trim() || null,
        brand: () => "H&M",
        description: () => {
            const desc = document.querySelector("[class*='description'], .product-description");
            return desc?.textContent?.trim() || null;
        },
        materials: () => {
            // H&M has a dedicated materials/composition section
            const comp = document.querySelector("[class*='composition'], [class*='material']");
            return comp?.textContent?.trim() || null;
        },
    },

    "zara.com": {
        name: () =>
            document.querySelector("h1.product-detail-info__header-name, h1[class*='product-name']")?.textContent?.trim() || null,
        brand: () => "Zara",
        description: () => {
            const desc = document.querySelector("[class*='product-detail-description'], [class*='description']");
            return desc?.textContent?.trim() || null;
        },
        materials: () => {
            // Zara typically has composition in a care/composition section
            const comp = document.querySelector("[class*='composition'], [class*='care-detail']");
            return comp?.textContent?.trim() || null;
        },
    },

    "target.com": {
        name: () =>
            document.querySelector("h1[data-test='product-title'], h1")?.textContent?.trim() || null,
        brand: () =>
            document.querySelector("[data-test='product-brand'] a, .h-text-grayDark")?.textContent?.trim() || null,
        description: () => {
            const desc = document.querySelector("[data-test='product-description'], .product-description");
            return desc?.textContent?.trim() || null;
        },
        materials: () => {
            const spec = document.querySelector("[data-test='product-specifications'], .product-specifications");
            if (!spec) return null;
            return spec.textContent.trim();
        },
    },

    "etsy.com": {
        name: () =>
            document.querySelector("h1[data-buy-box-listing-title], h1.wt-text-body-03")?.textContent?.trim() || null,
        brand: () =>
            document.querySelector("[data-shop-name], .wt-text-link-no-underline")?.textContent?.trim() || null,
        description: () => {
            const desc = document.querySelector("[data-id='description-text'], .wt-content-toggle__body");
            return desc?.textContent?.trim() || null;
        },
        materials: () => {
            // Etsy often has materials in attributes
            const attrs = document.querySelectorAll(".wt-text-caption");
            let text = "";
            attrs.forEach((el) => {
                const content = el.textContent.toLowerCase();
                if (content.includes("material") || content.includes("fabric")) {
                    text += el.textContent.trim() + "\n";
                }
            });
            return text || null;
        },
    },

    "nordstrom.com": {
        name: () =>
            document.querySelector("h1[itemprop='name'], h1.nui-fw3gl5")?.textContent?.trim() || null,
        brand: () =>
            document.querySelector("[itemprop='brand'] span, a[class*='brand']")?.textContent?.trim() || null,
        description: () => {
            const desc = document.querySelector("[itemProp='description'], .product-details-content");
            return desc?.textContent?.trim() || null;
        },
        materials: () => {
            const details = document.querySelector("[class*='product-details'], .product-details-content");
            if (!details) return null;
            const content = details.textContent;
            // Look for material-related lines
            const lines = content.split("\n").filter((line) => {
                const l = line.toLowerCase();
                return l.includes("material") || l.includes("fabric") || l.includes("cotton") || l.includes("polyester");
            });
            return lines.join("\n") || null;
        },
    },

    // ──────────────────────────────────────────
    // Fallback: Generic extractor for any site
    // ──────────────────────────────────────────
    _fallback: {
        name: () =>
            document.querySelector("h1")?.textContent?.trim() ||
            document.title?.split("|")[0]?.split("-")[0]?.trim() ||
            null,
        brand: () => {
            const meta = document.querySelector('meta[property="og:site_name"]');
            return meta?.content || null;
        },
        description: () => {
            // Combine multiple possible description sources
            const parts = [];
            const metaDesc = document.querySelector('meta[name="description"]');
            if (metaDesc) parts.push(metaDesc.content);
            const ogDesc = document.querySelector('meta[property="og:description"]');
            if (ogDesc && !parts.includes(ogDesc.content)) parts.push(ogDesc.content);
            // Try to get main content
            const mainContent = document.querySelector("main, article, [role='main']");
            if (mainContent) {
                parts.push(mainContent.textContent.trim().slice(0, 3000));
            }
            return parts.join("\n") || null;
        },
        materials: () => null,
    },
};

// ──────────────────────────────────────────
// Extraction Logic
// ──────────────────────────────────────────
function cleanText(text, maxLength = 1500) {
    if (!text) return "";
    // Remove multiple spaces, newlines, and tabs
    const cleaned = text.replace(/\s+/g, " ").trim();
    if (maxLength && cleaned.length > maxLength) {
        return cleaned.slice(0, maxLength) + "...";
    }
    return cleaned;
}

function getExtractor() {
    const hostname = window.location.hostname.replace("www.", "").replace("www2.", "");
    for (const domain of Object.keys(EXTRACTORS)) {
        if (domain !== "_fallback" && hostname.includes(domain)) {
            console.log(`[EcoScan] Using ${domain} extractor`);
            return EXTRACTORS[domain];
        }
    }
    console.log("[EcoScan] Using fallback extractor");
    return EXTRACTORS._fallback;
}

function extractProductData() {
    const extractor = getExtractor();

    // Extract with individual length caps for specific fields
    const name = cleanText(safeExtract(extractor.name), 200);
    const brand = cleanText(safeExtract(extractor.brand), 100);
    const description = cleanText(safeExtract(extractor.description), 2000);
    const materials = cleanText(safeExtract(extractor.materials), 1000);

    // Combine into one semi-structured block
    const parts = [
        name ? `Product: ${name}` : "",
        brand ? `Brand: ${brand}` : "",
        description ? `Info: ${description}` : "",
        materials ? `Composition: ${materials}` : "",
    ].filter(Boolean);

    // Hard limit on total text sent to LLM to save tokens
    let productText = parts.join("\n").slice(0, 4000);

    console.log(`[EcoScan] Refined payload: ${productText.length} chars`);

    return {
        product_url: window.location.href,
        product_text: productText,
        brand_name: brand,
        has_data: parts.length > 1,
    };
}

function safeExtract(fn) {
    try {
        return fn();
    } catch (e) {
        console.warn("[EcoScan] Extraction error:", e.message);
        return null;
    }
}

// ──────────────────────────────────────────
// Communication with Background Worker
// ──────────────────────────────────────────
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === "EXTRACT_PRODUCT") {
        const data = extractProductData();
        sendResponse(data);
    }
    return true;
});

// Auto-detect product on page load
window.addEventListener("load", () => {
    setTimeout(() => {
        const data = extractProductData();
        if (data.has_data) {
            chrome.runtime.sendMessage({
                action: "PRODUCT_DETECTED",
                data: data,
            });
            console.log("[EcoScan] Product detected, notified background");
        }
    }, 2500);
});
