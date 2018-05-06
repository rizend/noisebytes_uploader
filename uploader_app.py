"""Noisebyte uploader flask app"""
import os
import binascii
from subprocess import call
import threading
from secrets import APPROVE_SLACK_TOKEN, TRASH_SLACK_TOKEN, SLACK_WEBHOOK_URL, FLASK_SECRET_KEY
from flask import Flask, request, redirect, flash, render_template
import requests
import youtube_uploader

UPLOAD_FOLDER = './uploads'
TEMP_FOLDER = './temp'
ALLOWED_EXTENSIONS = set(['mov', 'mp4', 'avi', 'mkv', 'wmv', 'mpeg4', 'mpg'])
BASE_ADDR='/noisebytes/'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.url_map.strict_slashes = False
app.secret_key = FLASK_SECRET_KEY

def youtube_video_url(id):
  return 'https://www.youtube.com/watch?v=' + id

def log_to_slack(msg):
    payload = {
        "channel": "#noisebytes",
        "username": "noisebytes-moderation-bot",
        "text": msg,
        "icon_emoji": ":vibration_mode:"
    }
    return requests.post(SLACK_WEBHOOK_URL, json=payload)

@app.route("/slack/approve", methods=['POST'])
def approve_command_handler():
    if request.form['token'] != APPROVE_SLACK_TOKEN:
        return ':('
    video_id = request.form['text']
    user = request.form['user_name']
    ret = youtube_uploader.approve_video(video_id)
    if ret == "Approved":
        log_to_slack(user + ' approved video ' + youtube_video_url(video_id))
        return "Video successfully approved"
    if ret == "AlreadyApproved":
        return "That video has already been approved :)"
    return "Unknown return value, please contact @beka and/or @rizend"

@app.route("/slack/trash", methods=['POST'])
def trash_command_handler():
    if request.form['token'] != TRASH_SLACK_TOKEN:
        return ':('
    video_id = request.form['text']
    user = request.form['user_name']
    ret = youtube_uploader.trash_video(video_id)
    if ret == "Trashed":
        log_to_slack(user + ' trashed video ' + youtube_video_url(video_id))
        return "Video successfully trashed"
    if ret == "AlreadyTrashed":
        return "That video has already been trashed :)"
    return "Unknown return value, please contact @beka and/or @rizend"

def title_of_processed_video(title, author):
    return "Noisebytes - " + title + " by " + author

def description_of_video(title, author):
    return "Title: " + title + "\n" +
           "Author: " + author + "\n" +
           "Patreon: https://patreon.com/noisebridge\n" +
           "Website: https://noisebridge.net/\n\n" +
           "Noisebridge is a 501(c)3 non-profit hackerspace in San Francisco's Mission District, located at 2169 Mission St.\n\n"+
           "We're open to the public every day from 11am to 10pm, so feel free to drop by!\n\n" +
           "We're also funded entirely by the community, so please donate if you like what we do, or the content we produce.\n\n" +
           "Noisebridge is a safe space. You can read about what that means to us at the pages listed here: https://www.noisebridge.net/wiki/Safe_Space"""

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
            return redirect(BASE_ADDR)
        posted_file = request.files['file']
        
        if posted_file.filename == '':
            flash('No selected file')
            print "No selected file"
            return redirect(BASE_ADDR)
        
        if not allowed_file(posted_file.filename):
            flash('Invalid file type. Try these: ' + ' '.join(x for x in ALLOWED_EXTENSIONS))
            print "Invalid file type"
            return redirect(BASE_ADDR)
        
        if posted_file:
            flash('Your file is uploading.')
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
                                                         description_of_video(title, author),
                                                         processed_file)
                if video_id:
                    log_to_slack("Video " + youtube_video_url(video_id) + " ready for moderation. " +
                                 "You can approve it by typing `/approve_noisebyte " + video_id + "`, or trash it "+
                                 "by typing `/trash_noisebyte " + video_id + "`")
                else:
                    log_to_slack("An error was encountered while uploading a video")
                os.remove(upload_file)
                os.remove(processed_file)
            threading.Thread(target=upload_to_youtube_thread).start()

            return redirect(BASE_ADDR)

    return render_template('uploader_app.html')

if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.run(host="127.0.0.1", port=int("3114"), debug=False)
