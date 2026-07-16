import streamlit as st
from streamlit_option_menu import option_menu
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import base64
import os

# ---------------------------------------------------------
# 1. PAGE SETUP
# ---------------------------------------------------------
st.set_page_config(
    page_title="Road Accident Analysis | Intelligence Dashboard",
    page_icon="🚧",
    layout="wide",
    initial_sidebar_state="expanded",
)

PLOTLY_TEMPLATE = "plotly_dark"
COLOR_SEQ = ["#E63946", "#FFB703", "#1C7293", "#4E9F3D", "#9B5DE5", "#3E92CC"]
SEVERITY_COLORS = {"Slight Injury": "#FFB703", "Serious Injury": "#1C7293", "Fatal injury": "#E63946"}
WEATHER_COLORS = {"Normal": "#FFB703", "Raining": "#1C7293", "Other": "#E63946"}

# ---------------------------------------------------------
# 2. LOAD + CLEAN DATA
# (pipeline matches the project's cleaning notebook)
# ---------------------------------------------------------
@st.cache_data
def load_data():
    raw = pd.read_csv("Road_cleaned.csv", na_values=["na", "NA", "Na", "N/A", "", "NaN"])

    df = raw.copy()
    df.drop(columns=["Service_year_of_vehicle", "Defect_of_vehicle"], errors="ignore", inplace=True)

    for col in df.columns:
        if df[col].dtype == "object" or str(df[col].dtype) == "str":
            if df[col].isnull().any():
                df[col] = df[col].fillna(df[col].mode()[0])
        elif df[col].dtype == "float64":
            if df[col].isnull().any():
                df[col] = df[col].fillna(df[col].mean())

    df["Type_of_vehicle"] = df["Type_of_vehicle"].replace({
        "Lorry (41?100Q)": "Lorry (41-100Q)",
        "Lorry (11?40Q)": "Lorry (11-40Q)",
        "Public (13?45 seats)": "Public (13-45 seats)",
    })
    df["Area_accident_occured"] = df["Area_accident_occured"].str.strip()
    df.drop_duplicates(inplace=True)
    df.reset_index(drop=True, inplace=True)

    df["hour"] = pd.to_datetime(df["Time"], format="%H:%M:%S", errors="coerce").dt.hour

    def group_weather(w):
        if w == "Normal": return "Normal"
        elif w in ["Raining", "Raining and Windy"]: return "Raining"
        else: return "Other"

    df["weather_group"] = df["Weather_conditions"].apply(group_weather)
    return df, raw

df_raw_clean, df_original = load_data()

# ---------------------------------------------------------
# 3. BACKGROUND IMAGES — main area + sidebar, both optional
# ---------------------------------------------------------
def set_backgrounds(main_png, sidebar_png):
    css = "<style>"
    if os.path.exists(main_png):
        with open(main_png, "rb") as f:
            main_b64 = base64.b64encode(f.read()).decode()
        css += f"""
        [data-testid="stAppViewContainer"] {{
            background-image:
                linear-gradient(rgba(20,27,37,0.90), rgba(20,27,37,0.93)),
                url("data:image/png;base64,{main_b64}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        """
    if os.path.exists(sidebar_png):
        with open(sidebar_png, "rb") as f:
            side_b64 = base64.b64encode(f.read()).decode()
        css += f"""
        [data-testid="stSidebar"] {{
            background-image:
                linear-gradient(rgba(16,22,30,0.85), rgba(16,22,30,0.90)),
                url("data:image/png;base64,{side_b64}");
            background-size: cover;
            background-position: center;
        }}
        """
    css += "</style>"
    st.markdown(css, unsafe_allow_html=True)

set_backgrounds("background.png", "sidebar_background.png")

# ---------------------------------------------------------
# 4. SIDEBAR — NAVIGATION + FILTERS
# ---------------------------------------------------------
st.sidebar.title("🚧 Road Accident Analysis")
st.sidebar.caption("Traffic Safety Intelligence System")
st.sidebar.divider()

