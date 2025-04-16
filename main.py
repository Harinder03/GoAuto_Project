import streamlit as st
import pandas as pd
import streamlit.components.v1 as components  
import numpy as np
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

# Page config
st.set_page_config(page_title="Car Sales App", layout="wide")

# Load data
@st.cache_data
def load_data():
    url = "https://drive.google.com/uc?export=download&id=1ELFg0FB42MzAHAgWkERFuvn45d8S-pBh"
    return pd.read_csv(url)

df = load_data()

# Sidebar navigation
st.sidebar.title("Navigation")
menu = st.sidebar.radio("Go to", ["Overview", "Analysis", "Model", "About"])

if menu == "Overview":
    st.title("🚗 Edmonton Car Sales Insights")
    st.markdown("#### 📍 Your data-driven hub for understanding car sales trends across Edmonton")

    st.markdown("""
Welcome! This interactive dashboard allows you to explore key patterns in vehicle sales across the Edmonton region using dynamic filters, cluster-based mapping, and dealership analytics.

Whether you're a business analyst, dealership manager, or student, this tool helps you:

- 🧭 Navigate car sales by **location**, **type**, **make**, and **engine**
- 🗺️ Visualize dealership **clusters** and performance
- 📉 Analyze **pricing**, **mileage**, and most-sold models
- 🏆 Discover top-selling **dealers** and **brands**

---

#### 🚀 Quick Stats
    """)

    col1, col2, col3 = st.columns(3)
    col1.metric("🚘 Total Vehicles", f"{len(df):,}")
    col2.metric("💲 Avg. Price", f"${int(df['price'].mean()):,}")
    col3.metric("🏆 Most Common Make", df['make'].mode()[0])

    st.success("👉 Head to the **'Model' tab** to explore clusters and interactive mapping.")
    st.info("Use the **filters** in the 'Model' tab to focus on specific makes, price ranges, or regions.")


elif menu == "Analysis":
    st.title("📊 Analysis")
    st.markdown("Visual and statistical analysis of car sales data is presented below.")

    st.subheader("📈 Power BI Dashboard Insight")
    st.info("Explore interactive charts and sales statistics directly from our Power BI Dashboard.")

    # Embed Power BI dashboard
    powerbi_url = "https://app.powerbi.com/reportEmbed?reportId=760b6d9f-a087-4501-8d7a-64e28f840607&autoAuth=true&ctid=2ba011f1-f50a-44f3-a200-db3ea74e29b7"
    components.iframe(src=powerbi_url, width=1100, height=700, scrolling=True)

