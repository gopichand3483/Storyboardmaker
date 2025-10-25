# This version hardcodes the API key for troubleshooting ease.
# FOR REAL APPS, USE ENVIRONMENT VARIABLES!
import streamlit as st
import io 
import base64 
import os 
from openai import OpenAI
from openai import APIError 
import time # Import time for better error handling/display

# --- CONFIGURATION: PASTE YOUR KEY HERE ---
# 🚨 IMPORTANT: Replace 'PASTE_YOUR_API_KEY_HERE' with your actual key.
OPENAI_KEY = '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'
# --- END CONFIGURATION ---

# Initialize client only if key is available
client = None
if OPENAI_KEY and OPENAI_KEY != 'PASTE_YOUR_API_KEY_HERE':
    client = OpenAI(api_key=OPENAI_KEY) 
    model_name = "dall-e-3" 
else:
    # If key is missing or is the default placeholder, client remains None.
    model_name = "dall-e-3"

st.set_page_config(layout="wide")
st.title("🎬 AI Storyboard Generator (DALL-E)")
st.markdown("If you see an error below, please check your key in the code.")

# --- CHECK FOR AUTHENTICATION STATUS ---
if not client:
    st.error("""
        🚨 **STOP! API Key Error**
        
        You must replace **'PASTE_YOUR_API_KEY_HERE'** in the Python code
        with your actual OpenAI API key to make this application work.
        
        Go back to your `app.py` file and fix the configuration section.
    """)
    st.stop()
# --- END AUTHENTICATION CHECK ---


# 1. INPUTS
st.sidebar.header("Scene Setup")
base_prompt = st.sidebar.text_area(
    "Core Scene Prompt (for Visual Consistency)",
    "A dark fantasy forest at night, detailed bioluminescent plants, cinematic lighting, style of a concept art painting."
)
num_shots = st.sidebar.slider("Number of Shots (DALL-E 3 Max is 4)", 2, 4, 3) 

# Use columns for a cleaner layout of shots
shot_details = []
st.header("Define Individual Shots")
cols = st.columns(num_shots)

IMAGE_SIZE = "1024x1024"

# Pre-populate some useful details
default_details = [
    "A lonely traveler standing by a twisted ancient tree, looking nervous.",
    "Close up shot of the traveler's lantern illuminating a strange, glowing mushroom.",
    "Wide shot showing the path ahead disappearing into a thick, magical mist.",
    "A sudden movement: a pair of glowing eyes peeking from the shadows."
]

for i in range(num_shots):
    with cols[i]:
        st.subheader(f"Shot {i+1}")
        
        details = st.text_area(
            f"Details for Shot {i+1}",
            key=f"details_{i}",
            height=100,
            value=default_details[i] if i < len(default_details) else "",
            placeholder="Close-up shot of the astronaut's face, tension, sweaty brow..."
        )
        
        angle = st.selectbox(
            f"Camera Angle for Shot {i+1}", 
            ["Medium Shot", "Close Up", "Wide Shot", "High Angle", "Low Angle"],
            key=f"angle_{i}"
        )
        
        shot_details.append({"details": details, "angle": angle})

# --- GENERATION LOGIC ---

if st.button("✨ Generate Storyboard"):
    if not base_prompt or not any(s['details'] for s in shot_details):
        st.error("Please enter a **Core Scene Prompt** and details for at least one shot.")
        st.stop()

    st.subheader("Generated Storyboard")
    
    with st.spinner("Generating Storyboard... This may take a moment for multiple shots."):
        
        output_cols = st.columns(num_shots)
        
        for i, shot in enumerate(shot_details):
            if not shot['details']:
                with output_cols[i]:
                    st.warning(f"Skipping Shot {i+1}: No details provided.")
                continue

            full_prompt = f"A storyboard frame: {shot['details']}, {shot['angle']} view. The entire scene setting is: {base_prompt}. Cinematic, high detail, no text overlays, consistent style."
            
            try:
                # 1. API Call
                response = client.images.generate(
                    model=model_name,
                    prompt=full_prompt,
                    size=IMAGE_SIZE,
                    quality="standard",
                    n=1,
                    response_format="b64_json" 
                )
                
                # 2. Decode and Display
                base64_image = response.data[0].b64_json
                image_data = base64.b64decode(base64_image)

                with output_cols[i]:
                    st.image(image_data, caption=f"Shot {i+1}", use_column_width=True)
                    st.caption(f"**Camera:** {shot['angle']} | **Details:** {shot['details']}")

            except APIError as e:
                with output_cols[i]:
                    st.error(f"OpenAI API Error (Shot {i+1}): {e.message}")
                    st.caption("Check your key, billing status, or model access.")

            except Exception as e:
                with output_cols[i]:
                    st.error(f"General Error (Shot {i+1}): {e}")
