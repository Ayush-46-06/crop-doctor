import os
import io
import json
import base64
import requests
import streamlit as st
from pathlib import Path
from PIL import Image

# ---------------------------------------------------------
# Configuration & Paths
# ---------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/api/analyze/")
if "backend:8000" in API_URL and not os.path.exists("/.dockerenv") and not os.getenv("DOCKER_CONTAINER"):
    API_URL = "http://127.0.0.1:8000/api/analyze/"

st.set_page_config(
    page_title="Crop Doctor AI - Detect Plant Diseases",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed",
)

def get_base64_data_uri(file_path: Path) -> str:
    if file_path.exists():
        mime = "image/png" if file_path.suffix.lower() == ".png" else "image/jpeg"
        with open(file_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
            return f"data:{mime};base64,{encoded}"
    return ""

banner_img_uri = get_base64_data_uri(ASSETS_DIR / "banner_tomatoes.jpg")
sample_leaf_uri = get_base64_data_uri(ASSETS_DIR / "sample_leaf.jpg")

case_uris = [
    get_base64_data_uri(ASSETS_DIR / "cases" / f"case{i}.jpg") for i in range(1, 6)
]

# ---------------------------------------------------------
# Session State Initialization (No Result On Start)
# ---------------------------------------------------------
if "selected_crop" not in st.session_state:
    st.session_state.selected_crop = "Tomato"
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None  # None on start so no result shows before upload!
if "displayed_image_uri" not in st.session_state:
    st.session_state.displayed_image_uri = None
if "stats" not in st.session_state:
    st.session_state.stats = {
        "analyzed": 12,
        "tomato_scans": 3,
        "healthy": 9,
        "diseased": 3,
    }

# ---------------------------------------------------------
# Strictly Forced Light Theme CSS & Modern Dashboard Styling
# ---------------------------------------------------------
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Caveat:wght@600;700&display=swap" rel="stylesheet">

<style>
/* 1. Global Reset to Pure Light Theme */
:root {
    color-scheme: light !important;
}

html, body, [class*="css"], .stApp {
    font-family: 'Plus Jakarta Sans', -apple-system, sans-serif !important;
    background-color: #F8FAFB !important;
    color: #1F2937 !important;
    color-scheme: light !important;
}

/* 2. Completely Hide Streamlit Sidebar, Top Header, and Hamburger */
section[data-testid="stSidebar"],
[data-testid="collapsedControl"],
header[data-testid="stHeader"] {
    display: none !important;
}

.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 2.5rem !important;
    padding-left: 3rem !important;
    padding-right: 3rem !important;
    max-width: 1440px !important;
    margin: 0 auto !important;
}

/* 3. Force All Buttons and Inputs to Light Theme (Prevent Dark Button Inversion) */
button,
button[kind="secondary"],
button[kind="primary"],
[data-testid="baseButton-secondary"],
[data-testid="baseButton-primary"],
.stButton > button {
    color-scheme: light !important;
    text-transform: none !important;
}

/* Secondary Buttons: Crisp White, Dark Text, Light Gray Border */
button[kind="secondary"],
[data-testid="baseButton-secondary"],
div.stButton > button:not([kind="primary"]) {
    background-color: #FFFFFF !important;
    color: #1E293B !important;
    border: 1.5px solid #E2E8F0 !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    padding: 0.6rem 1rem !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03) !important;
    transition: all 0.15s ease !important;
}

button[kind="secondary"]:hover,
[data-testid="baseButton-secondary"]:hover,
div.stButton > button:not([kind="primary"]):hover {
    background-color: #F0FDF4 !important;
    border-color: #16A34A !important;
    color: #15803D !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 3px 8px rgba(22, 163, 74, 0.1) !important;
}

/* Primary Button: Deep Forest Green */
button[kind="primary"],
[data-testid="baseButton-primary"],
div.stButton > button[kind="primary"] {
    background-color: #14532D !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    font-size: 0.96rem !important;
    padding: 0.75rem 1.5rem !important;
    box-shadow: 0 4px 14px rgba(20, 83, 45, 0.22) !important;
    transition: all 0.2s ease !important;
}

