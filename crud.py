import os
import shutil
from typing import List

import cv2

from detection.server import detect_objects
from models import Object, logger,db
from utils import generate_uuid

MIMES = {
    "png": "png",
    "jpg": "jpeg",
    "jpeg": "jpeg"
}
VIDEO_FRAME_LIMIT = 100


def get_mime(exten: str):
    return MIMES.get(exten) or "application/octet-stream"


def save_image_db(image_path: str):
    logger.info(f"Processing file {image_path}")
    filename = image_path.split(f"{os.sep}")[-1]
    mime = get_mime(filename.split(".")[1].lower())
    with open(image_path, "rb") as im:
        bin_data = im.read()
    classes = detect_objects(image_path)
    logger.info(f"Detected classes for {image_path}: {classes}")
    for cl in classes:
        Object(cl, bin_data, mime, path=image_path).save()
    os.remove(image_path)


def process_video(video_path: str):
    vid = cv2.VideoCapture(video_path)
    success, image = vid.read()
    count = 0
    vid_uid = generate_uuid()
    os.makedirs(f"static/images/videoprocessing/{vid_uid}")
    while success and count <= VIDEO_FRAME_LIMIT:
        filename = f"static/images/videoprocessing/{vid_uid}/{count}.jpg"
        cv2.imwrite(filename, image)
        success, image = vid.read()
        count += 1
        save_image_db(f"{filename}")
    if vid.isOpened():
        vid.release()
    shutil.rmtree(f"static/images/videoprocessing/{vid_uid}")
    os.remove(video_path)


def get_image_db(name) -> List[Object]:
    objs = Object.query.filter(
        Object.object_name == name
    ).order_by(Object.record_time.asc()).all()
    return objs

def get_items_db():
    result =   db.engine.execute("SELECT distinct  object_name from  object");
    return result



def objects_from_image():
    logger.info(detect_objects("static/images/image2.jpg"))


if __name__ == '__main__':
    objects_from_image()
