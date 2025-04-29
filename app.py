import os
import pandas as pd
import logging 
from flask import Flask, request, jsonify, render_template, send_from_directory
from werkzeug.utils import secure_filename


logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)


GROQ_API_KEY = os.getenv("API_KEY")


UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"xls", "xlsx", "csv"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def count_tokens(text):
    """Helper function to count the number of tokens in a string."""
    return len(text.split())  

def truncate_text(text, max_tokens):
    """Truncate text to fit within the max token limit."""
    tokens = text.split()
    if len(tokens) > max_tokens:
        text = ' '.join(tokens[:max_tokens])  
    return text

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(file_path)

        return jsonify({"message": "File uploaded successfully", "filename": filename})
    
    return jsonify({"error": "Invalid file format"}), 400

@app.route("/ask", methods=["POST"])
def ask_ai():
    try:
        data = request.json
        filename = data.get("filename")
        query = data.get("query")

        if not filename or not query:
            return jsonify({"error": "Missing filename or query"}), 400

        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        if not os.path.exists(file_path):
            return jsonify({"error": "File not found"}), 404

        
        try:
            if filename.endswith(("xls", "xlsx")):
                df = pd.read_excel(file_path)
            else:
                df = pd.read_csv(file_path)
        except Exception as e:
            return jsonify({"error": f"Error processing file: {str(e)}"}), 500

        
        if "names" in query.lower():
            student_names = df['Name'].tolist()
            return jsonify({"answer": student_names})

        
        if "marks" in query.lower():
            subject = "VLSI marks" if "vlsi" in query.lower() else "CN marks" if "cn" in query.lower() else "MES marks"
            student_marks = df[["Name", subject]].to_dict(orient="records")
            return jsonify({"answer": student_marks})

        
        return jsonify({"error": "Query not recognized. Please ask for 'names' or 'marks'."})

    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