button[kind="primary"]:hover,
[data-testid="baseButton-primary"]:hover,
div.stButton > button[kind="primary"]:hover {
    background-color: #0F3D20 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 18px rgba(20, 83, 45, 0.3) !important;
}

/* Radio Buttons: Force Pure White Background and Dark Text */
[data-testid="stRadio"] {
    background-color: transparent !important;
}
[data-testid="stRadio"] label,
[data-testid="stRadio"] span,
[data-testid="stRadio"] p {
    color: #1E293B !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
}
div[data-baseweb="radio"] {
    background-color: transparent !important;
}
div[data-baseweb="radio"] div {
    background-color: #FFFFFF !important;
    border-color: #CBD5E1 !important;
}
div[data-baseweb="radio"][aria-checked="true"] div {
    border-color: #16A34A !important;
    background-color: #16A34A !important;
}

/* File Uploader Dropzone: Clean Light Background */
[data-testid="stFileUploader"] section {
    background-color: #F8FAFC !important;
    border: 2px dashed #CBD5E1 !important;
    border-radius: 14px !important;
    padding: 1.4rem !important;
    transition: border-color 0.2s !important;
}
[data-testid="stFileUploader"] section:hover {
    border-color: #16A34A !important;
    background-color: #F0FDF4 !important;
}
[data-testid="stFileUploader"] span,
[data-testid="stFileUploader"] p,
[data-testid="stFileUploader"] small {
    color: #475569 !important;
}
[data-testid="stFileUploader"] button {
    background-color: #FFFFFF !important;
    color: #15803D !important;
    border: 1.5px solid #DCFCE7 !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
}

/* Top Branding Bar */
.brand-top-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1.2rem;
    padding-bottom: 0.8rem;
    border-bottom: 1px solid #EEF2F6;
}
.brand-logo-wrap {
    display: flex;
    align-items: center;
    gap: 12px;
}
.brand-icon-box {
    width: 40px;
    height: 40px;
    background: #EAF7EC;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #15803D;
    font-size: 1.3rem;
}
.brand-header-text h2 {
    font-size: 1.4rem;
    font-weight: 800;
    color: #111827;
    margin: 0;
    line-height: 1.15;
}
.brand-header-text h2 span {
    color: #16A34A;
}
.brand-header-text p {
    font-size: 0.8rem;
    color: #64748B;
    margin: 0;
    font-weight: 500;
}
.brand-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #F0FDF4;
    border: 1px solid #DCFCE7;
    color: #166534;
    padding: 6px 14px;
    border-radius: 9999px;
    font-size: 0.78rem;
    font-weight: 700;
}

