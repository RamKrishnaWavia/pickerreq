import streamlit as st
import pandas as pd
import math
from io import BytesIO

# --- Streamlit App Configuration ---
st.set_page_config(layout="wide")
st.title("Component-Based Picker Requirement Calculator")

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

# 2. Calculate the time required to complete each task for a SINGLE order
# Milk Task
time_per_milk_item_sec = 3600 / milk_picking_rate_per_hour
time_for_milk_task_per_order = time_per_milk_item_sec * milk_items_per_order

# Non-Milk Task (including binning)
# Assumption: The non-milk picker performs the binning task for the order.
if non_milk_pick_qty > 0:
    time_per_non_milk_item_sec = non_milk_pick_time_sec / non_milk_pick_qty
else:
    time_per_non_milk_item_sec = 0

time_for_non_milk_picking_per_order = time_per_non_milk_item_sec * non_milk_items_per_order
time_for_non_milk_task_per_order = time_for_non_milk_picking_per_order + binning_time_per_order_sec

# 3. Generate the data for the table
order_counts = list(range(start_orders, end_orders + 1, step))
data = []

for orders in order_counts:
    # Calculate total workload in seconds for each task type
    total_milk_workload_sec = orders * time_for_milk_task_per_order
    total_non_milk_workload_sec = orders * time_for_non_milk_task_per_order

    # Calculate pickers required for each workload
    if shift_duration_sec > 0:
        milk_pickers_required = total_milk_workload_sec / shift_duration_sec
        non_milk_pickers_required = total_non_milk_workload_sec / shift_duration_sec
    else:
        milk_pickers_required = 0
        non_milk_pickers_required = 0

    # Round up to the nearest whole person for each task
    milk_pickers_rounded = math.ceil(milk_pickers_required)
    non_milk_pickers_rounded = math.ceil(non_milk_pickers_required)

    data.append({
        "Orders to Fulfill": orders,
        "Milk Pickers Required": milk_pickers_rounded,
        "Non-Milk Pickers Required": non_milk_pickers_rounded,
        "Total Pickers Required": milk_pickers_rounded + non_milk_pickers_rounded,
        "Milk Pickers (Exact)": round(milk_pickers_required, 2), # For reference
        "Non-Milk Pickers (Exact)": round(non_milk_pickers_required, 2) # For reference
    })

df = pd.DataFrame(data)
# Reorder columns for clarity
df = df[[
    "Orders to Fulfill",
    "Milk Pickers Required",
    "Non-Milk Pickers Required",
    "Total Pickers Required",
    "Milk Pickers (Exact)",
    "Non-Milk Pickers (Exact)"
]]

# --- Display Results ---

st.subheader("Calculation Summary for a Single Order")
st.info("This shows the time breakdown to process one order. The binning time is allocated to the Non-Milk Picker's workload.", icon="ℹ️")

col1, col2 = st.columns(2)
with col1:
    st.metric(
        "Milk Task Time per Order",
        f"{round(time_for_milk_task_per_order)} seconds",
        help=f"Based on picking {milk_items_per_order} milk item(s)."
    )
with col2:
    st.metric(
        "Non-Milk Task Time per Order",
        f"{round(time_for_non_milk_task_per_order)} seconds",
        help=f"Includes {round(time_for_non_milk_picking_per_order)}s for picking {non_milk_items_per_order} item(s) + {binning_time_per_order_sec}s for binning."
    )


st.subheader("Picker Requirement Headcount")
st.dataframe(df, use_container_width=True)

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

excel_data = convert_df_to_excel(df)
st.download_button(
    label="📥 Download as Excel",
    data=excel_data,
    file_name="picker_requirement_by_task.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
