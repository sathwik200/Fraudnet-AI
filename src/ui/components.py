"""Cyberpunk Command Centre UI Components for FRAUDNET AI.
=========================================================
Reusable HUD widgets, telemetry strips, neon metric tiles, risk meters,
and terminal windows styled for high-assurance cybersecurity operations.
"""

from datetime import datetime, timezone
import os
import streamlit as st

from config.settings import GROQ_API_KEY, GROQ_MODEL, get_groq_api_key, get_groq_model
from src.ui.theme import CYAN, BLUE, GREEN, RED, AMBER, PURPLE
from src.ui.styles import get_risk_badge_html


def render_command_header(module_title: str):
    """Render top operational command-centre status bar with live telemetry."""
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    active_key = get_groq_api_key()
    active_model = get_groq_model()
    has_groq = bool(active_key)
    groq_label = f"GROQ//READY [{active_model}]" if has_groq else "DETERMINISTIC//AML-RULES"
    groq_pill_class = "pill-cyan" if has_groq else "pill-amber"

    header_html = f"""
    <div class="cyber-top-header">
        <div class="cyber-header-left">
            <div class="cyber-header-badge">
                <span class="pulse-dot dot-cyan"></span>
                <span>FRAUDNET COMMAND CENTRE // LIVE OPERATIONS</span>
            </div>
            <div class="cyber-header-title">{module_title}</div>
        </div>
        <div class="cyber-header-right">
            <div class="cyber-status-pill pill-operational">
                <span class="pulse-dot dot-green"></span>
                <span>SYSTEM NOMINAL</span>
            </div>
            <div class="cyber-status-pill {groq_pill_class}">
                <span>{groq_label}</span>
            </div>
            <div style="color:#8892B0;">
                <span style="color:#00F5FF;margin-right:4px;">TEL:</span>{now_utc}
            </div>
        </div>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)


def render_hero_banner(title: str, subtitle: str, quote: str = "", telemetry: str = ""):
    """Render futuristic command hero section."""
    telemetry_html = f"<div style='font-family:\"JetBrains Mono\", monospace; font-size:0.75rem; color:#00F5FF; margin-top:8px;'>// TELEMETRY: {telemetry}</div>" if telemetry else ""
    quote_html = f"<div class='cyber-hero-desc'>\"{quote}\"</div>" if quote else ""

    html = f"""
    <div class="cyber-hero-banner">
        <div class="cyber-hero-title">{title}</div>
        <div class="cyber-hero-sub">{subtitle}</div>
        {quote_html}
        {telemetry_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_cyber_metric(
    title: str,
    value: str,
    subtitle: str = "",
    color: str = "cyan",
    icon: str = "",
):
    """Render a high-tech metric tile with distinct neon accent."""
    color_map = {
        "cyan": ("#00F5FF", "rgba(0, 245, 255, 0.25)"),
        "green": ("#00FF9C", "rgba(0, 255, 156, 0.25)"),
        "red": ("#FF3158", "rgba(255, 49, 88, 0.3)"),
        "blue": ("#168BFF", "rgba(22, 139, 255, 0.25)"),
        "amber": ("#FFB547", "rgba(255, 181, 71, 0.25)"),
        "purple": ("#A970FF", "rgba(169, 112, 255, 0.25)"),
    }
    top_color, glow_color = color_map.get(color, ("#00F5FF", "rgba(0, 245, 255, 0.25)"))

    icon_html = f"<span style='color:{top_color};margin-right:6px;'>{icon}</span>" if icon else ""

    html = f"""
    <div class="cyber-metric-card" style="border-top-color:{top_color};">
        <div class="cyber-metric-label">
            <span>{icon_html}{title}</span>
            <span style="color:{top_color};font-size:0.8rem;">●</span>
        </div>
        <div class="cyber-metric-value" style="text-shadow: 0 0 12px {glow_color};">{value}</div>
        {"<div class='cyber-metric-sub' style='color:" + top_color + ";'>" + subtitle + "</div>" if subtitle else ""}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_risk_gauge_hud(probability: float, risk_category: str):
    """Render a futuristic cyber risk assessment gauge with progress bar and badges."""
    prob_pct = probability * 100
    prob_clamped = min(max(float(probability), 0.0), 1.0)

    color_bar = "#00FF9C"
    if "critical" in risk_category.lower():
        color_bar = "#FF3158"
    elif "high" in risk_category.lower():
        color_bar = "#FFB547"
    elif "moderate" in risk_category.lower():
        color_bar = "#168BFF"

    badge_html = get_risk_badge_html(risk_category)

    html = f"""
    <div class="cyber-card" style="border-left: 3px solid {color_bar};">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
            <div>
                <span style="font-family:'JetBrains Mono',monospace; font-size:0.75rem; color:#8892B0; letter-spacing:1px; text-transform:uppercase;">
                    THREAT RISK ASSESSMENT // ML INFERENCE
                </span>
                <div style="font-family:'Chakra Petch',sans-serif; font-size:1.6rem; font-weight:700; color:#FFFFFF;">
                    {prob_pct:.2f}% <span style="font-size:0.9rem; color:#8892B0; font-family:'JetBrains Mono',monospace;">ILLICIT PROBABILITY</span>
                </div>
            </div>
            <div>
                {badge_html}
            </div>
        </div>
        <div style="width:100%; height:10px; background:#05080D; border:1px solid rgba(0,245,255,0.3); border-radius:3px; overflow:hidden;">
            <div style="width:{prob_pct}%; height:100%; background:{color_bar}; box-shadow:0 0 10px {color_bar};"></div>
        </div>
        <div style="display:flex; justify-content:space-between; margin-top:6px; font-family:'JetBrains Mono',monospace; font-size:0.68rem; color:#495670;">
            <span>0.00 (NOMINAL LICIT)</span>
            <span>0.25 (MODERATE)</span>
            <span>0.50 (CALIBRATED THRESHOLD)</span>
            <span>0.85 (CRITICAL THREAT)</span>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_terminal_prompt(command: str, output: str = ""):
    """Render a cyberpunk terminal CLI snippet."""
    output_html = f"<div style='margin-top:6px; color:#8892B0;'>{output}</div>" if output else ""
    html = f"""
    <div class="cyber-terminal-box">
        <div><span class="cyber-terminal-prompt">[FRAUDNET//OPS]$</span>{command}</div>
        {output_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

