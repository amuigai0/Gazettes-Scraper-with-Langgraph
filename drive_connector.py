import streamlit as st
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import HttpError
import json

# Define the OAuth 2.0 scopes
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']


CLIENT_SECRET_FILE = 'secret.json'


st.sidebar.title("KRL Nav")
app_mode = st.sidebar.selectbox("Choose to Upload", ["Connect to Google Drive", "Upload Files"])

# Function to authenticate and return the credentials
def authenticate():
    
    creds = None

    if 'token' in st.session_state:
        creds = Credentials.from_authorized_user_info(json.loads(st.session_state['token']), SCOPES)
    
    else:
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRET_FILE, scopes=SCOPES)
    
        # The following line sets the redirect_uri to the current app URL
        flow.redirect_uri = st.experimental_get_query_params().get("redirect_uri", ["http://localhost:8501/"])[0]

        # Force login and consent
        auth_url, _ = flow.authorization_url(prompt='consent')
        
        # Change from markdown link to a button
        if st.sidebar.button("Connect to Drive"):
            st.experimental_set_query_params(redirect_uri=flow.redirect_uri)
            st.write(f'<meta http-equiv="refresh" content="0; url={auth_url}">', unsafe_allow_html=True)
        
        # If the user has completed the OAuth flow, fetch the token
        query_params = st.experimental_get_query_params()
        if 'code' in query_params:
            flow.fetch_token(code=query_params['code'][0])
            creds = flow.credentials
            st.session_state['token'] = creds.to_json()

    return creds

# Handles disconnection
def disconnect():
    if 'token' in st.session_state:
        del st.session_state['token']
        st.success("Disconnected from Google Drive.")
        st.rerun()

# Lists files from Google Drive
def list_files(creds):

    folders = []

    try:
        service = build('drive', 'v3', credentials=creds)
        page_token = None

        while True:    
            results = (
                        service.files().list(pageSize=10, q="mimeType = 'application/vnd.google-apps.folder'",
                        spaces="drive",
                        fields="nextPageToken, files(id, name)",
                        pageToken = page_token).execute()
                        )
            
            items = results.get('files', [])
            for item in items:
                folders.append(item['name'])

            if page_token is None:
                break
    except HttpError as error:
        st.error(f"An error occurred: {error}")
    
    return folders


if app_mode == "Upload Files":
    st.title("File Upload")
    uploaded_files = st.file_uploader("Choose a file", accept_multiple_files=True)
    
    if uploaded_files:
        for uploaded_file in uploaded_files:
            st.write(f"Uploaded file: {uploaded_file.name}")
            
    
elif app_mode == "Connect to Google Drive":
    st.title("Google Drive Integration")
    
    creds = authenticate()

    if st.sidebar.button("Disconect"):
        st.success("Disconnected Google Drive Successfully!")

    
    if creds and creds.valid:
        folders = list_files(creds)
        
        if folders:
            st.header('Folders in your Google Drive:')
            for folder in folders:
                st.write(folder)
        else:
            st.write('No folders found in your Google Drive.')
