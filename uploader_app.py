"""Noisebyte uploader flask app"""
import os
import binascii
from subprocess import call
import threading
from flask import Flask, request, redirect, url_for, flash
import youtube_uploader

UPLOAD_FOLDER = './uploads'
TEMP_FOLDER = './temp'
ALLOWED_EXTENSIONS = set(['mov', 'mp4', 'avi', 'mkv', 'wmv', 'mpeg4', 'mpg'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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
            return redirect(request.url)
        posted_file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if posted_file.filename == '':
            flash('No selected file')
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
                youtube_uploader.upload_video(title_of_processed_video(title, author),
                                              processed_file)
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
    app.run(debug=True)
