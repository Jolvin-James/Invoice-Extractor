import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash
from PIL import Image
import io
import google.generativeai as genai
import base64

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Initialize Flask
app = Flask(__name__)
app.secret_key = os.urandom(24)  # for flash messages

# Load the Gemini model
model = genai.GenerativeModel("gemini-2.0-flash-lite")

def get_gemini_response(context_prompt, image_parts, user_question):
    # Calls the Gemini model
    response = model.generate_content([context_prompt, image_parts[0], user_question])
    return response.text

def prepare_image_parts(uploaded_file):
    """
    Convert Werkzeug FileStorage into the format Gemini expects.
    """
    raw = uploaded_file.read()
    return [{
        "mime_type": uploaded_file.mimetype,
        "data": raw
    }]

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        question = request.form.get("question", "").strip()
        file = request.files.get("invoice_image")

        if not question:
            flash("Please enter a prompt/question about the invoice.", "warning")
            return redirect(url_for("index"))

        if not file or file.filename == "":
            flash("Please upload an invoice image.", "warning")
            return redirect(url_for("index"))

        # Prepare payload and call Gemini
        try:
            image_parts = prepare_image_parts(file)
            context = (
                "You are an expert in invoice extraction. "
                "Answer any questions related to the uploaded invoice image."
            )
            answer = get_gemini_response(context, image_parts, question)
        except Exception as e:
            flash(f"Error processing image or contacting Gemini API: {e}", "danger")
            return redirect(url_for("index"))

        # Render result
        # Convert image back to displayable format
        file.stream.seek(0)
        image_bytes = file.read()                       # raw bytes
        b64_bytes = base64.b64encode(image_bytes)       # encode to base64 bytes
        b64_str = b64_bytes.decode("utf-8")             # convert to string
        img_data = f"data:{file.mimetype};base64,{b64_str}"

        return render_template("index.html", result=answer, img_data=img_data)

    # GET
    return render_template("index.html", result=None, img_data=None)

if __name__ == "__main__":
    app.run(debug=True)