page = st.sidebar.radio(
    "Navigate",
    ["📊 Overview", "🧹 Data Cleaning", "📈 Analytics", "👤 Driver Explorer",
     "⏰ Time Analysis", "💡 Insights", "⬇️ Export"],
)

st.sidebar.divider()
st.sidebar.subheader("Filters")

hour_range = st.sidebar.slider(
    "Hour of day", 0, 23, (0, 23)
)
weather_sel = st.sidebar.multiselect(
    "Weather", sorted(df_raw_clean.weather_group.unique()),
    default=sorted(df_raw_clean.weather_group.unique())
)
vehicle_sel = st.sidebar.multiselect(
    "Vehicle type", sorted(df_raw_clean.Type_of_vehicle.unique()),
    default=sorted(df_raw_clean.Type_of_vehicle.unique())
)
severity_sel = st.sidebar.multiselect(
    "Severity", sorted(df_raw_clean.Accident_severity.unique()),
    default=sorted(df_raw_clean.Accident_severity.unique())
)

df = df_raw_clean[
    df_raw_clean.hour.between(*hour_range) &
    df_raw_clean.weather_group.isin(weather_sel) &
    df_raw_clean.Type_of_vehicle.isin(vehicle_sel) &
    df_raw_clean.Accident_severity.isin(severity_sel)
]

st.sidebar.divider()
st.sidebar.caption(f"{len(df):,} of {len(df_raw_clean):,} records match filters")

if df.empty:
    st.warning("No records match the current filters. Try widening your selection.")
    st.stop()

# ===========================================================
# PAGE: OVERVIEW
# ===========================================================
if page == "📊 Overview":
    st.title("🚧 ROAD ACCIDENT INTELLIGENCE")
    st.caption("ANALYTICS & RISK PATTERN DETECTION SYSTEM")

    st.markdown("""Understanding when, where, and why road accidents happen.

This project analyzes:

⏰ Time & Weather Patterns

🚗 Vehicle Type & Collision Type

⚠️ Cause & Severity

👤 Driver Profile & Experience

🛣️ Road & Junction Conditions""")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Records", f"{len(df):,}")
    c2.metric("Vehicle Types", df.Type_of_vehicle.nunique())
    c3.metric("Avg Casualties", f"{df.Number_of_casualties.mean():.2f}")
    c4.metric("% Fatal", f"{(df.Accident_severity=='Fatal injury').mean()*100:.1f}%")
    c5.metric("Columns", df.shape[1])

    st.divider()
    # col1, col2 = st.columns(2)

    # with col1:
    st.subheader("Top Vehicle Types by Accidents")
    counts = df.Type_of_vehicle.value_counts().head(8).reset_index()
    counts.columns = ["vehicle", "count"]
    fig = px.bar(counts, x="count", y="vehicle", orientation="h",
                     template=PLOTLY_TEMPLATE, color="vehicle", color_discrete_sequence=COLOR_SEQ)
    fig.update_layout(showlegend=True, yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, width='stretch')

    # with col2:
    st.subheader("Avg Casualties by Hour")
    by_hour = df.groupby("hour")["Number_of_casualties"].mean().reset_index()
    fig = px.line(by_hour, x="hour", y="Number_of_casualties", template=PLOTLY_TEMPLATE, markers=True, color_discrete_sequence=["#E63946"])
    fig.update_layout(xaxis_title="Hour of Day", yaxis_title="Average Casualties")
    st.plotly_chart(fig, width='stretch')          

