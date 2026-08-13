import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
import io

# Setup page configuration
st.set_page_config(page_title="Gemini Image Generator", page_icon="🖼️", layout="centered")

# PIN Authentication
def check_password():
    """Returns True if the user entered the correct PIN."""
    APP_PIN = st.secrets.get("APP_PIN")
    
    if not APP_PIN:
        return True
    
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if st.session_state.authenticated:
        return True
    
    st.title("🔐 Authentication Required")
    pin_input = st.text_input("Enter PIN to access the app:", type="password")
    
    if st.button("Submit", type="primary"):
        if pin_input == APP_PIN:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect PIN. Please try again.")
    
    return False

if not check_password():
    st.stop()

st.title("🖼️ Gemini Image Generator")
st.write("Upload reference images (optional), enter a prompt, and generate a new image!")

# Setup API Key
API_KEY = st.secrets.get("GEMINI_API_KEY")
if not API_KEY:
    st.error("Please set GEMINI_API_KEY in Streamlit secrets.")
    st.stop()
client = genai.Client(api_key=API_KEY)

# Available Gemini image models
MODELS = [
    "gemini-2.0-flash-preview-image-generation",
    "gemini-2.0-flash-exp-image-generation",
    "gemini-3-pro-image-preview",
]

# Model Selection
st.subheader("1. Select Model")
selected_model = st.selectbox(
    "Choose a Gemini model:",
    options=MODELS,
    index=0,
    help="Select the Gemini model to use for image generation"
)

# 2. Image Upload (0~n images)
st.subheader("2. Upload Reference Images")
uploaded_files = st.file_uploader(
    "Upload 0 or more reference images", 
    type=["png", "jpg", "jpeg", "webp"], 
    accept_multiple_files=True
)

images = []
if uploaded_files:
    st.write(f"Uploaded {len(uploaded_files)} image(s).")
    cols = st.columns(min(len(uploaded_files), 4))
    for i, uploaded_file in enumerate(uploaded_files):
        img = Image.open(uploaded_file)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        images.append(img)
        cols[i % 4].image(img, use_container_width=True, caption=f"Image {i+1}")

# 3. Prompt Input
st.subheader("3. Enter Prompt")
prompt = st.text_area("What do you want to generate?", height=150, placeholder="Describe the image you want to generate...")

# 4. Generate Button
st.subheader("4. Generate")
if st.button("Generate Image", type="primary"):
    if not prompt:
        st.warning("Please enter a prompt to generate an image.")
    else:
        with st.spinner(f"Generating image with {selected_model}... This may take a few moments."):
            try:
                contents = [prompt]
                contents.extend(images)
                
                response = client.models.generate_content(
                    model=selected_model,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        response_modalities=['Text', 'Image'],
                        image_config=types.ImageConfig(
                            image_size="1K"
                        ),
                        thinking_config=types.ThinkingConfig(
                            include_thoughts=True
                        )
                    )
                )
                
                output_image = None
                output_text = []
                
                for part in response.parts:
                    if part.text:
                        output_text.append(part.text)
                    elif part.thought:
                        output_text.append(f"Thought: {part.text}")
                    elif img := part.as_image():
                        output_image = img
                
                if output_text:
                    with st.expander("Show AI Thoughts / Text"):
                        for text in output_text:
                            st.write(text)
                
                if output_image:
                    st.success("Image generated successfully!")
                    st.image(output_image, caption="Generated Image", use_container_width=True)
                    
                    buf = io.BytesIO()
                    output_image.save(buf, format="PNG")
                    byte_im = buf.getvalue()
                    
                    st.download_button(
                        label="Download Generated Image",
                        data=byte_im,
                        file_name="generated_image.png",
                        mime="image/png"
                    )
                else:
                    st.error("No image was generated. Please try again or modify your prompt.")
            except Exception as e:
                st.error(f"An error occurred: {e}")
