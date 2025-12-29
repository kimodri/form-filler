import os
from flask import Flask, render_template, session, redirect, request

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
    app.run(debug=True)