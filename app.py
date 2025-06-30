import streamlit as st
import pandas as pd
import math
from io import BytesIO

# --- Streamlit App Configuration ---
st.set_page_config(layout="wide")
st.title("Picker Requirement Calculator")

# --- Sidebar for Input Parameters ---
st.sidebar.header("Input Parameters")

# Section for Picking & Binning Logic
st.sidebar.subheader("Picking & Binning Parameters")
milk_items_per_order = st.sidebar.number_input("Milk Items per Order", min_value=1, value=1, help="Based on the rule 'at least one milk item will be there'.")
non_milk_items_per_order = st.sidebar.number_input("Non-Milk Items per Order", min_value=0, value=2)
milk_picking_rate_per_hour = st.sidebar.number_input("Milk Picking Rate (Qty/Hour/Picker)", min_value=1, value=1800)
non_milk_pick_time_sec = st.sidebar.number_input("Non-Milk Picking Time (seconds)", min_value=1, value=60)
non_milk_pick_qty = st.sidebar.number_input("Quantity for Non-Milk Picking Time", min_value=1, value=3)
binning_time_per_order = st.sidebar.number_input("Binning Time per Order (seconds)", min_value=1, value=20)

# Section for Shift and Order Volume
st.sidebar.subheader("Shift & Order Volume")
shift_duration_min = st.sidebar.number_input("Shift Duration (minutes)", min_value=30, value=120)
start_orders = st.sidebar.number_input("Start Order Count", min_value=1, value=100, step=50)
end_orders = st.sidebar.number_input("End Order Count", min_value=start_orders, value=2000, step=50)
step = st.sidebar.number_input("Step Size", min_value=1, value=50)


# --- Calculations ---

# 1. Calculate time per item for each category
time_per_milk_item_sec = 3600 / milk_picking_rate_per_hour  # 3600 seconds in an hour

# Avoid division by zero if non_milk_pick_qty is 0
if non_milk_pick_qty > 0:
    time_per_non_milk_item_sec = non_milk_pick_time_sec / non_milk_pick_qty
else:
    time_per_non_milk_item_sec = 0

# 2. Calculate total time per order
total_picking_time_per_order_sec = (milk_items_per_order * time_per_milk_item_sec) + \
                                   (non_milk_items_per_order * time_per_non_milk_item_sec)

total_time_per_order_sec = total_picking_time_per_order_sec + binning_time_per_order
total_time_per_order_min = total_time_per_order_sec / 60

# 3. Calculate how many orders one picker can complete in a shift
# Avoid division by zero if total time is 0
if total_time_per_order_min > 0:
    orders_per_picker_per_shift = shift_duration_min / total_time_per_order_min
else:
    orders_per_picker_per_shift = float('inf') # Theoretically infinite if time is zero

# 4. Generate the data for the table
order_counts = list(range(start_orders, end_orders + 1, step))

data = []
for orders in order_counts:
    # Avoid division by zero
    if orders_per_picker_per_shift > 0:
        pickers_required = orders / orders_per_picker_per_shift
    else:
        pickers_required = 0

    data.append({
        "Orders to Fulfill": orders,
        "Pickers Required (Exact)": round(pickers_required, 2),
        "Pickers Required (Rounded Up)": math.ceil(pickers_required)
    })

df = pd.DataFrame(data)


# --- Display Results ---

st.subheader("Calculation Summary")
col1, col2, col3 = st.columns(3)
abq = milk_items_per_order + non_milk_items_per_order
col1.metric("Average Basket Quantity (ABQ)", f"{abq} items")
col2.metric("Total Time per Order", f"{round(total_time_per_order_sec)} seconds")
col3.metric("Orders per Picker per Shift", f"{round(orders_per_picker_per_shift, 1)}")

st.subheader("Picker Requirement Table")
st.dataframe(df, use_container_width=True)

# --- Excel Export Functionality ---
@st.cache_data
def convert_df_to_excel(df_to_convert):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_to_convert.to_excel(writer, index=False, sheet_name='Picker Requirement')
        # Optional: Auto-adjust column widths
        worksheet = writer.sheets['Picker Requirement']
        for idx, col in enumerate(df_to_convert):
            series = df_to_convert[col]
            max_len = max((series.astype(str).map(len).max(), len(str(series.name)))) + 1
            worksheet.set_column(idx, idx, max_len)
    return output.getvalue()

excel_data = convert_df_to_excel(df)
st.download_button(
    label="📥 Download as Excel",
    data=excel_data,
    file_name="picker_requirement_analysis.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
