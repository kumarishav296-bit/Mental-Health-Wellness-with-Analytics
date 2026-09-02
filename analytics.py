"""
analytics.py — Trend analysis, pattern detection, and therapist flag logic.
"""

import pandas as pd
import numpy as np
from typing import Optional
import database as db


# ── Flag thresholds ──────────────────────────────────────────────────────────

CRITICAL_MOOD_THRESHOLD = 3          # mood ≤ 3 for N days
HIGH_STRESS_THRESHOLD = 8            # stress ≥ 8 for N days
CRITICAL_SLEEP_THRESHOLD = 4.0       # sleep < 4 hours
CONSECUTIVE_LOW_MOOD_DAYS = 3        # consecutive low-mood days trigger flag
CONSECUTIVE_HIGH_STRESS_DAYS = 3


# ── Core dataframe builder ────────────────────────────────────────────────────

def entries_to_df(entries: list[dict]) -> pd.DataFrame:
    if not entries:
        return pd.DataFrame()
    df = pd.DataFrame(entries)
    df["entry_date"] = pd.to_datetime(df["entry_date"])
    df = df.sort_values("entry_date").reset_index(drop=True)
    return df


# ── Rolling statistics ────────────────────────────────────────────────────────

def compute_rolling_stats(df: pd.DataFrame, window: int = 7) -> pd.DataFrame:
    """Add 7-day rolling averages for mood, stress, energy, sleep."""
    for col in ["mood", "stress", "energy", "sleep_hours"]:
        if col in df.columns:
            df[f"{col}_rolling"] = (
                df[col].rolling(window=window, min_periods=1).mean().round(2)
            )
    return df


# ── Streak / consecutive pattern detection ───────────────────────────────────

def count_consecutive(series: pd.Series, condition) -> int:
    """Count trailing consecutive True values in a boolean series."""
    bool_series = condition(series)
    streak = 0
    for val in reversed(bool_series.tolist()):
        if val:
            streak += 1
        else:
            break
    return streak


# ── Summary statistics ────────────────────────────────────────────────────────

def compute_summary(entries: list[dict]) -> dict:
    if not entries:
        return {}
    df = entries_to_df(entries)
    summary = {
        "total_entries": len(df),
        "avg_mood": float(round(df["mood"].mean(), 1)),
        "avg_stress": float(round(df["stress"].mean(), 1)),
        "avg_energy": float(round(df["energy"].mean(), 1)),
        "avg_sleep": float(round(df["sleep_hours"].mean(), 1)),
        "min_mood": int(df["mood"].min()),
        "max_mood": int(df["mood"].max()),
        "mood_std": float(round(df["mood"].std(), 2)) if len(df) > 1 else 0.0,
        "high_stress_days": int((df["stress"] >= HIGH_STRESS_THRESHOLD).sum()),
        "low_mood_days": int((df["mood"] <= CRITICAL_MOOD_THRESHOLD).sum()),
    }
    # Trend direction over last 7 vs previous 7
    if len(df) >= 14:
        recent = df.tail(7)["mood"].mean()
        previous = df.iloc[-14:-7]["mood"].mean()
        summary["mood_trend"] = "improving" if recent > previous + 0.5 else (
            "declining" if recent < previous - 0.5 else "stable"
        )
    else:
        summary["mood_trend"] = "insufficient data"
    return summary


# ── Emotion frequency analysis ────────────────────────────────────────────────

def emotion_frequency(entries: list[dict]) -> dict:
    freq: dict = {}
    for e in entries:
        for emotion in e.get("emotions", []):
            freq[emotion] = freq.get(emotion, 0) + 1
    return dict(sorted(freq.items(), key=lambda x: x[1], reverse=True))


# ── Activity correlation ──────────────────────────────────────────────────────

