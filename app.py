# # from src import app
# from flask import Flask, request
# from datetime import datetime
# from dotenv import load_dotenv
# load_dotenv()
# import os
# from flask_mail import Mail, Message

# app = Flask(__name__)
# app.config['MAIL_SERVER']= os.getenv('MAIL_SERVER')
# app.config['MAIL_PORT'] = os.getenv('MAIL_PORT')
# app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
# app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
# app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS') is True
# app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL')
# mail = Mail(app)


# PORT =  int(5000 if os.getenv('PORT') is None else os.getenv('PORT'))
# @app.route('/', methods=['GET', 'POST','PUT', 'DELETE'])
# def default():
#    print(type(app.config['MAIL_USE_TLS']))
#    msg = Message('Hello', sender = 'Khanh', recipients = ['nguyentuankhanhcqt@gmail.com', '19120540@student.hcmus.edu.vn'])
#    msg.body = "Hello Flask message sent from Flask-Mail"
# #    mail.connect()
#    with mail.connect() as conn:
#     conn.send(msg)
#    return "Sent"

# # Authentication
# @app.route('/api/auth/register', methods=['POST'])
# def RegisterAccount():
#     try:
#         email = request.json["email"]
#         password = request.json["password"]
#         return f"<div>{email}</div><div>{password}</div>"
#     except KeyError as e:
#         return f"<h1>No email or pass word</h1><div>{e.__str__()}</div>"

# #Email
# # If modifying these scopes, delete the file token.json.
# def SendMail(subject, sender, recipients, text_body, html_body):
#     try:
#         msg = Message(subject, sender=sender, recipients=recipients)
#         msg.body = text_body
#         msg.html = html_body
#         with mail.connect() as conn:
#             mail.send(msg)
#     except Exception as e:
#         print(f'Error: {e.__str__()}')

from src import create_app
app = create_app()

if __name__ == '__main__':
    app.run(threaded=True)
    # app.run(debug=True, port=PORT)