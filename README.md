# 📦 Picker Requirement Calculator (Streamlit App)

This Streamlit app helps calculate the number of warehouse pickers required based on:

- Average Basket Quantity (ABQ)
- Picking time per item
- Binning time per order
- Shift duration (in minutes)
- Order volume range (100 to 2000+)

## 🚀 Features
- Dynamic picker calculation from 100 to 2000+ orders
- Time per item and binning logic configurable
- Export results as Excel file
- Easy to deploy on Streamlit Cloud

## 🧮 Formula Used

**Total Time per Order**  
`(ABQ × picking_time_per_item) + binning_time_per_order`

**Pickers Required**  
`Total Orders ÷ (Shift Time ÷ Total Time per Order)`

## 📦 How to Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
