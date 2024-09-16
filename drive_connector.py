import json
import logging
import requests
import streamlit as st
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from requests_oauthlib import OAuth2Session
from googleapiclient.http import HttpError


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Log format
                    datefmt='%Y-%m-%d %H:%M:%S')# Date format


with open('secret.json', 'r') as f:
    config = json.load(f)

CLIENT_SECRET_FILE = config["web"]["path"]
MICROSOFT_SECRET_FILE = config["microsoft"]


st.sidebar.title("KRL Nav")
app_mode = st.sidebar.selectbox("Choose to Upload", ["Upload Files", "Connect to Google Drive", "Connect to Microsoft One Drive"])

# Function to authenticate to google drive and return the credentials
def authenticate_gdrive():
    logging.info(f"Authenticating with Google drive")

    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
    
    creds = None

    if 'token' in st.session_state:
        creds = Credentials.from_authorized_user_info(json.loads(st.session_state['token']), SCOPES)
    
    else:
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRET_FILE, scopes=SCOPES)
    
        # The following line sets the redirect_uri to the current app URL
        flow.redirect_uri = st.experimental_get_query_params().get("redirect_uri", ["http://localhost:8501/"])[0]
        logging.info(f"Using redirect URI: {flow.redirect_uri}")

        # Force login and consent
        auth_url, _ = flow.authorization_url(prompt='consent')
        
        # Change from markdown link to a button
        if st.sidebar.button("Connect to Drive"):
            st.experimental_set_query_params(redirect_uri=flow.redirect_uri)
            st.write(f'<meta http-equiv="refresh" content="0; url={auth_url}">', unsafe_allow_html=True)
        
        # If the user has completed the OAuth flow, fetch the token
        query_params = st.experimental_get_query_params()
        if 'code' in query_params:
            try:
                flow.fetch_token(code=query_params['code'][0])
                creds = flow.credentials
                st.session_state['token'] = creds.to_json()
            except Exception as e:
                logging.info(f"Error fetching token: {e}")
                st.error("Authentication failed. Please try again.")

    return creds

# Initialize session state
if 'authenticated_microsoft' not in st.session_state:
    st.session_state['authenticated_microsoft'] = False

if 'onedrive_token' not in st.session_state:
    st.session_state['onedrive_token'] = None

# Function to authenticate to Microsoft One Drive and return the credentials
def authenticate_onedrive():
    logging.info("Authenticating with Microsoft OneDrive")

    MICROSOFT_CLIENT_ID = config["microsoft"]["client_id"]
    MICROSOFT_TENANT_ID = config["microsoft"]["tenant_id"]
    MICROSOFT_CLIENT_SECRET = config["microsoft"]["client_secret"]
    REDIRECT_URI = config["microsoft"]["redirect_uris"][0]
    AUTH_URL = f'https://login.microsoftonline.com/{MICROSOFT_TENANT_ID}/oauth2/v2.0/authorize'
    TOKEN_URL = f'https://login.microsoftonline.com/{MICROSOFT_TENANT_ID}/oauth2/v2.0/token'

    
    SCOPES = ['openid', 'profile', 'email', 'Files.Read']


    if 'onedrive_token' in st.session_state and st.session_state['onedrive_token']:
        token = st.session_state['onedrive_token']

    else:
        onedrive = OAuth2Session(MICROSOFT_CLIENT_ID, scope=SCOPES, redirect_uri=REDIRECT_URI)
        auth_url, state = onedrive.authorization_url(AUTH_URL, prompt="consent")

        # Display the button for authentication
        if st.sidebar.button("Connect to OneDrive"):
            st.experimental_set_query_params(redirect_uri=REDIRECT_URI)
            st.write(f'<meta http-equiv="refresh" content="0; url={auth_url}">', unsafe_allow_html=True)

            return None

        query_params = st.experimental_get_query_params()
        if 'code' in query_params:
            try:
                token = onedrive.fetch_token(
                    TOKEN_URL,
                    code=query_params['code'][0],
                    client_secret=MICROSOFT_CLIENT_SECRET
                )
                st.session_state['onedrive_token'] = token
            except Exception as e:
                logging.error(f"Error fetching OneDrive token: {e}")
                st.error("Authentication failed. Please try again.")
                return None

    return st.session_state.get('onedrive_token')

    
