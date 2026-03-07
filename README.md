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
- **🔍 Platform Support**: High-fidelity extraction for Amazon, Walmart, Patagonia, H&M, Zara, and more.
- **⚡ Smart Caching**: Instant results for previously analyzed products via local storage caching.

---

## 🎨 Design Aesthetic: White Glassmorphism
The extension features a high-fidelity "White Glassmorphism" design system, optimized for clarity and premium feel:
- **Translucent Surfaces**: 70-85% white opacity with 24px background blur.
- **Animated Counters**: Real-time score animation from 0 to final result.
- **Micro-Animations**: Smooth accordion transitions and hover effects.

---

## ⚙️ Project Architecture

```bash
eco_scan/
├── backend/              # FastAPI + Gemini AI Service
│   ├── app/
│   │   ├── api/          # Middlewares & Routes
│   │   ├── core/         # Prompt Engineering & Data Libraries
│   │   ├── models/       # Pydantic Schemas & DB
│   │   └── services/     # Scoring Engine & GWRD Pipeline
│   └── requirements.txt
│
└── extension/            # Chrome Extension (V3)
    ├── src/              # background, contentScript, popup JS
    ├── styles/           # Premium CSS Design System
    └── manifest.json     # Extension Config
```

---

## 🚀 Installation & Setup

### 1. Backend Service
Requires Python 3.10+ and a Gemini API Key.

```bash
# Navigate to backend
cd backend

# Create & activate environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure settings
cp .env.example .env
# Open .env and add your GEMINI_API_KEY

# Start the server
uvicorn app.main:app --reload
```

### 2. Chrome Extension
1. Open Chrome and go to `chrome://extensions/`.
2. Turn on **Developer mode** (top right).
3. Click **Load unpacked**.
4. Select the `extension/` folder in this repository.

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
