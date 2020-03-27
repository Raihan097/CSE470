import logging
from datetime import datetime

import imagehash
from PIL import Image
from flask import Flask, redirect, url_for
from flask_cors import CORS
from flask_executor import Executor
from flask_login import LoginManager, UserMixin
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import BYTEA


class Config:
    SECRET_KEY = "B8yTvTe7rJr79PH3NproIfVD4yyMV01URca3DDC4WxJCWL5gL0uPGWPMhGv7JDbFtZHsB6Dycn9zs"
    UPLOAD_FOLDER = 'image_storage'
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres:letsplay@127.0.0.1:5432/object_detection"
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False


app = Flask(__name__)
app.config.from_object(Config)
CORS(app)
login_manager = LoginManager(app=app)
db = SQLAlchemy(app)
migrate = Migrate(app=app, db=db)
executor = Executor(app)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s: %(asctime)s \
        pid:%(process)s module:%(module)s %(message)s',
    datefmt='%d/%m/%y %H:%M:%S',
)
logger = logging.getLogger("OBJECT DETECTOR")


class User(UserMixin, db.Model):
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, index=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

    def __init__(self, username, password):
        self.username = username
        self.password = password


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@login_manager.unauthorized_handler
def unauthorized():
    return redirect(url_for("login"))


class Object(db.Model):
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    object_name = db.Column(db.String(255), index=True)
    image = db.Column(BYTEA)
    image_hash = db.Column(db.String(100), index=True)
    mimetype = db.Column(db.String(255))
    record_time = db.Column(db.DateTime, default=datetime.now)

    def __init__(self, name, image_blob, mimetype, **kwargs):
        self.object_name = name
        self.image = image_blob
        self.mimetype = mimetype
        if "path" in kwargs:
            try:
                self.image_hash = imagehash.dhash(Image.open(kwargs.get("path")), hash_size=12).__str__()
            except:
                pass

    def save(self):
        object_saver(self)


def object_saver(ob: Object):
    logger.info(f"Image hash: {ob.image_hash}")
    if ob.image_hash:
        same_image: Object = Object.query.filter(
            Object.image_hash == ob.image_hash,
            Object.object_name == ob.object_name
        ).first()
        logger.info(same_image)
        if same_image:
            logger.info(f"Hash collision: {ob.image_hash}")
            return
    past_objects = Object.query.filter(
        Object.object_name == ob.object_name
    ).order_by(Object.record_time.desc()).offset(100).all()
    if past_objects:
        for po in past_objects:
            db.session.delete(po)
        db.session.commit()
    db.session.add(ob)
    db.session.commit()
    logger.info("Saving as new object")
