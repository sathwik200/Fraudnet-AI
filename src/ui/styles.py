"""Cyberpunk Interface Stylesheet and CSS Injection for FRAUDNET AI.
==================================================================
Injects ultra-high-definition futuristic cybersecurity command centre aesthetics,
scanlines, glowing neon accents, monospaced telemetry, and HUD component styling.
"""

import streamlit as st

CYBER_COMMAND_CSS = """
<style>
/* -------------------------------------------------------------------------
   FONTS INGESTION & GLOBAL RESETS
   ------------------------------------------------------------------------- */
@import url('https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@500;600;700&family=JetBrains+Mono:wght@400;500;700&family=Rajdhani:wght@500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Rajdhani', -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    color: #E6F1FF;
}

/* Base App Background: Deep Obsidian Abyss with Fine Cyan Grid Matrix */
.stApp {
    background-color: #05080D;
    background-image: 
        linear-gradient(rgba(0, 245, 255, 0.025) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0, 245, 255, 0.025) 1px, transparent 1px),
        radial-gradient(circle at 50% 0%, rgba(22, 139, 255, 0.08) 0%, transparent 65%);
    background-size: 36px 36px, 36px 36px, 100% 100%;
    background-attachment: fixed;
    color: #E6F1FF;
}

/* Custom Scrollbar */
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}
::-webkit-scrollbar-track {
    background: #05080D;
}
::-webkit-scrollbar-thumb {
    background: #111D2A;
    border: 1px solid rgba(0, 245, 255, 0.3);
    border-radius: 2px;
}
::-webkit-scrollbar-thumb:hover {
    background: #00F5FF;
    box-shadow: 0 0 10px #00F5FF;
}

/* -------------------------------------------------------------------------
   SIDEBAR CYBER OPERATIONS DESK
   ------------------------------------------------------------------------- */
[data-testid="stSidebar"] {
    background-color: #060B12 !important;
    border-right: 1px solid rgba(0, 245, 255, 0.15) !important;
    box-shadow: 4px 0 24px rgba(0, 0, 0, 0.7);
}

[data-testid="stSidebar"] hr {
    border-color: rgba(22, 139, 255, 0.2) !important;
    margin: 14px 0;
}

/* Sidebar Brand Header */
.cyber-sidebar-logo {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 8px 0;
    margin-bottom: 2px;
}

.cyber-sidebar-icon {
    width: 38px;
    height: 38px;
    background: linear-gradient(135deg, rgba(0, 245, 255, 0.2) 0%, rgba(22, 139, 255, 0.4) 100%);
    border: 1px solid #00F5FF;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    box-shadow: 0 0 12px rgba(0, 245, 255, 0.4);
}

.cyber-sidebar-title {
    font-family: 'Chakra Petch', sans-serif;
    font-size: 1.45rem;
    font-weight: 700;
    letter-spacing: 2px;
    color: #FFFFFF;
    text-shadow: 0 0 12px rgba(0, 245, 255, 0.6);
}

.cyber-sidebar-sub {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    letter-spacing: 1.5px;
    color: #00F5FF;
    text-transform: uppercase;
    margin-top: -4px;
    margin-bottom: 18px;
    display: flex;
    align-items: center;
    gap: 6px;
}

/* Radio Navigation Overrides */
[data-testid="stSidebar"] .stRadio > div {
    gap: 4px;
}

[data-testid="stSidebar"] .stRadio label {
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 1.05rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.8px !important;
    color: #8892B0 !important;
    background: transparent;
    padding: 8px 12px !important;
    border-radius: 4px !important;
    border: 1px solid transparent !important;
    transition: all 0.2s ease-in-out !important;
}

[data-testid="stSidebar"] .stRadio label:hover {
    color: #00F5FF !important;
    background: rgba(0, 245, 255, 0.05) !important;
    border-color: rgba(0, 245, 255, 0.2) !important;
    transform: translateX(3px);
}

/* Sidebar Telemetry Box */
.cyber-telemetry-box {
    background: #09121D;
    border: 1px solid rgba(0, 245, 255, 0.2);
    border-left: 3px solid #00F5FF;
    padding: 10px 12px;
    border-radius: 4px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    line-height: 1.5;
    color: #8892B0;
    margin: 10px 0;
}

.cyber-telemetry-box strong {
    color: #E6F1FF;
}

.cyber-telemetry-box span.active {
    color: #00FF9C;
    font-weight: 700;
}

/* -------------------------------------------------------------------------
   COMMAND CENTRE TOP HEADER BAR
   ------------------------------------------------------------------------- */
.cyber-top-header {
    background: linear-gradient(90deg, #080F18 0%, #0C1520 60%, #080F18 100%);
    border: 1px solid rgba(0, 245, 255, 0.25);
    border-top: 2px solid #00F5FF;
    border-radius: 6px;
    padding: 12px 20px;
    margin-bottom: 22px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(0, 245, 255, 0.2);
}

.cyber-header-left {
    display: flex;
    flex-direction: column;
}

.cyber-header-badge {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    font-weight: 700;
    color: #00F5FF;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    display: flex;
    align-items: center;
    gap: 8px;
}

.cyber-header-title {
    font-family: 'Chakra Petch', sans-serif;
    font-size: 1.5rem;
    font-weight: 700;
    letter-spacing: 1.5px;
    color: #FFFFFF;
    margin: 2px 0 0 0;
    text-shadow: 0 0 10px rgba(0, 245, 255, 0.4);
}

.cyber-header-right {
    display: flex;
    align-items: center;
    gap: 16px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.76rem;
}

.cyber-status-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 10px;
    border-radius: 3px;
    font-weight: 700;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}

.pill-operational {
    background: rgba(0, 255, 156, 0.12);
    border: 1px solid #00FF9C;
    color: #00FF9C;
    box-shadow: 0 0 8px rgba(0, 255, 156, 0.3);
}

.pill-threat {
    background: rgba(255, 49, 88, 0.15);
    border: 1px solid #FF3158;
    color: #FF3158;
    box-shadow: 0 0 8px rgba(255, 49, 88, 0.4);
}

.pill-amber {
    background: rgba(255, 181, 71, 0.15);
    border: 1px solid #FFB547;
    color: #FFB547;
}

.pill-cyan {
    background: rgba(0, 245, 255, 0.12);
    border: 1px solid #00F5FF;
    color: #00F5FF;
}

/* Pulsing Status Dot Animation */
@keyframes pulseGlow {
    0% { transform: scale(0.95); opacity: 0.8; }
    50% { transform: scale(1.15); opacity: 1; filter: drop-shadow(0 0 6px currentColor); }
    100% { transform: scale(0.95); opacity: 0.8; }
}

.pulse-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
    animation: pulseGlow 1.8s infinite ease-in-out;
}

.dot-green { background-color: #00FF9C; color: #00FF9C; }
.dot-red { background-color: #FF3158; color: #FF3158; }
.dot-cyan { background-color: #00F5FF; color: #00F5FF; }
.dot-amber { background-color: #FFB547; color: #FFB547; }

/* -------------------------------------------------------------------------
   CYBER METRIC CARDS & PANELS
   ------------------------------------------------------------------------- */
.cyber-card {
    background: linear-gradient(145deg, #0C1520 0%, #080F18 100%);
    border: 1px solid rgba(0, 245, 255, 0.2);
    border-radius: 6px;
    padding: 18px 20px;
    margin-bottom: 16px;
    position: relative;
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4);
    transition: all 0.25s ease-in-out;
}

.cyber-card:hover {
    border-color: rgba(0, 245, 255, 0.45);
    box-shadow: 0 8px 24px rgba(0, 245, 255, 0.15);
    transform: translateY(-2px);
}

/* Cyber Card Corner Bracket Accents */
.cyber-card::before {
    content: '';
    position: absolute;
    top: -1px;
    left: -1px;
    width: 10px;
    height: 10px;
    border-top: 2px solid #00F5FF;
    border-left: 2px solid #00F5FF;
}

.cyber-card::after {
    content: '';
    position: absolute;
    bottom: -1px;
    right: -1px;
    width: 10px;
    height: 10px;
    border-bottom: 2px solid #00F5FF;
    border-right: 2px solid #00F5FF;
}

.cyber-metric-card {
    background: linear-gradient(135deg, #0C1520 0%, #111D2A 100%);
    border: 1px solid rgba(22, 139, 255, 0.25);
    border-top: 2px solid #00F5FF;
    border-radius: 5px;
    padding: 16px 18px;
    margin-bottom: 14px;
    position: relative;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5);
    transition: all 0.25s ease;
}

.cyber-metric-card:hover {
    border-top-color: #00FF9C;
    border-color: rgba(0, 245, 255, 0.5);
    box-shadow: 0 6px 20px rgba(0, 245, 255, 0.2);
    transform: translateY(-2px);
}

.cyber-metric-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    color: #8892B0;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;
}

.cyber-metric-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.85rem;
    font-weight: 700;
    color: #FFFFFF;
    letter-spacing: 0.5px;
    text-shadow: 0 0 10px rgba(0, 245, 255, 0.3);
}

.cyber-metric-sub {
    font-family: 'Rajdhani', sans-serif;
    font-size: 0.82rem;
    color: #168BFF;
    font-weight: 600;
    margin-top: 4px;
    letter-spacing: 0.4px;
}

/* -------------------------------------------------------------------------
   HERO COMMAND BANNER
   ------------------------------------------------------------------------- */
.cyber-hero-banner {
    background: linear-gradient(135deg, rgba(12, 21, 32, 0.95) 0%, rgba(8, 15, 24, 0.98) 100%);
    border: 1px solid rgba(0, 245, 255, 0.3);
    border-left: 4px solid #00F5FF;
    border-radius: 6px;
    padding: 24px 28px;
    margin-bottom: 22px;
    position: relative;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6), inset 0 0 24px rgba(0, 245, 255, 0.05);
}

.cyber-hero-title {
    font-family: 'Chakra Petch', sans-serif;
    font-size: 2.1rem;
    font-weight: 700;
    letter-spacing: 2px;
    color: #FFFFFF;
    text-shadow: 0 0 16px rgba(0, 245, 255, 0.5);
    margin: 0;
}

.cyber-hero-sub {
    font-family: 'Rajdhani', sans-serif;
    font-size: 1.15rem;
    font-weight: 600;
    color: #00F5FF;
    letter-spacing: 1px;
    margin-top: 4px;
    margin-bottom: 8px;
}

.cyber-hero-desc {
    font-size: 0.95rem;
    color: #8892B0;
    max-width: 850px;
    line-height: 1.5;
    margin: 0;
}

/* -------------------------------------------------------------------------
   TERMINAL & RISK HUD ELEMENTS
   ------------------------------------------------------------------------- */
.cyber-terminal-box {
    background-color: #060B12;
    border: 1px solid rgba(0, 245, 255, 0.25);
    border-radius: 4px;
    padding: 14px 18px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
    color: #E6F1FF;
    box-shadow: inset 0 0 12px rgba(0, 0, 0, 0.8);
    margin-bottom: 16px;
}

.cyber-terminal-prompt {
    color: #00FF9C;
    font-weight: 700;
    margin-right: 8px;
}

/* Forensic Risk Level Badges */
.badge-threat-critical {
    background: rgba(255, 49, 88, 0.2);
    border: 1px solid #FF3158;
    color: #FF3158;
    padding: 5px 12px;
    border-radius: 3px;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 700;
    font-size: 0.85rem;
    letter-spacing: 1px;
    box-shadow: 0 0 12px rgba(255, 49, 88, 0.4);
    display: inline-block;
}

.badge-threat-high {
    background: rgba(255, 181, 71, 0.2);
    border: 1px solid #FFB547;
    color: #FFB547;
    padding: 5px 12px;
    border-radius: 3px;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 700;
    font-size: 0.85rem;
    letter-spacing: 1px;
    box-shadow: 0 0 10px rgba(255, 181, 71, 0.3);
    display: inline-block;
}

.badge-threat-moderate {
    background: rgba(22, 139, 255, 0.2);
    border: 1px solid #168BFF;
    color: #168BFF;
    padding: 5px 12px;
    border-radius: 3px;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 700;
    font-size: 0.85rem;
    letter-spacing: 1px;
    display: inline-block;
}

.badge-threat-low {
    background: rgba(0, 255, 156, 0.15);
    border: 1px solid #00FF9C;
    color: #00FF9C;
    padding: 5px 12px;
    border-radius: 3px;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 700;
    font-size: 0.85rem;
    letter-spacing: 1px;
    box-shadow: 0 0 8px rgba(0, 255, 156, 0.25);
    display: inline-block;
}

/* -------------------------------------------------------------------------
   STREAMLIT NATIVE COMPONENT OVERRIDES
   ------------------------------------------------------------------------- */
/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #0C1520 0%, #111D2A 100%) !important;
    border: 1px solid #00F5FF !important;
    color: #00F5FF !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 0.95rem !important;
    font-weight: 700 !important;
    letter-spacing: 1px !important;
    text-transform: uppercase !important;
    border-radius: 4px !important;
    padding: 8px 18px !important;
    transition: all 0.25s ease !important;
    box-shadow: 0 0 10px rgba(0, 245, 255, 0.15) !important;
}

.stButton > button:hover {
    background: #00F5FF !important;
    color: #05080D !important;
    box-shadow: 0 0 20px #00F5FF !important;
    transform: translateY(-1px) !important;
}

.stDownloadButton > button {
    background: linear-gradient(135deg, rgba(0, 255, 156, 0.15) 0%, #0C1520 100%) !important;
    border: 1px solid #00FF9C !important;
    color: #00FF9C !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: 1px !important;
}

.stDownloadButton > button:hover {
    background: #00FF9C !important;
    color: #05080D !important;
    box-shadow: 0 0 18px #00FF9C !important;
}

/* Text Inputs */
.stTextInput input, .stTextArea textarea, .stSelectbox [data-baseweb="select"] {
    background-color: #09121D !important;
    border: 1px solid rgba(0, 245, 255, 0.3) !important;
    border-radius: 4px !important;
    color: #FFFFFF !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.9rem !important;
}

.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: #00F5FF !important;
    box-shadow: 0 0 12px rgba(0, 245, 255, 0.4) !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid rgba(0, 245, 255, 0.2) !important;
    gap: 8px !important;
}

.stTabs [data-baseweb="tab"] {
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 1.05rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.8px !important;
    color: #8892B0 !important;
    background: #09121D !important;
    border: 1px solid rgba(22, 139, 255, 0.2) !important;
    border-bottom: none !important;
    border-radius: 4px 4px 0 0 !important;
    padding: 8px 16px !important;
}

.stTabs [aria-selected="true"] {
    color: #00F5FF !important;
    background: #0C1520 !important;
    border-color: #00F5FF !important;
    border-top: 2px solid #00F5FF !important;
    box-shadow: 0 -2px 10px rgba(0, 245, 255, 0.2) !important;
}

/* Dataframe Overrides */
[data-testid="stDataFrame"] {
    border: 1px solid rgba(0, 245, 255, 0.25) !important;
    border-radius: 4px !important;
    background: #080F18 !important;
}

/* Chat Message Styling */
[data-testid="stChatMessage"] {
    background-color: #09121D !important;
    border: 1px solid rgba(22, 139, 255, 0.25) !important;
    border-radius: 6px !important;
    margin-bottom: 10px !important;
}
</style>
"""


def apply_custom_styles():
    """Inject futuristic cyber command centre stylesheet into Streamlit."""
    st.markdown(CYBER_COMMAND_CSS, unsafe_allow_html=True)


def get_risk_badge_html(category: str) -> str:
    """Return futuristic HUD badge for risk tiers."""
    cat_lower = str(category).lower()
    if "critical" in cat_lower:
        return '<span class="badge-threat-critical">⚡ CRITICAL THREAT</span>'
    elif "high" in cat_lower:
        return '<span class="badge-threat-high">⚠️ HIGH RISK</span>'
    elif "moderate" in cat_lower or "medium" in cat_lower:
        return '<span class="badge-threat-moderate">🔷 MODERATE RISK</span>'
    else:
        return '<span class="badge-threat-low">🛡️ LOW RISK (NOMINAL)</span>'


def render_metric_card(title: str, value: str, subtitle: str = ""):
    """Render a high-tech metric tile."""
    html = f"""
    <div class="cyber-metric-card">
        <div class="cyber-metric-label">{title}</div>
        <div class="cyber-metric-value">{value}</div>
        {"<div class='cyber-metric-sub'>" + subtitle + "</div>" if subtitle else ""}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
