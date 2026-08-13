import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
import io

# Setup page configuration
st.set_page_config(page_title="Gemini Image Generator", page_icon="🖼️", layout="centered")

st.title("🖼️ Gemini Image Generator")
st.write("Upload reference images (optional), enter a prompt, and generate a new image!")

# Setup API Key
API_KEY = st.secrets.get("GEMINI_API_KEY", "AIzaSyCF0nRew3uydZs4rRET0_-n5e6Xof3N7-A")
client = genai.Client(api_key=API_KEY)

# 1. Image Upload (0~n images)
st.subheader("1. Upload Reference Images")
uploaded_files = st.file_uploader(
    "Upload 0 or more reference images", 
    type=["png", "jpg", "jpeg", "webp"], 
    accept_multiple_files=True
)

images = []
if uploaded_files:
    st.write(f"Uploaded {len(uploaded_files)} image(s).")
    # Display thumbnails
    cols = st.columns(len(uploaded_files))
    for i, uploaded_file in enumerate(uploaded_files):
        img = Image.open(uploaded_file)
        # Convert to RGB to ensure compatibility
        if img.mode != 'RGB':
            img = img.convert('RGB')
        images.append(img)
        cols[i].image(img, use_container_width=True, caption=f"Image {i+1}")

# 2. Prompt Input
st.subheader("2. Enter Prompt")
prompt = st.text_area("What do you want to generate?", height=150, placeholder="Describe the image you want to generate...")

# 3. Generate Button
st.subheader("3. Generate")
if st.button("Generate Image", type="primary"):
    if not prompt:
        st.warning("Please enter a prompt to generate an image.")
    else:
        with st.spinner("Generating image... This may take a few moments."):
            try:
                # Prepare contents for the API call
                contents = [prompt]
                contents.extend(images)
                
                # Make the API call
                response = client.models.generate_content(
                    model="gemini-3-pro-image-preview",
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
                
                # Extract image and text from the response
                for part in response.parts:
                    if part.text:
                        output_text.append(part.text)
                    elif part.thought:
                        output_text.append(f"Thought: {part.text}")
                    elif img := part.as_image():
                        output_image = img
                
                # Output Text (if any)
                if output_text:
                    with st.expander("Show AI Thoughts / Text"):
                        for text in output_text:
                            st.write(text)
                
                # Display the output image
                if output_image:
                    st.success("Image generated successfully!")
                    st.image(output_image, caption="Generated Image", use_container_width=True)
                    
                    # 4. Download Button
                    buf = io.BytesIO()
                    output_image.save(buf, format="PNG")
                    byte_im = buf.getvalue()
                    
                    st.download_button(
                        label="Download Generated Image ⬇️",
                        data=byte_im,
                        file_name="generated_image.png",
                        mime="image/png"
                    )
                else:
                    st.error("No image was generated. Please try again or modify your prompt.")
            except Exception as e:
                st.error(f"An error occurred: {e}")
