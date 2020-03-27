import os

from flask import request, make_response, jsonify, render_template, redirect, url_for
from flask_json_schema import JsonSchema, JsonValidationError
from flask_login import login_required, login_user, logout_user
from werkzeug.utils import secure_filename

from crud import save_image_db, get_image_db, objects_from_image, process_video, get_items_db
from models import app, executor, User, db
from schemaTest import todo_schema
from utils import generate_uuid, clear_dir

schema = JsonSchema(app)
todos = []


@app.errorhandler(JsonValidationError)
def validation_error(e):
    return make_response(jsonify({
        "error": {
            "msgs": [
                ve.message[:ve.message.index("does not match")] + " is invalid value" if "does not match" in ve.message \
                    else ve.message
                for ve in e.errors
            ]
        }
    }), 400)


@app.route('/schemaTesting', methods=['GET', 'POST'])
@schema.validate(todo_schema)
def create_message():
    if request.method == 'POST':
        todos.append(request.get_json())
        return jsonify({'success': True, 'message': 'Data received'})

    return jsonify(todos)


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
ALLOWED_VIDEO_EXTENSIONS = {"mp4", "avi"}


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def allowed_video_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS


@app.before_first_request
def before_start():
    clear_dir("static/images/tmp")
    clear_dir("static/images/videoprocessing")
    clear_dir("image_storage")


@app.route("/ping")
def ping():
    return "pong"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/image/save", methods=["POST"])
@login_required
def save_image():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            return make_response(jsonify({
                "error": {
                    "msg": "No file part"
                }
            }), 400)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            return make_response(jsonify({
                "error": {
                    "msg": "No selected file"
                }
            }), 400)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            saved_filename = generate_uuid() + "." + filename.split(".")[1].lower()

            file.save(os.path.join(app.config['UPLOAD_FOLDER'], saved_filename))
            executor.submit(save_image_db, os.path.join(app.config['UPLOAD_FOLDER'], saved_filename))

            return make_response(jsonify({
                "status": "okay",
                "msg": "image uploaded and sent for processing"
            }), 200)

        return make_response(jsonify({
            "error": {
                "msg": "Invalid file format"
            }
        }), 400)


@app.route("/video/save", methods=["POST", "GET"])
@login_required
def save_video_and_process():
    if request.method == 'GET':
        return render_template('fileuploadform.html')

    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            return make_response(jsonify({
                "error": {
                    "msg": "No file part"
                }
            }), 400)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            return make_response(jsonify({
                "error": {
                    "msg": "No selected file"
                }
            }), 400)

        if file and allowed_video_file(file.filename):
            filename = secure_filename(file.filename)
            saved_filename = generate_uuid() + "." + filename.split(".")[1].lower()

            file.save(os.path.join(app.config['UPLOAD_FOLDER'], saved_filename))
            executor.submit(process_video, os.path.join(app.config['UPLOAD_FOLDER'], saved_filename))

            return make_response(jsonify({
                "status": "okay",
                "msg": "video uploaded and sent for processing"
            }), 200)

        return make_response(jsonify({
            "error": {
                "msg": "Invalid file format"
            }
        }), 400)


@app.route("/search")
@login_required
def search():
    objects_from_image()
    return "search"


@app.route('/registration', methods=["POST", "GET"])
def registration():
    if request.method == "GET":
        return render_template("register.html")
    elif request.method == "POST":

        username = request.form['username']
        password = request.form['password']

        print(username, password)

        userExists = User.query.filter(
            User.username == username
        ).first()

        if userExists is not None:
            return make_response(jsonify({
                "error": {
                    "msg": "user name not available"
                }
            }), 403)

        newUser = User(username=username, password=password)

        try:
            db.session.add(newUser)
            db.session.commit()
        except:
            return make_response(jsonify({
                "error": {
                    "msg": "something went wrong, try again later"
                }
            }), 500)

        return redirect(url_for("login"))


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    if request.method == 'POST':
        print(request.form)

        username = request.form['username']
        password = request.form['password']

        user = User.query.filter(
            (User.username == username) & (User.password == password)
        ).first()

        if user is None:
            return make_response(jsonify({
                "error": {
                    "msg": "invalid credentials"
                }
            }), 403)  # 401 is Unauthorized

        login_user(user)
        return redirect(url_for("index"))  # 200 because everything went well


@app.route('/logout', methods=['GET'])
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/image/get/<string:name>")
@login_required
def get_image(name: str):
    objs = get_image_db(name)
    if not objs:
        return make_response(jsonify({
            "error": {
                "msg": "not found"
            }
        }), 404)

    files = []
    clear_dir("static/images/tmp")
    for i, ob in enumerate(objs):
        uid_name = generate_uuid()
        with open(f"static/images/tmp/{uid_name}.{ob.mimetype}", "wb") as f:
            f.write(ob.image)
            files.append(f"{uid_name}.{ob.mimetype}")
    return render_template("index.html", objs=files)


@app.route("/items")
@login_required
def get_items():
    result = get_items_db()
    result_set = result.fetchall()
    return render_template('listitem.html', posts=result_set)
