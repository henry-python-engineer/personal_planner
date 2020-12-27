import smtplib
import imaplib
import email
import pandas as pd
from email.mime.text import MIMEText
import os
import time
 

def get_config():
    config = pd.read_csv('config/config.txt')
    id = config.loc[0, 'id']
    pw = config.loc[0, 'pw']
    return id, pw


def send_email(**kwargs):
    subject = kwargs.get("subject", "Empty Subject")
    content = kwargs.get("content", "Empty Contents")
    id, pw = get_config()
    to = kwargs.get("to", id)
    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.starttls()
    s.login(id, pw)
    msg = MIMEText(content)
    msg['Subject'] = subject
    s.sendmail(id, to, msg.as_string())
    s.quit()


def unit_test(**kwargs):
    send_email(subject="test subject")
    print("test contents")


if __name__ == '__main__':
    unit_test()