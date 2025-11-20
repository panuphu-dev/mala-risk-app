import streamlit as st
import pandas as pd
import numpy as np
import joblib
import os

# ==========================================
# 1. ตั้งค่าหน้าเว็บ (Config)
# ==========================================
st.set_page_config(
    page_title="MALA Risk Calculator",
    page_icon="🩺",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ใส่ CSS ให้สวยงาม (MDCalc Style)
st.markdown("""
    <style>
    .main-header {font-size: 24px; font-weight: bold; color: #2C3E50; margin-bottom: 10px;}
    .sub-text {font-size: 14px; color: #7F8C8D; margin-bottom: 20px;}
    .result-card {padding: 20px; border-radius: 10px; text-align: center; color: white; margin-top: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);}
    .stButton>button {width: 100%; background-color: #007bff; color: white; border-radius: 5px; font-weight: bold; padding: 10px;}
    .stButton>button:hover {background-color: #0056b3;}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. โหลดโมเดล (Load Model)
# ==========================================
@st.cache_resource
def load_model():
    # ชื่อไฟล์โมเดล
    model_path = 'mala_model.pkl'
    
    # เช็คว่ามีไฟล์ไหม
    if os.path.exists(model_path):
        try:
            model = joblib.load(model_path)
            return model
        except Exception as e:
            st.error(f"โหลดโมเดลไม่ได้: {e}")
            return None
    else:
        return None

model = load_model()

# ==========================================
# 3. ส่วนแสดงผล (User Interface)
# ==========================================
st.markdown('<div class="main-header">MALA Risk Score</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-text">Metformin-Associated Lactic Acidosis Prediction Tool</div>', unsafe_allow_html=True)

# แจ้งเตือนถ้าหาไฟล์โมเดลไม่เจอ
if model is None:
    st.warning("⚠️ ไม่พบไฟล์ 'mala_model.pkl' ระบบจะทำงานในโหมดสาธิต (Demo Mode)")

# --- ฟอร์มรับค่า (Input Form) ---
with st.form("risk_form"):
    st.markdown("### Patient Demographics")
    col1, col2 = st.columns(2)
    
    with col1:
        # รับค่าอายุ
        age = st.number_input("Age (years)", min_value=18, max_value=100, value=60)
        # รับค่าน้ำหนัก
        weight = st.number_input("Weight (kg)", min_value=30.0, max_value=200.0, value=70.0)
        
    with col2:
        # รับค่า Creatinine
        creatinine = st.number_input("Serum Creatinine (mg/dL)", min_value=0.1, max_value=20.0, value=1.2, step=0.1)
        # รับค่า eGFR
        egfr = st.number_input("eGFR (mL/min/1.73m²)", min_value=0.0, max_value=200.0, value=60.0)

    st.markdown("### Clinical Factors")
    col3, col4 = st.columns(2)
    
    with col3:
        # รับขนาดยา Metformin
        metformin_dose = st.selectbox("Metformin Daily Dose", 
                                      options=[500, 1000, 1500, 2000, 2500],
                                      index=1, # default ที่ 1000
                                      format_func=lambda x: f"{x} mg")
    with col4:
        # ประวัติ Sepsis
        has_sepsis = st.radio("Sepsis History", options=["No", "Yes"])

    # ปุ่มคำนวณ
    submitted = st.form_submit_button("Calculate Risk Score")

# ==========================================
# 4. คำนวณผล (Calculation)
# ==========================================
if submitted:
    # แปลงค่า Sepsis (Yes=1, No=0)
    sepsis_val = 1 if has_sepsis == "Yes" else 0

    # --- จุดสำคัญที่สุด! จัดเรียงข้อมูลให้ตรงกับตอนเทรนเป๊ะๆ ---
    # ลำดับต้องเป็น: age -> weight -> creatinine -> egfr -> metformin_dose -> sepsis
    input_data = pd.DataFrame([[age, weight, creatinine, egfr, metformin_dose, sepsis_val]], 
                              columns=['age', 'weight', 'creatinine', 'egfr', 'metformin_dose', 'sepsis'])

    risk_percent = 0.0
    
    # ถ้ามีโมเดลจริง ให้ใช้โมเดลคำนวณ
    if model:
        try:
            # predict_proba จะให้ค่า [โอกาสไม่เป็น, โอกาสเป็น] -> เลือกตัวที่ 1
            probability = model.predict_proba(input_data)[0][1]
            risk_percent = probability * 100
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดในการคำนวณ: {e}")
            # ถ้า Error ให้ใช้สูตรสมมติแทนไปก่อนเพื่อไม่ให้เว็บล่ม
            risk_percent = min(99, (creatinine * 10) + (age * 0.2))
    else:
        # ถ้าไม่มีโมเดล (Demo Mode) ใช้สูตรสมมติ
        risk_percent = min(99, (creatinine * 15) + (age * 0.1))
        if has_sepsis == "Yes": risk_percent += 20

    # --- แสดงผลลัพธ์ (Output) ---
    st.markdown("---")
    
    # กำหนดสีตามความเสี่ยง (Traffic Light System)
    if risk_percent < 30:
        bg_color = "#28a745" # เขียว
        risk_level = "LOW RISK"
        advice = "ความเสี่ยงต่ำ: สามารถใช้ยา Metformin ต่อได้ โดยติดตามค่าไตตามระยะ"
    elif risk_percent < 70:
        bg_color = "#ffc107" # เหลือง
        risk_level = "MODERATE RISK"
        advice = "ความเสี่ยงปานกลาง: ควรเฝ้าระวังอาการ หรือพิจารณาลดขนาดยา"
    else:
        bg_color = "#dc3545" # แดง
        risk_level = "HIGH RISK"
        advice = "⚠️ ความเสี่ยงสูง: พิจารณาหยุดยาและตรวจประเมินภาวะ Acidosis ทันที"

    # สร้างการ์ดแสดงผล
    st.markdown(f"""
        <div class="result-card" style="background-color: {bg_color};">
            <h3 style="margin:0;">{risk_level}</h3>
            <h1 style="font-size: 48px; margin: 10px 0;">{risk_percent:.1f}%</h1>
            <p style="margin:0;">Probability of MALA Event</p>
        </div>
    """, unsafe_allow_html=True)

    st.info(f"**คำแนะนำ:** {advice}")