# ===========================================================
# PAGE: DATA CLEANING
# ===========================================================
elif page == "🧹 Data Cleaning":
    st.title("Data Cleaning")

    c1, c2, c3 = st.columns(3)
    c1.metric("Original Rows", f"{len(df_original):,}")
    c2.metric("Missing Values", int(df_original.isna().sum().sum()))
    c3.metric("Duplicate Rows", int(df_original.duplicated().sum()))

    st.divider()
    st.subheader("Cleaning Pipeline")
    st.markdown("""
    - Drop unused columns (`Service_year_of_vehicle`, `Defect_of_vehicle`)
    - Fill missing text values with column mode, numeric values with column mean
    - Fix encoding typos in `Type_of_vehicle` (e.g. `Lorry (41?100Q)` → `Lorry (41-100Q)`)
    - Strip inconsistent whitespace from `Area_accident_occured`
    - Remove exact duplicate rows
    - Engineer `hour` and `weather_group` from raw columns
    """)

    if st.button("▶ Run Cleaning Summary", type="primary"):
        st.subheader("Cleaning Report")
        r1, r2, r3, r4 = st.columns(4)
        r1.metric("Rows After Clean", f"{len(df_raw_clean):,}")
        r2.metric("Rows Removed", int(df_original.duplicated().sum()))
        r3.metric("Numeric Columns", df_raw_clean.select_dtypes("number").shape[1])
        r4.metric("Categorical Columns", df_raw_clean.select_dtypes("object").shape[1])
        st.success("Cleaning summary generated.")

# ===========================================================
# PAGE: ANALYTICS
# ===========================================================
elif page == "📈 Analytics":
    st.title("Accident Analytics")
    st.caption(f"Analyzing {len(df):,} records after filters")

    t1, t2, t3, t4 = st.tabs(["By Vehicle Type", "By Severity", "Weather vs Casualties", "Correlation"])

    with t1:
        top_vehicles = df.Type_of_vehicle.value_counts().head(6).index
        subset = df[df.Type_of_vehicle.isin(top_vehicles)]
        fig = px.box(subset, x="Type_of_vehicle", y="Number_of_casualties", color="Type_of_vehicle",
                     template=PLOTLY_TEMPLATE, color_discrete_sequence=COLOR_SEQ)
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, width='stretch')

    with t2:
        counts = df.Accident_severity.value_counts().reset_index()
        counts.columns = ["severity", "count"]
        col1, col2 = st.columns(2)
        with col1:
            fig = px.pie(counts, names="severity", values="count", hole=0.55,
                         color="severity", color_discrete_map=SEVERITY_COLORS, template=PLOTLY_TEMPLATE)
            st.plotly_chart(fig, width='stretch')
        with col2:
            fig = px.bar(counts, x="severity", y="count", color="severity",
                         color_discrete_map=SEVERITY_COLORS, template=PLOTLY_TEMPLATE)
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, width='stretch')

    with t3:
        fig = px.box(df, x="weather_group", y="Number_of_casualties", color="weather_group",
                     category_orders={"weather_group": ["Normal", "Raining", "Other"]},
                     color_discrete_map=WEATHER_COLORS, template=PLOTLY_TEMPLATE)
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, width='stretch')

    
    with t4:
        numeric_cols = ["Number_of_vehicles_involved", "Number_of_casualties", "hour"]
        corr = df[numeric_cols].corr()
        fig = px.imshow(corr, text_auto=".2f", template=PLOTLY_TEMPLATE, color_continuous_scale=["#FFB703", "#1A1A24", "#E63946"], zmin=-1, zmax=1)
        st.plotly_chart(fig, width='stretch')

# ===========================================================
# PAGE: DRIVER EXPLORER
# ===========================================================
elif page == "👤 Driver Explorer":
    st.title("Driver Explorer")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Casualties by Driver Sex")
        subset = df[df.Sex_of_driver.isin(["Male", "Female"])]
        fig = px.violin(subset, x="Sex_of_driver", y="Number_of_casualties", color="Sex_of_driver", box=True,
                         template=PLOTLY_TEMPLATE, color_discrete_sequence=COLOR_SEQ)
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, width='stretch')
    with col2:
        st.subheader("Casualties by Driving Experience")
        exp_order = ["Below 1yr", "1-2yr", "2-5yr", "5-10yr", "Above 10yr", "No Licence", "unknown"]
        fig = px.box(df, x="Driving_experience", y="Number_of_casualties", color="Driving_experience",
                     category_orders={"Driving_experience": exp_order},
                     template=PLOTLY_TEMPLATE, color_discrete_sequence=COLOR_SEQ)
        fig.update_layout(showlegend=False, xaxis_tickangle=-20)
        st.plotly_chart(fig, width='stretch')

    st.divider()
    st.subheader("Highest-Casualty Accidents")
    top_risk = df.nlargest(10, "Number_of_casualties")[
        ["Day_of_week", "hour", "Type_of_vehicle", "Driving_experience",
         "weather_group", "Number_of_casualties", "Accident_severity"]
    ]
    st.dataframe(top_risk, width='stretch')

