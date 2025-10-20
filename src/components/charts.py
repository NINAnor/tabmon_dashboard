"""
Chart components for the TABMON dashboard.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config.settings import HEATMAP_COLORSCALE, HEATMAP_ROW_HEIGHT, MIN_HEATMAP_HEIGHT


def render_activity_heatmap(matrix_data: pd.DataFrame):
    """Render improved activity heatmap with better styling."""
    if matrix_data.empty:
        st.info("ℹ️ No recording data available for the selected period")
        return

    # Prepare data for visualization
    ytick_labels = _create_y_labels(matrix_data)

    # Reverse for top-down display
    ytick_labels = ytick_labels[::-1]
    z_data = matrix_data.values[::-1]
    x_labels = matrix_data.columns.tolist()

    # Create improved heatmap
    fig = go.Figure(
        data=go.Heatmap(
            z=z_data,
            x=x_labels,
            y=ytick_labels,
            colorscale=HEATMAP_COLORSCALE,
            colorbar=dict(title="📊 Recordings", thickness=15, len=0.8),
            hoverongaps=False,
            hovertemplate=(
                "<b>Device:</b> %{y}<br><b>Recordings:</b> %{z}<extra></extra>"
            ),
        )
    )

    # Calculate dynamic height
    chart_height = max(MIN_HEATMAP_HEIGHT, len(matrix_data) * HEATMAP_ROW_HEIGHT)

    fig.update_layout(
        title=dict(
            text="🎵 Recording Activity by day",
            x=0.5,
            font=dict(size=18, color="#2E86AB"),
        ),
        xaxis=dict(
            title=dict(text="📅 Day", font=dict(size=14)),
            tickangle=45 if len(x_labels) > 10 else 0,
        ),
        yaxis=dict(title=dict(text="🎙️ Device (by Country)", font=dict(size=14))),
        height=chart_height,
        margin=dict(l=200, r=80, t=80, b=100),
        font=dict(size=12),
        plot_bgcolor="white",
        paper_bgcolor="white",
    )

    st.plotly_chart(fig, use_container_width=True)


def render_country_bar_chart(status_df: pd.DataFrame):
    """Render a bar chart showing device counts by country."""
    if status_df.empty or "Country" not in status_df.columns:
        return

    # Aggregate data by country
    country_stats = (
        status_df.groupby("Country")
        .agg({"status": lambda x: [(x == "Online").sum(), (x == "Offline").sum()]})
        .reset_index()
    )

    countries = country_stats["Country"].tolist()
    online_counts = [stats[0] for stats in country_stats["status"]]
    offline_counts = [stats[1] for stats in country_stats["status"]]

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            name="Online",
            x=countries,
            y=online_counts,
            marker_color="#11998e",
            hovertemplate="<b>%{x}</b><br>Online: %{y}<extra></extra>",
        )
    )

    fig.add_trace(
        go.Bar(
            name="Offline",
            x=countries,
            y=offline_counts,
            marker_color="#ff6b6b",
            hovertemplate="<b>%{x}</b><br>Offline: %{y}<extra></extra>",
        )
    )

    fig.update_layout(
        title=dict(
            text="🌍 Device Status by Country",
            x=0.5,
            font=dict(size=16, color="#2E86AB"),
        ),
        xaxis_title="Country",
        yaxis_title="Number of Devices",
        barmode="stack",
        height=400,
        margin=dict(t=80, b=80, l=60, r=60),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    st.plotly_chart(fig, use_container_width=True)


def _create_y_labels(matrix_data: pd.DataFrame) -> list:
    """Create y-axis labels with country grouping."""
    ytick_labels = []
    prev_country = None

    for country, device in matrix_data.index:
        if country != prev_country:
            ytick_labels.append(f"<b>{country}</b> - {device}")
            prev_country = country
        else:
            ytick_labels.append(f"     {device}")

    return ytick_labels
