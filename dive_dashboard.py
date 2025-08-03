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

# --- Upload Multiple Dive Log CSVs ---
st.subheader("📤 Upload Dive Log CSV(s)")
uploaded_files = st.file_uploader(
    "Upload one or more dive log CSV files",
    type="csv",
    accept_multiple_files=True
)

if uploaded_files:
    df_list = []
    for file in uploaded_files:
        try:
            df_temp = pd.read_csv(file)
            df_list.append(df_temp)
        except Exception as e:
            st.error(f"Error reading {file.name}: {e}")

    if df_list:
        df = pd.concat(df_list, ignore_index=True)
        st.success(f"Loaded {len(df)} dives from {len(df_list)} files.")

        # --- Dashboard Summary ---
        st.subheader("📈 Dive Dashboard Summary")
        st.markdown(f"**Total Dives:** {len(df)}")
        st.markdown(f"**Total Time:** {df['Duration (min)'].sum()} min")
        st.markdown(f"**Average Depth:** {df['Depth (m)'].mean():.1f} m")
        st.markdown(f"**Deepest Dive:** {df['Depth (m)'].max():.1f} m")

        # --- Favorite Locations ---
        if 'Location' in df.columns:
            top_locations = df['Location'].value_counts().head(5)
            st.subheader("📌 Top Dive Locations")
            st.bar_chart(top_locations)

        # --- Dive Activity Breakdown ---
        if 'Activity' in df.columns:
            st.subheader("🧭 Dive Activities")
            activity_counts = df['Activity'].value_counts()
            st.plotly_chart(px.pie(values=activity_counts.values, names=activity_counts.index, title="Activity Distribution"))

        # --- Dive Time vs Depth Scatter ---
        if 'Duration (min)' in df.columns and 'Depth (m)' in df.columns:
            st.subheader("🕒 Time vs Depth")
            st.plotly_chart(px.scatter(df, x='Duration (min)', y='Depth (m)', color='Diver' if 'Diver' in df.columns else None,
                                       title="Dive Duration vs. Depth"))

        # --- Dive Map ---
        if 'Latitude' in df.columns and 'Longitude' in df.columns:
            st.subheader("📍 Dive Site Map")
            st.map(df.rename(columns={"Latitude": "lat", "Longitude": "lon"}))

        # --- Raw Data ---
        st.subheader("📋 Raw Dive Log Data")
        st.dataframe(df)

        # --- Export Combined CSV ---
        st.download_button(
            "Download Combined Dive Log as CSV",
            data=df.to_csv(index=False),
            file_name="combined_divelog.csv",
            mime="text/csv"
        )

        # --- Export PDF ---
        if st.button("Download Combined Dive Log as PDF"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=10)
            pdf.cell(200, 10, txt="Dive Log Summary", ln=True, align="C")

            for i, row in df.iterrows():
                for key, value in row.items():
                    pdf.cell(200, 5, txt=f"{key}: {value}", ln=True)
                pdf.cell(200, 5, txt="---", ln=True)

            tmp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            pdf.output(tmp_pdf.name)
            with open(tmp_pdf.name, "rb") as f:
                st.download_button("Download PDF", f.read(), file_name="combined_divelog.pdf", mime="application/pdf")
else:
    st.info("Upload one or more CSV files to view dashboard.")
