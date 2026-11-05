"""UI package for FRAUDNET AI."""

from src.ui.styles import apply_custom_styles, get_risk_badge_html, render_metric_card
from src.ui.theme import apply_cyber_theme, CYAN, BLUE, GREEN, RED, AMBER, PURPLE
from src.ui.components import (
    render_command_header,
    render_hero_banner,
    render_cyber_metric,
    render_risk_gauge_hud,
)

__all__ = [
    "apply_custom_styles",
    "get_risk_badge_html",
    "render_metric_card",
    "apply_cyber_theme",
    "CYAN",
    "BLUE",
    "GREEN",
    "RED",
    "AMBER",
    "PURPLE",
    "render_command_header",
    "render_hero_banner",
    "render_cyber_metric",
    "render_risk_gauge_hud",
]
