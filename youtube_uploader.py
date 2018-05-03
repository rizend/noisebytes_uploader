#!/usr/bin/python
"""Noisebytes youtube video uploader module"""

import httplib
import random
import time
import pickle
import re
import httplib2

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

httplib2.RETRIES = 1

MAX_RETRIES = 10
RETRIABLE_EXCEPTIONS = (
    httplib2.HttpLib2Error, IOError, httplib.NotConnected,
    httplib.IncompleteRead, httplib.ImproperConnectionState,
    httplib.CannotSendRequest, httplib.CannotSendHeader,
    httplib.ResponseNotReady, httplib.BadStatusLine)

RETRIABLE_STATUS_CODES = [500, 502, 503, 504]
CLIENT_SECRETS_FILE = './client_secrets.json'
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'
VALID_PRIVACY_STATUSES = ('public', 'private', 'unlisted')
CREDS_FILE = 'creds.priv'

def load_credentials():
    handle = open(CREDS_FILE, "r")
    credentials = pickle.load(handle)
    handle.close()
    return credentials

def get_authenticated_service():
    credentials = load_credentials()
    return build(API_SERVICE_NAME, API_VERSION, credentials=credentials)

def initialize_upload(youtube, title, filename):
    body = dict(
        snippet=dict(title=title),
        status=dict(privacyStatus='unlisted')
    )

    insert_request = youtube.videos().insert(
        part=','.join(body.keys()),
        body=body,
        media_body=MediaFileUpload(filename, chunksize=-1, resumable=True)
    )

    return resumable_upload(insert_request)

def resumable_upload(request):
    response = None
    error = None
    retry = 0
    while response is None:
        try:
            print 'Uploading file...'
            _, response = request.next_chunk()
            if response is not None:
                if 'id' in response:
                    print 'Video id "%s" was successfully uploaded.' % response['id']
                    handle = open('./uploads/queue.txt', 'a')
                    handle.write(response['id'] + '\n')
                    handle.close()
                    return response['id']
                exit('The upload failed with an unexpected response: %s' % response)
        except HttpError, err:
            if err.resp.status in RETRIABLE_STATUS_CODES:
                error = 'A retriable HTTP error %d occurred:\n%s' % \
                        (err.resp.status, err.content)
            else:
                raise
        except RETRIABLE_EXCEPTIONS, err:
            error = 'A retriable error occurred: %s' % err

        if error is not None:
            print error
            retry += 1
            if retry > MAX_RETRIES:
                exit('No longer attempting to retry.')

            max_sleep = 2 ** retry
            sleep_seconds = random.random() * max_sleep
            print 'Sleeping %f seconds and then retrying...' % sleep_seconds
            time.sleep(sleep_seconds)

def upload_video(title, filename):
    youtube = get_authenticated_service()

    try:
        return initialize_upload(youtube, title, filename)
    except HttpError, err:
        print 'An HTTP error %d occurred:\n%s' % (err.resp.status, err.content)

def approve_video(video_id):
    youtube = get_authenticated_service()

    handle = open('./uploads/queue.txt', 'r')
    queue = handle.read()
    handle.close()

    needle = re.compile('^'+video_id+'$', re.M).search(queue)

    if needle:
        # video is in queue, update it and remove
        handle = open('./uploads/queue.txt', 'w')
        handle.write(queue[0:needle.start()] + queue[needle.end()+1:-1])
        handle.close()

        properties = dict(
            id=video_id,
            status=dict(privacyStatus='public')
        )
        youtube.videos().update(body=properties, part='status').execute()

        playlist_properties = dict(
            snippet=dict(
                playlistId='PLpphGRHXhSFiiH9MD5GyVArhCnO_Dpt5A',
                resourceId=dict(
                    kind='youtube#video',
                    videoId=video_id
                ),
                position=0
            )
        )
        youtube.playlistItems().insert(body=playlist_properties, part='snippet').execute()

        return "Approved"
    
    return "AlreadyApproved"

def trash_video(video_id):
    youtube = get_authenticated_service()

    handle = open('./uploads/queue.txt', 'r')
    queue = handle.read()
    handle.close()

    needle = re.compile('^'+video_id+'$', re.M).search(queue)

    if needle:
        # video is in queue, update it and remove
        handle = open('./uploads/queue.txt', 'w')
        handle.write(queue[0:needle.start()] + queue[needle.end()+1:-1])
        handle.close()

        properties = dict(
            id=video_id,
            status=dict(privacyStatus='public')
        )
        youtube.videos().delete(id = video_id).execute()

        return "Trashed"

    return "AlreadyTrashed"
