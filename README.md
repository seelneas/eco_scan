# 🌿 EcoScan
### AI-Powered Sustainability Intelligence & Greenwashing Detection

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Gemini](https://img.shields.io/badge/Gemini_2.5_Flash-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://deepmind.google/technologies/gemini/)
[![Chrome Extension](https://img.shields.io/badge/Chrome_Extension-4285F4?style=for-the-badge&logo=google-chrome&logoColor=white)](https://chrome.google.com/webstore)

**EcoScan** is a premium Chrome extension that seamlessly embeds sustainability intelligence into your shopping experience. It uses advanced LLM logic to audit product claims, verify certifications, and provide a transparency-driven "EcoScore."

---

## ✨ Key Features

- **🛡️ Active Greenwashing Detection**: Identifies vague marketing buzzwords vs. verifiable evidence.
- **🧵 Deep Material Analysis**: Tiers materials from "High" (sustainable) to "Low" (harmful) based on environmental impact.
- **✅ Certification Verification**: Distinguishes between trusted 3rd-party audits (GOTS, Fair Trade) and brand-internal labels.
- **💎 Glassmorphism UI**: A stunning, modern interface with animated score rings and micro-interactions.
- **🔍 Platform Support**: High-fidelity extraction for Amazon, Walmart, Patagonia, H&M, Zara, Target, and more.
- **🌊 Streaming Responses (Phase 7)**: Real-time analysis updates using Server-Sent Events (SSE) for zero-wait UX.
- **🗄️ Brand Intelligence (Phase 6)**: Persistent brand profiles tracking overall ethical performance across multiple products.
- **🔒 Privacy First**: Strips PII and tracking parameters automatically; uses one-way hashed anonymous identifiers.
- **⏱️ Secure API**: In-memory rate limiting and optional API key validation for production deployments.

---

## 🎨 Design Aesthetic: White Glassmorphism
The extension features a high-fidelity "White Glassmorphism" design system, optimized for clarity and premium feel:
- **Translucency**: 70-85% white opacity with 24px background blur.
- **Live Progress**: Real-time loading steps (Extracting → Analyzing → Scoring) during streaming.
- **Interactive Feedback**: 3-state user feedback system for reporting inaccuracies or model errors.

---

## ⚙️ Project Architecture

```bash
eco_scan/
├── backend/              # FastAPI + Gemini AI Service
│   ├── app/
│   │   ├── api/          # Middlewares, Routes & Rate Limiting
│   │   ├── core/         # Config, Security & Prompt Design
│   │   ├── models/       # Pydantic Schemas & SQLAlchemy DB
│   │   └── services/     # Scoring Engine, Brand Service & LLM Streaming
│   └── requirements.txt
│
└── extension/            # Chrome Extension (V3)
    ├── src/              # background (SSE), contentScript, popup JS
    ├── styles/           # Premium Glassmorphism CSS
    └── manifest.json     # Extension Config with Domain Scoping
```

---

## 🚀 Installation & Setup

### 1. Simple Setup (Shell Script)
```bash
chmod +x setup_ecoscan.sh
./setup_ecoscan.sh
```

### 2. Manual Backend Setup
Requires Python 3.10+ and a Gemini API Key.

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure settings
cp .env.example .env
# Edit .env with your GEMINI_API_KEY

# Start the server
uvicorn app.main:app --reload
```

### 3. Load the Extension
1. Open Chrome and go to `chrome://extensions/`.
2. Turn on **Developer mode**.
3. Click **Load unpacked**.
4. Select the `extension/dist` folder (if built) or `extension/` folder in this repository.

---

## 📊 Scoring Framework

| Weight | Category | Signals |
|---|---|---|
| **35%** | **Materials** | Organic vs conventional, recycled content, bio-based alternatives. |
| **25%** | **Certs** | GOTS, Fair Trade, OEKO-TEX, Bluesign, B-Corp validation. |
| **20%** | **Transparency** | Factory disclosure, country of manufacture, supply chain depth. |
| **20%** | **Ethics** | Living wage, circularity programs, carbon neutrality verification. |

**The GWR Index**: Products with high Greenwashing Risk receive a penalty of up to **40%** deducted from their final score.

---

## 🤝 Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License
MIT License - Copyright (c) 2026 EcoScan Team
