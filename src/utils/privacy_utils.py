"""
Privacy utilities for location data protection.
"""

import math
import random

import pandas as pd


def add_location_jitter(
    latitude: float, longitude: float, radius_meters: float = 500
) -> tuple[float, float]:
    """
    Add random jitter to coordinates within a specified radius.

    Args:
        latitude: Original latitude
        longitude: Original longitude
        radius_meters: Maximum jitter radius in meters

    Returns:
        Tuple of (jittered_lat, jittered_lon)
    """
    if pd.isna(latitude) or pd.isna(longitude):
        return latitude, longitude

    # Convert radius from meters to degrees (approximate)
    # 1 degree latitude ≈ 111,000 meters
    # 1 degree longitude ≈ 111,000 * cos(latitude) meters
    lat_radius_deg = radius_meters / 111000.0
    lon_radius_deg = radius_meters / (111000.0 * math.cos(math.radians(latitude)))

    # Generate random angle and distance
    angle = random.uniform(0, 2 * math.pi)  # nosec B311  # noqa: S311
    distance = (
        random.uniform(0, 1) ** 0.5  # nosec B311  # noqa: S311
    )  # Square root for uniform distribution in circle

    # Calculate offset
    lat_offset = distance * lat_radius_deg * math.cos(angle)
    lon_offset = distance * lon_radius_deg * math.sin(angle)

    # Apply jitter
    jittered_lat = latitude + lat_offset
    jittered_lon = longitude + lon_offset

    return jittered_lat, jittered_lon


def apply_privacy_protection(
    df: pd.DataFrame,
    enable_privacy: bool = True,
    jitter_radius: float = 500,
    seed: int = None,
) -> pd.DataFrame:
    """
    Apply privacy protection to a dataframe with location data.

    Args:
        df: DataFrame with Latitude and Longitude columns
        enable_privacy: Whether to apply privacy protection
        jitter_radius: Jitter radius in meters
        seed: Random seed for reproducible jittering (optional)

    Returns:
        DataFrame with privacy-protected coordinates
    """
    if not enable_privacy or df.empty:
        return df.copy()

    # Set random seed for reproducible results if provided
    if seed is not None:
        random.seed(seed)  # nosec B311

    # Create a copy to avoid modifying original data
    protected_df = df.copy()

    # Apply jittering to each row
    for idx, row in protected_df.iterrows():
        if "Latitude" in row and "Longitude" in row:
            jittered_lat, jittered_lon = add_location_jitter(
                row["Latitude"], row["Longitude"], jitter_radius
            )
            protected_df.at[idx, "Latitude"] = jittered_lat
            protected_df.at[idx, "Longitude"] = jittered_lon

    return protected_df


def get_privacy_notice_text(jitter_radius: float) -> str:
    """
    Generate privacy notice text for display to users.

    Args:
        jitter_radius: Jitter radius in meters

    Returns:
        Formatted privacy notice text
    """
    if jitter_radius < 1000:
        radius_text = f"{int(jitter_radius)}m"
    else:
        radius_text = f"{jitter_radius / 1000:.1f}km"

    return (
        f"🔒 **Privacy Protection Active**: Device locations are randomly offset "
        f"by up to {radius_text} to protect sensitive site information while "
        f"maintaining general geographic accuracy."
    )
