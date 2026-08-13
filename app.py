import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
import io

# Setup page configuration
st.set_page_config(page_title="Gemini Tools", page_icon="🛠️", layout="centered")

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

# Setup API Key
API_KEY = st.secrets.get("GEMINI_API_KEY")
if not API_KEY:
    st.error("Please set GEMINI_API_KEY in Streamlit secrets.")
    st.stop()
client = genai.Client(api_key=API_KEY)


def part_to_pil(part):
    """Return a PIL Image for an image part, or None. Streamlit needs a real
    PIL Image, since the SDK's own Image type lacks the .format attribute."""
    inline = getattr(part, "inline_data", None)
    if inline is None or not inline.data:
        return None
    if inline.mime_type and not inline.mime_type.startswith("image/"):
        return None
    return Image.open(io.BytesIO(inline.data))

# Create tabs for different features
tab1, tab2 = st.tabs(["🖼️ Image Generator", "✍️ Text Rewriter"])

# ============== TAB 1: Image Generator ==============
with tab1:
    st.header("Image Generator")
    st.write("Upload reference images (optional), enter a prompt, and generate a new image!")

    # Available Gemini image models
    IMAGE_MODELS = [
        "gemini-3-pro-image-preview",
        "gemini-3-pro-image",
        "gemini-3.1-flash-image",
        "gemini-3.1-flash-image-preview",
        "gemini-3.1-flash-lite-image",
    ]

    # Model Selection
    st.subheader("1. Select Model")
    selected_image_model = st.selectbox(
        "Choose a Gemini model:",
        options=IMAGE_MODELS,
        index=0,
        key="image_model",
        help="Select the Gemini model to use for image generation"
    )

    # Image Upload (0~n images)
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

    # Prompt Input
    st.subheader("3. Enter Prompt")
    image_prompt = st.text_area(
        "What do you want to generate?", 
        height=150, 
        placeholder="Describe the image you want to generate...",
        key="image_prompt"
    )

    # Generate Button
    st.subheader("4. Generate")
    if st.button("Generate Image", type="primary", key="gen_image_btn"):
        if not image_prompt:
            st.warning("Please enter a prompt to generate an image.")
        else:
            with st.spinner(f"Generating image with {selected_image_model}... This may take a few moments."):
                try:
                    contents = [image_prompt]
                    contents.extend(images)
                    
                    full_config = types.GenerateContentConfig(
                        response_modalities=['Text', 'Image'],
                        image_config=types.ImageConfig(image_size="1K"),
                        thinking_config=types.ThinkingConfig(include_thoughts=True),
                    )
                    basic_config = types.GenerateContentConfig(
                        response_modalities=['Text', 'Image'],
                    )

                    # Flash/Flash-Lite image models reject image_size and thinking,
                    # so fall back to the minimal config if the full one is refused.
                    try:
                        response = client.models.generate_content(
                            model=selected_image_model,
                            contents=contents,
                            config=full_config,
                        )
                    except Exception as first_error:
                        try:
                            response = client.models.generate_content(
                                model=selected_image_model,
                                contents=contents,
                                config=basic_config,
                            )
                        except Exception:
                            raise first_error
                    
                    output_image = None
                    output_text = []
                    
                    for part in response.parts or []:
                        if part.text:
                            label = "Thought: " if getattr(part, "thought", False) else ""
                            output_text.append(f"{label}{part.text}")
                        else:
                            pil = part_to_pil(part)
                            if pil is not None:
                                output_image = pil
                    
                    if output_text:
                        with st.expander("Show AI Thoughts / Text"):
                            for text in output_text:
                                st.write(text)
                    
                    if output_image:
                        st.success("Image generated successfully!")
                        st.image(output_image, caption="Generated Image", use_container_width=True)
                        
                        buf = io.BytesIO()
                        if output_image.mode not in ("1", "L", "LA", "P", "RGB", "RGBA"):
                            output_image = output_image.convert("RGB")
                        output_image.save(buf, format="PNG")
                        byte_im = buf.getvalue()
                        
                        st.download_button(
                            label="Download Generated Image",
                            data=byte_im,
                            file_name="generated_image.png",
                            mime="image/png",
                            key="download_img_btn"
                        )
                    else:
                        st.error("No image was generated. Please try again or modify your prompt.")
                except Exception as e:
                    st.error(f"An error occurred: {e}")

# ============== TAB 2: Text Rewriter ==============
with tab2:
    st.header("Text Rewriter")
    st.write("Use AI to rewrite text based on your instructions.")

    # Available text models
    TEXT_MODELS = [
        "gemini-3.1-flash-lite",
        "gemini-3.5-flash-lite",
        "gemini-3.6-flash",
        "gemini-3.5-flash",
        "gemini-3.1-pro-preview",
    ]

    # Model Selection
    st.subheader("1. Select Model")
    selected_text_model = st.selectbox(
        "Choose a Gemini model:",
        options=TEXT_MODELS,
        index=0,
        key="text_model",
        help="Select the Gemini model to use for text rewriting"
    )

    # Instruction Prompt
    st.subheader("2. Enter Instruction")
    rewrite_instruction = st.text_area(
        "How should the text be rewritten?",
        value="Rewrite this like a native speaker",
        height=100,
        key="rewrite_instruction",
        placeholder="e.g., Rewrite this like a native speaker, Make it more formal, Simplify this..."
    )

    # Text Parameter (the text to rewrite)
    st.subheader("3. Enter Text to Rewrite")
    text_to_rewrite = st.text_area(
        "Paste the text you want to rewrite:",
        height=150,
        key="text_to_rewrite",
        placeholder="e.g., please share your availability"
    )

    # Rewrite Button
    st.subheader("4. Rewrite")
    if st.button("Rewrite Text", type="primary", key="rewrite_btn"):
        if not text_to_rewrite:
            st.warning("Please enter text to rewrite.")
        elif not rewrite_instruction:
            st.warning("Please enter rewriting instructions.")
        else:
            with st.spinner(f"Rewriting with {selected_text_model}..."):
                try:
                    full_prompt = f"{rewrite_instruction}:\n\n{text_to_rewrite}"
                    
                    response = client.models.generate_content(
                        model=selected_text_model,
                        contents=full_prompt,
                    )
                    
                    rewritten_text = response.text
                    
                    if rewritten_text:
                        st.session_state.rewrite_result = rewritten_text
                    else:
                        st.session_state.rewrite_result = None
                        st.error("No output was generated. Please try again.")
                except Exception as e:
                    st.session_state.rewrite_result = None
                    st.error(f"An error occurred: {e}")

    # Result is kept in session state so switching view tabs or changing a
    # dropdown doesn't discard it.
    result = st.session_state.get("rewrite_result")
    if result:
        st.subheader("Result")
        formatted_tab, markdown_tab = st.tabs(["Formatted", "Markdown"])

        with formatted_tab:
            st.markdown(result)

        with markdown_tab:
            st.code(result, language="markdown")

        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="Download .txt",
                data=result,
                file_name="rewritten_text.txt",
                mime="text/plain",
                key="download_txt_btn",
                use_container_width=True,
            )
        with col2:
            st.download_button(
                label="Download .md",
                data=result,
                file_name="rewritten_text.md",
                mime="text/markdown",
                key="download_md_btn",
                use_container_width=True,
            )
