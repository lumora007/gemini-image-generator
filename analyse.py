from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO

client = genai.Client(api_key="AIzaSyCF0nRew3uydZs4rRET0_-n5e6Xof3N7-A")
image = Image.open("input4.jpg")
# image1 = Image.open("stanford-logo-transparent.png")
# prompt = """

# Input image is my profile photo.
# Generate a realistic camera-taken (1200*320) photo.
# I'm presenting with the title of "Beyond Generative AI: What Comes Next?"
# I'm at Vention and I'm standing bottom right of dark hall in front of many IT experts. 
# Vention is small company and this presentation is just intro about AI.
# I look small in output photo because camera is top left of hall.
# """

# prompt = """
# Input image is my profile photo.
# I'm Tech Lead of large company.
# Give my camera-taken photo for an Linkedin Avatar.
# """

prompt = """

Input image is my photo and I'm tech lead at one US company 
Input is real camera-taken photo sitting and spending time at my own officer room so I can post on Linkedin. 

I'm going to write a post about What Tech Lead do. Today is June 21th.
Output a post title and script as text more than 300 words!
"""

# model = "gemini-3-pro-image-preview"

response = client.models.generate_content(
    model="gemini-3-pro-image-preview",
    contents=[prompt, image],
    config=types.GenerateContentConfig(
        response_modalities=['Text'],
        # image_config=types.ImageConfig(
        #         image_size="4K"
        # ),
        thinking_config=types.ThinkingConfig(
            include_thoughts=True # Enable thoughts
        )
    )
)

for part in response.parts:
    if part.text is not None:
        print(part.text)