# ===========================================================
# PAGE: TIME ANALYSIS
# ===========================================================
elif page == "⏰ Time Analysis":
    st.title("Time-Based Analysis")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Accidents by Hour")
        by_hour = df.groupby("hour").size().reset_index(name="count")
        fig = px.bar(by_hour, x="hour", y="count", template=PLOTLY_TEMPLATE,
                     color_discrete_sequence=["#E63946"])
        st.plotly_chart(fig, width='stretch')
    with col2:
        st.subheader("Vehicles Involved by Hour")
        by_hour2 = df.groupby("hour")["Number_of_vehicles_involved"].mean().reset_index()
        fig = px.bar(by_hour2, x="hour", y="Number_of_vehicles_involved", template=PLOTLY_TEMPLATE,
                     color_discrete_sequence=["#FFB703"])
        st.plotly_chart(fig, width='stretch')

# ===========================================================
# PAGE: INSIGHTS
# ===========================================================
elif page == "💡 Insights":
    st.title("Analytical Insights")

    if st.button("⚡ Generate Insights", type="primary"):
        top_vehicle = df.Type_of_vehicle.value_counts().idxmax()
        worst_hour = df.groupby("hour")["Number_of_casualties"].mean().idxmax()
        fatal_pct = (df.Accident_severity == "Fatal injury").mean() * 100
        corr_val = df["Number_of_vehicles_involved"].corr(df["Number_of_casualties"])
        direction = "negatively" if corr_val < 0 else "positively"
        normal_cas = df[df.weather_group == "Normal"]["Number_of_casualties"].mean()
        rain_cas = df[df.weather_group == "Raining"]["Number_of_casualties"].mean()
        top_cause = df.Cause_of_accident.value_counts().idxmax()
        top_cause_pct = (df.Cause_of_accident == top_cause).mean() * 100

        st.subheader("Key Findings")
        st.info(f"🚗 **{top_vehicle}** is the most frequently involved vehicle type — "
                f"{(df.Type_of_vehicle==top_vehicle).mean()*100:.1f}% of accidents.")
        st.warning(f"⏰ Hour **{worst_hour}:00** shows the highest average casualties per accident "
                   f"in this filtered set.")
        st.error(f"🚨 **{fatal_pct:.1f}%** of accidents in this selection are fatal.")
        st.info(f"🚙 Vehicles involved is {direction} correlated with casualties (r = {corr_val:.2f}).")
        st.warning(f"🌧️ Normal-weather accidents average **{normal_cas:.2f}** casualties, "
                   f"vs **{rain_cas:.2f}** in rain.")
        st.error(f"⚠️ **{top_cause}** is the top reported cause — **{top_cause_pct:.1f}%** of accidents.")
    else:
        st.info("Click **Generate Insights** to compute key findings from the current filtered data.")

# ===========================================================
# PAGE: EXPORT
# ===========================================================
elif page == "⬇️ Export":
    st.title("Export Data")
    st.write(f"Exporting **{len(df):,}** of **{len(df_raw_clean):,}** total records based on active filters.")
    table_height = min(35 * len(df) + 38, 800)
    st.dataframe(df, width='stretch', height=table_height)
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download Filtered CSV", data=csv,
                        file_name="road_accidents_filtered.csv", mime="text/csv")
