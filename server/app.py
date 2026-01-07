import os
from flask import Flask, render_template, session, redirect, request, jsonify
from Token import Tokenizer
from Parser import Parser
from database import init_db, get_db

app = Flask(__name__)
app.secret_key = "my_secret_key"  

# Point to the root directory (one level up from /server)
base_dir = os.path.abspath('..')
template_dir = os.path.join(base_dir, 'templates')
static_dir = os.path.join(base_dir, 'static')

app = Flask(__name__, 
            template_folder=template_dir, 
            static_folder=static_dir)

@app.route('/')
def index():
    print(session.get("fullname"))
    return render_template('index.html')


@app.route('/process')
def process():
    # path = ""
    path = "../form_images/onboarding_form.png"

    # Tokenize the uploaded file
    tokenizer = Tokenizer(path)
    try:
        tokens, height_width_dim = tokenizer.tokenize_file()  # Add error in the tokens
    except Exception as e:
        print(e)

    # Parse the tokens taken from the previous step
    parser = Parser()
    accepted, errors = parser(tokens)

    if accepted:
        # Dimensions

        # Serialize tokens - assuming tokens are objects with attributes
        serialized_tokens = [
            {
                'id': token.id,
                'type': token.type,
                'value': token.value,
                'x': token.bbox[0],
                'y': token.bbox[1],
                'w': token.bbox[2],
                'h': token.bbox[3],
                'page': token.page
            }
            for token in tokens
        ]
        
        # Get mappings from parser (adjust based on your Parser implementation)
        mappings = parser.mappings  # or however you access the mappings
        
        return jsonify({
            'success': True,
            'height_width_dim': height_width_dim,
            'tokens': serialized_tokens,
            'mappings': mappings,
        }), 200
    else:
        return jsonify({
            'success': False,
            'errors': errors
        }), 400


# Route for when analyze with OCR 
# @app.route('/submit', methods=["POST"])
# def submit():
#     print("Got here!")

#     names = [
#         "fullname",
#         "dateofbirth",
#         "gender",
#         "nationality",
#         "email",
#         "phonenumber",
#         "alternatephone",
#         "address",
#         "highesteducationlevel",
#         "school",
#         "course",
#         "yeargraduated",
#         "currentemployer",
#         "jobtitle",
#         "yearsofexperience",
#         "monthlysalary",
#         "sssnumber",
#         "tinnumber",
#         "philhealthnumber",
#         "pagibignumber"
#     ]

#     for name in names:
#         session[name] = request.form.get(name)

#     return redirect("/")

if __name__ == "__main__":
    init_db
    app.run(debug=True)