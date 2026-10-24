import os
import json
import requests
import streamlit as st
from PIL import Image

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/api/analyze/")
# Smart fallback: if backend:8000 was set in .env but running outside Docker on host
if "backend:8000" in API_URL and not os.path.exists("/.dockerenv") and not os.getenv("DOCKER_CONTAINER"):
    API_URL = "http://127.0.0.1:8000/api/analyze/"

st.set_page_config(page_title="Crop Doctor AI", page_icon="🌿", layout="wide")

st.markdown("""
<style>
.stApp { background: linear-gradient(180deg, #f3fbf3 0%, #ffffff 48%); }
.hero { padding: 1.5rem 1.7rem; border-radius: 18px; background: linear-gradient(120deg, #14532d, #15803d); color: white; margin-bottom: 1.2rem; box-shadow: 0 4px 15px rgba(20,83,45,0.15); }
.hero h1 { color: white; margin-bottom: .3rem; font-size: 2.1rem; }
.hero p { color: #e7fbe9; font-size: 1.05rem; margin-bottom: 0; }
.report-card { background: white; padding: 1.2rem 1.5rem; border-radius: 12px; border: 1px solid #e2e8f0; margin-top: 1rem; box-shadow: 0 2px 8px rgba(0,0,0,0.04); }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("🌱 Crop Doctor AI")
    st.caption("AI-Powered Crop Disease Diagnosis & Health Assistant")
    crop = st.selectbox("Select Crop Type", ["Tomato", "Potato", "Maize", "Rice", "Wheat", "Other / Not sure"])
    st.markdown("---")
    st.subheader("📸 Photography Tips")
    st.write("• Take a clear close-up of a single leaf.\n\n• Use natural, bright daylight.\n\n• Keep the leaf in focus.\n\n• Avoid crowded, cluttered backgrounds.")
    st.markdown("---")
    st.caption("Powered by Groq Vision AI + Django + Streamlit")

st.markdown("""
<div class="hero">
<h1>🌿 Crop Doctor AI</h1>
<p>Instant plant disease detection & non-chemical care advice powered by multimodal Vision AI.</p>
</div>
""", unsafe_allow_html=True)

left, right = st.columns([1, 1], gap="large")

with left:
    st.subheader("1. Provide a Leaf Photo")
    input_tab1, input_tab2 = st.tabs(["📁 Upload Image", "📷 Take Photo"])
    
    selected_file = None
    with input_tab1:
        uploaded = st.file_uploader("Choose a JPG or PNG leaf image", type=["jpg", "jpeg", "png"], key="file_upload")
        if uploaded:
            selected_file = uploaded

    with input_tab2:
        camera_photo = st.camera_input("Take a photo with your camera / mobile", key="camera_snap")
        if camera_photo:
            selected_file = camera_photo

    if selected_file:
        try:
            st.image(Image.open(selected_file), caption="Leaf Image for Analysis", use_container_width=True)
        except Exception:
            st.error("Could not preview this image. Please upload a valid image file.")

    analyze = st.button("🔍 Analyze Crop Leaf", type="primary", use_container_width=True, disabled=selected_file is None)

with right:
    st.subheader("2. AI Health Report")
    
    if not (analyze and selected_file):
        st.write("Upload or capture a leaf photo and click **Analyze Crop Leaf** to receive an instant diagnostic report.")
        st.info("ℹ️ Designed for educational crop disease identification and natural crop-care guidance.")
    else:
        with st.spinner("Analyzing leaf with Groq Vision AI..."):
            try:
                crop_payload = crop.lower().replace(" / not sure", "").replace(" ", "_")
                response = requests.post(
                    API_URL,
                    files={"image": (selected_file.name, selected_file.getvalue(), getattr(selected_file, "type", "image/jpeg") or "image/jpeg")},
                    data={"crop": crop_payload},
                    timeout=90,
                )
                if not response.ok:
                    error_msg = response.json().get("error", "The backend service returned an error.") if response.headers.get("content-type", "").startswith("application/json") else response.text
                    st.error(f"Analysis failed: {error_msg}")
                    st.caption("Please check that the backend is running and `GROQ_API_KEY` is configured.")
                else:
                    result = response.json()
                    health = result.get("health_status", "Unclear image")
                    
                    if health == "Appears healthy":
                        st.success(f"### 🟢 Health Status: {health}")
                    elif health == "Possible disease signs":
                        st.error(f"### 🔴 Health Status: {health}")
                    else:
                        st.warning(f"### 🟡 Health Status: {health}")

                    st.markdown(f"**Image Assessment:** {result.get('image_assessment', 'Not available')}")
                    st.markdown(f"**Possible Issue:** `{result.get('possible_issue', 'Not determined')}`")
                    st.markdown(f"**Explanation:** {result.get('explanation', 'Not available')}")

                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown("#### 🔎 Observed Symptoms")
                        for item in result.get("observed_symptoms", []):
                            st.markdown(f"- {item}")
                    with c2:
                        st.markdown("#### 🌱 Safe Prevention Tips")
                        for item in result.get("prevention_tips", []):
                            st.markdown(f"- {item}")

                    st.markdown("#### ✅ Recommended Next Steps")
                    for item in result.get("next_steps", []):
                        st.markdown(f"- {item}")

                    st.warning(f"⚠️ {result.get('disclaimer', 'Educational observation only. Consult local agriculture experts before applying treatments.')}")

                    st.download_button(
                        "📥 Download Full Report (JSON)",
                        data=json.dumps(result, indent=2, ensure_ascii=False),
                        file_name=f"crop_doctor_report_{crop_payload}.json",
                        mime="application/json",
                        use_container_width=True,
                    )
            except requests.exceptions.ConnectionError:
                st.error(f"Cannot connect to the diagnostic API at `{API_URL}`. Ensure backend service is running.")
            except requests.exceptions.Timeout:
                st.error("Analysis request timed out. Please try again.")
            except Exception as exc:
                st.error(f"Unexpected error occurred: {exc}")

st.markdown("---")
st.caption("Responsible Use Notice: Crop Doctor AI provides educational observations based on visual patterns. Do not apply chemical pesticides based solely on this result. Always seek confirmation from a certified agronomist or local agricultural extension office.")
