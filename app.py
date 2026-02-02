import streamlit as st
import pandas as pd
import datetime
import os

# --- 1. SETUP & CONFIGURATION ---
DB_FILE = "system_status.csv"

# ตรวจสอบว่ามีไฟล์ฐานข้อมูลจำลองหรือไม่ ถ้าไม่มีให้สร้างใหม่
if not os.path.exists(DB_FILE):
    df = pd.DataFrame(columns=["timestamp", "moisture_level", "pump_status"])
    df.to_csv(DB_FILE, index=False)

def load_data():
    return pd.read_csv(DB_FILE)

def update_status(moisture, pump):
    new_data = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "moisture_level": moisture,
        "pump_status": "ON" if pump else "OFF"
    }
    df = pd.concat([load_data(), pd.DataFrame([new_data])], ignore_index=True)
    # เก็บข้อมูลแค่ 20 รายการล่าสุดเพื่อความรวดเร็ว
    df.tail(20).to_csv(DB_FILE, index=False)

# --- 2. USER INTERFACE ---
st.set_page_config(page_title="Smart Greenhouse Control", page_icon="🌱")

st.title("🌱 ระบบโรงเรือนอัจฉริยะ (Smart Greenhouse)")
st.write("โครงการเกษตรวิทยาลัย - ระบบควบคุมความชื้นอัตโนมัติ")

# Sidebar: ควบคุมการตั้งค่า
st.sidebar.header("⚙️ การตั้งค่าระบบ")
threshold = st.sidebar.slider("กำหนดค่าความชื้นที่ต้องรดน้ำ (%)", 0, 100, 30)

# จำลองค่าจากเซ็นเซอร์ (ในสถานการณ์จริงจะอ่านค่าจาก API/MQTT)
st.subheader("📊 สถานะปัจจุบัน")
col1, col2 = st.columns(2)

# ดึงข้อมูลล่าสุด
df_history = load_data()
current_moisture = 45 # ค่าจำลอง (Simulation)
if not df_history.empty:
    last_status = df_history.iloc[-1]["pump_status"]
else:
    last_status = "OFF"

with col1:
    st.metric(label="ความชื้นในดิน", value=f"{current_moisture}%")
with col2:
    st.metric(label="สถานะปั๊มน้ำ", value=last_status)

# --- 3. LOGIC CONTROL ---
st.divider()
st.subheader("🕹️ แผงควบคุม (Manual Override)")

if st.button("สั่งเปิดปั๊มน้ำด้วยตนเอง"):
    update_status(current_moisture, True)
    st.success("กำลังเปิดปั๊มน้ำ...")
    st.rerun()

if st.button("สั่งปิดปั๊มน้ำ"):
    update_status(current_moisture, False)
    st.warning("ปิดปั๊มน้ำแล้ว")
    st.rerun()

# แสดงประวัติการทำงาน
st.divider()
st.subheader("📜 ประวัติการทำงาน (Logs)")
st.dataframe(df_history.sort_index(ascending=False), use_container_width=True)

# อัตโนมัติ: ถ้าความชื้นต่ำกว่าค่าที่กำหนด
if current_moisture < threshold:
    st.error(f"⚠️ คำเตือน: ความชื้นต่ำกว่า {threshold}% ระบบกำลังทำงานอัตโนมัติ")