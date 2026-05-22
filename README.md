# 🛡️ Sentinel AI

## AI-Powered Cybercrime Complaint Management System

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Hackathon Winner](https://img.shields.io/badge/🏆%202nd%20Rank-INDORE%20TECH%20HACKATHON%202025-blue)](.)

> ### 🚀 **"Empowering Citizens. Protecting Communities. Detecting Threats."**
>
> Award-winning AI platform combining citizen reporting with advanced threat detection. **2nd Rank - INDORE TECH HACKATHON 2025** 🏆

</div>

---

## ⭐ Overview

**Sentinel AI** is a comprehensive cybercrime management platform featuring:

- 🎯 AI-powered complaint management & analysis
- 🤖 5 intelligent detection modules (malicious text, call scams, summarization, similarity, biometrics)
- 🔐 Enterprise security (CAPTCHA, typing biometrics, VPN detection)
- 📱 Real-time notifications & tracking
- 🌐 Production-ready with Docker & AWS deployment

---

## 🎯 Core Features

### Citizens

| Feature               | Purpose                                 |
| --------------------- | --------------------------------------- |
| 🚨 Register Complaint | Submit reports with multimedia evidence |
| 🔍 Scam Detector      | Verify suspicious calls & messages      |
| 💬 AI Chatbot         | 24/7 cybercrime guidance                |
| 📱 Track Status       | Real-time complaint updates             |
| 🔔 Nudge System       | Request urgent attention                |

### Administrators

| Feature                | Purpose                               |
| ---------------------- | ------------------------------------- |
| 📊 Analytics Dashboard | Real-time complaint statistics        |
| 🧠 AI Analysis         | Auto-summarization & severity scoring |
| 🔗 Duplicate Detection | Find related complaints               |
| 👀 Security Monitoring | Login anomaly & VPN detection         |
| 🔒 Audit Trail         | Secure deletion with verification     |

---

## 🌐 Project Modules

### 1. **Web Sentinel** - Phishing Detection Chrome Extension

Real-time phishing detection using 16 heuristics and ML classifier.

```
Phishing Detection Chrome Extension/Web-Sentinel/
├── manifest.json
├── popup.html & popup.js
├── content.js (page scanner)
└── MODEL.md (ML details)
```

**Features:** Auto-scan on page load, heuristic-based detection, reputable-root allowlist

### 2. **Sentinel AI Core** - Main Platform

Complete cybercrime complaint system with AI modules.

```
api/                    # FastAPI backend
frontend-react/         # React + TypeScript frontend
summarizer/             # Complaint analysis
call_scam_detector/     # Audio analysis
IAP_AI_Malicious_Detector/  # Text analysis
chatbot/                # RAG-based assistant
TypingIPVPNDetector/    # Security verification
```

---

## 🚀 Quick Start

### Prerequisites

```bash
Python 3.8+  |  Node.js 16+  |  Docker (optional)
```

### Backend Setup

```bash
cd d:\Complete_package\abc
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn api.main:app --reload
```

**API runs on:** http://localhost:8000/docs

### Frontend Setup

```bash
cd frontend-react
npm install
npm run dev
```

**Frontend runs on:** http://localhost:5173

### Chrome Extension Setup

```
1. Open chrome://extensions
2. Enable Developer mode
3. Click "Load unpacked" → Select Phishing Detection Chrome Extension/Web-Sentinel/
```

---

## 🏗️ Architecture

### Backend Stack

- **Framework:** FastAPI (Python)
- **Database:** SQLite
- **Auth:** JWT + CAPTCHA + Biometrics
- **APIs:** Groq LLM, Tavily Search

### Frontend Stack

- **Framework:** React 18 + TypeScript
- **Build:** Vite
- **Styling:** CSS

### AI/ML Capabilities

- **Text Analysis:** Groq LLM for malicious content detection
- **Audio Analysis:** Vosk speech-to-text + scam classification
- **Summarization:** Extractive + abstractive summarization
- **Similarity:** FAISS vector search for duplicate detection
- **Biometrics:** Typing pattern analysis for anomaly detection

---

## 📦 Project Structure

```
.
├── README.md                              # Main documentation
├── LICENSE                                # MIT License
├── CONTRIBUTING.md                        # Guidelines
├── docker-compose.yml                     # Docker setup
├── requirements.txt                       # Python dependencies
│
├── api/                                   # FastAPI Backend
│   ├── main.py                            # Main app
│   ├── database.py                        # Database models
│   ├── similarity.py                      # NLP matching
│   └── uploads/                           # User evidence
│
├── frontend-react/                        # React Frontend
│   ├── src/pages/                         # Page components
│   ├── src/components/                    # Reusable components
│   └── package.json
│
├── Phishing Detection Chrome Extension/   # Chrome Extension
│   └── Web-Sentinel/
│       ├── manifest.json
│       ├── popup.html
│       └── content.js
│
├── call_scam_detector/                    # Audio analysis
├── IAP_AI_Malicious_Detector/             # Text analysis
├── TypingIPVPNDetector/                   # Security module
├── chatbot/                               # AI assistant
├── summarizer/                            # Complaint analysis
│
└── docs/                                  # Archived documentation
```

---

## 🔒 Security Features

- **CAPTCHA Verification** - 6-character alphanumeric
- **Typing Biometrics** - WPM analysis + anomaly detection
- **IP/VPN Detection** - Geolocation + proxy identification
- **Login Monitoring** - Complete audit trail
- **Password Hashing** - bcrypt with salt
- **Data Encryption** - Evidence file protection

---

## 🤖 AI/ML Modules

### Complaint Summarization

- Multi-format support (PDF, images, audio, video)
- Automatic evidence extraction
- Severity classification (1-5 score)

### Malicious Text Detection

- Input: Chat messages, emails, SMS
- Detection: Phishing, social engineering, scareware
- Output: Threat score (0-100)
- **Accuracy: 94%**

### Call Scam Detection

- Audio processing: Vosk (English & Hindi)
- Classification: Safe → Scam
- Processing time: < 5 seconds

### Duplicate Detection

- Technology: Sentence Transformers + FAISS
- Performance: O(1) lookup
- Identifies related fraud patterns

---

## 🐳 Deployment

### Local Docker

```bash
docker-compose up -d --build
```

Access: http://localhost

### AWS EC2 (Free Tier)

```bash
# Launch Ubuntu 22.04 t2.micro instance
ssh -i key.pem ubuntu@YOUR_IP
curl -fsSL https://get.docker.com | sh
docker-compose up -d --build
```

Access: http://YOUR_EC2_IP

---

## 🏆 Awards & Recognition

🥈 **2nd Rank Winner** - INDORE TECH HACKATHON 2025

**Organized by:** INDORE SMART CITY LTD (Government of India)

**Achievement:** Top 5 finalist from multiple entries

---

## 👥 Team

**Team Name:** EENA MEENA DEEKA  
**Organization:** Government of Indore, Madhya Pradesh (MP)

| Name                  | Role      |
| --------------------- | --------- |
| Yogendra Singh        | Developer |
| Sanskriti Jain        | Developer |
| Rishabh Mahesh Khadse | Developer |
| Paawni Gulati         | Developer |

---

## 📜 License

This project is licensed under the **MIT License** - see [LICENSE](LICENSE) file for details.

---

<div align="center">

Made with ❤️ by Sentinel AI Team

**Award-Winning Hackathon Project • 2025**

</div>