def activity_mood_correlation(entries: list[dict]) -> dict:
    activity_stats: dict = {}
    for e in entries:
        for act in e.get("activities", []):
            if act not in activity_stats:
                activity_stats[act] = []
            activity_stats[act].append(e["mood"])
    result = {
        act: float(round(np.mean(moods), 1))
        for act, moods in activity_stats.items()
        if len(moods) >= 2
    }
    return dict(sorted(result.items(), key=lambda x: x[1], reverse=True))


# ── Automated flag analysis ───────────────────────────────────────────────────

def analyse_and_flag(entry: dict, recent_entries: list[dict]) -> list[dict]:
    """
    Returns a list of flag dicts: {flag_type, severity, description}
    based on the latest entry and recent history.
    """
    flags = []
    df = entries_to_df(recent_entries) if recent_entries else pd.DataFrame()

    # ── Single-entry critical checks ─────────────────────────────────────
    if entry["mood"] <= 2:
        flags.append({
            "flag_type": "critical_mood",
            "severity": "critical",
            "description": (
                f"Mood score of {entry['mood']}/10 recorded — "
                "extremely low mood requires immediate attention."
            ),
        })
    elif entry["mood"] <= CRITICAL_MOOD_THRESHOLD:
        flags.append({
            "flag_type": "low_mood",
            "severity": "high",
            "description": f"Low mood score of {entry['mood']}/10 recorded.",
        })

    if entry["stress"] >= 9:
        flags.append({
            "flag_type": "critical_stress",
            "severity": "critical",
            "description": (
                f"Stress level {entry['stress']}/10 — critically high stress level reported."
            ),
        })
    elif entry["stress"] >= HIGH_STRESS_THRESHOLD:
        flags.append({
            "flag_type": "high_stress",
            "severity": "high",
            "description": f"High stress level of {entry['stress']}/10 recorded.",
        })

    if entry["sleep_hours"] < CRITICAL_SLEEP_THRESHOLD:
        flags.append({
            "flag_type": "sleep_deprivation",
            "severity": "high",
            "description": (
                f"Only {entry['sleep_hours']} hours of sleep reported — "
                "severe sleep deprivation detected."
            ),
        })

    # ── Pattern-based checks (need history) ──────────────────────────────
    if not df.empty and len(df) >= CONSECUTIVE_LOW_MOOD_DAYS:
        low_mood_streak = count_consecutive(df["mood"], lambda s: s <= CRITICAL_MOOD_THRESHOLD)
        if low_mood_streak >= CONSECUTIVE_LOW_MOOD_DAYS:
            flags.append({
                "flag_type": "persistent_low_mood",
                "severity": "critical",
                "description": (
                    f"Low mood persisted for {low_mood_streak} consecutive days. "
                    "Persistent low mood pattern requires therapist review."
                ),
            })

        stress_streak = count_consecutive(df["stress"], lambda s: s >= HIGH_STRESS_THRESHOLD)
        if stress_streak >= CONSECUTIVE_HIGH_STRESS_DAYS:
            flags.append({
                "flag_type": "chronic_stress",
                "severity": "high",
                "description": (
                    f"High stress maintained for {stress_streak} consecutive days. "
                    "Chronic stress pattern detected."
                ),
            })

        # Mood volatility (high standard deviation)
        if len(df) >= 7:
            recent_std = df.tail(7)["mood"].std()
            if recent_std > 2.5:
                flags.append({
                    "flag_type": "mood_instability",
                    "severity": "medium",
                    "description": (
                        f"High mood variability (σ={recent_std:.1f}) over the past 7 days — "
                        "possible emotional dysregulation."
                    ),
                })

        # Sharp mood drop
        if len(df) >= 3:
            prev_avg = df.tail(7).head(-1)["mood"].mean() if len(df) >= 7 else df.iloc[:-1]["mood"].mean()
            current = entry["mood"]
            if prev_avg - current >= 3:
                flags.append({
                    "flag_type": "acute_mood_drop",
                    "severity": "high",
                    "description": (
                        f"Sudden mood drop of {prev_avg - current:.1f} points detected "
                        "compared to recent average."
                    ),
                })

    return flags