# Lists files from Google Drive
def list_gdrive_files(creds):
    logging.info("Listing google drive files")

    files = []

    try:
        service = build('drive', 'v3', credentials=creds)
        page_token = None

        while True:    
            results = (
                        service.files().list(pageSize=100, q="mimeType = 'application/pdf' or" \
                                             "mimeType = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' or " \
                                                "mimeType = 'application/vnd.openxmlformats-officedocument.presentationml.presentation' or "\
                                                    "mimeType = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' or "\
                                                        "mimeType = 'application/vnd.ms-excel' or" \
                                                            "mimeType = 'text/csv' or" \
                                                                "mimeType = 'text/plain'",
                        spaces="drive",
                        fields="nextPageToken, files(id, name)",
                        pageToken = page_token).execute()
                        )
            
            items = results.get('files', [])
            for item in items:
                files.append(item['name'])

            if page_token is None:
                break
    except HttpError as error:
        logging.error("Failed to list files")
        st.error(f"An error occurred: {error}")
    
    return files

def list_onedrive_files(token):
    logging.info(f"Access token: {token.get('access_token', 'None')}")
    print(f"TOKEN: {token['access_token']}")

    MICROSOFT_GRAPH_API_URL = "https://graph.microsoft.com/v1.0"
    ONEDRIVE_API_ENDPOINT = f"{MICROSOFT_GRAPH_API_URL}/me/drive/root/children"

    if not token or 'access_token' not in token:
        st.error("Access token is missing.")
        return

    headers = {
        'Authorization': f'Bearer {token["access_token"]}',
        'Content-Type': 'application/json'
    }

    

    try:
        response = requests.get(ONEDRIVE_API_ENDPOINT, headers=headers)
        response.raise_for_status()  # Raises an HTTPError for bad responses

        

        files = response.json().get('value', [])
        if files:
            st.write("Files in OneDrive:")
            for file in files:
                st.write(f"Name: {file['name']}, Type: {file.get('file', 'Folder')}")
        else:
            st.write("No files found in OneDrive.")

    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
        st.write(f"HTTP error occurred: {http_err}")

    except Exception as err:
        logging.error(f"Other error occurred: {err}")
        st.write(f"Other error occurred: {err}")



# Handles disconnection
def disconnect():
    logging.info("Disconnecting User")

    if 'token' in st.session_state:
        del st.session_state['token']
        logging.info("Cleared session token")
    
    if 'onedrive_token' in st.session_state:
        del st.session_state['onedrive_token']
        logging.info("Cleared one drive session token")
        
    if 'authenticated_microsoft' in st.session_state:
        st.session_state['authenticated_microsoft'] = False
    
    if 'files' in st.session_state:
        del st.session_state['files']
        logging.info("Cleared files list from session")

    st.success("Disconnected from drive")

if app_mode == "Upload Files":
    logging.info("Files Uploaded")
    st.title("File Upload")
    uploaded_files = st.file_uploader("Choose a file", accept_multiple_files=True)
    
    if uploaded_files:
        for uploaded_file in uploaded_files:
            st.write(f"Uploaded file: {uploaded_file.name}")
            
    
elif app_mode == "Connect to Google Drive":
    st.title("Google Drive Integration")
    
    creds = authenticate_gdrive()      

    
    if creds and creds.valid:
        st.sidebar.button("Disconnect", on_click=disconnect)

        files = list_gdrive_files(creds)
        
        if files:
            st.header('Files in your Google Drive:')
            for file in files:
                st.write(file)
        else:
            st.write('No files found in your Google Drive.')

elif app_mode == "Connect to Microsoft One Drive":
    st.title("Microsoft OneDrive Integration")

    
    
    token = authenticate_onedrive()
    
    if token:
        st.sidebar.button("Disconnect", on_click=disconnect)
        
        list_onedrive_files(token)
    else:
        st.write("Please authenticate with OneDrive.")