/* Hero Banner */
.hero-banner {
    position: relative;
    border-radius: 20px;
    overflow: hidden;
    margin-bottom: 1.4rem;
    box-shadow: 0 4px 20px rgba(20, 83, 45, 0.12);
    display: flex;
    min-height: 190px;
    background-color: #0F3D20;
}
.hero-bg-img {
    position: absolute;
    right: 0;
    top: 0;
    bottom: 0;
    width: 65%;
    object-fit: cover;
    object-position: right center;
}
.hero-overlay {
    position: absolute;
    inset: 0;
    background: linear-gradient(90deg, #0D351B 0%, #134826 42%, rgba(19, 72, 38, 0.72) 70%, rgba(19, 72, 38, 0.2) 100%);
    z-index: 1;
}
.hero-content {
    position: relative;
    z-index: 2;
    padding: 1.8rem 2.2rem;
    max-width: 650px;
    color: white;
}
.hero-title {
    font-size: 1.85rem;
    font-weight: 800;
    color: #FFFFFF;
    margin: 0 0 0.35rem 0;
    letter-spacing: -0.02em;
}
.hero-title span {
    color: #4ADE80;
}
.hero-subtitle {
    font-size: 0.95rem;
    color: #D1FAE5;
    margin: 0 0 1.2rem 0;
    font-weight: 500;
}
.workflow-pills {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
}
.workflow-step {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 12px;
    border-radius: 9999px;
    background: rgba(255, 255, 255, 0.12);
    backdrop-filter: blur(4px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    font-size: 0.75rem;
    font-weight: 600;
    color: #FFFFFF;
}
.workflow-step svg {
    color: #4ADE80;
}
.workflow-arrow {
    color: rgba(255, 255, 255, 0.5);
    font-size: 0.75rem;
}
.hero-sticker {
    position: absolute;
    right: 2.2rem;
    bottom: 1.4rem;
    z-index: 2;
    font-family: 'Caveat', cursive;
    color: #FFFFFF;
    font-size: 1.4rem;
    font-weight: 700;
    text-shadow: 0 2px 8px rgba(0,0,0,0.4);
    transform: rotate(-3deg);
}

/* Metric Cards Row */
.metric-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1.1rem;
    margin-bottom: 1.5rem;
}
.metric-card {
    background: #FFFFFF;
    border: 1px solid #EEF2F6;
    border-radius: 16px;
    padding: 1.1rem 1.2rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 2px 8px rgba(0,0,0,0.02);
}
.metric-left {
    display: flex;
    align-items: center;
    gap: 14px;
}
.metric-icon-wrap {
    width: 44px;
    height: 44px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.25rem;
}
.icon-green { background: #EAF7EC; color: #16A34A; }
.icon-coral { background: #FEE2E2; color: #EF4444; }
.metric-value {
    font-size: 1.55rem;
    font-weight: 800;
    color: #0F172A;
    line-height: 1.1;
}
.metric-label {
    font-size: 0.78rem;
    color: #64748B;
    font-weight: 600;
}
.mini-bars {
    display: flex;
    align-items: flex-end;
    gap: 3px;
    height: 26px;
}
.bar-green { background: #A7F3D0; width: 4px; border-radius: 2px; }
.bar-green.high { background: #10B981; }
.bar-coral { background: #FECACA; width: 4px; border-radius: 2px; }
.bar-coral.high { background: #EF4444; }

/* Panels Styling */
.main-panel-card {
    background: #FFFFFF;
    border: 1px solid #EEF2F6;
    border-radius: 18px;
    padding: 1.5rem;
    box-shadow: 0 2px 10px rgba(0,0,0,0.03);
    height: 100%;
}
.panel-title {
    font-size: 1.15rem;
    font-weight: 800;
    color: #111827;
    margin: 0;
}
.panel-desc {
    font-size: 0.82rem;
    color: #64748B;
    margin-bottom: 1.1rem;
}

/* Stepper Indicator */
.stepper-wrap {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 1.2rem;
}
.step-pill {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.78rem;
    font-weight: 600;
    color: #94A3B8;
}
.step-pill.active {
    color: #0F172A;
}
.step-num {
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: #E2E8F0;
    color: #64748B;
    font-size: 0.72rem;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
}
.step-pill.active .step-num {
    background: #14532D;
    color: white;
}
.step-line {
    flex: 1;
    height: 1px;
    background: #E2E8F0;
    max-width: 40px;
}

/* Crop Selection Label */
.crop-select-label {
    font-size: 0.82rem;
    font-weight: 700;
    color: #334155;
    margin-bottom: 0.6rem;
}

/* Empty State Card (Before User Analyzes) */
.empty-state-box {
    border: 2px dashed #E2E8F0;
    background: #FAFBFB;
    border-radius: 16px;
    padding: 3.5rem 2rem;
    text-align: center;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 480px;
}
.empty-icon-circle {
    width: 64px;
    height: 64px;
    border-radius: 50%;
    background: #F0FDF4;
    border: 1px solid #DCFCE7;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2rem;
    margin-bottom: 1rem;
    box-shadow: 0 4px 12px rgba(22, 163, 74, 0.1);
}
.empty-title {
    font-size: 1.15rem;
    font-weight: 800;
    color: #0F172A;
    margin-bottom: 0.4rem;
}
.empty-desc {
    font-size: 0.85rem;
    color: #64748B;
    max-width: 360px;
    line-height: 1.45;
    margin-bottom: 1.4rem;
}
.empty-features {
    display: flex;
    flex-direction: column;
    gap: 8px;
    text-align: left;
    background: #FFFFFF;
    border: 1px solid #EEF2F6;
    border-radius: 12px;
    padding: 1rem 1.4rem;
    width: 100%;
    max-width: 360px;
}
.empty-feature-item {
    font-size: 0.78rem;
    color: #334155;
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
}

/* Result Section Styles (After Analysis) */
.result-top-grid {
    display: grid;
    grid-template-columns: 160px 1fr;
    gap: 1.2rem;
    margin-bottom: 1.2rem;
}
.result-leaf-img {
    width: 160px;
    height: 160px;
    border-radius: 14px;
    object-fit: cover;
    border: 1px solid #E2E8F0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.disease-badge-card {
    border-radius: 14px;
    padding: 1rem 1.2rem;
    display: flex;
    flex-direction: column;
    justify-content: center;
    border: 1px solid transparent;
}
.disease-badge-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.4rem;
}
.disease-tag-wrap {
    display: flex;
    align-items: center;
    gap: 8px;
}
.disease-icon-circle {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.1rem;
}
.disease-tag {
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.confidence-box {
    text-align: right;
}
.confidence-lbl {
    font-size: 0.68rem;
    color: #64748B;
    font-weight: 600;
}
.confidence-pct {
    font-size: 1.5rem;
    font-weight: 800;
    line-height: 1;
}
.disease-name {
    font-size: 1.35rem;
    font-weight: 800;
    color: #0F172A;
    margin: 0;
}
.scientific-name {
    font-size: 0.78rem;
    color: #64748B;
    font-style: italic;
    margin-bottom: 0.5rem;
}
.disease-desc {
    font-size: 0.8rem;
    color: #475569;
    line-height: 1.4;
    margin: 0;
}

/* Details Cards (Symptoms & Prevention) */
.detail-cards-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
    margin-bottom: 1.2rem;
}
.symptoms-card {
    background: #FFFBEB;
    border: 1px solid #FEF3C7;
    border-radius: 14px;
    padding: 1rem;
}
.prevention-card {
    background: #F0FDF4;
    border: 1px solid #DCFCE7;
    border-radius: 14px;
    padding: 1rem;
}
.detail-card-head {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 0.6rem;
}
.symptoms-title {
    font-size: 0.88rem;
    font-weight: 800;
    color: #92400E;
    margin: 0;
}
.prevention-title {
    font-size: 0.88rem;
    font-weight: 800;
    color: #166534;
    margin: 0;
}
.detail-list {
    list-style: none;
    padding: 0;
    margin: 0;
}
.detail-list li {
    font-size: 0.76rem;
    color: #334155;
    margin-bottom: 5px;
    display: flex;
    align-items: flex-start;
    gap: 7px;
    line-height: 1.3;
}
.dot-amber {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #F59E0B;
    margin-top: 5px;
    flex-shrink: 0;
}
.check-green {
    width: 14px;
    height: 14px;
    color: #16A34A;
    flex-shrink: 0;
    margin-top: 1px;
}

/* Similar Cases & Learning Resource */
.bottom-result-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
    align-items: stretch;
}
.cases-card {
    background: #FFFFFF;
}
.cases-title {
    font-size: 0.82rem;
    font-weight: 700;
    color: #1E293B;
    margin-bottom: 0.5rem;
}
.cases-gallery {
    display: flex;
    gap: 8px;
}
.case-thumb {
    width: 48px;
    height: 48px;
    border-radius: 8px;
    object-fit: cover;
    border: 1px solid #E2E8F0;
    transition: transform 0.2s;
    cursor: pointer;
}
.case-thumb:hover {
    transform: scale(1.1);
    box-shadow: 0 4px 10px rgba(0,0,0,0.12);
}

.resource-card {
    background: #F5F3FF;
    border: 1px solid #EDE9FE;
    border-radius: 12px;
    padding: 0.75rem 1rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    cursor: pointer;
    text-decoration: none;
    transition: all 0.2s;
}
.resource-card:hover {
    background: #EDE9FE;
}
.resource-left {
    display: flex;
    align-items: center;
    gap: 10px;
}
.resource-icon {
    width: 32px;
    height: 32px;
    border-radius: 8px;
    background: #DDD6FE;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1rem;
    color: #6D28D9;
}
.resource-title {
    font-size: 0.8rem;
    font-weight: 700;
    color: #4C1D95;
    margin: 0;
}
.resource-sub {
    font-size: 0.7rem;
    color: #6D28D9;
    margin: 0;
    line-height: 1.2;
}
.resource-arrow {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    background: #FFFFFF;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #6D28D9;
    font-size: 0.8rem;
    font-weight: 700;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Clean Top Brand Header (Replaces Sidebar & Class 7 Search)
# ---------------------------------------------------------
st.markdown("""
<div class="brand-top-bar">
    <div class="brand-logo-wrap">
        <div class="brand-icon-box">🌿</div>
        <div class="brand-header-text">
            <h2>Crop Doctor <span>AI</span></h2>
            <p>Intelligent Agricultural Vision Diagnostic Platform</p>
        </div>
    </div>
    # <div class="brand-badge">
    #     <span>⚡</span> Powered by Groq Multimodal Vision
    # </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Hero Banner
# ---------------------------------------------------------
st.markdown(f"""
<div class="hero-banner">
    <img class="hero-bg-img" src="{banner_img_uri}" alt="Tomatoes">
    <div class="hero-overlay"></div>
    <div class="hero-content">
        <h1 class="hero-title">Crop Doctor <span>AI</span></h1>
        <p class="hero-subtitle">Detect crop diseases instantly with AI</p>
        <div class="workflow-pills">
            <span class="workflow-step">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
                Upload Image
            </span>
            <span class="workflow-arrow">></span>
            <span class="workflow-step">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>
                AI Analysis
            </span>
            <span class="workflow-arrow">></span>
            <span class="workflow-step">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
                Get Results
            </span>
            <span class="workflow-arrow">></span>
            <span class="workflow-step">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/></svg>
                Care Advice
            </span>
        </div>
    </div>
    <div class="hero-sticker">Healthy Crops, Happier Tomorrow! 🌿</div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Statistics Cards Row
# ---------------------------------------------------------
stats = st.session_state.stats
# st.markdown(f"""
<div class="metric-grid">
    <div class="metric-card">
        <div class="metric-left">
            <div class="metric-icon-wrap icon-green">🌱</div>
            <div>
                <div class="metric-value">{stats['analyzed']}</div>
                <div class="metric-label">Images Analyzed</div>
            </div>
        </div>
        <div class="mini-bars">
            <div class="bar-green" style="height: 40%;"></div>
            <div class="bar-green" style="height: 65%;"></div>
            <div class="bar-green" style="height: 50%;"></div>
            <div class="bar-green high" style="height: 90%;"></div>
        </div>
    </div>
    <div class="metric-card">
        <div class="metric-left">
            <div class="metric-icon-wrap icon-coral">🍅</div>
            <div>
                <div class="metric-value">{stats['tomato_scans']}</div>
                <div class="metric-label">Tomato Scans</div>
            </div>
        </div>
        <div class="mini-bars">
            <div class="bar-coral" style="height: 30%;"></div>
            <div class="bar-coral" style="height: 70%;"></div>
            <div class="bar-coral" style="height: 45%;"></div>
            <div class="bar-coral high" style="height: 85%;"></div>
        </div>
    </div>
    <div class="metric-card">
        <div class="metric-left">
            <div class="metric-icon-wrap icon-green">📋</div>
            <div>
                <div class="metric-value">{stats['healthy']}</div>
                <div class="metric-label">Healthy Plants</div>
            </div>
        </div>
        <div class="mini-bars">
            <div class="bar-green" style="height: 55%;"></div>
            <div class="bar-green" style="height: 75%;"></div>
            <div class="bar-green" style="height: 60%;"></div>
            <div class="bar-green high" style="height: 100%;"></div>
        </div>
    </div>
    <div class="metric-card">
        <div class="metric-left">
            <div class="metric-icon-wrap icon-coral">🐞</div>
            <div>
                <div class="metric-value">{stats['diseased']}</div>
                <div class="metric-label">Diseased Plants</div>
            </div>
        </div>
        <div class="mini-bars">
            <div class="bar-coral" style="height: 40%;"></div>
            <div class="bar-coral" style="height: 60%;"></div>
            <div class="bar-coral" style="height: 50%;"></div>
            <div class="bar-coral high" style="height: 80%;"></div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Main Two Columns: Left (Analyze) & Right (Result)
# ---------------------------------------------------------
col_left, col_right = st.columns([1, 1], gap="large")

# =========================================================
# LEFT COLUMN: Analyze Crop Image
# =========================================================
with col_left:
    st.markdown("""
    <div class="main-panel-card">
        <h3 class="panel-title">Analyze Crop Image</h3>
        <p class="panel-desc">Upload a clear image of a crop leaf to detect diseases.</p>
        <div class="stepper-wrap">
            <div class="step-pill active">
                <div class="step-num">1</div>
                <span>Upload Image</span>
            </div>
            <div class="step-line"></div>
            <div class="step-pill">
                <div class="step-num">2</div>
                <span>Select Crop</span>
            </div>
            <div class="step-line"></div>
            <div class="step-pill">
                <div class="step-num">3</div>
                <span>Analyze</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    input_mode = st.radio(
        "Upload Mode",
        ["📁 Upload File", "📷 Camera Capture", "✨ Try Sample Early Blight Leaf"],
        horizontal=True,
        label_visibility="collapsed",
    )

    uploaded_file = None
    if input_mode == "📁 Upload File":
        uploaded_file = st.file_uploader(
            "Choose a JPG or PNG leaf image",
            type=["jpg", "jpeg", "png"],
            help="Supports JPG, PNG up to 5MB",
            label_visibility="collapsed",
            key="file_uploader_input",
        )
    elif input_mode == "📷 Camera Capture":
        uploaded_file = st.camera_input("Take photo of leaf", label_visibility="collapsed", key="camera_input")
    else:
        sample_path = ASSETS_DIR / "sample_leaf.jpg"
        if sample_path.exists():
            uploaded_file = io.BytesIO(sample_path.read_bytes())
            uploaded_file.name = "sample_tomato_early_blight.jpg"
            uploaded_file.type = "image/jpeg"
            st.info("Loaded sample tomato early blight leaf. Click **Analyze Crop Image** below to test.")

    # Crop Selection
    st.markdown('<div class="crop-select-label">Select Crop</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("🍅 Tomato", key="btn_crop_tomato", use_container_width=True, type="primary" if st.session_state.selected_crop == "Tomato" else "secondary"):
            st.session_state.selected_crop = "Tomato"
            st.rerun()
    with c2:
        if st.button("🥔 Potato", key="btn_crop_potato", use_container_width=True, type="primary" if st.session_state.selected_crop == "Potato" else "secondary"):
            st.session_state.selected_crop = "Potato"
            st.rerun()
    with c3:
        if st.button("🌽 Maize", key="btn_crop_maize", use_container_width=True, type="primary" if st.session_state.selected_crop == "Maize" else "secondary"):
            st.session_state.selected_crop = "Maize"
            st.rerun()
    with c4:
        if st.button("🌿 Other", key="btn_crop_other", use_container_width=True, type="primary" if st.session_state.selected_crop == "Other" else "secondary"):
            st.session_state.selected_crop = "Other"
            st.rerun()

    if uploaded_file is not None:
        try:
            st.image(uploaded_file, caption="Leaf Selected for Analysis", width=160)
        except Exception:
            pass

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # Action Trigger
    analyze_clicked = st.button("✨ Analyze Crop Image", type="primary", use_container_width=True)

    if analyze_clicked:
        if uploaded_file is None:
            st.warning("Please upload a leaf image, snap a photo, or choose 'Try Sample Early Blight Leaf'.")
        else:
            with st.spinner("Inspecting leaf symptoms with Groq AI..."):
                try:
                    file_bytes = uploaded_file.getvalue() if hasattr(uploaded_file, "getvalue") else uploaded_file.read()
                    mime_type = getattr(uploaded_file, "type", "image/jpeg") or "image/jpeg"
                    crop_key = st.session_state.selected_crop.lower()

                    # Save displayed base64 image
                    b64_img = base64.b64encode(file_bytes).decode("utf-8")
                    st.session_state.displayed_image_uri = f"data:{mime_type};base64,{b64_img}"

                    # Post to Django API
                    response = requests.post(
                        API_URL,
                        files={"image": (uploaded_file.name, file_bytes, mime_type)},
                        data={"crop": crop_key},
                        timeout=90,
                    )

                    if response.ok:
                        data = response.json()
                        st.session_state.analysis_result = data
                        st.session_state.stats["analyzed"] += 1
                        if crop_key == "tomato":
                            st.session_state.stats["tomato_scans"] += 1
                        if data.get("disease_detected"):
                            st.session_state.stats["diseased"] += 1
                        else:
                            st.session_state.stats["healthy"] += 1
                        st.rerun()
                    else:
                        err_text = response.text
                        try:
                            err_text = response.json().get("error", err_text)
                        except Exception:
                            pass
                        st.error(f"Backend analysis error: {err_text}")
                except requests.exceptions.ConnectionError:
                    st.error(f"Cannot connect to diagnostic API at `{API_URL}`. Ensure backend is running.")
                except Exception as ex:
                    st.error(f"Error during analysis: {ex}")

    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# RIGHT COLUMN: Result Card (Only Shows After Image is Put & Analyzed)
# =========================================================
with col_right:
    res = st.session_state.analysis_result
    leaf_uri = st.session_state.displayed_image_uri

    # If no analysis has been run yet: Show clean empty state!
    if res is None or leaf_uri is None:
        st.markdown("""
        <div class="main-panel-card">
            <h3 class="panel-title">Result</h3>
            <p class="panel-desc">Diagnostic report, confidence score, and care advice will appear here.</p>
            <div class="empty-state-box">
                <div class="empty-icon-circle">🍃</div>
                <div class="empty-title">Awaiting Crop Leaf Image</div>
                <p class="empty-desc">
                    Upload or take a photo of a crop leaf on the left, then click <strong>Analyze Crop Image</strong> to generate an instant diagnosis.
                </p>
                <div class="empty-features">
                    <div class="empty-feature-item">
                        <span style="color:#16A34A;">✓</span> Multimodal visual leaf disease detection
                    </div>
                    <div class="empty-feature-item">
                        <span style="color:#16A34A;">✓</span> Specific pathogen & scientific classification
                    </div>
                    <div class="empty-feature-item">
                        <span style="color:#16A34A;">✓</span> Concentric spot & chlorosis symptom breakdown
                    </div>
                    <div class="empty-feature-item">
                        <span style="color:#16A34A;">✓</span> Actionable non-chemical care & prevention tips
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Full diagnostic report shown ONLY after user uploaded & analyzed!
        header_col1, header_col2 = st.columns([1, 1])
        with header_col1:
            st.markdown('<h3 class="panel-title" style="margin-top: 6px;">Result</h3>', unsafe_allow_html=True)
        with header_col2:
            if st.button("🔄 New Analysis", key="btn_reset_analysis", use_container_width=False):
                st.session_state.analysis_result = None
                st.session_state.displayed_image_uri = None
                st.rerun()

        disease_name = res.get("possible_issue", "Early Blight")
        scientific = res.get("scientific_name", "")
        confidence = res.get("confidence_score", 87)
        explanation = res.get("explanation", "The leaf shows dark brown spots with yellowing around the edges, which are common symptoms of Early Blight in tomato plants.")
        symptoms = res.get("observed_symptoms", [])
        prevention = res.get("prevention_tips", [])

        is_healthy = res.get("health_status") == "Appears healthy"
        badge_tag = "HEALTHY PLANT" if is_healthy else "DISEASE DETECTED"
        badge_bg = "#F0FDF4" if is_healthy else "#FEF2F2"
        badge_border = "#DCFCE7" if is_healthy else "#FEE2E2"
        badge_color = "#16A34A" if is_healthy else "#DC2626"
        badge_icon = "🟢" if is_healthy else "🐞"
        scientific_html = f'<div class="scientific-name">({scientific})</div>' if scientific and scientific != "N/A" else ""

        # Top Section: Leaf Image & Disease Card
        st.markdown(f"""
        <div class="result-top-grid">
            <img class="result-leaf-img" src="{leaf_uri}" alt="Crop Leaf">
            <div class="disease-badge-card" style="background:{badge_bg}; border-color:{badge_border};">
                <div class="disease-badge-header">
                    <div class="disease-tag-wrap">
                        <div class="disease-icon-circle" style="background:{badge_border};">{badge_icon}</div>
                        <span class="disease-tag" style="color:{badge_color};">{badge_tag}</span>
                    </div>
                    <div class="confidence-box">
                        <div class="confidence-lbl">Confidence</div>
                        <div class="confidence-pct" style="color:{badge_color};">{confidence}%</div>
                    </div>
                </div>
                <h4 class="disease-name">{disease_name}</h4>
                {scientific_html}
                <p class="disease-desc">{explanation}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Middle Section: Symptoms & Prevention Cards
        symptoms_html = "".join([f'<li><div class="dot-amber"></div><span>{s}</span></li>' for s in symptoms[:5]])
        prevention_html = "".join([
            f'<li><svg class="check-green" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg><span>{p}</span></li>'
            for p in prevention[:5]
        ])

        st.markdown(f"""
        <div class="detail-cards-grid">
            <div class="symptoms-card">
                <div class="detail-card-head">
                    <span style="font-size: 1.1rem;">⚠️</span>
                    <h5 class="symptoms-title">Symptoms</h5>
                </div>
                <ul class="detail-list">
                    {symptoms_html}
                </ul>
            </div>
            <div class="prevention-card">
                <div class="detail-card-head">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#16A34A" stroke-width="2.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                    <h5 class="prevention-title">Prevention & Care</h5>
                </div>
                <ul class="detail-list">
                    {prevention_html}
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Bottom Section: Similar Cases & Learning Resource
        cases_html = "".join([f'<img class="case-thumb" src="{uri}" alt="Case">' for uri in case_uris if uri])

        st.markdown(f"""
        <div class="bottom-result-grid">
            <div class="cases-card">
                <div class="cases-title">Similar Cases</div>
                <div class="cases-gallery">
                    {cases_html}
                </div>
            </div>
            <a class="resource-card" href="https://en.wikipedia.org/wiki/{disease_name.replace(' ', '_')}" target="_blank">
                <div class="resource-left">
                    <div class="resource-icon">📖</div>
                    <div>
                        <div class="resource-title">Learning Resource</div>
                        <div class="resource-sub">Learn more about {disease_name}, its biology and management.</div>
                    </div>
                </div>
                <div class="resource-arrow">→</div>
            </a>
        </div>
        """, unsafe_allow_html=True)
