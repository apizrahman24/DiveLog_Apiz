
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dive Dashboard", layout="wide")
st.title("📊 Dive Dashboard")
st.write("Visualize your diving log data from CSV file.")

uploaded_csv = st.file_uploader("Upload your Dive Log CSV", type="csv")

if uploaded_csv:
    df = pd.read_csv(uploaded_csv)
    st.subheader("📋 Dive Log Data")
    st.dataframe(df)

    # Auto-detect columns
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    datetime_cols = df.select_dtypes(include=['datetime64', 'object']).columns.tolist()

    # Summary
    st.subheader("📈 Summary Stats")
    if "Duration (min)" in df.columns:
        st.metric("Total Duration (min)", int(df["Duration (min)"].sum()))
    if "Depth (m)" in df.columns:
        st.metric("Average Depth (m)", round(df["Depth (m)"].mean(), 1))
        st.metric("Deepest Dive (m)", df["Depth (m)"].max())
    if "Location" in df.columns:
        fav_loc = df["Location"].mode().iloc[0] if not df["Location"].mode().empty else "-"
        st.metric("Favorite Location", fav_loc)
    st.markdown(f"**Total Logged Dives:** {len(df)}")

    # Plotting
    st.subheader("📉 Dive Data Visualization")
    if "Date" in df.columns and "Depth (m)" in df.columns:
        try:
            df["Date"] = pd.to_datetime(df["Date"])
            fig = px.line(df.sort_values("Date"), x="Date", y="Depth (m)", title="Depth Over Time")
            fig.update_yaxes(autorange="reversed")
            st.plotly_chart(fig, use_container_width=True)
        except:
            st.warning("Date format unrecognized for plotting.")

    # Map
    if "Latitude" in df.columns and "Longitude" in df.columns:
        st.subheader("📍 Dive Locations Map")
        st.map(df.rename(columns={"Latitude": "lat", "Longitude": "lon"}))
else:
    st.info("Please upload a dive log CSV file to begin.")
