# -*- coding: utf-8 -*-
"""
this file provides some function to send a email.
"""

from config import ML_ADDRESS, MAIL_SUBJECT_FORMAT, MAIL_FROM, MAIL_PASSWD
from email.MIMEText import MIMEText
from email.Utils import formatdate
from email.Header import Header
import smtplib

from string import Template

def buildTitle(room_name, topic_name):
    """
    build a email title from room name and topic name according to
    config.MAIL_SUBJECT_FORMAT.
    """
    s = Template(MAIL_SUBJECT_FORMAT)
    return s.substitute(topic = topic_name, room = room_name)
    

def createMsg(room_name, topic_name, body):
    """
    create a MIMEText instance.
    """
    msg = MIMEText(body.encode('utf-8'), 'plain', 'utf-8')
    msg['Subject'] = Header(buildTitle(room_name, topic_name).encode('utf-8'),
                            'utf-8')
    msg['From'] = MAIL_FROM
    msg["To"] = ML_ADDRESS
    msg['Date'] = formatdate()
    return msg
    
def sendMail(room_name, topic_name, body):
    """
    send a email to ML_ADDRESS from MAIL_PASSWD via gmail.
    the subject of the mail is defined by room_name and topic_name.
    body is the message of the mail.
    """
    msg = createMsg(room_name, topic_name, body)
    s = smtplib.SMTP("smtp.gmail.com", 587)
    s.ehlo()
    s.starttls()
    s.ehlo()
    s.login(MAIL_FROM, MAIL_PASSWD)
    s.sendmail(MAIL_FROM, [ML_ADDRESS], msg.as_string())
    s.close()
    return True
