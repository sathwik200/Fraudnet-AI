"""Cyberpunk Visual Design System & Theming Engine for FRAUDNET AI.
===================================================================
Establishes the futuristic cyber-intelligence command centre color palette,
Plotly visualization themes, typography standards, and HUD styling helpers.
"""

from typing import Any, Dict, Optional
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# CORE CYBER INTELLIGENCE COLOR SYSTEM
# -----------------------------------------------------------------------------
BG_DARK = "#05080D"        # Almost-black abyss background
BG_NAVY = "#080F18"        # Deep cyber navy foundation
BG_PANEL = "#0C1520"       # Secondary operations panel surface
BG_SURFACE = "#111D2A"     # Elevated HUD module surface
BG_ELEVATED = "#172638"    # Active focus / highlighted surface

# Neon Accents
CYAN = "#00F5FF"           # Primary cyber intelligence neon
BLUE = "#168BFF"           # Deep electric blue data flow
GREEN = "#00FF9C"          # Verified licit / system nominal green
RED = "#FF3158"            # Threat illicit / critical risk laser red
AMBER = "#FFB547"          # High warning / caution gold
PURPLE = "#A970FF"         # Target transaction / focal anchor purple
MAGENTA = "#FF007F"        # High-voltage alert magenta

# Typography Color Hierarchy
TEXT_BRIGHT = "#FFFFFF"    # Crisp pure white for primary metric numbers
TEXT_PRIMARY = "#E6F1FF"   # High-contrast cyber silver-blue
TEXT_MUTED = "#8892B0"     # Technical descriptor slate
TEXT_DIM = "#495670"       # Subdued grid telemetry and borders

# Subtle Glow Gradients
BORDER_CYAN_GLOW = "rgba(0, 245, 255, 0.35)"
BORDER_BLUE_GLOW = "rgba(22, 139, 255, 0.25)"
BORDER_RED_GLOW = "rgba(255, 49, 88, 0.45)"
BORDER_GREEN_GLOW = "rgba(0, 255, 156, 0.35)"

# -----------------------------------------------------------------------------
# PLOTLY CYBER COMMAND TEMPLATE
# -----------------------------------------------------------------------------
def get_cyber_layout_dict(
    title: str = "",
    height: int = 380,
    show_legend: bool = True,
    margin: Optional[Dict[str, int]] = None,
) -> Dict[str, Any]:
    """Return dictionary of Plotly layout properties matching cyber command center."""
    if margin is None:
        margin = dict(l=45, r=45, t=45 if title else 25, b=40)

    layout = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#080F18",
        font=dict(
            family="'JetBrains Mono', 'Rajdhani', 'SF Mono', monospace",
            color=TEXT_MUTED,
            size=11,
        ),
        title=(
            dict(
                text=f"<span style='color:{CYAN};font-family:Rajdhani;font-weight:700;letter-spacing:1px;'>// {title.upper()}</span>",
                x=0.01,
                y=0.96,
                font=dict(size=14),
            )
            if title
            else None
        ),
        xaxis=dict(
            gridcolor="rgba(22, 139, 255, 0.12)",
            linecolor="rgba(0, 245, 255, 0.25)",
            tickfont=dict(color=TEXT_MUTED, size=10),
            titlefont=dict(color=TEXT_PRIMARY, size=11),
            zerolinecolor="rgba(0, 245, 255, 0.2)",
        ),
        yaxis=dict(
            gridcolor="rgba(22, 139, 255, 0.12)",
            linecolor="rgba(0, 245, 255, 0.25)",
            tickfont=dict(color=TEXT_MUTED, size=10),
            titlefont=dict(color=TEXT_PRIMARY, size=11),
            zerolinecolor="rgba(0, 245, 255, 0.2)",
        ),
        legend=(
            dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1.0,
                font=dict(color=TEXT_PRIMARY, size=11),
                bgcolor="rgba(8, 15, 24, 0.8)",
                bordercolor="rgba(0, 245, 255, 0.3)",
                borderwidth=1,
            )
            if show_legend
            else dict(visible=False)
        ),
        margin=margin,
        height=height,
        hoverlabel=dict(
            bgcolor="#0C1520",
            bordercolor=CYAN,
            font=dict(
                family="'JetBrains Mono', monospace",
                color=TEXT_BRIGHT,
                size=11,
            ),
        ),
    )
    return layout


def apply_cyber_theme(fig: go.Figure, title: str = "", height: int = 380, show_legend: bool = True) -> go.Figure:
    """Apply the unified dark futuristic command centre theme to any Plotly figure."""
    fig.update_layout(**get_cyber_layout_dict(title=title, height=height, show_legend=show_legend))
    return fig

