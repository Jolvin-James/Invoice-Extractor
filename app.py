from dotenv import load_dotenv
import streamlit as st
from PIL import Image
import os
import google.generativeai as genai


load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Function to load the gemini model
model = genai.GenerativeModel("gemini-2.0-flash-lite")

def get_gemini_response(input, image, prompt):
    response = model.generate_content([input, image[0], prompt])
    return response.text

def input_image_details(uploaded_file):
    if uploaded_file is not None:
        # Read the file into bytes
        bytes_data = uploaded_file.getvalue()

        image_parts = [
            {
                "mime_type": uploaded_file.type, # Get the MIME type of the uploaded file
                "data": bytes_data
            }
        ]
        return image_parts
    else:
        raise FileNotFoundError("No file uploaded")
    

# Initialize Streamlit app
st.set_page_config(page_title = "MultiLanguage Invoice Extractor", page_icon=":money_with_wings:", layout="wide")

st.header("Invoice Extractor")
input = st.text_input("Input prompt: ", key="input")
uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
image =""
if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image", use_column_width=True)

submit = st.button("Tell me about the invoice")

input_prompt = """
You are an expert in invoice extraction.
You are given an image of an invoice and you will have to answer any questions related to the uploaded invoice image.
"""

if submit:
    image_data = input_image_details(uploaded_file)
    response = get_gemini_response(input_prompt, image_data, input)
    st.subheader("The response is:")
    st.write(response)