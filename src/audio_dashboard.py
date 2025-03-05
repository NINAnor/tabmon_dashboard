import streamlit as st
import pandas as pd
from data_loader import load_index_parquet, process_audio_df

def show_audio_dashboard(parquet_file):

    df = load_index_parquet(parquet_file)
    df = process_audio_df(df)

    # Sidebar filtering for country and device
    st.sidebar.header("Filter by Country and Device")
    countries = [c for c in df['country'].unique().tolist() if c is not None]
    selected_country = st.sidebar.selectbox("Select Country", sorted(countries))
    
    filtered_df = df[df['country'] == selected_country]
    devices = filtered_df['device'].unique().tolist()
    selected_device = st.sidebar.selectbox("Select Device", sorted(devices))
    device_files = filtered_df[filtered_df['device'] == selected_device]

    st.title("Acoustic Devices Dashboard")
    st.write(f"### Files for Device: {selected_device} in Country: {selected_country}")

    # Display summary statistics
    total_files = device_files.shape[0]
    total_size = device_files['Size'].sum()
    st.write(f"**Total Files:** {total_files}")
    st.write(f"**Total Size:** {total_size} bytes")

    # Compute the time of the last uploaded file (convert ModTime to datetime)
    device_files['ModTime_dt'] = pd.to_datetime(device_files['ModTime'], errors='coerce')
    last_uploaded = device_files['ModTime_dt'].max()
    if pd.notnull(last_uploaded):
        st.write(f"**Last Uploaded File:** {last_uploaded}")
    else:
        st.write("**Last Uploaded File:** N/A")

    # Search bar for file filtering
    search_term = st.text_input("Search Files", "")
    if search_term:
        device_files = device_files[device_files['file'].str.contains(search_term, case=False)]

    # Display file details in a table
    st.dataframe(device_files[['file', 'Size', 'ModTime', 'Path']])
    
    # Audio player for a selected file
    if not device_files.empty:
        selected_file = st.selectbox("Select a File to Play", device_files['Path'].tolist())
        if selected_file:
            # Adjust the URL as needed for your setup.
            file_url = f"http://localhost:8081/{selected_file}"
            st.audio(file_url)
            # NEED TO SERVE THE DATA FOR IT TO WORK