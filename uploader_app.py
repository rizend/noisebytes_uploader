"""Noisebyte uploader flask app"""
import os
import binascii
from subprocess import call
import threading
from secrets import SLACK_TOKEN, SLACK_WEBHOOK_URL
from flask import Flask, request, redirect, url_for, flash
import requests
import youtube_uploader

UPLOAD_FOLDER = './uploads'
TEMP_FOLDER = './temp'
ALLOWED_EXTENSIONS = set(['mov', 'mp4', 'avi', 'mkv', 'wmv', 'mpeg4', 'mpg'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def log_to_slack(msg):
    payload = {
        "channel": "#noisebytes",
        "username": "noisebytes-moderation-bot",
        "text": msg,
        "icon_emoji": ":vibration_mode:"
    }
    return requests.post(SLACK_WEBHOOK_URL, json=payload)

@app.route("/slack", methods=['POST'])
def slack_command_handler():
    if request.form['token'] != SLACK_TOKEN:
        return ':('
    txt = request.form['text']
    user = request.form['user_name']
    ret = youtube_uploader.approve_video(txt)
    if ret == "Approved":
        log_to_slack(user + ' approved video id ' + txt)
        return "Video successfully approved"
    if ret == "NoVideo":
        return "No video found with given id"
    if ret == "AlreadyApproved":
        return "That video has already been approved :)"
    return "Unknown return value, please contact @augur and/or @rizend"

def title_of_processed_video(title, author):
    return "Noisebytes - " + title + " by " + author

def random_name():
    return binascii.b2a_hex(os.urandom(16))

def allowed_file(filename):
    return '.' in filename and \
                filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_file_handler():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            print "No file part"
            return redirect(request.url)
        posted_file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if posted_file.filename == '':
            flash('No selected file')
            print "no selected file"
            return redirect(request.url)
        if posted_file and allowed_file(posted_file.filename):
            title = request.form['title']
            author = request.form['author']
            temp_name = random_name()
            extension = posted_file.filename.rsplit('.', 1)[1].lower()
            upload_file = os.path.join(UPLOAD_FOLDER, temp_name + '.' + extension)
            processed_file = os.path.join(TEMP_FOLDER, temp_name + '.mp4')

            posted_file.save(upload_file)

            def upload_to_youtube_thread():
                call(["bash", "./process_video.sh", title, author,
                      upload_file,
                      processed_file])
                video_id = youtube_uploader.upload_video(title_of_processed_video(title, author),
                                                         processed_file)
                if video_id:
                    log_to_slack("Video " + video_id + " ready for moderation")
                else:
                    log_to_slack("An error was encountered while uploading a video")
                os.remove(upload_file)
                os.remove(processed_file)
            threading.Thread(target=upload_to_youtube_thread).start()

            return redirect(url_for('upload_file'))
    return '''
    <!doctype html>
    <title>Upload a Noisebyte!</title>
    <h1>Upload a Noisebyte!</h1>
    <form method=post enctype=multipart/form-data>
        <p>Title: <input name=title></p>
        <p>Author: <input name=author></p>
        <p><input type=file name=file>
              <input type=submit value=Upload>
    </form>
    '''

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=int("3114"), debug=False)
