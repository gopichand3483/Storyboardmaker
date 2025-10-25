import streamlit as st
import base64
import io 
import json

# Set page configuration for a wide layout
st.set_page_config(layout="wide")
st.title("🎬 AI Storyboard Generator (Free Tool)")
st.markdown("Generate cinematic storyboard frames using the **Imagen 3.0** model.")

# --- CONFIGURATION & API SETUP (FREE TOOL) ---

# We define the API call logic entirely in a JavaScript function, as required 
# by the environment for tool access.

# Note: The API Key (if needed) and Model URL are handled automatically 
# by the environment when using the dedicated endpoint.

JS_API_CALL_FUNCTION = """
async function generateImage(prompt, size) {
    const apiKey = ""; // API Key is automatically provided by the environment
    const apiUrl = `https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict?key=${apiKey}`;
    
    // Size mapping for Imagen 3.0
    let width = 1024;
    let height = 1024;
    if (size === '1792x1024') {
        width = 1792;
        height = 1024;
    } else if (size === '1024x1792') {
        width = 1024;
        height = 1792;
    }

    const payload = { 
        instances: [{ prompt: prompt }], 
        parameters: { 
            "sampleCount": 1,
            "aspectRatio": `${width}:${height}`
        } 
    };

    try {
        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const result = await response.json();
        
        if (result.predictions && result.predictions.length > 0 && result.predictions[0].bytesBase64Encoded) {
            // Success: return the base64 image data
            return { success: true, data: result.predictions[0].bytesBase64Encoded };
        } else if (result.error) {
            // API returned an error object
            return { success: false, error: result.error.message || 'Unknown API error during generation.' };
        } else {
            // Unexpected response structure
            return { success: false, error: 'Image generation failed with an unexpected response structure.' };
        }

    } catch (e) {
        // Network or fetch error
        return { success: false, error: e.message || 'Network error during API call.' };
    }
}
"""

# Inject the JavaScript function into the Streamlit app
st.components.v1.html(f"<script>{JS_API_CALL_FUNCTION}</script>", height=0, width=0)

# --- SIDEBAR INPUTS ---
st.sidebar.header("Scene Setup")

image_size_option = st.sidebar.selectbox(
    "Select Aspect Ratio (Imagen 3.0)",
    ["1024x1024 (Square)", "1792x1024 (Wide 16:9)", "1024x1792 (Tall 9:16)"],
    index=1 # Defaulting to cinematic wide view
)
base_prompt = st.sidebar.text_area(
    "Core Scene Prompt (for Visual Consistency)",
    "A majestic, bioluminescent forest at night, cinematic studio lighting, highly detailed concept art style."
)
num_shots = st.sidebar.slider("Number of Shots", 1, 4, 3) # Max 4 for layout consistency

# --- SHOT INPUTS ---
shot_details = []
st.header("Define Individual Shots")
cols = st.columns(num_shots)

IMAGE_SIZE = image_size_option.split(" ")[0] 

default_details = [
    "A lonely traveler standing by a twisted ancient tree, looking nervous. Medium shot.",
    "Close up shot of the traveler's hand holding a strange, glowing, iridescent orb.",
    "Wide shot showing the path ahead disappearing into a thick, magical mist, cinematic view.",
    "A sudden movement: a pair of glowing yellow eyes peeking from the shadows. Extreme close up."
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
            ["Medium Shot", "Close Up", "Wide Shot", "High Angle", "Low Angle", "Extreme Close Up"],
            key=f"angle_{i}"
        )
        shot_details.append({"details": details, "angle": angle})

# --- GENERATION ---
if st.button("✨ Generate Storyboard"):
    if not base_prompt or not any(s['details'] for s in shot_details):
        st.error("Please enter a **Core Scene Prompt** and at least one shot description.")
        st.stop()

    st.subheader("Generated Storyboard")
    output_cols = st.columns(num_shots)

    # Use a shared state for loading across all shots
    with st.spinner("Generating Storyboard (This may take up to 30 seconds per image)..."):
        
        # --- Asynchronous JavaScript Execution ---
        
        # 1. Prepare all prompts and sizes in a list
        prompts_to_generate = []
        for shot in shot_details:
            if shot['details']:
                full_prompt = (
                    f"A highly detailed, professional cinematic storyboard sketch in black and white. {shot['details']}, {shot['angle']} view. "
                    f"Scene setting: {base_prompt}. "
                    "Focus on composition and lighting, thin line art, no text overlays, consistent style."
                )
                prompts_to_generate.append({
                    'prompt': full_prompt,
                    'size': IMAGE_SIZE
                })

        # 2. Convert the Python list to a JSON string for JavaScript
        prompts_json = json.dumps(prompts_to_generate)
        
        # 3. Create the JavaScript execution block
        js_execution = f"""
        const prompts = JSON.parse('{prompts_json}');
        const results = [];
        
        for (const p of prompts) {{
            const result = await generateImage(p.prompt, p.size);
            results.push(result);
        }}
        
        // This is the output sent back to Streamlit
        return JSON.stringify(results);
        """
        
        # 4. Execute the JavaScript code and get the results
        try:
            results_json = st.components.v1.html(
                f"<script>{js_execution}</script>", 
                height=1, 
                width=1, 
                scrolling=False,
                key="js_runner"
            )
            
            # The component call returns a string which is the output of the script
            if results_json:
                results = json.loads(results_json)
            else:
                st.error("Error: Could not retrieve results from the JavaScript execution.")
                st.stop()

        except Exception as e:
            st.error(f"Critical execution error: {str(e)}")
            st.stop()

        # --- Display Results ---

        # The results list contains success/failure objects for each attempted shot
        for i, result in enumerate(results):
            shot = shot_details[i] # Get original shot details
            
            # Get the column corresponding to the shot
            with output_cols[i]:
                
                if result['success']:
                    # Image Data Processing
                    image_bytes = base64.b64decode(result['data'])
                    image_data_io = io.BytesIO(image_bytes)
                    
                    st.image(image_data_io, caption=f"Shot {i+1}", use_column_width=True)
                    st.caption(f"**Camera:** {shot['angle']} | **Details:** {shot['details']}")
                    
                else:
                    # Error Display
                    st.error(f"❌ Shot {i+1} Failed: {result['error']}")
                    st.caption(f"**Camera:** {shot['angle']} | **Details:** {shot['details']}")
                    
                # Display the full prompt used for debugging
                full_prompt = (
                    f"A professional cinematic storyboard sketch in black and white. {shot['details']}, {shot['angle']} view. "
                    f"Scene setting: {base_prompt}. "
                    "Focus on composition and lighting, thin line art, no text overlays, consistent style."
                )
                with st.expander("Show Prompt"):
                    st.code(full_prompt, language="text")

# --- HINT ---
st.markdown("---")
st.markdown("""
    💡 **Note:** This version uses the **free** Imagen 3.0 model, eliminating the API key and billing issues we faced previously. Generation may take longer than DALL·E 3 (up to 30 seconds per image).
""")
