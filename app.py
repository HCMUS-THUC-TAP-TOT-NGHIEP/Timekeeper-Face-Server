# from src import app
from flask import Flask, request, jsonify, render_template
from datetime import datetime


# from __future__ import print_function
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import google.auth
import base64
from email.message import EmailMessage

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST','PUT', 'DELETE'])
def default():
    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    return f"<h1>Welcome Server!. Today is {now}</h1>"

# Authentication
@app.route('/api/auth/register', methods=['POST'])
def RegisterAccount():
    try:
        
        email = request.json["email"]
        password = request.json["password"]
        return f"<div>{email}</div><div>{password}</div>"
    except KeyError as e:
        return f"<h1>No email or pass word</h1><div>{e.__str__()}</div>"

#Email
# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.send']
@app.route('/api/mail', methods=['GET', "POST"])
def mail():
    try:
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        # # Call the Gmail API
        # service = build('gmail', 'v1', credentials=creds)
        # results = service.users().labels().list(userId='me').execute()
        # labels = results.get('labels', [])
        # if not labels:
        #     print('No labels found.')
        #     return
        # print('Labels:')
        # for label in labels:
        #     print(label['name'])
        # return jsonify(labels)

        # create gmail api client
        service = build('gmail', 'v1', credentials=creds)

        message = EmailMessage()

        content = 'This is automated draft mail'
        html_message = render_template("test_email.html", content=content)
        print(F'html_message: {html_message}')
        message.set_content(html_message)

        # message['To'] = '19120540@student.hcmus.edu.vn'
        message['To'] = 'nguyentuankhanhcqt@gmail.com'
        message['From'] = 'nguyentuankhanhcqt@gmail.com'
        message['Subject'] = 'Automated draft'

        # encoded message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        create_message = {
            'raw': encoded_message
        }
        send_message = (service.users().messages().send
                        (userId="me", body=create_message).execute())
        # print(F'Message Id: {send_message["id"]}')
        return jsonify(send_message)
    except HttpError  as error:
        # TODO(developer) - Handle errors from gmail API.
        return f'An error occurred: {error}'
    except KeyError:
        return f'<div>An error occurred {error}</div>'

if __name__ == '__main__':
    # app.run()
    app.run(debug=True)