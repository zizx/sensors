import pandas as pd
import streamlit as st
import numpy as np
from scipy import stats
from PIL import Image
import datetime as dt
import time
import random

# Configure the Streamlit page.
st.set_page_config(page_title="Senseware IAQ Analytics", layout="wide")

@st.cache_data
def load_and_process_data():
    """
    Load and preprocess sensor data from CSV files.
    We use melt() so that the measurement variable names are preserved,
    then extract just the measurement values for analysis.
    """
    file_mapping = {
        'co2': "abi-rm3-carbon-dioxide-co_abi-.csv",
        'humidity': "abi-rm3-humidity_abi-rm1-humid.csv",
        'pm10': "abi-rm3-pm-10-mass-concentrati.csv",
        'pm25': "abi-rm3-pm-25-mass-concentrati.csv",
        'temperature': "abi-rm3-temperature_abi-rm1-te.csv",
        'voc': "abi-rm3-volatile-organic-compo.csv"
    }

    processed = {}
    for sensor, path in file_mapping.items():
        try:
            df = pd.read_csv(path)
            if 'DateTime' not in df.columns:
                st.warning(f"DateTime column missing in {sensor} data")
                continue

            # Convert date and set as index.
            df['Date_Time'] = pd.to_datetime(df['DateTime'])
            df = df.drop('DateTime', axis=1).set_index('Date_Time')

            # Keep only columns with less than 50% missing values and drop NaNs.
            threshold = 0.5
            valid_cols = df.columns[df.isna().mean() < threshold]
            df = df[valid_cols].dropna()

            # Use melt() to unpivot the DataFrame (preserving measurement names).
            melted_df = df.reset_index().melt(id_vars='Date_Time', var_name='measurement', value_name='value')
            processed[sensor] = melted_df['value']
        except Exception as e:
            st.error(f"Error processing {sensor}: {str(e)}")
    return processed

def real_time_simulation():
    """
    Simulate real-time sensor data updates.
    Instead of a blocking while-loop, we update the data and then trigger a rerun,
    so that the UI remains responsive (and the Stop button stays visible).
    """
    st.write("## Live Air Quality Monitoring")
    
    # Initialize rt_data with explicit types if it doesn't already exist.
    if 'rt_data' not in st.session_state:
        st.session_state.rt_data = pd.DataFrame({
            'timestamp': pd.Series([], dtype='datetime64[ns]'),
            'co2': pd.Series([], dtype='int'),
            'pm10': pd.Series([], dtype='float'),
            'pm25': pd.Series([], dtype='float')
        })
    
    # Layout two columns for the Start and Stop buttons.
    col1, col2 = st.columns(2)
    if not st.session_state.get("monitoring_active", False):
        if col1.button("Start Live Monitoring", type="primary", key="start_btn"):
            st.session_state.monitoring_active = True
            try:
                st.experimental_rerun()
            except AttributeError:
                st._rerun()
    else:
        if col2.button("Stop Monitoring", key="stop_btn"):
            st.session_state.monitoring_active = False
            try:
                st.experimental_rerun()
            except AttributeError:
                st._rerun()
    
    # If monitoring is active, update the sensor data and show the chart.
    if st.session_state.get("monitoring_active", False):
        new_entry = {
            'timestamp': dt.datetime.now(),
            'co2': random.randint(400, 600),
            'pm10': random.uniform(0, 50),
            'pm25': random.uniform(0, 35)
        }
        st.session_state.rt_data = pd.concat(
            [st.session_state.rt_data, pd.DataFrame([new_entry])],
            ignore_index=True
        )
        
        # Prepare the DataFrame for the chart.
        rt_df = st.session_state.rt_data.copy()
        rt_df['timestamp'] = pd.to_datetime(rt_df['timestamp'])
        rt_df = rt_df.set_index('timestamp')
        rt_df['co2'] = pd.to_numeric(rt_df['co2'], errors='coerce')
        rt_df['pm10'] = pd.to_numeric(rt_df['pm10'], errors='coerce')
        rt_df['pm25'] = pd.to_numeric(rt_df['pm25'], errors='coerce')
        
        # Display the latest sensor metrics.
        cols = st.columns(3)
        latest = rt_df.iloc[-1]
        cols[0].metric("CO₂", f"{latest['co2']} ppm")
        cols[1].metric("PM₁₀", f"{latest['pm10']:.2f} µg/m³")
        cols[2].metric("PM₂.₅", f"{latest['pm25']:.2f} µg/m³")
        
        # Render the live chart by explicitly specifying which columns to plot.
        st.line_chart(rt_df, y=['co2', 'pm10', 'pm25'], height=300)
        
        # Pause briefly then re-run the script to update the UI.
        time.sleep(1)
        try:
            st.experimental_rerun()
        except AttributeError:
            st._rerun()

def display_analysis(sensor_data, user_inputs):
    """
    Compare the user inputs to historical sensor data via percentile ranking.
    Some metrics are reversed (e.g. lower CO₂ is better) so that a higher percentile
    indicates better performance.
    """
    st.write("## Air Quality Benchmarking")
    
    # Each entry: (sensor key, reverse flag)
    metrics = {
        'CO₂ (ppm)': ('co2', False),
        'PM₁₀ (µg/m³)': ('pm10', False),
        'PM₂.₅ (µg/m³)': ('pm25', False),
        'VOC (ppb)': ('voc', False),
        'Temperature (°F)': ('temperature', True),
        'Humidity (%)': ('humidity', True)
    }
    
    for label, (sensor, reverse) in metrics.items():
        data = sensor_data.get(sensor)
        value = user_inputs.get(sensor)
        if data is None or value is None:
            continue
        
        percentile = stats.percentileofscore(data, value)
        score = 100 - percentile if not reverse else percentile
        
        container = st.container()
        container.subheader(label)
        col1, col2 = container.columns([1, 3])
        col1.metric("Your Value", f"{value:.2f}")
        col2.markdown(f"**Percentile Rank:** {score:.1f}%")
        if score >= 50:
            col2.success(f"Better than {score:.1f}% of buildings")
        else:
            col2.error(f"Worse than {100 - score:.1f}% of buildings")

def main():
    # Header: logo and title.
    img = Image.open('Senseware_Logo.jpg')
    st.image(img, width=300)
    st.title("Indoor Air Quality Analytics")
    
    # Load CSV sensor data.
    with st.spinner("Loading sensor data..."):
        sensor_data = load_and_process_data()
    
    # Run the live monitoring simulation.
    real_time_simulation()
    
    # User input form for comparing air quality.
    st.write("## Compare Your Air Quality")
    with st.form("user_inputs"):
        cols = st.columns(2)
        user_inputs = {
            'co2': cols[0].number_input("CO₂ (ppm)", min_value=300, max_value=2000, value=600),
            'pm10': cols[0].number_input("PM₁₀ (µg/m³)", min_value=0.0, max_value=500.0, value=25.0),
            'pm25': cols[0].number_input("PM₂.₅ (µg/m³)", min_value=0.0, max_value=500.0, value=15.0),
            'voc': cols[1].number_input("VOC (ppb)", min_value=0.0, max_value=1000.0, value=50.0),
            'temperature': cols[1].number_input("Temperature (°F)", min_value=-20.0, max_value=120.0, value=72.0),
            'humidity': cols[1].number_input("Humidity (%)", min_value=0.0, max_value=100.0, value=45.0)
        }
        st.form_submit_button("Analyze", type="primary")
    
    # Display analysis if the user provided any inputs.
    if any(user_inputs.values()):
        display_analysis(sensor_data, user_inputs)

if __name__ == "__main__":
    main()
