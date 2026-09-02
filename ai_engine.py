"""
ai_engine.py — Gemini 3.6 Flash integration for wellness insights and analysis.
Uses the google-genai SDK (v1+).
"""

import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

_client = None


def _get_client():
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not api_key:
            return None
        from google import genai
        _client = genai.Client(api_key=api_key)
    return _client


def is_configured() -> bool:
    return bool(os.getenv("GEMINI_API_KEY", "").strip())


MODEL = "gemini-3.6-flash"


# ── Daily entry insight ────────────────────────────────────────────────────────

def generate_entry_insight(entry: dict, recent_entries: list[dict]) -> str:
    """
    Generate a compassionate, personalized AI insight for a journal entry.
    Returns a plain-text insight string.
    """
    client = _get_client()
    if not client:
        return "⚠️ AI insights unavailable — please configure your Gemini API key in the sidebar."

    emotions_str = ", ".join(entry.get("emotions", [])) or "none specified"
    activities_str = ", ".join(entry.get("activities", [])) or "none specified"

    history_lines = []
    for e in recent_entries[-7:]:
        history_lines.append(
            f"  - {e['entry_date']}: mood={e['mood']}/10, stress={e['stress']}/10, "
            f"sleep={e['sleep_hours']}h"
        )
    history_str = "\n".join(history_lines) or "  (No prior entries)"

    prompt = f"""You are a compassionate mental wellness AI assistant helping someone understand their emotional wellbeing. 
Analyse this journal entry and provide a warm, supportive, and insightful response.

**Today's Entry:**
- Date: {entry['entry_date']}
- Mood: {entry['mood']}/10
- Stress: {entry['stress']}/10
- Energy: {entry['energy']}/10
- Sleep: {entry['sleep_hours']} hours
- Emotions felt: {emotions_str}
- Activities: {activities_str}
- Personal notes: {entry.get('notes', 'None')}

**Recent history (last 7 days):**
{history_str}

Please provide:
1. A brief empathetic acknowledgement of how they're feeling today (2-3 sentences)
2. One key pattern or observation from their recent data (2-3 sentences)
3. One specific, actionable wellness suggestion tailored to their situation (2-3 sentences)
4. A brief encouraging closing (1-2 sentences)

Keep the tone warm, supportive, and non-clinical. Do NOT use bullet points — write in natural flowing paragraphs.
Total length: 150-250 words."""

    try:
        response = client.models.generate_content(model=MODEL, contents=prompt)
        return response.text.strip()
    except Exception as e:
        return f"⚠️ Could not generate insight: {str(e)}"


# ── Weekly / period summary ────────────────────────────────────────────────────

def generate_period_summary(entries: list[dict], period: str = "week") -> str:
    """
    Generate an AI summary/analysis of a set of journal entries.
    period: 'week' | 'month'
    """
    client = _get_client()
    if not client:
        return "⚠️ AI insights unavailable — please configure your Gemini API key."

    if not entries:
        return "No entries available to summarize."

    entry_lines = []
    for e in entries:
        emotions_str = ", ".join(e.get("emotions", [])) or "none"
        entry_lines.append(
            f"- {e['entry_date']}: mood={e['mood']}/10, stress={e['stress']}/10, "
            f"energy={e['energy']}/10, sleep={e['sleep_hours']}h, emotions=[{emotions_str}]"
        )
    entries_str = "\n".join(entry_lines)

    prompt = f"""You are a mental wellness AI analyst. Analyse this {period}'s journal data and provide a comprehensive wellness summary.

**Journal Data:**
{entries_str}

Provide a structured analysis with the following sections:

**Overall Wellbeing Summary** — A 3-4 sentence overview of the person's wellbeing during this period, highlighting the dominant emotional tone.

**Key Patterns & Trends** — 3-4 sentences identifying notable patterns in mood, stress, sleep, or energy. Mention any correlations you observe.

**Positive Highlights** — 2-3 sentences acknowledging what went well or any improvements noticed.

**Areas of Concern** — 2-3 sentences noting any worrying patterns or areas that need attention (if any).

**Recommendations** — 3 specific, actionable suggestions to improve wellbeing in the coming {period}.

**Message to Therapist** — A brief 2-3 sentence clinical note summarizing key concerns that a therapist should be aware of.

Keep the tone professional yet compassionate. Total length: 300-400 words."""

    try:
        response = client.models.generate_content(model=MODEL, contents=prompt)
        return response.text.strip()
    except Exception as e:
        return f"⚠️ Could not generate summary: {str(e)}"


