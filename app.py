import os
import base64
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, session
import google.generativeai as genai

# Load API key
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Initialize Flask
app = Flask(__name__)
app.secret_key = os.urandom(24)

# Load Gemini model
model = genai.GenerativeModel("gemini-2.0-flash-lite")

def get_gemini_response(context_prompt, image_parts, user_question):
    response = model.generate_content([context_prompt, image_parts[0], user_question])
    return response.text

def prepare_image_parts(file):
    raw = file.read()
    return [{
        "mime_type": file.mimetype,
        "data": raw
    }]

def is_invoice_image(image_parts):
    try:
        response = model.generate_content([
            "You are a helpful assistant. Is the image provided an invoice or not? Reply strictly with 'Yes' or 'No'.",
            image_parts[0]
        ])
        return "yes" in response.text.lower()
    except Exception as e:
        print(f"Error during invoice detection: {e}")
        return False


@app.route("/", methods=["GET", "POST"])
def index():
    if "chat_history" not in session:
        session["chat_history"] = []

    img_data = None

    if request.method == "POST":
        question = request.form.get("question", "").strip()
        file = request.files.get("invoice_image")

        if not question:
            flash("Please enter a question.", "warning")
            return redirect(url_for("index"))

        if not file or file.filename == "":
            flash("Please upload an image.", "warning")
            return redirect(url_for("index"))

        try:
            image_parts = prepare_image_parts(file)

            # Check if uploaded image is likely an invoice
            if not is_invoice_image(image_parts):
                flash("The uploaded image does not appear to be an invoice. Please upload a valid invoice image.", "warning")
                return redirect(url_for("index"))
            
            context = "You are an expert in invoice extraction."
            answer = get_gemini_response(context, image_parts, question)

            session["chat_history"].append(("You", question))
            session["chat_history"].append(("Gemini", answer))
            session.modified = True

            # Prepare image for preview
            file.stream.seek(0)
            image_bytes = file.read()
            b64_bytes = base64.b64encode(image_bytes).decode("utf-8")
            img_data = f"data:{file.mimetype};base64,{b64_bytes}"

        except Exception as e:
            flash(f"Gemini error: {e}", "danger")
            return redirect(url_for("index"))

    return render_template(
        "index.html",
        img_data=img_data,
        chat_history=session.get("chat_history", [])
    )

@app.route("/clear", methods=["POST"])
def clear_chat():
    session.pop("chat_history", None)
    flash("Chat history cleared.", "info")
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
