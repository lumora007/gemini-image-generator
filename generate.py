from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO

client = genai.Client(api_key="AIzaSyCF0nRew3uydZs4rRET0_-n5e6Xof3N7-A")
# image = Image.open("input4.jpg")

image = Image.open("BankStatement_Lan1.png")
# prompt = """
# Input image is my profile photo.
# I'm James Oli, a Founder and CEO at Curious Thing, Multilingual Voice Agent Platform
# Generate a realistic (no-blur) camera-taken (1200*320) photo.
# I'm standing bottom right of too light hall in front of clients with investor-like face.
# Presentation is "Voice AI and the end of the application black hole"
# """

prompt = """
Payment Rail: ACH
Bank Name: Lead Bank
Bank Address: 1801 Main St., Kansas City, 64108, US
Beneficiary Name: Davide Tonietto
Account Number: 210233977596
Routing Number: 101019644

I have to make the bank statement to send to the bank for verification. I gave you the template of the bank statement. Please generate a realistic bank statement photo for me with the above information. The bank statement should look like a real bank statement and should be clear and readable. 
use the template image I gave you as the background. The date has to be recent 2026-7-31 and the amount has to be relevant, not too much. Use the bank logo directly in the template image when making new bank statement.
And when making this bank statement use the above info i gave, just swap. in above info, some won't  be use in bank statement, just use ncessary info, you don't need to put all info I gave you unnecessary
And the date has to be recent 2026-7-31 and amout has to be relevant, not too much.
Use template directly!!!
"""

# prompt = """
# Generate a professional creative background (1200*320) photo for ai/data tech icons like Claude code or MCP or databricks
# """

# prompt = """
# Input image is my sample photo and I'm a tech lead at my US company
# I'm sitting and spending rest time at my officer room and putting my eyes to camera
# Output real camera-taken photo (1:1) of me.
# """

# model = "gemini-3-pro-image-preview"

response = client.models.generate_content(
    model="gemini-3-pro-image-preview",
    contents=[prompt, image],
    config=types.GenerateContentConfig(
        response_modalities=['Text', 'Image'],
        image_config=types.ImageConfig(
                image_size="1K"
        ),
        thinking_config=types.ThinkingConfig(
            include_thoughts=True # Enable thoughts
        )
    )
)


for part in response.parts:
  if part.text is not None:
        print(part.text)  
  elif part.thought:
    print(f"Thought: {part.text}")
  elif image:= part.as_image():
    image.save("demo29.png")