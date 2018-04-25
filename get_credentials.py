"""CLI utility used to generate the creds.priv file which is then used to authorize us to upload to youtube"""
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow

CLIENT_SECRETS_FILE = './client_secrets.json'
SCOPES = ['https://www.googleapis.com/auth/youtube']
CREDS_FILE = 'creds.priv'

def save_credentials(credentials):
    handle = open(CREDS_FILE, "wb")
    pickle.dump(credentials, handle)
    handle.close()

def get_credentials():
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
    flow.authorization_url(access_type='offline', include_granted_scopes='true')
    credentials = flow.run_console()
    save_credentials(credentials)

if __name__ == '__main__':
    get_credentials()
