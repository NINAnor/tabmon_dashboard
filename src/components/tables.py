"""
Table components for the TABMON dashboard.
"""

import pandas as pd
import streamlit as st


def render_status_table(status_df: pd.DataFrame):
    """Render improved status table with formatting."""
    if status_df.empty:
        st.info("ℹ️ No device status data available")
        return

    # Prepare display data
    display_cols = [
        "Cluster",
        "Site",
        "DeploymentID",
        "Country",
        "status",
        "last_recorded",
        "days_since_last",
    ]

    # Check which columns exist
    available_cols = [col for col in display_cols if col in status_df.columns]
    table_data = status_df[available_cols].copy()

    # Format dates and handle NaN values
    if "last_recorded" in table_data.columns:
        table_data["last_recorded"] = table_data["last_recorded"].apply(
            lambda x: x.strftime("%Y-%m-%d %H:%M") if pd.notna(x) else "Never"
        )

    if "days_since_last" in table_data.columns:
        table_data["days_since_last"] = table_data["days_since_last"].apply(
            lambda x: f"{x:.1f}" if pd.notna(x) else "N/A"
        )

    # Rename columns for better display
    column_rename = {
        "DeploymentID": "Device ID",
        "last_recorded": "Last Recording",
        "days_since_last": "Days Since Last",
        "status": "Status",
    }

    table_data = table_data.rename(columns=column_rename)

    # Style function for better visual appeal
    def style_status(row):
        if "Status" in row and row["Status"] == "Online":
            return ["background-color: #d4edda; color: #155724"] * len(row)
        elif "Status" in row and row["Status"] == "Offline":
            return ["background-color: #f8d7da; color: #721c24"] * len(row)
        else:
            return [""] * len(row)

    # Display the table
    try:
        styled_df = table_data.style.apply(style_status, axis=1)
        st.dataframe(styled_df, use_container_width=True, height=400)
    except Exception:
        # Fallback to unstyled table if styling fails
        st.dataframe(table_data, use_container_width=True, height=400)


def render_summary_table(status_df: pd.DataFrame):
    """Render a summary table grouped by country or cluster."""
    if status_df.empty:
        return

    # Group by country and calculate summary stats
    if "Country" in status_df.columns:
        summary = (
            status_df.groupby("Country")
            .agg({"status": lambda x: (x == "Online").sum(), "DeploymentID": "count"})
            .reset_index()
        )

        summary.columns = ["Country", "Online Devices", "Total Devices"]
        summary["Offline Devices"] = (
            summary["Total Devices"] - summary["Online Devices"]
        )
        summary["Online Rate %"] = (
            summary["Online Devices"] / summary["Total Devices"] * 100
        ).round(1)

        st.markdown("#### 📊 Summary by Country")
        st.dataframe(summary, use_container_width=True)
