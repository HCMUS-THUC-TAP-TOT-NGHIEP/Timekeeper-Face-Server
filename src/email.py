from flask import current_app
from flask_mail import Message, Mail
from threading import Thread 
mail = Mail()

def send_async_email(app, msg):
    with app.app_context():
        with mail.connect() as cnn:
            cnn.send(msg)

def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()