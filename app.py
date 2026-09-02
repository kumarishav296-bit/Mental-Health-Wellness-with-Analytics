"""
Mental Health Mood & Wellness Journal with Analytics
AI-powered Streamlit app using Gemini 2.5 Flash
"""

import os
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import date, datetime, timedelta
from dotenv import load_dotenv

import database as db
import analytics as an
import ai_engine as ai

load_dotenv()

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Wellness Journal",
    page_icon="🧘",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Init DB ───────────────────────────────────────────────────────────────────
db.init_db()

# ── Colour palette constants ──────────────────────────────────────────────────
MOOD_COLOURS = {
    "critical": "#ef4444",
    "high": "#f97316",
    "medium": "#eab308",
    "low": "#22c55e",
}

EMOTION_OPTIONS = [
    "😊 Happy", "😢 Sad", "😠 Angry", "😰 Anxious", "😌 Calm",
    "😔 Depressed", "😤 Frustrated", "🥰 Grateful", "😴 Tired",
    "😤 Overwhelmed", "🤩 Excited", "😶 Numb", "😟 Worried",
    "💪 Motivated", "😕 Confused", "🥺 Lonely", "😎 Confident",
]

ACTIVITY_OPTIONS = [
    "🏃 Exercise", "📚 Reading", "🧘 Meditation", "👥 Social time",
    "💼 Work/Study", "🎮 Gaming", "🎨 Creative activity", "🌿 Nature walk",
    "🎵 Music", "🍳 Cooking", "📺 Watching TV", "🛁 Self-care",
    "✍️ Journaling", "📞 Therapy session", "💊 Medication", "🙏 Prayer/Spirituality",
]

SEVERITY_BADGE = {
    "critical": "🔴 Critical",
    "high": "🟠 High",
    "medium": "🟡 Medium",
    "low": "🟢 Low",
}


