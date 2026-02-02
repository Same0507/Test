import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- 1. การเตรียมข้อมูล (Simulation / Persistence) ---
# ใช้ @st.cache_data เพื่อให้โหลดข้อมูลครั้งเดียว ไม่ต้องเจนใหม่ทุกครั้งที่กดปุ่ม
@st.cache_data
def generate_mock_data():
    """จำลองข้อมูลการขายย้อนหลัง 2 ปี"""
    np.random.seed(42)
    rows = 2000
    
    # วันที่ย้อนหลัง 2 ปี
    end_date = datetime.today()
    start_date = end_date - timedelta(days=730)
    date_range = pd.date_range(start=start_date, end=end_date, periods=rows)
    
    products = ['เสื้อยืด Oversize', 'กางเกงยีนส์', 'เดรสเกาหลี', 'เสื้อเชิ้ตทำงาน', 'กระเป๋าผ้า']
    ages = ['18-24', '25-34', '35-44', '45+']
    platforms = ['Facebook', 'Shopee']
    
    data = {
        'Date': date_range,
        'Product': np.random.choice(products, rows, p=[0.3, 0.2, 0.2, 0.2, 0.1]),
        'Price': np.random.choice([290, 590, 450, 390, 150], rows),
        'Age_Group': np.random.choice(ages, rows, p=[0.4, 0.3, 0.2, 0.1]),
        'Platform': np.random.choice(platforms, rows),
        'Units': np.random.randint(1, 4, rows)
    }
    
    df = pd.DataFrame(data)
    df['Total_Sales'] = df['Price'] * df['Units']
    df['Month_Year'] = df['Date'].dt.to_period('M').astype(str)
    return df

# โหลดข้อมูล
df = generate_mock_data()

# --- 2. ส่วนติดต่อผู้ใช้ (Streamlit Interface) ---
st.set_page_config(page_title="Fashion Store Analytics", layout="wide")

st.title("🛍️ แดชบอร์ดวิเคราะห์ยอดขายร้านเสื้อผ้า (FB & Shopee)")
st.markdown("---")

# Sidebar: ตัวกรองข้อมูล
st.sidebar.header("ตัวกรองข้อมูล (Filters)")
selected_year = st.sidebar.multiselect(
    "เลือกปี:", 
    options=sorted(df['Date'].dt.year.unique()),
    default=sorted(df['Date'].dt.year.unique())
)

selected_platform = st.sidebar.multiselect(
    "เลือกช่องทางขาย:",
    options=df['Platform'].unique(),
    default=df['Platform'].unique()
)

# กรองข้อมูลตามที่เลือก
filtered_df = df[
    (df['Date'].dt.year.isin(selected_year)) & 
    (df['Platform'].isin(selected_platform))
]

# --- 3. ส่วนแสดงผล (Metrics & Charts) ---

# 3.1 KPI หลัก
col1, col2, col3 = st.columns(3)
total_sales = filtered_df['Total_Sales'].sum()
total_orders = len(filtered_df)
top_product = filtered_df.groupby('Product')['Units'].sum().idxmax()

col1.metric("ยอดขายรวม (บาท)", f"{total_sales:,.0f}")
col2.metric("จำนวนออเดอร์ (รายการ)", f"{total_orders:,.0f}")
col3.metric("สินค้าขายดีที่สุด (จำนวน)", top_product)

st.markdown("---")

# 3.2 กราฟตอบคำถามโจทย์
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.subheader("1. สินค้าขายดีที่สุดในแต่ละเดือน")
    # Group ข้อมูลเพื่อดูยอดขายตามเดือนและสินค้า
    monthly_product = filtered_df.groupby(['Month_Year', 'Product'])['Units'].sum().reset_index()
    fig_line = px.bar(monthly_product, x='Month_Year', y='Units', color='Product', 
                      title='แนวโน้มยอดขายสินค้าตามเดือน', barmode='stack')
    st.plotly_chart(fig_line, use_container_width=True)

with col_chart2:
    st.subheader("2. ลูกค้ากลุ่มอายุใดซื้อบ่อยที่สุด")
    age_counts = filtered_df.groupby('Age_Group')['Total_Sales'].sum().reset_index()
    fig_pie = px.pie(age_counts, values='Total_Sales', names='Age_Group', 
                     title='สัดส่วนยอดขายตามกลุ่มอายุ', hole=0.4)
    st.plotly_chart(fig_pie, use_container_width=True)

# 3.3 Recommendation Section
st.subheader("3. คำแนะนำการจัดโปรโมชั่น (AI Insight)")

# Logic การวิเคราะห์เพื่อแนะนำ
analysis_col1, analysis_col2 = st.columns([2, 1])

with analysis_col1:
    st.info(f"💡 **วิเคราะห์:** จากข้อมูลช่วงที่เลือก พบว่าลูกค้าหลักคือกลุ่ม **{age_counts.iloc[age_counts['Total_Sales'].argmax()]['Age_Group']}**")
    
    # หา Correlation ง่ายๆ ระหว่างสินค้า
    basket = filtered_df.groupby('Product')['Units'].sum().sort_values(ascending=False)
    best_seller = basket.index[0]
    slow_seller = basket.index[-1]
    
    st.success(f"""
    **✅ ข้อเสนอแนะโปรโมชั่น:**
    1. **Bundle Sale:** ควรจัดเซตคู่สินค้าระหว่าง **"{best_seller}"** (ตัวดึงลูกค้า) คู่กับ **"{slow_seller}"** (ตัวระบายสต็อก) เพื่อเพิ่มยอดขายสินค้าที่ออกช้า
    2. **Platform Focus:** หากยอดขาย Shopee ต่ำกว่า Facebook ในเดือนนี้ ควรแจกคูปองเฉพาะ Shopee Live
    3. **Targeted Ad:** ยิงโฆษณาเน้นกลุ่มอายุ {age_counts.iloc[age_counts['Total_Sales'].argmax()]['Age_Group']} โดยใช้รูปภาพสินค้า {best_seller} เป็นตัวนำ
    """)

with analysis_col2:
    st.dataframe(filtered_df[['Date', 'Product', 'Age_Group', 'Total_Sales']].sort_values('Date', ascending=False).head(5),
                 use_container_width=True)
    st.caption("ตัวอย่างข้อมูลล่าสุด 5 รายการ")