import streamlit as st
import pandas as pd
import math
from io import BytesIO

# --- Streamlit App Configuration ---
st.set_page_config(layout="wide")
st.title("Comparative Picker Requirement Calculator")
st.markdown("Analyze picker needs by including or excluding binning time from the total workload.")

# --- Sidebar for Input Parameters ---
st.sidebar.header("Input Parameters")

# Section for Order Composition
st.sidebar.subheader("Order Composition")
milk_items_per_order = st.sidebar.number_input("Milk Items per Order", min_value=1, value=1)
non_milk_items_per_order = st.sidebar.number_input("Non-Milk Items per Order", min_value=0, value=2)

# Section for Task Timings
st.sidebar.subheader("Task Timings & Rates")
milk_picking_rate_per_hour = st.sidebar.number_input("Milk Picking Rate (Qty/Hour/Picker)", min_value=1, value=1800)
non_milk_pick_time_sec = st.sidebar.number_input("Non-Milk Picking Time (seconds)", min_value=1, value=60, help="Time taken to pick a certain quantity of non-milk items.")
non_milk_pick_qty = st.sidebar.number_input("Quantity for Non-Milk Picking Time", min_value=1, value=3, help="Number of non-milk items picked in the time above.")
binning_time_per_order_sec = st.sidebar.number_input("Binning Time per Order (seconds)", min_value=0, value=20)

# Section for Shift and Order Volume
st.sidebar.subheader("Shift & Order Volume")
shift_duration_min = st.sidebar.number_input("Shift Duration (minutes)", min_value=30, value=120)
start_orders = st.sidebar.number_input("Start Order Count", min_value=1, value=100, step=50)
end_orders = st.sidebar.number_input("End Order Count", min_value=start_orders, value=2000, step=50)
step = st.sidebar.number_input("Step Size", min_value=1, value=50)


# --- Calculations ---

# 1. Calculate the capacity of one picker for the entire shift in seconds
shift_duration_sec = shift_duration_min * 60

# 2. Calculate the base time required for each task component for a SINGLE order
time_per_milk_item_sec = 3600 / milk_picking_rate_per_hour
time_for_milk_picking_per_order = time_per_milk_item_sec * milk_items_per_order

if non_milk_pick_qty > 0:
    time_per_non_milk_item_sec = non_milk_pick_time_sec / non_milk_pick_qty
else:
    time_per_non_milk_item_sec = 0
time_for_non_milk_picking_per_order = time_per_non_milk_item_sec * non_milk_items_per_order

# 3. Define the full task time for each scenario
# Scenario 1 (With Binning): Non-milk picker does the picking and binning.
non_milk_task_time_with_binning = time_for_non_milk_picking_per_order + binning_time_per_order_sec
# Scenario 2 (Without Binning): Binning time is ignored.
non_milk_task_time_without_binning = time_for_non_milk_picking_per_order

# 4. Generate the data for both scenarios
order_counts = list(range(start_orders, end_orders + 1, step))
data_with_binning = []
data_without_binning = []

for orders in order_counts:
    # --- Calculate for "With Binning" Scenario ---
    total_milk_workload_sec = orders * time_for_milk_picking_per_order
    total_non_milk_workload_with_binning_sec = orders * non_milk_task_time_with_binning

    milk_pickers_required = total_milk_workload_sec / shift_duration_sec if shift_duration_sec > 0 else 0
    non_milk_pickers_with_binning_req = total_non_milk_workload_with_binning_sec / shift_duration_sec if shift_duration_sec > 0 else 0

    data_with_binning.append({
        "Orders to Fulfill": orders,
        "Milk Pickers": math.ceil(milk_pickers_required),
        "Non-Milk Pickers": math.ceil(non_milk_pickers_with_binning_req),
        "Total Pickers": math.ceil(milk_pickers_required) + math.ceil(non_milk_pickers_with_binning_req),
        "Milk Pickers (Exact)": round(milk_pickers_required, 2),
        "Non-Milk Pickers (Exact)": round(non_milk_pickers_with_binning_req, 2)
    })

    # --- Calculate for "Without Binning" Scenario ---
    total_non_milk_workload_without_binning_sec = orders * non_milk_task_time_without_binning
    non_milk_pickers_without_binning_req = total_non_milk_workload_without_binning_sec / shift_duration_sec if shift_duration_sec > 0 else 0

    data_without_binning.append({
        "Orders to Fulfill": orders,
        "Milk Pickers": math.ceil(milk_pickers_required),
        "Non-Milk Pickers": math.ceil(non_milk_pickers_without_binning_req),
        "Total Pickers": math.ceil(milk_pickers_required) + math.ceil(non_milk_pickers_without_binning_req),
        "Milk Pickers (Exact)": round(milk_pickers_required, 2),
        "Non-Milk Pickers (Exact)": round(non_milk_pickers_without_binning_req, 2)
    })


# --- Create DataFrames and Reorder Columns ---
def create_and_format_df(data):
    df = pd.DataFrame(data)
    return df[[
        "Orders to Fulfill", "Milk Pickers", "Non-Milk Pickers", "Total Pickers",
        "Milk Pickers (Exact)", "Non-Milk Pickers (Exact)"
    ]]

df_with_binning = create_and_format_df(data_with_binning)
df_without_binning = create_and_format_df(data_without_binning)


# --- Display Results ---

st.subheader("Calculation Summary for a Single Order")
col1, col2, col3 = st.columns(3)
col1.metric("Milk Picking Time", f"{round(time_for_milk_picking_per_order)} seconds")
col2.metric("Non-Milk Picking Time", f"{round(time_for_non_milk_picking_per_order)} seconds")
col3.metric("Binning Time", f"{round(binning_time_per_order_sec)} seconds")
st.info("In the 'With Binning' scenario, the Binning Time is added to the Non-Milk Picker's workload.", icon="ℹ️")


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
