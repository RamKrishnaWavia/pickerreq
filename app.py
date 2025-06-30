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
st.sidebar.subheader("Order & Timing Parameters")
items_per_basket = st.sidebar.number_input(
    "Items per Basket (ABQ)", min_value=1, value=3,
    help="The total number of items in a standard order basket. Your logic specifies 1 milk + 2 non-milk."
)
picking_time_per_basket_sec = st.sidebar.number_input(
    "Picking Time for a Full Basket (seconds)", min_value=1, value=60,
    help="Based on your logic: '1 picker can pick 3 units in 60 seconds'."
)
binning_time_per_order_sec = st.sidebar.number_input(
    "Binning Time per Order (seconds)", min_value=0, value=20,
    help="Additional time for sorting and binning after all items are picked. Set to 0 if included in picking time."
)

# Section for Shift and Order Volume
st.sidebar.subheader("Shift & Order Volume")
shift_duration_min = st.sidebar.number_input("Shift Duration (minutes)", min_value=30, value=120)
start_orders = st.sidebar.number_input("Start Order Count", min_value=1, value=100, step=50)
end_orders = st.sidebar.number_input("End Order Count", min_value=start_orders, value=2000, step=50)
step = st.sidebar.number_input("Step Size", min_value=1, value=50)


# --- Calculations ---

# 1. Calculate total time to process one complete order (picking + binning)
total_time_per_order_sec = picking_time_per_basket_sec + binning_time_per_order_sec
total_time_per_order_min = total_time_per_order_sec / 60

# 2. Calculate how many orders one picker can complete in a shift
if total_time_per_order_min > 0:
    orders_per_picker_per_shift = shift_duration_min / total_time_per_order_min
else:
    orders_per_picker_per_shift = float('inf')

# 3. Calculate picker throughput in units per hour for the summary display
if total_time_per_order_sec > 0:
    units_per_picker_per_hour = (items_per_basket / total_time_per_order_sec) * 3600
else:
    units_per_picker_per_hour = 0


# 4. Generate the data for the table
order_counts = list(range(start_orders, end_orders + 1, step))
data = []
for orders in order_counts:
    if orders_per_picker_per_shift > 0:
        pickers_required = orders / orders_per_picker_per_shift
    else:
        pickers_required = 0

    data.append({
        "Orders to Fulfill": orders,
        "Total Units to Pick": orders * items_per_basket,
        "Pickers Required (Exact)": round(pickers_required, 2),
        "Pickers Required (Rounded Up)": math.ceil(pickers_required)
    })

df = pd.DataFrame(data)


# --- Display Results ---

st.subheader("Picker & Order Summary")
st.markdown(
    """
    This summary shows the calculated efficiency of a single picker based on the input parameters.
    - **Total Time per Order**: The full cycle time from starting a pick to finishing the binning.
    - **Orders per Picker**: How many complete orders one person can fulfill in a single shift.
    - **Units per Hour**: The total number of individual items a picker can process in one hour.
    """
)
col1, col2, col3 = st.columns(3)
col1.metric("Total Time per Order", f"{total_time_per_order_sec} sec")
col2.metric("Orders per Picker (in a shift)", f"{round(orders_per_picker_per_shift, 1)}")
col3.metric("Units per Picker (per hour)", f"{round(units_per_picker_per_hour)}")


st.subheader("Picker Requirement Table")
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
    file_name="picker_requirement_analysis.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
