"""
FRAUDNET AI — UI Theme & Plotly Charts Verification Tests
==========================================================
Verifies that all Plotly figures, cyber layout templates, and representative chart
types (Line, Bar, Donut/Pie, Network Scatter, Heatmap) render and update cleanly
without deprecated properties (e.g., 'titlefont') across Plotly versions.
"""

import unittest
from pathlib import Path
import sys

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from src.ui.theme import (
    CYAN,
    BLUE,
    GREEN,
    RED,
    AMBER,
    PURPLE,
    TEXT_MUTED,
    TEXT_PRIMARY,
    apply_cyber_theme,
    get_cyber_layout_dict,
)


class TestPlotlyCyberTheme(unittest.TestCase):
    """Test suite for cyber theme layout compatibility and Plotly chart rendering."""

    def test_cyber_layout_dict_schema(self):
        """Layout dict must not contain deprecated 'titlefont' properties."""
        layout = get_cyber_layout_dict(title="SURVEILLANCE TELEMETRY", height=380, show_legend=True)
        self.assertIsInstance(layout, dict)

        # Verify x-axis does not have deprecated titlefont
        self.assertIn("xaxis", layout)
        self.assertNotIn("titlefont", layout["xaxis"], "xaxis contains deprecated 'titlefont' key")
        self.assertIn("title", layout["xaxis"])
        self.assertIn("font", layout["xaxis"]["title"])
        self.assertEqual(layout["xaxis"]["title"]["font"]["color"], TEXT_PRIMARY)

        # Verify y-axis does not have deprecated titlefont
        self.assertIn("yaxis", layout)
        self.assertNotIn("titlefont", layout["yaxis"], "yaxis contains deprecated 'titlefont' key")
        self.assertIn("title", layout["yaxis"])
        self.assertIn("font", layout["yaxis"]["title"])
        self.assertEqual(layout["yaxis"]["title"]["font"]["color"], TEXT_PRIMARY)

    def test_line_chart_temporal_surveillance(self):
        """Test dual-axis line chart matching Executive Dashboard temporal surveillance."""
        df_timeline = pd.DataFrame({
            "time_step": list(range(1, 10)),
            "total_transactions": [100, 200, 150, 300, 250, 400, 350, 500, 450],
            "illicit_count": [2, 5, 3, 10, 8, 15, 12, 20, 18],
        })

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=df_timeline["time_step"],
                y=df_timeline["total_transactions"],
                mode="lines",
                name="TOTAL TRANSACTION VOLUME",
                line=dict(color=CYAN, width=2.5),
                fill="tozeroy",
                fillcolor="rgba(0, 245, 255, 0.05)",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=df_timeline["time_step"],
                y=df_timeline["illicit_count"],
                mode="lines+markers",
                name="CONFIRMED ILLICIT SURGE",
                line=dict(color=RED, width=2.5),
                marker=dict(size=5, color=RED, symbol="diamond"),
                yaxis="y2",
            )
        )
        fig.update_layout(
            yaxis2=dict(
                title=dict(text="Illicit Txs (Count)", font=dict(color=RED, size=11)),
                overlaying="y",
                side="right",
                gridcolor="rgba(0,0,0,0)",
                tickfont=dict(color=RED, size=10),
            )
        )

        # Applying cyber theme must succeed without raising ValueError
        updated_fig = apply_cyber_theme(fig, height=360, show_legend=True)
        self.assertIsInstance(updated_fig, go.Figure)
        self.assertEqual(updated_fig.layout.yaxis2.title.text, "Illicit Txs (Count)")

    def test_bar_chart_feature_importance(self):
        """Test horizontal bar chart matching Model Intelligence & Explainability."""
        df_feats = pd.DataFrame({
            "feature": ["in_degree", "out_degree", "local_feature_1", "agg_feature_2"],
            "importance": [0.35, 0.25, 0.20, 0.15],
        })

        fig_bar = px.bar(
            df_feats,
            x="importance",
            y="feature",
            orientation="h",
            color="importance",
            color_continuous_scale=[[0, "#168BFF"], [1, "#00FF9C"]],
            labels={"importance": "Gini Impurity Importance", "feature": "Feature"},
        )
        fig_bar.update_layout(
            yaxis=dict(autorange="reversed"),
            coloraxis_showscale=False,
        )

        updated_bar = apply_cyber_theme(fig_bar, height=330, show_legend=False)
        self.assertIsInstance(updated_bar, go.Figure)
        self.assertFalse(updated_bar.layout.showlegend)

    def test_pie_donut_chart_ground_truth(self):
        """Test donut pie chart matching Executive Dashboard ground truth composition."""
        labels = ["UNKNOWN / UNLABELED", "LICIT (CLASS 2)", "ILLICIT (CLASS 1)"]
        values = [157205, 42019, 4545]
        colors = ["#172638", GREEN, RED]

        fig_pie = go.Figure(
            data=[
                go.Pie(
                    labels=labels,
                    values=values,
                    hole=0.62,
                    marker=dict(colors=colors, line=dict(color="#05080D", width=2)),
                    textinfo="percent",
                    textfont=dict(family="'JetBrains Mono', monospace", size=11, color="#FFFFFF"),
                    hoverinfo="label+value+percent",
                )
            ]
        )
        fig_pie.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5,
                font=dict(family="'JetBrains Mono', monospace", size=9, color="#8892B0"),
            ),
            margin=dict(l=10, r=10, t=10, b=30),
            height=360,
        )
        self.assertIsInstance(fig_pie, go.Figure)
        self.assertEqual(fig_pie.data[0].hole, 0.62)

    def test_network_scatter_topology(self):
        """Test 2D network scatter graph matching Network Topology Visualizer."""
        edge_x = [0, 1, None, 1, 2]
        edge_y = [0, 1, None, 1, 0]
        node_x = [0, 1, 2]
        node_y = [0, 1, 0]

        edge_trace = go.Scatter(
            x=edge_x,
            y=edge_y,
            line=dict(width=1, color="rgba(22, 139, 255, 0.4)"),
            hoverinfo="none",
            mode="lines",
        )
        node_trace = go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers",
            hoverinfo="text",
            text=["Node 0", "Node 1", "Node 2"],
            marker=dict(
                color=[PURPLE, RED, GREEN],
                size=[14, 12, 10],
                symbol=["diamond", "circle", "circle"],
                line=dict(width=1.5, color="#FFFFFF"),
            ),
        )

        fig = go.Figure(
            data=[edge_trace, node_trace],
            layout=go.Layout(
                title=dict(
                    text="<span style='color:#00F5FF;'>// TOPOLOGY GRAPH</span>",
                    x=0.01,
                    y=0.97,
                    font=dict(size=14),
                ),
                showlegend=False,
                hovermode="closest",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="#060B12",
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                margin=dict(b=20, l=20, r=20, t=45),
                height=580,
            ),
        )
        self.assertIsInstance(fig, go.Figure)
        self.assertEqual(len(fig.data), 2)

    def test_heatmap_confusion_matrix(self):
        """Test confusion matrix heatmap matching Model Dashboard."""
        cm = [[41800, 219], [450, 4095]]
        labels_x = ["PRED LICIT", "PRED ILLICIT"]
        labels_y = ["ACTUAL LICIT", "ACTUAL ILLICIT"]

        fig_cm = go.Figure(
            data=go.Heatmap(
                z=cm,
                x=labels_x,
                y=labels_y,
                colorscale=[[0, "#080F18"], [0.5, "#168BFF"], [1, "#00F5FF"]],
                text=[[f"<b>{v:,}</b>" for v in row] for row in cm],
                texttemplate="%{text}",
                textfont=dict(size=15, color="#FFFFFF", family="'JetBrains Mono', monospace"),
                colorbar=dict(
                    title=dict(text="Count", font=dict(color="#8892B0", size=10)),
                    tickfont=dict(color="#8892B0", size=9),
                ),
            )
        )
        updated_cm = apply_cyber_theme(fig_cm, height=330, show_legend=False)
        self.assertIsInstance(updated_cm, go.Figure)


