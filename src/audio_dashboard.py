import streamlit as st
import duckdb
import pandas as pd

def get_unique_values_duckdb(parquet_file, column):
    query = f"SELECT DISTINCT {column} FROM read_parquet('{parquet_file}') WHERE {column} IS NOT NULL"
    df = duckdb.query(query).to_df()
    return df[column].tolist()

def get_filtered_audio_data_duckdb(parquet_file, country, device):
    query = f"""
        SELECT *
        FROM read_parquet('{parquet_file}')
        WHERE country = '{country}' AND device = '{device}'
    """
    df = duckdb.query(query).to_df()
    return df

def show_audio_dashboard(parquet_file):
    # Get unique countries
    countries = get_unique_values_duckdb(parquet_file, 'country')
    if not countries:
        st.error("No countries found in the dataset.")
        return

    selected_country = st.sidebar.selectbox("Select Country", sorted(countries))
    
    query_devices = f"""
        SELECT DISTINCT device
        FROM read_parquet('{parquet_file}')
        WHERE country = '{selected_country}' AND device IS NOT NULL
    """
    devices_df = duckdb.query(query_devices).to_df()
    devices = devices_df['device'].tolist()
    if not devices:
        st.error("No devices found for the selected country.")
        return

    selected_device = st.sidebar.selectbox("Select Device", sorted(devices))
    
    df = get_filtered_audio_data_duckdb(parquet_file, selected_country, selected_device)
    
    st.title("Acoustic Devices Dashboard")
    st.write(f"### Files for Device: {selected_device} in Country: {selected_country}")

    total_files = df.shape[0]
    total_size = df['Size'].sum() if 'Size' in df.columns else 0
    st.write(f"**Total Files:** {total_files}")
    st.write(f"**Total Size:** {total_size} bytes")

    if 'ModTime' in df.columns:
        df['ModTime_dt'] = pd.to_datetime(df['ModTime'], errors='coerce')
        last_uploaded = df['ModTime_dt'].max()
        st.write(f"**Last Uploaded File:** {last_uploaded if pd.notnull(last_uploaded) else 'N/A'}")
    else:
        st.write("**Last Uploaded File:** N/A")

    search_term = st.text_input("Search Files", "")
    if search_term:
        df = df[df['file'].str.contains(search_term, case=False, na=False)]
    
    st.dataframe(df[['file', 'Size', 'ModTime', 'Path']])
    
    if not df.empty:
        selected_file = st.selectbox("Select a File to Play", df['Path'].tolist())
        if selected_file:
            file_url = f"http://localhost:8081/{selected_file}"
            st.audio(file_url)
    else:
        st.write("No files found for the selected filters.")

