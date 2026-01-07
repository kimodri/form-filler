import os
from flask import Flask, render_template, session, request, send_file
from werkzeug.utils import secure_filename

from Token import Tokenizer
from Parser import Parser
from Generator import Generator
from database import init_db

KEY_MAPPING = {
    "fullName": "Full Name",
    "dateOfBirth": "Date of Birth",
    "gender": "Gender",
    "nationality": "Nationality",
    "email": "Email Address",
    "phone": "Phone Number",
    "alternatePhone": "Alternate Phone Number",
    "address": "Address",
    "currentEmployer": "Current Employer",
    "jobTitle": "Job Title",
    "monthlySalary": "Monthly Salary",
    "sssNumber": "SSS Number",
    "tinNumber": "TIN Number",
    "philhealthNumber": "PhilHealth Number",
    "pagibigNumber": "Pag-IBIG Number",
}


# --------------------
# App setup
# --------------------
base_dir = os.path.abspath('..')
template_dir = os.path.join(base_dir, 'templates')
static_dir = os.path.join(base_dir, 'static')

app = Flask(
    __name__,
    template_folder=template_dir,
    static_folder=static_dir
)

app.secret_key = "my_secret_key"

UPLOAD_FOLDER = os.path.join(base_dir, "uploaded_files")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# --------------------
# Routes
# --------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("document")
    if not file or file.filename == "":
        return {"error": "No file uploaded"}, 400

    if not allowed_file(file.filename):
        return {"error": "Invalid file type"}, 400

    filename = secure_filename(file.filename)
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(save_path)

    session["save_path"] = os.path.abspath(save_path)
    session.modified = True

    return {"status": "ok", "filename": filename}, 200



@app.route("/submit", methods=["POST"])
def submit_profile():
    data = request.get_json()
    if not data:
        return {"error": "No data received"}, 400

    # Map keys to what Generator expects
    session["user_data"] = {KEY_MAPPING[k]: v for k, v in data.items() if k in KEY_MAPPING}
    session.modified = True
    return {"status": "ok"}, 200

@app.route("/clear_profile", methods=["POST"])
def clear_profile():
    session.pop("user_data", None)
    session.modified = True
    return {"status": "ok"}, 200

@app.route("/get_profile")
def get_profile():
    return {"user_data": session.get("user_data")}



@app.route("/process", methods=["POST"])
def process():
    path = session.get("save_path")
    user = session.get("user_data")

    if not path or not os.path.exists(path):
        return {"errors": ["Uploaded file not found"]}, 400

    if not user:
        return {"errors": ["User data not submitted"]}, 400

    # 1. Tokenize (PDF handled internally)
    tokenizer = Tokenizer(path)
    tokens, dimensions = tokenizer.tokenize_file()

    # 2. Parse
    parser = Parser()
    accepted, errors = parser(tokens)

    if not accepted:
        return {"errors": errors}, 400

    # 3. Generate filled form image
    output_path = os.path.join(
        os.path.dirname(path),
        "filled_out_form.jpg"
    )

    gen = Generator()
    gen.generate(
        path,
        parser.mappings,
        user,
        output_path
    )

    # 4. Return image (NOT JSON)
    return send_file(
        output_path,
        mimetype="image/jpeg",
        as_attachment=False
    )


# --------------------
# Main
# --------------------
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
