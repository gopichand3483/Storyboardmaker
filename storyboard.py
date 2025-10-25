import streamlit as st
import io
import base64
from openai import OpenAI, APIError

st.set_page_config(layout="wide")
st.title("🎬 AI Storyboard Generator (DALL-E 3)")
st.markdown("Generate cinematic storyboard frames using OpenAI DALL·E 3")

# --- CONFIGURATION ---
# Try to get key from Streamlit Secrets
try:
    OPENAI_KEY = st.secrets["OPENAI_API_KEY"]
except Exception:
    OPENAI_KEY = None

if not OPENAI_KEY:
    st.error("""
        🚨 **API Key Missing**

        This app needs your OpenAI API key to work.
        If running locally, create a `.streamlit/secrets.toml` file with:

        ```
        [general]
        OPENAI_API_KEY = "sk-your-key-here"
        ```

        On Streamlit Cloud, go to **Settings → Secrets** and add:
        ```
        OPENAI_API_KEY = sk-your-key-here
        ```
    """)
    st.stop()

# Initialize client
client = OpenAI(api_key=OPENAI_KEY)
model_name = "gpt-image-1"  # safer model alias

# --- SIDEBAR INPUTS ---
st.sidebar.header("Scene Setup")
base_prompt = st.sidebar.text_area(
    "Core Scene Prompt (for Visual Consistency)",
    "A dark fantasy forest at night, detailed bioluminescent plants, cinematic lighting, style of a concept art painting."
)
num_shots = st.sidebar.slider("Number of Shots (DALL-E 3 Max is 4)", 2, 4, 3)

# --- SHOT INPUTS ---
shot_details = []
st.header("Define Individual Shots")
cols = st.columns(num_shots)
IMAGE_SIZE = "1024x1024"

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
        )
        angle = st.selectbox(
            f"Camera Angle for Shot {i+1}",
            ["Medium Shot", "Close Up", "Wide Shot", "High Angle", "Low Angle"],
            key=f"angle_{i}"
        )
        shot_details.append({"details": details, "angle": angle})

# --- GENERATION ---
if st.button("✨ Generate Storyboard"):
    if not base_prompt or not any(s['details'] for s in shot_details):
        st.error("Please enter a **Core Scene Prompt** and at least one shot description.")
        st.stop()

    st.subheader("Generated Storyboard")
    with st.spinner("Generating Storyboard..."):
        output_cols = st.columns(num_shots)

        for i, shot in enumerate(shot_details):
            if not shot['details']:
                with output_cols[i]:
                    st.warning(f"Skipping Shot {i+1}: No details provided.")
                continue

            full_prompt = (
                f"A storyboard frame: {shot['details']}, {shot['angle']} view. "
                f"The entire scene setting is: {base_prompt}. "
                "Cinematic, high detail, no text overlays, consistent style."
            )

            try:
                response = client.images.generate(
                    model=model_name,
                    prompt=full_prompt,
                    size=IMAGE_SIZE,
                    n=1,
                    response_format="b64_json",
                )

                image_data = base64.b64decode(response.data[0].b64_json)

                with output_cols[i]:
                    st.image(image_data, caption=f"Shot {i+1}", use_column_width=True)
                    st.caption(f"**Camera:** {shot['angle']} | **Details:** {shot['details']}")

            except APIError as e:
                with output_cols[i]:
                    st.error(f"OpenAI API Error (Shot {i+1}): {str(e)}")

            except Exception as e:
                with output_cols[i]:
                    st.error(f"General Error (Shot {i+1}): {str(e)}")
