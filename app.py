import streamlit as st
import pandas as pd
import numpy as np
import joblib
import os

# ==========================================
# 1. ตั้งค่าหน้าเว็บ
# ==========================================
st.set_page_config(
    page_title="MALA Risk Calculator",
    page_icon="🩺",
    layout="centered"
)

# CSS ปรับแต่ง
st.markdown("""
    <style>
    .main-header {font-size: 24px; font-weight: bold; color: #2C3E50; margin-bottom: 10px;}
    .sub-text {font-size: 14px; color: #7F8C8D; margin-bottom: 20px;}
    .result-card {padding: 20px; border-radius: 10px; text-align: center; color: white; margin-top: 20px;}
    .stButton>button {width: 100%; background-color: #007bff; color: white; border-radius: 5px;}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. โหลดโมเดล
# ==========================================
@st.cache_resource
def load_model():
    # พยายามโหลดไฟล์โมเดล
    if os.path.exists('mala_model.pkl'):
        try:
            return joblib.load('mala_model.pkl')
        except Exception as e:
            st.error(f"โหลดโมเดลไม่ได้: {e}")
            return None
    return None

model = load_model()

# ==========================================
# 3. ส่วนแสดงผล
# ==========================================
st.markdown('<div class="main-header">MALA Risk Score</div>', unsafe_allow_html=True)

if model is None:
    st.warning("⚠️ ไม่พบไฟล์โมเดล (mala_model.pkl) ในโฟลเดอร์นี้")
    st.info("ระบบจะใช้โหมดจำลอง (Demo Mode) เพื่อแสดงตัวอย่างการทำงานแทน")

# ฟอร์มรับค่า
with st.form("input_form"):
    col1, col2 = st.columns(2)
    with col1:
        age = st.number_input("Age (ปี)", 18, 100, 60)
        creatinine = st.number_input("Creatinine (mg/dL)", 0.1, 20.0, 1.2)
        weight = st.number_input("Weight (kg)", 30.0, 200.0, 70.0)
    with col2:
        egfr = st.number_input("eGFR", 0.0, 200.0, 60.0)
        metformin = st.selectbox("Metformin Dose (mg)", [500, 1000, 1500, 2000, 2500])
        sepsis = st.selectbox("Sepsis History", ["No", "Yes"])
    
    submitted = st.form_submit_button("Calculate Risk")

# คำนวณผลเมื่อกดปุ่ม
if submitted:
    # ถ้ามีโมเดลจริงให้ใช้โมเดลจริง ถ้าไม่มีให้คำนวณหลอกๆ
    if model:
        # เตรียมข้อมูลให้ตรงกับโมเดล (ต้องแก้ชื่อตัวแปรให้ตรงกับตอนเทรน)
        # อันนี้ใส่เป็นตัวอย่างไว้ก่อน
        sepsis_val = 1 if sepsis == "Yes" else 0
        input_data = pd.DataFrame([[age, weight, creatinine, metformin, sepsis_val, egfr]], 
                                columns=['age', 'weight', 'creatinine', 'metformin_dose', 'sepsis', 'egfr'])
        try:
            risk = model.predict_proba(input_data)[0][1] * 100
        except:
            st.error("ชื่อตัวแปรในโมเดลไม่ตรงกับโค้ด (กรุณาเช็คชื่อ column)")
            risk = 0
    else:
        # คำนวณจำลอง (Demo Logic)
        risk = min(99, (creatinine * 10) + (age * 0.2))
        if sepsis == "Yes": risk += 20

    # แสดงผล
    if risk < 30:
        color, level = "#28a745", "Low Risk"
    elif risk < 70:
        color, level = "#ffc107", "Moderate Risk"
    else:
        color, level = "#dc3545", "High Risk"
        
    st.markdown(f"""
        <div class="result-card" style="background-color: {color};">
            <h2>{level}</h2>
            <h1>{risk:.1f}%</h1>
            <p>Probability of MALA</p>
        </div>
    """, unsafe_allow_html=True)