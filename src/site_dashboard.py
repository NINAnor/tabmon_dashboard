# site_dashboard.py
import streamlit as st
import pandas as pd
from urllib.parse import quote
from data_loader import load_site_info
from urllib.parse import unquote

def show_site_dashboard(site_csv, mapping_csv):
    site_info = load_site_info(site_csv)
    pictures_mapping = pd.read_csv(mapping_csv)

    sites = site_info['site'].unique().tolist()
    selected_site = st.sidebar.selectbox("Select Site", sorted(sites))
    
    site_data = site_info[site_info['site'] == selected_site]
    
    st.title(f"Site: {selected_site}")
    
    record = site_data.iloc[0]
    
    st.write("### Site Details")
    st.markdown(f"**Country:** {record.get('country', 'N/A')}")
    st.markdown(f"**Device ID:** {record.get('deviceID', 'N/A')}")
    st.markdown(f"**Coordinates:** Latitude: {record.get('latitude', 'N/A')}, Longitude: {record.get('longitude', 'N/A')}")
    st.markdown(f"**Date:** {record.get('2. Date', 'N/A')}")
    st.markdown(f"**Time (UTC):** {record.get('3. Time (UTC!!! Check here  https://www.utctime.net/)', 'N/A')}")
    st.markdown(f"**Coordinates Uncertainty (meters):** {record.get('6. Coordinates uncertainty (meters)', 'N/A')}")
    st.markdown(f"**GPS Device:** {record.get('7. GPS device (e.g. Garmin 63r, samsung galaxy S24 with google maps)', 'N/A')}")
    st.markdown(f"**Deployment ID:** {record.get('9. DeploymentID: countryCode_deploymentNumber_DeviceID (ex: NO_1_ 7ft35sm)', 'N/A')}")
    st.markdown(f"**Microphone Height (cm):** {record.get('10. Microphone height (in cm)', 'N/A')}")
    st.markdown(f"**Microphone Direction:** {record.get('11. Microphone direction', 'N/A')}")
    st.markdown(f"**Habitat:** {record.get('12. Habitat', 'N/A')}")
    st.markdown(f"**Email:** {record.get('Adresse e-mail', 'N/A')}")
    st.markdown(f"**Comment/Remark:** {record.get('Comment/remark', 'N/A')}")
    st.markdown(f"**Score:** {record.get('Score', 'N/A')}")

    # Filter pictures mapping for images corresponding to this device.
    full_device_id = record.get('deviceID', '')
    short_device_id = full_device_id[-8:]
    device_images = pictures_mapping[pictures_mapping['deviceID'] == short_device_id]
    
    if not device_images.empty:
        st.write("### Device Images")
        for idx, row in device_images.iterrows():
            # Decode the URL once to remove double encoding.
            decoded_url = unquote(row['url'])
            print(decoded_url)
            st.image(decoded_url, caption=f"{row['picture_type']} view", use_container_width=True)
    else:
        st.write("No images found for this device.")
