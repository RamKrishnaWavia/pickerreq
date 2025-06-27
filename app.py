import streamlit as st
import pandas as pd
import math
from io import BytesIO

# Streamlit App
st.title("Picker Requirement Calculator")

st.sidebar.header("Input Parameters")
abq = st.sidebar.number_input("Average Basket Quantity (ABQ)", min_value=1, value=4)
picking_time_per_item = st.sidebar.number_input("Picking Time per Item (seconds)", min_value=1, value=20)
binning_time_per_order = st.sidebar.number_input("Binning Time per Order (seconds)", min_value=1, value=20)
shift_duration_min = st.sidebar.number_input("Shift Duration (minutes)", min_value=30, value=120)

start_orders = st.sidebar.number_input("Start Order Count", min_value=1, value=100, step=50)
end_orders = st.sidebar.number_input("End Order Count", min_value=start_orders, value=2000, step=50)
step = st.sidebar.number_input("Step Size", min_value=1, value=50)

# Calculations
total_time_per_order_sec = (abq * picking_time_per_item) + binning_time_per_order
total_time_per_order_min = total_time_per_order_sec / 60
orders_per_picker = shift_duration_min / total_time_per_order_min

order_counts = list(range(start_orders, end_orders + 1, step))

data = []
for orders in order_counts:
    pickers_required = orders / orders_per_picker
    data.append({
        "Orders": orders,
        "Pickers Required (Exact)": round(pickers_required, 2),
        "Pickers Required (Rounded Up)": math.ceil(pickers_required)
    })

df = pd.DataFrame(data)

st.subheader("Picker Requirement Table")
st.dataframe(df, use_container_width=True)

# Excel Export
def convert_df_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Picker Requirement')
    return output.getvalue()

excel_data = convert_df_to_excel(df)
st.download_button(
    label="📥 Download Excel",
    data=excel_data,
    file_name="picker_requirement.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