# ── Session state defaults ────────────────────────────────────────────────────
def init_session():
    defaults = {
        "chat_history": [],
        "api_key_input": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_session()


# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════

def render_sidebar():
    with st.sidebar:
        st.title("🧘 Wellness Journal")
        st.caption("AI-Powered Mental Health Tracker")
        st.divider()

        # Navigation
        page = st.radio(
            "Navigate",
            options=[
                "📝 Daily Journal",
                "📊 Analytics Dashboard",
                "🤖 AI Wellness Chat",
                "🏥 Therapist Review",
                "📋 Journal History",
            ],
            label_visibility="collapsed",
        )

        st.divider()

        # API Key setup
        st.subheader("🔑 Gemini API Key")
        api_key = st.text_input(
            "Enter your Gemini API Key",
            type="password",
            value=os.getenv("GEMINI_API_KEY", ""),
            help="Get your free API key at https://aistudio.google.com",
            placeholder="AIza...",
        )
        if api_key:
            os.environ["GEMINI_API_KEY"] = api_key
            st.success("✅ API key set", icon="✅")
        else:
            st.warning("⚠️ Add API key for AI features")

        st.divider()

        # Quick stats
        recent = db.get_recent_entries(7)
        if recent:
            summary = an.compute_summary(recent)
            st.subheader("📈 This Week")
            c1, c2 = st.columns(2)
            c1.metric("Avg Mood", f"{summary.get('avg_mood', '-')}/10")
            c2.metric("Avg Stress", f"{summary.get('avg_stress', '-')}/10")
            trend = summary.get("mood_trend", "")
            if trend == "improving":
                st.success("📈 Mood is improving")
            elif trend == "declining":
                st.error("📉 Mood is declining")
            elif trend == "stable":
                st.info("➡️ Mood is stable")

        st.divider()

        # Open flags indicator
        open_flags = db.get_open_flags()
        if open_flags:
            critical = sum(1 for f in open_flags if f["severity"] == "critical")
            high = sum(1 for f in open_flags if f["severity"] == "high")
            if critical:
                st.error(f"🚨 {critical} critical flag(s) need attention")
            elif high:
                st.warning(f"⚠️ {high} high-priority flag(s) pending")
            else:
                st.info(f"📌 {len(open_flags)} flag(s) pending review")

        st.caption("v1.0 · Powered by Gemini 2.5 Flash")

    return page


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — DAILY JOURNAL
# ═══════════════════════════════════════════════════════════════════════════════

def page_daily_journal():
    st.title("📝 Daily Journal Entry")
    st.caption("Log your mood, stress, and reflections for today.")

    today_str = date.today().isoformat()
    existing = db.get_entry_by_date(today_str)

    if existing:
        st.info(
            f"✅ You already logged today ({today_str}). "
            "You can add another entry below or review your insight.",
            icon="📅",
        )

    st.divider()

    with st.form("journal_form", clear_on_submit=True):
        col1, col2 = st.columns([1, 1])

        with col1:
            entry_date = st.date_input(
                "📅 Entry Date",
                value=date.today(),
                max_value=date.today(),
            )

            st.subheader("🎭 How are you feeling?")
            mood = st.slider(
                "Mood",
                min_value=1, max_value=10, value=5,
                help="1 = Very low / 10 = Excellent",
            )
            # Colour-coded feedback
            if mood <= 3:
                st.error(f"Mood: {mood}/10 — Feeling rough today 💔")
            elif mood <= 5:
                st.warning(f"Mood: {mood}/10 — Getting through it 💛")
            elif mood <= 7:
                st.info(f"Mood: {mood}/10 — Doing okay 🙂")
            else:
                st.success(f"Mood: {mood}/10 — Feeling great! ✨")

            stress = st.slider(
                "😤 Stress Level",
                min_value=1, max_value=10, value=5,
                help="1 = Very relaxed / 10 = Extremely stressed",
            )
            if stress >= 8:
                st.error(f"Stress: {stress}/10 — High stress detected 🔴")

            energy = st.slider(
                "⚡ Energy Level",
                min_value=1, max_value=10, value=5,
                help="1 = Completely drained / 10 = Full of energy",
            )

        with col2:
            sleep_hours = st.number_input(
                "😴 Sleep Last Night (hours)",
                min_value=0.0, max_value=24.0, value=7.0, step=0.5,
                help="How many hours did you sleep last night?",
            )
            if sleep_hours < 5:
                st.warning("⚠️ Low sleep detected. Sleep health is vital for wellbeing.")

            emotions = st.multiselect(
                "🌈 Emotions Experienced Today",
                options=EMOTION_OPTIONS,
                help="Select all emotions that apply",
            )

            activities = st.multiselect(
                "🏃 Activities Today",
                options=ACTIVITY_OPTIONS,
                help="What did you do today?",
            )

        st.subheader("✍️ Reflections & Notes")
        notes = st.text_area(
            "Write freely about your day, thoughts, or feelings...",
            height=150,
            placeholder="Today I felt... / Something that helped me... / I'm grateful for...",
            label_visibility="collapsed",
        )

        submitted = st.form_submit_button(
            "💾 Save Journal Entry & Get AI Insight",
            use_container_width=True,
            type="primary",
        )

    if submitted:
        entry_dict = {
            "entry_date": entry_date.isoformat(),
            "mood": mood,
            "stress": stress,
            "energy": energy,
            "sleep_hours": sleep_hours,
            "emotions": emotions,
            "notes": notes,
            "activities": activities,
        }

        # Save to DB
        entry_id = db.add_entry(**entry_dict)
        entry_dict["id"] = entry_id

        # Detect and save flags
        recent = db.get_recent_entries(14)
        flags = an.analyse_and_flag(entry_dict, recent)
        for flag in flags:
            db.save_flag(entry_id, flag["flag_type"], flag["severity"], flag["description"])

        st.success("✅ Journal entry saved successfully!", icon="💾")

        # Show any flags immediately
        if flags:
            st.divider()
            st.subheader("⚠️ Wellness Alerts")
            for flag in flags:
                severity = flag["severity"]
                if severity == "critical":
                    st.error(f"🔴 **{flag['flag_type'].replace('_', ' ').title()}**: {flag['description']}")
                elif severity == "high":
                    st.warning(f"🟠 **{flag['flag_type'].replace('_', ' ').title()}**: {flag['description']}")
                else:
                    st.info(f"🟡 **{flag['flag_type'].replace('_', ' ').title()}**: {flag['description']}")

        # AI Insight
        st.divider()
        st.subheader("🤖 AI Wellness Insight")
        if ai.is_configured():
            with st.spinner("Generating your personalised AI insight..."):
                recent_for_ai = [e for e in recent if e.get("entry_date") != entry_date.isoformat()]
                insight = ai.generate_entry_insight(entry_dict, recent_for_ai)
                db.save_ai_insight(entry_id, insight, [f["flag_type"] for f in flags])
            st.info(insight, icon="🤖")
        else:
            st.warning(
                "Add your Gemini API key in the sidebar to receive personalised AI insights.",
                icon="🔑",
            )

        # Crisis resources if critical mood
        if mood <= 2 or any(f["severity"] == "critical" for f in flags):
            st.divider()
            st.error(
                "🆘 **If you are in crisis or having thoughts of self-harm, please reach out immediately:**\n\n"
                "- **National Crisis Hotline (US):** 988 (call or text)\n"
                "- **Crisis Text Line:** Text HOME to 741741\n"
                "- **International Association for Suicide Prevention:** https://www.iasp.info/resources/Crisis_Centres/\n"
                "- **Emergency Services:** 911 (US) / 999 (UK) / 112 (EU)",
                icon="🆘",
            )


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — ANALYTICS DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

def page_analytics():
    st.title("📊 Wellness Analytics Dashboard")
    st.caption("Visual trends and insights from your journal data.")

    # Time range selector
    col_range, col_btn = st.columns([3, 1])
    with col_range:
        days_range = st.select_slider(
            "Time Range",
            options=[7, 14, 30, 60, 90, 180, 365],
            value=30,
            format_func=lambda x: f"Last {x} days",
        )
    with col_btn:
        show_ai = st.button("🤖 AI Period Summary", use_container_width=True)

    entries = db.get_recent_entries(days_range)

    if not entries:
        st.info(
            "📭 No journal entries found for this period. Start logging your daily mood to see analytics!",
            icon="📝",
        )
        return

    df = an.entries_to_df(entries)
    df = an.compute_rolling_stats(df)
    summary = an.compute_summary(entries)

    # ── KPI Row ──────────────────────────────────────────────────────────────
    st.divider()
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("📔 Entries", summary.get("total_entries", 0))
    k2.metric(
        "😊 Avg Mood",
        f"{summary.get('avg_mood', 0)}/10",
        delta=None,
    )
    k3.metric("😤 Avg Stress", f"{summary.get('avg_stress', 0)}/10")
    k4.metric("⚡ Avg Energy", f"{summary.get('avg_energy', 0)}/10")
    k5.metric("😴 Avg Sleep", f"{summary.get('avg_sleep', 0)}h")

    trend = summary.get("mood_trend", "")
    trend_icons = {"improving": "📈 Improving", "declining": "📉 Declining", "stable": "➡️ Stable"}
    if trend in trend_icons:
        st.caption(f"**Mood Trend (recent vs prior week):** {trend_icons[trend]}")

    st.divider()

    # ── AI Period Summary ────────────────────────────────────────────────────
    if show_ai:
        if ai.is_configured():
            with st.spinner("Generating AI period summary..."):
                period = "week" if days_range <= 7 else "month"
                summary_text = ai.generate_period_summary(entries, period)
            with st.expander("🤖 AI Period Analysis", expanded=True):
                st.markdown(summary_text)
        else:
            st.warning("Add your Gemini API key in the sidebar for AI summaries.", icon="🔑")

    # ── Mood, Stress, Energy over time ───────────────────────────────────────
    st.subheader("📈 Mood · Stress · Energy Trends")

    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(
        x=df["entry_date"], y=df["mood"],
        name="Mood", mode="lines+markers",
        line=dict(color="#3b82f6", width=2),
        marker=dict(size=6),
    ))
    fig_trend.add_trace(go.Scatter(
        x=df["entry_date"], y=df["mood_rolling"],
        name="Mood (7-day avg)", mode="lines",
        line=dict(color="#3b82f6", width=1, dash="dash"),
    ))
    fig_trend.add_trace(go.Scatter(
        x=df["entry_date"], y=df["stress"],
        name="Stress", mode="lines+markers",
        line=dict(color="#ef4444", width=2),
        marker=dict(size=6),
    ))
    fig_trend.add_trace(go.Scatter(
        x=df["entry_date"], y=df["stress_rolling"],
        name="Stress (7-day avg)", mode="lines",
        line=dict(color="#ef4444", width=1, dash="dash"),
    ))
    fig_trend.add_trace(go.Scatter(
        x=df["entry_date"], y=df["energy"],
        name="Energy", mode="lines+markers",
        line=dict(color="#22c55e", width=2),
        marker=dict(size=6),
    ))
    # Concern zone shading (mood ≤ 3)
    fig_trend.add_hrect(
        y0=0, y1=3,
        fillcolor="rgba(239,68,68,0.08)",
        line_width=0,
        annotation_text="Concern Zone",
        annotation_position="left",
    )
    fig_trend.update_layout(
        xaxis_title="Date",
        yaxis_title="Score (1–10)",
        yaxis=dict(range=[0, 11]),
        legend=dict(orientation="h", y=-0.2),
        height=380,
        margin=dict(l=0, r=0, t=10, b=0),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    fig_trend.update_xaxes(showgrid=True, gridcolor="rgba(0,0,0,0.06)")
    fig_trend.update_yaxes(showgrid=True, gridcolor="rgba(0,0,0,0.06)")
    st.plotly_chart(fig_trend, use_container_width=True)

    # ── Sleep chart ──────────────────────────────────────────────────────────
    col_sleep, col_scatter = st.columns(2)

    with col_sleep:
        st.subheader("😴 Sleep Patterns")
        fig_sleep = go.Figure()
        bar_colours = [
            "#ef4444" if h < 5 else "#eab308" if h < 7 else "#22c55e"
            for h in df["sleep_hours"]
        ]
        fig_sleep.add_trace(go.Bar(
            x=df["entry_date"], y=df["sleep_hours"],
            name="Sleep Hours",
            marker_color=bar_colours,
        ))
        fig_sleep.add_hline(y=8, line_dash="dot", line_color="#3b82f6",
                            annotation_text="Recommended 8h")
        fig_sleep.add_hline(y=5, line_dash="dot", line_color="#ef4444",
                            annotation_text="Low threshold")
        fig_sleep.update_layout(
            yaxis_title="Hours",
            height=280,
            margin=dict(l=0, r=0, t=10, b=0),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_sleep, use_container_width=True)

    with col_scatter:
        st.subheader("😴 Sleep vs Mood Correlation")
        fig_corr = px.scatter(
            df, x="sleep_hours", y="mood",
            color="stress",
            color_continuous_scale="RdYlGn_r",
            labels={"sleep_hours": "Sleep (hours)", "mood": "Mood Score", "stress": "Stress"},
            trendline="ols",
            size_max=12,
        )
        fig_corr.update_layout(
            height=280,
            margin=dict(l=0, r=0, t=10, b=0),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_corr, use_container_width=True)

    # ── Emotion analysis ─────────────────────────────────────────────────────
    col_emo, col_act = st.columns(2)

    with col_emo:
        st.subheader("🌈 Emotion Frequency")
        emotion_freq = an.emotion_frequency(entries)
        if emotion_freq:
            top_emotions = dict(list(emotion_freq.items())[:12])
            fig_emo = go.Figure(go.Bar(
                x=list(top_emotions.values()),
                y=list(top_emotions.keys()),
                orientation="h",
                marker_color="#7c5cd8",
            ))
            fig_emo.update_layout(
                height=320,
                margin=dict(l=0, r=0, t=10, b=0),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                yaxis=dict(autorange="reversed"),
            )
            st.plotly_chart(fig_emo, use_container_width=True)
        else:
            st.info("No emotion data recorded yet.")

    with col_act:
        st.subheader("🏃 Activity → Mood Impact")
        act_mood = an.activity_mood_correlation(entries)
        if act_mood:
            act_colours = [
                "#22c55e" if v >= 7 else "#eab308" if v >= 5 else "#ef4444"
                for v in act_mood.values()
            ]
            fig_act = go.Figure(go.Bar(
                x=list(act_mood.values()),
                y=list(act_mood.keys()),
                orientation="h",
                marker_color=act_colours,
            ))
            fig_act.add_vline(x=5, line_dash="dot", line_color="grey")
            fig_act.update_layout(
                xaxis=dict(range=[0, 10], title="Avg Mood When Active"),
                height=320,
                margin=dict(l=0, r=0, t=10, b=0),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                yaxis=dict(autorange="reversed"),
            )
            st.plotly_chart(fig_act, use_container_width=True)
        else:
            st.info("Log activities in your journal to see mood correlations.")

    # ── Mood distribution ────────────────────────────────────────────────────
    st.subheader("📊 Score Distribution")
    dist_col1, dist_col2 = st.columns(2)

    with dist_col1:
        fig_hist = go.Figure()
        for metric, colour, name in [
            ("mood", "#3b82f6", "Mood"),
            ("stress", "#ef4444", "Stress"),
            ("energy", "#22c55e", "Energy"),
        ]:
            fig_hist.add_trace(go.Histogram(
                x=df[metric], name=name,
                marker_color=colour, opacity=0.65,
                nbinsx=10, xbins=dict(start=1, end=11, size=1),
            ))
        fig_hist.update_layout(
            barmode="overlay",
            xaxis_title="Score",
            yaxis_title="Count",
            xaxis=dict(range=[0.5, 10.5]),
            height=280,
            margin=dict(l=0, r=0, t=10, b=0),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", y=1.1),
        )
        st.plotly_chart(fig_hist, use_container_width=True)

    with dist_col2:
        # Mood by day of week
        if len(df) >= 7:
            df["day_of_week"] = df["entry_date"].dt.day_name()
            day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            day_mood = df.groupby("day_of_week")["mood"].mean().reindex(day_order).dropna()
            if not day_mood.empty:
                colours_dow = [
                    "#ef4444" if v <= 4 else "#eab308" if v <= 6 else "#22c55e"
                    for v in day_mood.values
                ]
                fig_dow = go.Figure(go.Bar(
                    x=day_mood.index, y=day_mood.values,
                    marker_color=colours_dow,
                ))
                fig_dow.update_layout(
                    title_text="Avg Mood by Day of Week",
                    yaxis=dict(range=[0, 10], title="Avg Mood"),
                    height=280,
                    margin=dict(l=0, r=0, t=40, b=0),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                )
                st.plotly_chart(fig_dow, use_container_width=True)
        else:
            st.info("Log at least 7 entries to see day-of-week patterns.")

    # ── Heatmap calendar ─────────────────────────────────────────────────────
    if len(df) >= 7:
        st.subheader("📅 Mood Calendar")
        df_heat = df[["entry_date", "mood"]].copy()
        df_heat["week"] = df_heat["entry_date"].dt.isocalendar().week.astype(str)
        df_heat["day"] = df_heat["entry_date"].dt.day_name()
        fig_heat = px.density_heatmap(
            df_heat,
            x="week",
            y="day",
            z="mood",
            color_continuous_scale="RdYlGn",
            range_color=[1, 10],
            category_orders={"day": ["Monday", "Tuesday", "Wednesday",
                                      "Thursday", "Friday", "Saturday", "Sunday"]},
            labels={"week": "Week of Year", "day": "Day", "mood": "Mood"},
        )
        fig_heat.update_layout(
            height=280,
            margin=dict(l=0, r=0, t=10, b=0),
        )
        st.plotly_chart(fig_heat, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — AI WELLNESS CHAT
# ═══════════════════════════════════════════════════════════════════════════════

def page_ai_chat():
    st.title("🤖 AI Wellness Companion")
    st.caption(
        "Chat with your AI wellness companion for support, insights, and guidance. "
        "**This is not a substitute for professional mental health care.**"
    )

    if not ai.is_configured():
        st.warning(
            "🔑 Please enter your Gemini API key in the sidebar to use the AI companion.",
            icon="🔑",
        )
        return

    # Context summary
    recent_entries = db.get_recent_entries(7)
    if recent_entries:
        summary = an.compute_summary(recent_entries)
        with st.expander("📊 Your recent wellness context (shared with AI)", expanded=False):
            col1, col2, col3 = st.columns(3)
            col1.metric("Avg Mood (7d)", f"{summary.get('avg_mood', '-')}/10")
            col2.metric("Avg Stress (7d)", f"{summary.get('avg_stress', '-')}/10")
            col3.metric("Avg Sleep (7d)", f"{summary.get('avg_sleep', '-')}h")

    # Chat display
    chat_container = st.container(height=420)
    with chat_container:
        if not st.session_state.chat_history:
            st.chat_message("assistant").markdown(
                "👋 Hello! I'm your AI wellness companion, powered by Gemini 2.5 Flash. "
                "I'm here to support you on your mental wellness journey.\n\n"
                "You can ask me about:\n"
                "- Understanding your mood patterns\n"
                "- Stress management techniques\n"
                "- Sleep improvement tips\n"
                "- Mindfulness and self-care\n"
                "- Interpreting your journal trends\n\n"
                "How are you feeling today? 💙"
            )
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # Input
    user_input = st.chat_input("Type your message here...")

    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.spinner("Thinking..."):
            response = ai.chat_with_assistant(
                user_input,
                st.session_state.chat_history[:-1],
                recent_entries,
            )
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        st.rerun()

    # Quick prompts
    st.divider()
    st.caption("💡 Quick prompts:")
    prompt_cols = st.columns(4)
    quick_prompts = [
        "How can I manage my stress better?",
        "Why is sleep so important for mood?",
        "Give me a quick mindfulness exercise",
        "What do my recent trends say?",
    ]
    for i, prompt in enumerate(quick_prompts):
        if prompt_cols[i].button(prompt, use_container_width=True):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.spinner("Thinking..."):
                response = ai.chat_with_assistant(
                    prompt,
                    st.session_state.chat_history[:-1],
                    recent_entries,
                )
            st.session_state.chat_history.append({"role": "assistant", "content": response})
            st.rerun()

    if st.button("🗑️ Clear Chat History"):
        st.session_state.chat_history = []
        st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — THERAPIST REVIEW
# ═══════════════════════════════════════════════════════════════════════════════

def page_therapist_review():
    st.title("🏥 Therapist Review Panel")
    st.caption(
        "Flagged concerns, patterns, and AI-generated clinical notes for therapist review."
    )

    open_flags = db.get_open_flags()
    all_flags = db.get_all_flags()
    recent_entries = db.get_recent_entries(30)

    # ── Summary row ──────────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    total_open = len(open_flags)
    critical_count = sum(1 for f in open_flags if f["severity"] == "critical")
    high_count = sum(1 for f in open_flags if f["severity"] == "high")
    resolved_count = sum(1 for f in all_flags if f["resolved"] == 1)

    col1.metric("🚨 Open Flags", total_open)
    col2.metric("🔴 Critical", critical_count)
    col3.metric("🟠 High Priority", high_count)
    col4.metric("✅ Resolved", resolved_count)

    st.divider()

    # ── AI Clinical Analysis ─────────────────────────────────────────────────
    if ai.is_configured():
        if st.button("🤖 Generate AI Clinical Summary", use_container_width=True, type="primary"):
            with st.spinner("Generating clinical AI analysis..."):
                clinical_summary = ai.analyse_flags_for_therapist(open_flags, recent_entries)
            with st.expander("🤖 AI Clinical Note", expanded=True):
                st.markdown(clinical_summary)
    else:
        st.info("🔑 Add your Gemini API key for AI-generated clinical notes.")

    st.divider()

    # ── Open Flags ───────────────────────────────────────────────────────────
    st.subheader("⚠️ Open Flags Requiring Review")

    if not open_flags:
        st.success("✅ No open flags at this time. The patient appears to be doing well.", icon="✅")
    else:
        for flag in open_flags:
            severity = flag["severity"]
            badge = SEVERITY_BADGE.get(severity, severity)

            with st.expander(
                f"{badge} — {flag['flag_type'].replace('_', ' ').title()} "
                f"({flag.get('entry_date', 'N/A')})",
                expanded=(severity in ["critical", "high"]),
            ):
                cols = st.columns([3, 1])
                with cols[0]:
                    st.markdown(f"**Description:** {flag['description']}")
                    st.caption(
                        f"Entry: {flag.get('entry_date', 'N/A')} | "
                        f"Mood: {flag.get('mood', '-')}/10 | "
                        f"Stress: {flag.get('stress', '-')}/10 | "
                        f"Flagged: {flag.get('created_at', 'N/A')[:10]}"
                    )
                with cols[1]:
                    if st.button(
                        "✅ Resolve",
                        key=f"resolve_{flag['id']}",
                        use_container_width=True,
                    ):
                        db.resolve_flag(flag["id"])
                        st.success("Flag resolved.")
                        st.rerun()

    # ── Recent wellness overview for therapist ───────────────────────────────
    st.divider()
    st.subheader("📊 Patient Wellness Overview (Last 30 Days)")

    if recent_entries:
        summary = an.compute_summary(recent_entries)
        df = an.entries_to_df(recent_entries)
        df = an.compute_rolling_stats(df)

        # Mood + stress trend for therapist
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df["entry_date"], y=df["mood_rolling"],
            name="Mood (7-day avg)", line=dict(color="#3b82f6", width=2.5),
        ))
        fig.add_trace(go.Scatter(
            x=df["entry_date"], y=df["stress_rolling"],
            name="Stress (7-day avg)", line=dict(color="#ef4444", width=2.5),
        ))
        fig.add_hrect(y0=0, y1=3, fillcolor="rgba(239,68,68,0.1)", line_width=0,
                      annotation_text="Critical Zone")
        fig.update_layout(
            yaxis=dict(range=[0, 11], title="Score (1–10)"),
            xaxis_title="Date",
            height=300,
            margin=dict(l=0, r=0, t=10, b=0),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", y=-0.3),
        )
        st.plotly_chart(fig, use_container_width=True)

        # Stats table
        stats_df = pd.DataFrame([{
            "Metric": "Average Mood",
            "Value": f"{summary.get('avg_mood')}/10",
            "Low Days (≤3)": summary.get("low_mood_days"),
        }, {
            "Metric": "Average Stress",
            "Value": f"{summary.get('avg_stress')}/10",
            "High Days (≥8)": summary.get("high_stress_days"),
        }, {
            "Metric": "Average Sleep",
            "Value": f"{summary.get('avg_sleep')}h",
            "Low Days (<5h)": int(df[df["sleep_hours"] < 5].shape[0]),
        }, {
            "Metric": "Mood Trend",
            "Value": summary.get("mood_trend", "-"),
            "Entries": summary.get("total_entries"),
        }])
        st.dataframe(stats_df, use_container_width=True, hide_index=True)

    else:
        st.info("No journal entries in the last 30 days.")

    # ── Flag history ─────────────────────────────────────────────────────────
    st.divider()
    st.subheader("📋 Complete Flag History")
    if all_flags:
        flag_df = pd.DataFrame(all_flags)
        flag_df = flag_df[[
            "entry_date", "flag_type", "severity", "description", "resolved", "created_at"
        ]].rename(columns={
            "entry_date": "Date",
            "flag_type": "Flag Type",
            "severity": "Severity",
            "description": "Description",
            "resolved": "Resolved",
            "created_at": "Flagged At",
        })
        flag_df["Flag Type"] = flag_df["Flag Type"].str.replace("_", " ").str.title()
        flag_df["Resolved"] = flag_df["Resolved"].map({0: "❌ Open", 1: "✅ Resolved"})
        flag_df["Flagged At"] = flag_df["Flagged At"].str[:10]
        st.dataframe(flag_df, use_container_width=True, hide_index=True)
    else:
        st.info("No flags recorded yet.")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 5 — JOURNAL HISTORY