# ── Therapist flag analysis ────────────────────────────────────────────────────

def analyse_flags_for_therapist(flags: list[dict], entries: list[dict]) -> str:
    """
    Generate a clinical summary for a therapist based on flagged concerns.
    """
    client = _get_client()
    if not client:
        return "⚠️ AI insights unavailable — please configure your Gemini API key."

    if not flags:
        return "No active flags to analyse."

    flags_str = "\n".join(
        f"- [{f['severity'].upper()}] {f['flag_type']}: {f['description']} (Date: {f.get('entry_date', 'N/A')})"
        for f in flags
    )

    recent_data = ""
    if entries:
        for e in entries[-10:]:
            recent_data += (
                f"  {e['entry_date']}: mood={e['mood']}/10, stress={e['stress']}/10, "
                f"sleep={e['sleep_hours']}h\n"
            )

    prompt = f"""You are an AI clinical assistant preparing a concise summary for a licensed therapist.
Review the following flagged wellness concerns and recent journal data.

**Flagged Concerns:**
{flags_str}

**Recent Journal Data:**
{recent_data or "  (No recent data available)"}

Provide a structured clinical note for the therapist:

**Clinical Summary** — 3-4 sentences summarising the patient's current mental health status based on the data.

**Primary Concerns** — List the 2-3 most pressing issues that require clinical attention.

**Risk Assessment** — Brief assessment of risk level (Low / Moderate / High) with justification.

**Suggested Clinical Focus** — 2-3 evidence-based therapeutic approaches or interventions to consider.

**Follow-up Priority** — Recommendation on urgency of follow-up (Routine / Soon / Urgent).

Write in a professional clinical tone. Be precise and factual. Total: 200-300 words."""

    try:
        response = client.models.generate_content(model=MODEL, contents=prompt)
        return response.text.strip()
    except Exception as e:
        return f"⚠️ Could not generate therapist analysis: {str(e)}"


# ── Chat with wellness assistant ──────────────────────────────────────────────

def chat_with_assistant(
    user_message: str,
    chat_history: list[dict],
    recent_entries: list[dict],
) -> str:
    """
    Conversational wellness chatbot using Gemini multi-turn chat.
    chat_history: list of {"role": "user"|"assistant", "content": str}
    """
    client = _get_client()
    if not client:
        return "⚠️ AI assistant unavailable — please configure your Gemini API key in the sidebar."

    from google.genai import types

    # Build context from recent entries
    context_lines = []
    for e in recent_entries[-7:]:
        context_lines.append(
            f"  {e['entry_date']}: mood={e['mood']}/10, stress={e['stress']}/10, "
            f"energy={e['energy']}/10, sleep={e['sleep_hours']}h"
        )
    context_str = "\n".join(context_lines) or "  (No recent journal entries)"

    system_instruction = (
        "You are a compassionate mental wellness companion. Your role is to provide supportive, "
        "empathetic conversation and evidence-based wellness guidance. You are NOT a replacement for "
        "professional therapy.\n\n"
        f"The user's recent wellness data:\n{context_str}\n\n"
        "Guidelines:\n"
        "- Be warm, empathetic, and non-judgmental\n"
        "- Offer practical, evidence-based wellness tips\n"
        "- Always encourage professional help for serious concerns\n"
        "- Never diagnose or prescribe\n"
        "- Keep responses concise (100-200 words) unless the user asks for more detail\n"
        "- If the user expresses crisis or self-harm thoughts, immediately provide crisis hotline information"
    )

    # Build conversation history in Gemini format
    contents = []
    for msg in chat_history[-10:]:
        role = "user" if msg["role"] == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part(text=msg["content"])]))
    # Add current user message
    contents.append(types.Content(role="user", parts=[types.Part(text=user_message)]))

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                max_output_tokens=512,
            ),
        )
        return response.text.strip()
    except Exception as e:
        return f"⚠️ Could not send message: {str(e)}"
