import streamlit as st
import pandas as pd
import math
from io import BytesIO

# --- Streamlit App Configuration ---
st.set_page_config(layout="wide")
st.title("Picker Requirement Calculator (Contribution-Based Model)")

# --- Sidebar for Input Parameters ---
st.sidebar.header("Input Parameters")

# Section for Volume & Contribution
st.sidebar.subheader("Volume & Contribution")
start_orders = st.sidebar.number_input("Start Order Count", min_value=100, value=1000, step=100)
end_orders = st.sidebar.number_input("End Order Count", min_value=start_orders, value=3000, step=100)
step = st.sidebar.number_input("Step Size", min_value=50, value=100)
abq = st.sidebar.number_input("Average Basket Quantity (ABQ)", min_value=1.0, value=3.0, step=0.1)
milk_contribution_percent = st.sidebar.slider("Milk Contribution (%)", 0, 100, 70)
non_milk_contribution_percent = 100 - milk_contribution_percent
st.sidebar.metric("Non-Milk Contribution", f"{non_milk_contribution_percent}%")


# Section for Task Rates & Timings
st.sidebar.subheader("Picker Rates & Task Timings")
milk_picking_rate_per_hour = st.sidebar.number_input("Milk Picking Rate (Qty/Hour/Picker)", min_value=1, value=3600)
non_milk_picking_rate_per_hour = st.sidebar.number_input("Non-Milk Picking Rate (Qty/Hour/Picker)", min_value=1, value=180)
binning_time_per_order_sec = st.sidebar.number_input("Binning Time per Order (seconds)", min_value=0, value=20)

# Section for Shift Details
st.sidebar.subheader("Shift Details")
shift_duration_min = st.sidebar.number_input("Shift Duration (minutes)", min_value=30, value=180)


# --- Calculations ---

# 1. Calculate base times and capacities
shift_duration_sec = shift_duration_min * 60
time_per_milk_unit_sec = 3600 / milk_picking_rate_per_hour
time_per_non_milk_unit_sec = 3600 / non_milk_picking_rate_per_hour

# 2. Generate data for the tables
order_counts = list(range(start_orders, end_orders + 1, step))
data_with_binning = []
data_without_binning = []

for orders in order_counts:
    # Calculate total units based on contribution
    total_units = orders * abq
    total_milk_units = total_units * (milk_contribution_percent / 100)
    total_non_milk_units = total_units * (non_milk_contribution_percent / 100)

    # Calculate total workload in seconds for each task
    total_milk_workload_sec = total_milk_units * time_per_milk_unit_sec
    total_non_milk_picking_workload_sec = total_non_milk_units * time_per_non_milk_unit_sec
    total_binning_workload_sec = orders * binning_time_per_order_sec

    # Calculate required pickers for each workload
    milk_pickers_required = total_milk_workload_sec / shift_duration_sec if shift_duration_sec > 0 else 0

    # Scenario 1: With Binning
    total_non_milk_and_binning_workload_sec = total_non_milk_picking_workload_sec + total_binning_workload_sec
    non_milk_pickers_with_binning_req = total_non_milk_and_binning_workload_sec / shift_duration_sec if shift_duration_sec > 0 else 0

    data_with_binning.append({
        "Orders": orders,
        "Total Units": math.ceil(total_units),
        "Milk Pickers": math.ceil(milk_pickers_required),
        "Non-Milk Pickers (+Binning)": math.ceil(non_milk_pickers_with_binning_req),
        "Total Pickers": math.ceil(milk_pickers_required) + math.ceil(non_milk_pickers_with_binning_req)
    })

    # Scenario 2: Without Binning
    non_milk_pickers_without_binning_req = total_non_milk_picking_workload_sec / shift_duration_sec if shift_duration_sec > 0 else 0

    data_without_binning.append({
        "Orders": orders,
        "Total Units": math.ceil(total_units),
        "Milk Pickers": math.ceil(milk_pickers_required),
        "Non-Milk Pickers (Picking Only)": math.ceil(non_milk_pickers_without_binning_req),
        "Total Pickers": math.ceil(milk_pickers_required) + math.ceil(non_milk_pickers_without_binning_req)
    })

# --- Create DataFrames ---
df_with_binning = pd.DataFrame(data_with_binning)
df_without_binning = pd.DataFrame(data_without_binning)


# --- Display Results ---

st.subheader("Calculated Task Times per Unit")
col1, col2, col3 = st.columns(3)
col1.metric("Time per Milk Unit", f"{time_per_milk_unit_sec:.1f} seconds")
col2.metric("Time per Non-Milk Unit", f"{time_per_non_milk_unit_sec:.1f} seconds")
col3.metric("Time per Binning Task", f"{binning_time_per_order_sec:.1f} seconds")
st.info("The binning workload is assigned to the Non-Milk picker team in the 'With Binning' scenario.", icon="ℹ️")


# --- Excel Export Functionality ---
@st.cache_data
def convert_df_to_excel(df_to_convert):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_to_convert.to_excel(writer, index=False, sheet_name='Picker Requirement')
        worksheet = writer.sheets['Picker Requirement']
        for idx, col in enumerate(df_to_convert):
            series = df_to_convert[col]
            max_len = max((series.astype(str).map(len).max(), len(str(series.name)))) + 2
            worksheet.set_column(idx, idx, max_len)
    return output.getvalue()


# --- Tabs for Displaying DataFrames ---
tab1, tab2 = st.tabs(["With Binning Time", "Without Binning Time"])

with tab1:
    st.subheader("Scenario 1: Full Process (Picking + Binning)")
    st.dataframe(df_with_binning, use_container_width=True)
    excel_data_with_binning = convert_df_to_excel(df_with_binning)
    st.download_button(
        label="📥 Download 'With Binning' as Excel",
        data=excel_data_with_binning,
        file_name="picker_req_with_binning.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

with tab2:
    st.subheader("Scenario 2: Picking Only (No Binning Time)")
    st.dataframe(df_without_binning, use_container_width=True)
    excel_data_without_binning = convert_df_to_excel(df_without_binning)
    st.download_button(
        label="📥 Download 'Without Binning' as Excel",
        data=excel_data_without_binning,
        file_name="picker_req_without_binning.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
