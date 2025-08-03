import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from io import BytesIO
from PIL import Image
import base64
import os

st.set_page_config(page_title="Dive Log App", layout="wide")
st.title("🌊 Dive Log App")
st.write("Track your scuba diving adventures with images, stats, and dive computer data.")

# --- Initialize session state ---
if "divelog" not in st.session_state:
    st.session_state.divelog = pd.DataFrame(
        columns=["Date", "Location", "Latitude", "Longitude", "Depth (m)", "Duration (min)",
                 "Buddy", "Notes", "Equipment", "Tank Type", "Image"]
    )

# --- Dive Log Entry Form ---
st.sidebar.header("📝 Log a New Dive")
with st.sidebar.form("dive_form"):
    date = st.date_input("Dive Date", value=datetime.today())
    location = st.text_input("Location")
    lat = st.number_input("Latitude", format="%.6f")
    lon = st.number_input("Longitude", format="%.6f")
    depth = st.number_input("Max Depth (m)", min_value=0.0, format="%.1f")
    duration = st.number_input("Duration (min)", min_value=0)
    buddy = st.text_input("Dive Buddy")
    notes = st.text_area("Notes")
    equipment = st.text_input("Equipment Used")
    tank = st.selectbox("Tank Type", ["Air", "Nitrox", "Trimix", "Other"])
    image_file = st.file_uploader("Upload Dive Site Image", type=["jpg", "jpeg", "png"])
    submit = st.form_submit_button("Add Dive")

    if submit:
        img_data = ""
        if image_file:
            img_bytes = image_file.read()
            img_data = base64.b64encode(img_bytes).decode("utf-8")

        new_entry = {
            "Date": date,
            "Location": location,
            "Latitude": lat,
            "Longitude": lon,
            "Depth (m)": depth,
            "Duration (min)": duration,
            "Buddy": buddy,
            "Notes": notes,
            "Equipment": equipment,
            "Tank Type": tank,
            "Image": img_data
        }
        st.session_state.divelog = st.session_state.divelog.append(new_entry, ignore_index=True)
        st.sidebar.success("Dive logged!")

# --- Show Dive Logs ---
df = st.session_state.divelog
if df.empty:
    st.info("No dives logged yet.")
    st.stop()

st.subheader("📖 Logged Dives")
st.dataframe(df.drop(columns=["Image"]))

# --- Profile Summary ---
st.subheader("📈 Profile Summary")
total_dives = len(df)
total_duration = df["Duration (min)"].sum()
avg_depth = df["Depth (m)"].mean()
deepest = df["Depth (m)"].max()
fav_location = df["Location"].mode().iloc[0] if not df["Location"].mode().empty else "-"

st.markdown(f"- **Total Dives:** {total_dives}")
st.markdown(f"- **Total Time:** {total_duration} min")
st.markdown(f"- **Average Depth:** {avg_depth:.1f} m")
st.markdown(f"- **Deepest Dive:** {deepest:.1f} m")
st.markdown(f"- **Favorite Location:** {fav_location}")

# --- Dive Site Map ---
st.subheader("📍 Dive Site Map")
if "Latitude" in df.columns and "Longitude" in df.columns:
    st.map(df.rename(columns={"Latitude": "lat", "Longitude": "lon"}))

# --- Dive Site Images ---
st.subheader("🖼 Dive Site Photos")
img_cols = st.columns(4)
for i, row in df.iterrows():
    if row["Image"]:
        try:
            img_bytes = base64.b64decode(row["Image"])
            img = Image.open(BytesIO(img_bytes))
            img_cols[i % 4].image(img, caption=row["Location"], use_column_width=True)
        except:
            pass

# --- Dive Computer Data Upload ---
st.subheader("⌚ Dive Computer Profile Viewer")
uploaded_csv = st.file_uploader("Upload Dive Computer CSV (Time, Depth)", type="csv")
if uploaded_csv:
    dive_data = pd.read_csv(uploaded_csv)
    if "Time" in dive_data.columns and "Depth" in dive_data.columns:
        dive_data = dive_data.sort_values("Time")
        fig = px.line(dive_data, x="Time", y="Depth", title="Dive Profile", markers=True)
        fig.update_yaxes(autorange="reversed")  # Depth increases downward
        st.plotly_chart(fig)
    else:
        st.error("CSV must contain 'Time' and 'Depth' columns")

# --- Download Dive Log ---
st.subheader("📂 Export Dive Log")
st.download_button(
    "Download as CSV",
    data=df.drop(columns=["Image"]).to_csv(index=False),
    file_name="divelog.csv",
    mime="text/csv"
) 