class TestDeploymentModuleImports(unittest.TestCase):
    """Smoke test importing all application and UI modules for deployment readiness."""

    def test_ui_module_imports(self):
        """Ensure all UI dashboard modules import cleanly without runtime syntax or import errors."""
        import src.ui.theme
        import src.ui.styles
        import src.ui.components
        import src.ui.dashboard
        import src.ui.transaction_search
        import src.ui.network_visualization
        import src.ui.model_dashboard
        import src.ui.case_management
        import src.ui.report_viewer
        import src.ui.ai_assistant

        self.assertTrue(hasattr(src.ui.theme, "apply_cyber_theme"))
        self.assertTrue(hasattr(src.ui.dashboard, "render_dashboard_page"))
        self.assertTrue(hasattr(src.ui.transaction_search, "render_transaction_search_page"))
        self.assertTrue(hasattr(src.ui.network_visualization, "render_network_visualization_page"))
        self.assertTrue(hasattr(src.ui.model_dashboard, "render_model_dashboard_page"))
        self.assertTrue(hasattr(src.ui.case_management, "render_case_management_page"))
        self.assertTrue(hasattr(src.ui.report_viewer, "render_report_viewer_page"))
        self.assertTrue(hasattr(src.ui.ai_assistant, "render_ai_assistant_page"))


if __name__ == "__main__":
    unittest.main()
