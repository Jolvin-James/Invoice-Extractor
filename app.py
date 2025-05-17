import os
import base64

from datetime import datetime
from dotenv import load_dotenv
from flask import (
    Flask, render_template, request,
    redirect, url_for, flash, session
)
from pymongo import MongoClient
from bson.objectid import ObjectId
import google.generativeai as genai


load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
MONGO_URI      = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash-lite")

app = Flask(__name__)
app.secret_key = os.urandom(24)

client = MongoClient(MONGO_URI)
db     = client.invoice_extractor
chats  = db.chat_history


def get_gemini_response(context, parts, question):
    resp = model.generate_content([context, parts[0], question])
    return resp.text

def save_or_update_chat(doc_id, img_b64, mimetype, entries):
    """If doc_id is None, insert a new doc; else update existing."""
    if doc_id is None:
        result = chats.insert_one({
            "image_data": img_b64,
            "mimetype": mimetype,
            "chat_history": entries
        })
        return str(result.inserted_id)
    else:
        chats.update_one(
            {"_id": ObjectId(doc_id)},
            {
              "$set": {"image_data": img_b64, "mimetype": mimetype},
              "$push": {"chat_history": {"$each": entries}}
            }
        )
        return doc_id

def load_chat_document(doc_id):
    """Return the chat document, or None if not found or invalid ID."""
    try:
        return chats.find_one({"_id": ObjectId(doc_id)})
    except Exception:
        return None

@app.route("/", methods=["GET", "POST"])
def index():
    # Load existing chat doc if we have session_id
    session_id = session.get("session_id")
    chat_doc   = load_chat_document(session_id) if session_id else None

    # Unpack stored state
    img_data    = chat_doc["image_data"] if chat_doc else None
    mimetype    = chat_doc["mimetype"]   if chat_doc else None
    chat_history= chat_doc["chat_history"] if chat_doc else []

    if request.method == "POST":
        question = request.form.get("question", "").strip()
        file     = request.files.get("invoice_image")

        if not question:
            flash("Please enter a question.", "warning")
            return redirect(url_for("index"))

        # If we have no stored image, require upload
        if not img_data and (not file or file.filename == ""):
            flash("Please upload an invoice image (once).", "warning")
            return redirect(url_for("index"))

        # If user uploaded a new file, overwrite stored image
        if file and file.filename:
            raw = file.read()
            img_data = base64.b64encode(raw).decode("utf-8")
            mimetype = file.mimetype

        # Prepare for Gemini
        parts = [{
            "mime_type": mimetype,
            "data": base64.b64decode(img_data)
        }]
        answer = get_gemini_response(
            "You are an expert in invoice extraction.",
            parts,
            question
        )

        # Build the two new entries
        entries = [("You", question), ("Gemini", answer)]
        # Save or update in MongoDB
        new_session_id = save_or_update_chat(
            session_id, img_data, mimetype, entries
        )
        session["session_id"] = new_session_id

        # Append in‑memory for immediate rendering
        chat_history.extend(entries)

    # Always pass img_data (or None) into template
    return render_template(
        "index.html",
        img_data    = f"data:{mimetype};base64,{img_data}" if img_data else None,
        chat_history= chat_history
    )

@app.route("/clear", methods=["POST"])
def clear_chat():
    sid = session.pop("session_id", None)
    if sid:
        try:
            chats.delete_one({"_id": ObjectId(sid)})
        except Exception:
            pass
    flash("Chat history cleared.", "info")
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
