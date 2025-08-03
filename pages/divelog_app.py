import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, time
from io import BytesIO
from PIL import Image
import base64
from geopy.geocoders import Nominatim
import tempfile
from fpdf import FPDF

st.set_page_config(page_title="Dive Log App", layout="wide")
st.title("🌊 Dive Log App")
st.write("Track your scuba diving adventures with images, stats, and dive computer data.")

# --- Initialize session state ---
if "divelog" not in st.session_state:
    st.session_state.divelog = pd.DataFrame(
        columns=["Date", "Diver", "Location", "Latitude", "Longitude", "Start Time", "End Time",
                 "Depth (m)", "Duration (min)", "Activity", "Buddy", "Notes", "Equipment", "Tank Type",
                 "Air Before (bar)", "Air After (bar)", "Air Used (bar)", "Image"]
    )

geolocator = Nominatim(user_agent="divelog-app")

# --- Dive Log Entry Form ---
st.sidebar.header("📜 Log a New Dive")
with st.sidebar.form("dive_form"):
    diver_name = st.text_input("Diver Name", placeholder="e.g. Hafiz")
    date = st.date_input("Dive Date", value=datetime.today())
    location = st.text_input("Location")

    # Auto-geocoding
    lat, lon = 0.0, 0.0
    location_valid = False
    location_msg = ""
    if location:
        try:
            geo = geolocator.geocode(location)
            if geo:
                lat, lon = geo.latitude, geo.longitude
                location_valid = True
                location_msg = f"📍 Found: {geo.latitude:.4f}, {geo.longitude:.4f}"
            else:
                location_msg = "⚠️ Location not found. Please double-check."
        except:
            location_msg = "❌ Failed to connect to geocoding service."

    lat = st.number_input("Latitude", value=lat, format="%.6f")
    lon = st.number_input("Longitude", value=lon, format="%.6f")

    if location:
        st.info(location_msg)

    start_time = st.time_input("Dive Start Time", value=time(9, 0))
    end_time = st.time_input("Dive End Time", value=time(9, 45))

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
        if not location_valid:
            st.warning("❗ Please enter a valid location before submitting.")
            st.stop()

        img_data = ""
        if image_file:
            img_bytes = image_file.read()
            img_data = base64.b64encode(img_bytes).decode("utf-8")

        new_entry = {
            "Date": date,
            "Diver": diver_name,
            "Location": location,
            "Latitude": lat,
            "Longitude": lon,
            "Start Time": start_time.strftime("%H:%M"),
            "End Time": end_time.strftime("%H:%M"),
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
        st.success("Dive logged!")

# --- Show Dive Logs ---
df = st.session_state.divelog
if df.empty:
    st.info("No dives logged yet.")
    st.stop()

st.subheader("📖 Logged Dives")
del_col, log_col = st.columns([1, 5])
with del_col:
    delete_index = st.number_input("Index to Delete", min_value=0, max_value=len(df)-1 if len(df) > 0 else 0, step=1)
    if st.button("❌ Delete Dive"):
        st.session_state.divelog = st.session_state.divelog.drop(delete_index).reset_index(drop=True)
        st.success(f"Deleted dive at index {delete_index}")

with log_col:
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

# CSV Export
st.download_button(
    "Download Dive Log as CSV",
    data=df.drop(columns=["Image"]).to_csv(index=False),
    file_name="divelog.csv",
    mime="text/csv"
)

# PDF Export
if st.button("Export as PDF"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt="Dive Log Summary", ln=True, align="C")

    for i, row in df.iterrows():
        for key, value in row.drop("Image").items():
            pdf.cell(200, 5, txt=f"{key}: {value}", ln=True)
        pdf.cell(200, 5, txt="---", ln=True)

    tmp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(tmp_pdf.name)
    with open(tmp_pdf.name, "rb") as f:
        st.download_button("Download Dive Log as PDF", f.read(), file_name="divelog.pdf", mime="application/pdf")
