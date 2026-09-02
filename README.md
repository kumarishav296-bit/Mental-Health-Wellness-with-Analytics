# 🧘 Mental Health Mood & Wellness Journal with Analytics

An **AI-powered mental wellness journaling app** built with **Streamlit** and **Google Gemini 2.5 Flash**. Log your daily mood, stress, and reflections — the app visualises trends, detects concerning patterns, and generates AI insights for both users and therapists.

---

## ✨ Features

| Feature | Description |
|---|---|
| 📝 **Daily Journal** | Log mood (1–10), stress, energy, sleep, emotions, activities, and free-text notes |
| 📊 **Analytics Dashboard** | Interactive Plotly charts: trends, sleep patterns, emotion frequency, activity-mood correlation, heatmap calendar |
| 🤖 **AI Wellness Chat** | Conversational Gemini 2.5 Flash assistant with your wellness context baked in |
| 🏥 **Therapist Review Panel** | Automated flagging of critical/high-risk patterns with AI-generated clinical notes |
| 📋 **Journal History** | Searchable, filterable entry browser with AI insights attached |
| 🚨 **Auto-Flagging** | Detects: low mood streaks, chronic stress, sleep deprivation, mood volatility, acute drops |

---

## 🚀 Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set your Gemini API key

Create a `.env` file (copy from `.env.example`):

```bash
cp .env.example .env
```

Edit `.env` and replace `your_gemini_api_key_here` with your actual key from [Google AI Studio](https://aistudio.google.com/app/apikey).

> Alternatively, you can paste the API key directly in the **sidebar** within the app at runtime — no `.env` file needed.

### 3. Run the app

```bash
streamlit run app.py
```

The app opens at **http://localhost:8501**

---

## 🗂️ Project Structure

```
├── app.py            # Main Streamlit app (all 5 pages)
├── database.py       # SQLite persistence layer
├── analytics.py      # Trend analysis, pattern detection, flag logic
├── ai_engine.py      # Gemini 2.5 Flash integration (insights, chat, clinical notes)
├── requirements.txt  # Python dependencies
├── .env.example      # Environment variable template
└── wellness_journal.db  # Auto-created SQLite database (on first run)
```

---

## 📊 Analytics Capabilities

- **7-day rolling averages** for mood, stress, energy, sleep
- **Mood calendar heatmap** (week × day)
- **Sleep vs Mood scatter** with OLS trendline and stress colour coding
- **Emotion frequency** bar chart
- **Activity → Mood impact** showing which activities correlate with better mood
- **Day-of-week patterns** showing your best/worst days
- **Score distribution histograms** for mood, stress, energy

---

## 🚨 Auto-Flag Rules

| Flag | Severity | Trigger |
|---|---|---|
| Critical Mood | 🔴 Critical | Mood ≤ 2 |
| Low Mood | 🟠 High | Mood ≤ 3 |
| Critical Stress | 🔴 Critical | Stress ≥ 9 |
| High Stress | 🟠 High | Stress ≥ 8 |
| Sleep Deprivation | 🟠 High | Sleep < 4h |
| Persistent Low Mood | 🔴 Critical | Mood ≤ 3 for 3+ consecutive days |
| Chronic Stress | 🟠 High | Stress ≥ 8 for 3+ consecutive days |
| Mood Instability | 🟡 Medium | 7-day mood σ > 2.5 |
| Acute Mood Drop | 🟠 High | Mood drops 3+ points vs recent avg |

---

## 🔑 Gemini API Key

1. Go to [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click **"Create API Key"**
4. Paste it in the sidebar or `.env` file

The free tier is sufficient for personal use.

---

## ⚠️ Disclaimer

This app is a **wellness journaling tool** and is **not a medical device or a substitute for professional mental health care**. If you are experiencing a mental health crisis, please contact a licensed professional or call your local emergency services.

- **US Crisis Line:** 988 (call or text)
- **Crisis Text Line:** Text HOME to 741741
