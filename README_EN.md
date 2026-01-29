# 📊 IPIT Subscriber Analysis System (AI-Powered)

> **A smart subscriber analysis system that answers natural language questions with real-time visualizations.**

This project is a full-stack web application that analyzes telecommunication service (IPIT) subscription and cancellation data. It leverages **GPT-4o-mini** to translate natural language into SQL parameters, providing interactive dashboards and AI-generated insights.



---

## ✨ Key Features

* **NL2SQL Interface**: Automatically converts everyday language like "Show me new subscribers in Jan 2025" into structured SQL query parameters.
* **Real-time Data Visualization**: Generates interactive line/bar charts using **Chart.js** for monthly/daily trends and categorical comparisons.
* **AI Insight Commentary**: Beyond just numbers, GPT analyzes trends and provides human-readable reports on the data's significance.
* **Dynamic Filtering & Logic**: Handles complex business logic such as Age Bands, Product Price Bands, and Net Growth (New vs. Cancel) automatically.

## 🛠 Tech Stack

### Backend
- **Python 3.9+**
- **FastAPI**: High-performance asynchronous API framework.
- **SQLite**: Lightweight database for managing subscriber records.
- **OpenAI API (GPT-4o-mini)**: For intent parsing and data interpretation.

### Frontend
- **HTML5 / CSS3** (Responsive Modern UI)
- **Vanilla JavaScript**
- **Chart.js**: Interactive data rendering.

---

## 🚀 Getting Started

### 1. Environment Setup
Create a `.env` file in the root directory and add your OpenAI API Key:
```env
OPENAI_API_KEY=your_api_key_here