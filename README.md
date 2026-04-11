# 🧠 AskSphere- Enterprise AI Knowledge Platform

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![Groq](https://img.shields.io/badge/Groq-LLM-orange.svg)](https://groq.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **Your company's intelligent brain - Ask anything, find experts, track actions, and never forget a meeting decision again.**

![KnowLedger Demo](https://img.shields.io/badge/Demo-Available-brightgreen)



## 🎯 Overview

**KnowLedger** is an enterprise-grade AI knowledge platform that transforms how companies manage and access their internal information. Instead of searching through countless documents, Slack messages, and meeting notes, employees can simply ask natural language questions and get instant, accurate answers.

### The Problem We Solve
- ❌ Employees waste 2+ hours daily searching for information
- ❌ Tribal knowledge leaves when people leave
- ❌ Meeting decisions get forgotten or lost
- ❌ "Who knows about X?" takes 5 different Slack messages
- ❌ New hires take weeks to ramp up

### Our Solution
- ✅ Instant answers from all company data sources
- ✅ Automatic expert identification from documents and Slack
- ✅ Meeting analysis with action item extraction
- ✅ Role-based access control (RBAC)
- ✅ Voice-enabled recording and transcription

---

## ✨ Features

### 🔹 Core RAG Engine
| Feature | Description |
|---------|-------------|
| **Document Q&A** | Ask questions about PDFs, text files, and documents |
| **Semantic Search** | Finds meaning, not just keywords |
| **Source Citations** | Every answer shows which document it came from |
| **Context-Aware** | Understands follow-up questions |

### 🔹 Role-Based Access Control (RBAC)
| Role | Access Level |
|------|-------------|
| 👤 **Employee** | Public policies, benefits, general docs (Sensitivity 1-2) |
| 📊 **Manager** | Team data, salaries, performance (Sensitivity 1-3) |
| 👥 **HR** | All employee data, confidential docs (Sensitivity 1-5) |
| 👑 **Executive** | Complete access to everything |

### 🔹 Expert Finder
- Ask "Who knows about Kubernetes?" 
- Automatically identifies experts from:
  - Document uploads (who contributed what)
  - Slack conversations (who talks about what)
- Expertise scoring and ranking

### 🔹 Slack Integration
- Upload Slack export (JSON)
- Search through conversations
- Find experts from chat history
- Extract decisions from discussions

### 🔹 Meeting Analyzer ("Silent Attendee")
- Upload meeting transcripts
- Auto-extract action items with assignees
- Identify key decisions made
- Detect contradictions with past meetings
- Calculate meeting efficiency score

### 🔹 Live Meeting Recorder
- Real-time microphone recording
- Voice input support (speech-to-text)
- Live transcript generation
- Auto-save to `meetings/` folder
- Download transcripts as TXT/Markdown

### 🔹 Action Tracker
- Track tasks from meetings
- Set deadlines and assignees
- Mark tasks complete
- Overdue task alerts
- Completion rate analytics

### 🔹 Modern UI
- Dark theme with gradient animations
- Glassmorphism design
- Responsive layout
- Typing indicators
- Professional color scheme

---

## 🛠 Tech Stack

### Frontend
| Technology | Purpose |
|------------|---------|
| **Streamlit** | Web interface framework |
| **Custom CSS** | Professional dark theme |
| **HTML/CSS** | Animations and styling |

### AI & ML
| Technology | Purpose |
|------------|---------|
| **Groq Llama 3.3 70B** | LLM for answers and analysis |
| **Sentence Transformers** | Embeddings (all-MiniLM-L6-v2) |
| **Custom RAG** | Retrieval Augmented Generation |
| **SpeechRecognition** | Voice input (Google API) |

### Data Storage
| Technology | Purpose |
|------------|---------|
| **JSON** | Document storage |
| **NumPy** | Vector similarity search |
| **Local files** | Meeting transcripts and recordings |

### Integrations
| Technology | Purpose |
|------------|---------|
| **PyPDF** | PDF text extraction |
| **Groq API** | LLM inference |
| **SpeechRecognition** | Voice-to-text |

---

