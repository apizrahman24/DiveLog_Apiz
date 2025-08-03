import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from io import BytesIO
from PIL import Image
import base64
from geopy.geocoders import Nominatim

st.set_page_config(page_title="Dive Log App", layout="wide")
st.title("🌊 Dive Log App")
st.write("Track your scuba diving adventures with images, stats, and dive computer data.")

# --- Initialize session state ---
if "divelog" not in st.session_state:
    st.session_state.divelog = pd.DataFrame(
        columns=["Date", "Location", "Latitude", "Longitude", "Depth (m)", "Duration (min)",
                 "Activity", "Buddy", "Notes", "Equipment", "Tank Type",
                 "Air Before (bar)", "Air After (bar)", "Air Used (bar)", "Image"]
    )

geolocator = Nominatim(user_agent="divelog-app")

# --- Dive Log Entry Form ---
st.sidebar.header("📝 Log a New Dive")
with st.sidebar.form("dive_form"):
    date = st.date_input("Dive Date", value=datetime.today())
    location = st.text_input("Location")

    # Auto-geocoding
    lat, lon = 0.0, 0.0
    if location:
        try:
            geo = geolocator.geocode(location)
            if geo:
                lat, lon = geo.latitude, geo.longitude
                st.sidebar.success(f"📍 Found: {geo.latitude:.4f}, {geo.longitude:.4f}")
            else:
                st.sidebar.warning("No coordinates found.")
        except:
            st.sidebar.error("Failed to connect to geocoding service.")

    lat = st.number_input("Latitude", value=lat, format="%.6f")
    lon = st.number_input("Longitude", value=lon, format="%.6f")

    depth = st.number_input("Max Depth (m)", min_value=0.0, format="%.1f")
    duration = st.number_input("Duration (min)", min_value=0)
    activity = st.selectbox("Dive Activity", ["Fun Dive", "Training", "Check Dive", "Deep Dive", "Night Dive", "Other"])
    buddy = st.text_input("Dive Buddy")
    notes = st.text_area("Notes")
    equipment = st.text_input("Equipment Used")
    tank = st.selectbox("Tank Type", ["Air", "Nitrox", "Trimix", "Other"])

    air_before = st.number_input("Tank Pressure Before Dive (bar)", min_value=0, value=200)
    air_after = st.number_input("Tank Pressure After Dive (bar)", min_value=0, value=50)
    air_used = max(0, air_before - air_after)

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
            "Activity": activity,
            "Buddy": buddy,
            "Notes": notes,
            "Equipment": equipment,
            "Tank Type": tank,
            "Air Before (bar)": air_before,
            "Air After (bar)": air_after,
            "Air Used (bar)": air_used,
            "Image": img_data
        }
        st.session_state.divelog = pd.concat(
            [st.session_state.divelog, pd.DataFrame([new_entry])],
            ignore_index=True
        )
        st.sidebar.success("Dive logged!")

# --- Show Dive Logs ---
df = st.session_state.divelog
if df.empty:
    st.info("No dives logged yet.")
    st.stop()

st.subheader("📖 Logged Dives")
st.dataframe(df.drop(columns=["Image"]))

# --- Profile Summary ---
st.subheader("📊 Profile Summary")
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