# ═══════════════════════════════════════════════════════════════════════════════

def page_journal_history():
    st.title("📋 Journal History")
    st.caption("Browse and review all your past journal entries.")

    all_entries = db.get_all_entries(limit=200)

    if not all_entries:
        st.info(
            "📭 No journal entries yet. Head to Daily Journal to start logging!",
            icon="📝",
        )
        return

    # Search and filter
    col_search, col_mood_filter = st.columns([2, 1])
    with col_search:
        search_text = st.text_input("🔍 Search notes", placeholder="Search your journal entries...")
    with col_mood_filter:
        mood_filter = st.select_slider(
            "Filter by min mood",
            options=list(range(1, 11)),
            value=1,
        )

    filtered = [
        e for e in all_entries
        if e["mood"] >= mood_filter
        and (not search_text or search_text.lower() in e.get("notes", "").lower())
    ]

    st.caption(f"Showing {len(filtered)} of {len(all_entries)} entries")
    st.divider()

    if not filtered:
        st.warning("No entries match your filters.")
        return

    for entry in filtered:
        mood = entry["mood"]
        stress = entry["stress"]
        mood_icon = "🔴" if mood <= 3 else "🟡" if mood <= 6 else "🟢"

        with st.expander(
            f"{mood_icon} {entry['entry_date']} — Mood: {mood}/10 · Stress: {stress}/10",
            expanded=False,
        ):
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("😊 Mood", f"{mood}/10")
            col2.metric("😤 Stress", f"{stress}/10")
            col3.metric("⚡ Energy", f"{entry['energy']}/10")
            col4.metric("😴 Sleep", f"{entry['sleep_hours']}h")

            if entry.get("emotions"):
                st.caption(f"**Emotions:** {' · '.join(entry['emotions'])}")
            if entry.get("activities"):
                st.caption(f"**Activities:** {' · '.join(entry['activities'])}")
            if entry.get("notes"):
                st.markdown(f"**Notes:** {entry['notes']}")

            # Show AI insight if available
            insight = db.get_insight_for_entry(entry["id"])
            if insight:
                st.info(f"🤖 **AI Insight:** {insight['insight']}", icon="🤖")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ROUTER
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    page = render_sidebar()

    if page == "📝 Daily Journal":
        page_daily_journal()
    elif page == "📊 Analytics Dashboard":
        page_analytics()
    elif page == "🤖 AI Wellness Chat":
        page_ai_chat()
    elif page == "🏥 Therapist Review":
        page_therapist_review()
    elif page == "📋 Journal History":
        page_journal_history()


if __name__ == "__main__":
    main()
