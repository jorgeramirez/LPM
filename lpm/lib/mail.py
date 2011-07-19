# -*- coding: utf-8 -*-

"""
Este archivo contiene la clase que permite mandar mails a través del smtp de gmail 

@authors:
    - U{Carlos Bellino<mailto:carlosbellino@gmail.com>}
    - U{Nahuel Hernández<mailto:nahuel.11990@gmail.com>}
    - U{Jorge Ramírez<mailto:jorgeramirez1990@gmail.com>}

@since: 1.0
"""

# Import smtplib for the actual sending function
import smtplib
from email.mime.text import MIMEText

class Gmail():
    def __init__(self):
        smtpserver = "smtp.gmail.com"
        smtpuser = "sistema.lpm"
        smtppassword = "lambdaproject"
        self.session = smtplib.SMTP(smtpserver, 587)
        self.session.starttls()
        self.session.ehlo()
        self.session.login(smtpuser, smtppassword)

    def enviar_mail(self, to, text):
        me = "sistema.lpm@gmail.com"
        msg = MIMEText(text, 'plain', 'utf-8')

        msg['Subject'] = u"Recuperación de contraseña"
        msg['From'] = me
        msg['To'] = to
    
        self.session.sendmail(me, to, msg.as_string())

    def quit(self):
        self.session.quit()
