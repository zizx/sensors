
import pandas as pd
import streamlit as st
import numpy as np
from scipy import stats
from PIL import Image


co2_df1 = pd.read_csv("abi-rm3-carbon-dioxide-co_abi-.csv")
hum_df1 = pd.read_csv("abi-rm3-humidity_abi-rm1-humid.csv")
pm10mc_df1 = pd.read_csv("abi-rm3-pm-10-mass-concentrati.csv")
pm25mc_df1 = pd.read_csv("abi-rm3-pm-25-mass-concentrati.csv")
temp_df1 = pd.read_csv("abi-rm3-temperature_abi-rm1-te.csv")
voc_df1 = pd.read_csv("abi-rm3-volatile-organic-compo.csv")

df_list = [co2_df1, hum_df1, pm10mc_df1, pm25mc_df1, temp_df1, voc_df1]


def resetind(dfs):
    """    reset_index for all dfs"""
    for df in dfs:
        df.reset_index(drop=True, inplace=True)


def todate(dfs):
    # Function to convert datetime column to datetime type and make new Date_time col as index
    for i, df in enumerate(dfs):
        dfs[i]["Date_Time"] = pd.to_datetime(dfs[i]['DateTime'])
        dfs[i].drop("DateTime", axis=1, inplace=True)
        dfs[i].set_index("Date_Time", inplace=True)


def removecol(dfs):
    # remove a column if nan values are more than 50% of non Nan values
    for df in dfs:
        for i, col in enumerate(df.columns):
            if df[df.columns[i]].isna().sum() > df[df.columns[i]].notna().sum() * 0.5:
                print("Column '{}' has been dropped because it has too many nans".format(df.columns[i]))
                df.drop(df.columns[i], axis=1, inplace=True)


def drop_na(dfs):
    # drop all other nans
    for df in dfs:
        df.dropna(inplace=True)


resetind(df_list)
todate(df_list)
removecol(df_list)
drop_na(df_list)


co2 = pd.Series(co2_df1.values.ravel('F'))
pm10 = pd.Series(pm10mc_df1.values.ravel('F'))
pm25 = pd.Series(pm25mc_df1.values.ravel('F'))
voc = pd.Series(voc_df1.values.ravel('F'))
temp = pd.Series(temp_df1.values.ravel('F'))
humi = pd.Series(hum_df1.values.ravel('F'))

image = Image.open('Senseware_Logo.jpg')
st.image(image)
st.title('Senseware Data App')
st.write(co2_df1.head())
st.caption('Viewing co2_df1.head()')

with st.form(key='my_form'):
    co2_input = st.number_input(label='Enter CO2 value (ppm)', min_value=float(1), max_value=float(10000))
    pm10_input = st.number_input(label='Enter PM 1.0 concentration value value', min_value=float(1), max_value=float(10000))
    pm25_input = st.number_input(label='Enter PM 2.5 concentration value value', min_value=float(1), max_value=float(10000))
    voc_input = st.number_input(label='Enter VOC value (ppb)', min_value=float(1), max_value=float(10000))
    temp_input = st.number_input(label='Enter temperature value (°F)', min_value=float(-60), max_value=float(160))
    humi_input = st.number_input(label='Enter humidity value (ppm)', min_value=float(0.1), max_value=float(100))
    submit_button = st.form_submit_button(label='Submit')


if submit_button:
    ptile_co2 = stats.percentileofscore(co2, co2_input)
    ptile_pm10 = stats.percentileofscore(pm10, pm10_input)
    ptile_pm25 = stats.percentileofscore(pm25, pm25_input)
    ptile_voc = stats.percentileofscore(voc, voc_input)
    ptile_temp = stats.percentileofscore(temp, temp_input)
    ptile_humi = stats.percentileofscore(humi, humi_input)

    percentage_co2 = round(100 - ptile_co2)
    percentage_pm10 = round(100 - ptile_pm10)
    percentage_pm25 = round(100 - ptile_pm25)
    percentage_voc = round(100 - ptile_voc)
    percentage_temp = round(ptile_temp)
    percentage_humi = round(ptile_humi)

    if percentage_co2 >= 50:
        st.success(f"your CO2 iaq reading of {co2_input} ppm is in the top {percentage_co2}% of buildings!")
    if percentage_co2 < 50:
        st.error(
            f"your CO2 iaq reading of {co2_input} ppm is worse than {np.abs(percentage_co2 - 100)}% of buildings.")
    if percentage_pm10 >= 50:
        st.success(f"your pm10 iaq reading of {pm10_input} is in the top {percentage_pm10}% of buildings!")
    if percentage_pm10 < 50:
        st.error(f"your pm10 iaq reading of {pm10_input} is worse than {np.abs(percentage_pm10 - 100)}% of buildings.")
    if percentage_pm25 >= 50:
        st.success(f"your pm25 iaq reading of {pm25_input} is in the top {percentage_pm25}% of buildings!")
    if percentage_pm25 < 50:
        st.error(f"your pm25 iaq reading of {pm25_input} is worse than {np.abs(percentage_pm25 - 100)}% of buildings.")
    if percentage_voc >= 50:
        st.success(f"your VOC iaq reading of {voc_input} ppb is in the top {percentage_voc}% of buildings!")
    if percentage_voc < 50:
        st.error(
            f"your VOC iaq reading of {voc_input} ppb is worse than {np.abs(percentage_voc - 100)}% of buildings.")
    if percentage_temp >= 50:
        st.success(f"your VOC iaq reading of {temp_input} °F is in the top {percentage_temp}% of buildings!")
    if percentage_temp < 50:
        st.error(
            f"your temperature iaq reading of {temp_input} °F is worse than {np.abs(percentage_temp - 100)}% of buildings.")
    if percentage_humi >= 50:
        st.success(f"your humidity iaq reading of {humi_input} is in the top {percentage_humi}% of buildings!")
    if percentage_humi < 50:
        st.error(f"your humidity iaq reading of {humi_input} is worse than {np.abs(percentage_humi - 100)}% of buildings.")
