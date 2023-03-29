from src import mail
from flask import current_app
from flask_mail import Message
from threading import Thread
from pprint import pprint
 
def send_async_email(app, msg):
    with app.app_context():
        with mail.connect() as cnn:
            cnn.send(msg)
            print("Sent...")

def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()

# send_email(
#     subject="Hello",
#     html_body="<b>Hello Flask message sent from Flask-Mail</b>",
#     recipients=["nguyentuankhanhcqt@gmail.com", "19120540@student.hcmus.edu.vn"],
#     sender='nguyentuankhanhcqt@gmail.com',
#     text_body=''
# )