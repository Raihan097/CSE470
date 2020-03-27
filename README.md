# Object Detection from video stream

This is a project that we did in Human Interfacing (CSE472) course. 
This is a Flask api that uses a trained machine learning model to detect objects from image.

After processing the video, it saves the image data and detected objects in a PostgreSQL database to make it queryable.

An endpoint is exposed to let user search for objects. If the object exists in database, it gather all the images associated with the objects, sorting in descending manner based of timestamp(latest image first), and create a GIF and renders it in browser.


### Video Preview
For a video preview, visit [here](https://drive.google.com/file/d/1clAhhXCCyyaBQsuVbymbSEkNyn-N3c94/view)