elif menu == "Model":
    st.title("Clustering Model Dashboard")

    # Column visibility toggles
    with st.expander("Toggle Column Visibility", expanded=True):
        left_col_visible = st.checkbox("<< Show Filters", value=True)
        right_col_visible = st.checkbox(">> Show Tables", value=False)

    # Determine layout widths
    if left_col_visible and right_col_visible:
        col_widths = [1, 2.5, 1]
    elif left_col_visible:
        col_widths = [1, 3, 0.01]
    elif right_col_visible:
        col_widths = [0.01, 3, 1.5]
    else:
        col_widths = [0.01, 5, 0.01]

    layout = st.columns(col_widths)

    # Left Column: Filters
    if left_col_visible:
        with layout[0]:
            st.markdown("### :mag: Additional Filters")
            selected_type = st.multiselect("Type", options=df['stock_type'].unique())
            selected_engine = st.multiselect("Engine", options=df['engine_from_vin'].unique())
            selected_drivetrain = st.multiselect("Drivetrain", options=df['drivetrain_from_vin'].unique())
            selected_make = st.multiselect("Make", options=df['make'].unique())
            price_range = st.slider("💲 Price Range", 5000, 100000, (10000, 80000))
            exclude_autocanada = st.checkbox("Exclude AutoCanada", value=False)
    else:
        # Default price range when filter is hidden
        price_range = (10000, 80000)

    # Center Column: Cluster Table + Map
    with layout[1]:
        tab1, tab2 = st.tabs(["📋 Cluster Overview", "🗺️ Regional Map"])

        with tab1:
            st.subheader(":bar_chart: Cluster Overview & Selection")

            top_model_cluster = df.groupby(["Cluster", "model"]).size().reset_index(name="Model Count")
            top_model_cluster = top_model_cluster.sort_values(["Cluster", "Model Count"], ascending=[True, False])
            top_model_cluster = top_model_cluster.drop_duplicates("Cluster").set_index("Cluster")

            cluster_summary = df.groupby("Cluster").agg({
                'Region': lambda x: x.mode().iloc[0] if not x.mode().empty else 'N/A',
                'stock_type': lambda x: x.mode().iloc[0] if not x.mode().empty else 'N/A',
                'price': 'mean',
                'mileage': 'mean',
                'vehicle_id': 'count'
            }).reset_index()

            cluster_summary["Top Model (Count)"] = cluster_summary["Cluster"].map(
                lambda c: f"{top_model_cluster.loc[c, 'model']} ({top_model_cluster.loc[c, 'Model Count']})"
                if c in top_model_cluster.index else "N/A"
            )

            cluster_summary.columns = [
                'Cluster', 'Top Region', 'Top Type', 'Avg Price', 'Avg Mileage', 'Vehicles Sold', 'Top Model (Count)'
            ]

            cluster_region_map = df.groupby('Cluster')['Region'].unique().apply(lambda x: ', '.join(set(x))).to_dict()

            # Adjust table layout
            table_widths = [1, 2, 2, 2, 2, 2, 3] if not (left_col_visible and right_col_visible) else [1, 2.2, 1.5, 1.5, 1.5, 1.5, 2]
            header_cols = st.columns(table_widths)
            for col, header in zip(header_cols, cluster_summary.columns):
                col.markdown(f"**{header}**")

            selected_clusters = []
            for idx, row in cluster_summary.iterrows():
                cols = st.columns([1, 3, 2, 2, 2, 2, 3])  # Adjust column widths
                with cols[0]:
                    check = st.checkbox(
                        str(row['Cluster']),
                        key=f"cluster_{int(row['Cluster'])}",
                        help=f"Includes: {cluster_region_map.get(row['Cluster'], 'Region Info Not Available')}"
                    )
                with cols[1]:
                    st.write(row['Top Region'])
                with cols[2]:
                    st.write(row['Top Type'])
                with cols[3]:
                    st.write(f"${row['Avg Price']:,.0f}")
                with cols[4]:
                    st.write(f"{row['Avg Mileage']:,.0f}")
                with cols[5]:
                    st.write(f"{row['Vehicles Sold']:,}")
                with cols[6]:
                    st.write(row['Top Model (Count)'])
                if check:
                    selected_clusters.append(row['Cluster'])
            
            #KPI 
            if selected_clusters:
                kpi_df = df[df['Cluster'].isin(selected_clusters)]
            else:
                kpi_df = df.copy()

            total_vehicles_selected = kpi_df["vehicle_id"].count()
            top_make_selected = kpi_df['make'].mode().iloc[0] if not kpi_df['make'].mode().empty else "N/A"
            
            kpi_selected_1, kpi_selected_2 = st.columns(2)

            with kpi_selected_1:
                st.markdown("**Total Vehicles Sold**")
                st.markdown(f"<h2 style='text-align: center; color: #FF6347;'>{total_vehicles_selected:,}</h2>", unsafe_allow_html=True)

            with kpi_selected_2:
                st.markdown("**Top Make**")
                st.markdown(f"<h2 style='text-align: center; color: #FF6347;'>{top_make_selected}</h2>", unsafe_allow_html=True)
            
            # Apply filters
            filtered_df = df.copy()
            filtered_df = filtered_df[(filtered_df['price'] >= price_range[0]) & (filtered_df['price'] <= price_range[1])]
            if selected_clusters:
                filtered_df = filtered_df[filtered_df['Cluster'].isin(selected_clusters)]
            if left_col_visible:
                if selected_type:
                    filtered_df = filtered_df[filtered_df['stock_type'].isin(selected_type)]
                if selected_engine:
                    filtered_df = filtered_df[filtered_df['engine_from_vin'].isin(selected_engine)]
                if selected_drivetrain:
                    filtered_df = filtered_df[filtered_df['drivetrain_from_vin'].isin(selected_drivetrain)]
                if selected_make:
                    filtered_df = filtered_df[filtered_df['make'].isin(selected_make)]
                if exclude_autocanada:
                    filtered_df = filtered_df[~filtered_df['dealer_name'].str.contains("AutoCanada", case=False)]
        
        with tab2:
            # Map rendering
            st.subheader(":world_map: Clustered Regional Map")
            map_df = filtered_df.copy()
            region_map_data = map_df.groupby(["Cluster", "Region", "FSA_Latitude", "FSA_Longitude"]).agg({
                "vehicle_id": "count",
                "Region_dealerships": "first",
                "Top_performing_dealerships": lambda x: x.mode().iloc[0] if not x.mode().empty else "N/A",
                "Average_mileage": "mean",
                "make": lambda x: x.mode().iloc[0] if not x.mode().empty else "N/A"
            }).reset_index().rename(columns={
                "vehicle_id": "Vehicles Sold",
                "Region_dealerships": "Dealership Count",
                "make": "Top Make"
            })
            region_map_data["cluster_sales"] = region_map_data.groupby("Cluster")["Vehicles Sold"].transform("sum")
            cluster_color_map = {0: "red", 1: "blue", 2: "orange", 3: "green", 4: "purple",
                                5: "lightgray", 6: "cadetblue", 7: "pink", 8: "beige", 9: "darkred"}
            region_map_data["color"] = region_map_data["Cluster"].map(cluster_color_map)

            m = folium.Map(location=[53.5461, -113.4938], zoom_start=10)
            marker_cluster = MarkerCluster().add_to(m)

            search_input = st.text_input(":mag: Search Region (e.g., North, South)").lower()
            if search_input:
                region_map_data = region_map_data[region_map_data['Region'].str.lower().str.contains(search_input)]

            for _, row in region_map_data.iterrows():
                icon = folium.Icon(color=row.color, icon="car", prefix="fa")
                folium.Marker(
                    location=[row.FSA_Latitude, row.FSA_Longitude],
                    icon=icon,
                    popup=folium.Popup(f"""
                        <b>Region:</b> {row.Region}<br>
                        <b>Cluster:</b> {row.Cluster}<br>
                        <b>Top Performing Dealership:</b> {row.Top_performing_dealerships}<br>
                        <b>Top Make:</b> {row["Top Make"]}<br>
                        <b>Avg Mileage:</b> {row.Average_mileage:.0f}<br>
                        <b>Vehicles Sold:</b> {row["cluster_sales"]:,}<br>
                        <b>Dealerships:</b> {row["Dealership Count"]}
                    """, max_width=300)
                ).add_to(marker_cluster)

            st_folium(m, use_container_width=True)

    # Right Column: Tables
    if right_col_visible:
        with layout[2]:
            tab3, tab4 = st.tabs([":office: Top Dealerships", ":car: Most Sold Models"])
            with tab3:
                st.subheader(":office: Top Dealerships")
                top_dealer_summary = (
                    filtered_df.groupby("dealer_name").agg({
                        "model": "count",
                        "make": lambda x: x.mode().iloc[0] if not x.mode().empty else "N/A",
                        "mileage": "mean"
                    }).rename(columns={
                        "model": "Count",
                        "make": "Top Make",
                        "mileage": "Avg Mileage"
                    }).sort_values("Count", ascending=False)
                    .reset_index()
                    .head(10)
                )

                # Set 1–10 index for display
                top_dealer_summary.index = np.arange(1, len(top_dealer_summary) + 1)

                # Display table with formatting
                st.dataframe(top_dealer_summary.style.format({
                    "Avg Mileage": "{:,.0f}",
                    "Count": "{:,}"
                }), use_container_width=True)
        with tab4:
            st.subheader(":car: Most Sold Models")
            top_model_summary = (
                filtered_df.groupby(["make", "model"]).size().reset_index(name="Count")
                .sort_values("Count", ascending=False).head(10)
                .reset_index(drop=True)
            )
            
            if not top_model_summary.empty:
                top_model_summary.index = top_model_summary.index + 1
                top_model_summary["Count"] = pd.to_numeric(top_model_summary["Count"], errors="coerce").fillna(0).astype(int)
                st.dataframe(top_model_summary.style.format({"Count": "{:,}"}), use_container_width=True)
            else:
                st.warning("No data available for the selected filters.")

elif menu == "About":
    st.title(":information_source: About")
