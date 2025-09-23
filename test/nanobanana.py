import os
from google import genai
from PIL import Image
from io import BytesIO

# --- IMPORTANT ---
# Paste your API key here. For better security, we recommend using environment variables.
API_KEY=os.environ.get("GEMINI_API_KEY")
# -----------------

# Configure the client with your API key
client = genai.Client(api_key=API_KEY)

# The text prompt for image generation
prompt = "Create a photorealistic image of an orange cat with green eyes, sitting on a couch."

print("Generating image...")

# Call the API to generate the image
response = client.models.generate_content(
    model="gemini-2.5-flash-image-preview",
    contents=prompt,
)

image_parts = [
    part.inline_data.data
    for part in response.candidates[0].content.parts
    if part.inline_data
]
 
if image_parts:
    image = Image.open(BytesIO(image_parts[0]))
    image.save('cat.png')