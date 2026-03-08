# 🌿 EcoScan
### Evidence-Based Sustainability Intelligence & Greenwashing Detection

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Gemini](https://img.shields.io/badge/Gemini_2.5_Flash-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://deepmind.google/technologies/gemini/)
[![WikiRate](https://img.shields.io/badge/WikiRate_Verified-FF6B6B?style=for-the-badge&logo=wikipedia&logoColor=white)](https://wikirate.org/)

**EcoScan** is a premium Chrome extension that turns every shopper into an environmental auditor. Unlike static rating apps, EcoScan uses a **Hybrid Reality** engine: combining real-time AI product analysis with community-verified ESG data from **WikiRate.org**.

---

## 💎 The Unique Value (UVP)
**"We don't just tell you what's good; we warn you when you're being lied to."** 
EcoScan's core innovation is its **Active Deception Defense**. It doesn't just parse data; it deducts points for manipulative marketing, "grounds" AI claims with real-world corporate data, and summarizes everything in simple, "people-first" language.

---

## ✨ Key Features

- **🌐 Hybrid Truth Engine**: Cross-references AI extracted claims against 2M+ verified ESG data points from **WikiRate.org** (e.g., Fashion Transparency Index, GHG Emissions).
- **🛡️ Active Deception Defense**: Automatically detects and penalizes Greenwashing. It flags vague terms like "eco-friendly" while recognizing legitimate "Organic" materials.
- **🗣️ People-First Language**: Replaces complex auditor jargon with easy-to-understand explanations (e.g., *"Everything is made of chemicals, so calling this 'chemical-free' is misleading!"*).
- **🧵 Deep Material Analysis**: High-fidelity scoring for 100+ materials based on lifecycle impact (Econyl, Lyocell, Organic vs. Virgin Cotton).
- **✅ Gold-Standard Verification**: Distinguishes between trusted 3rd-party audits (GOTS, Fair Trade, OEKO-TEX) and brand-internal marketing labels.
- **🌊 Streaming Responses**: Results "unfold" in real-time as the AI processes the page, providing instant feedback without the wait.
- **🔒 Privacy-Focused**: Automatic PII stripping and anonymous hashed user identification to protect your data while you shop.

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
