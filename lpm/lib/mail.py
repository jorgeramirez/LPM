# Import smtplib for the actual sending function
import smtplib
from email.mime.text import MIMEText

class Gmail():
    def __init__():
        smtpserver = "smtp.gmail.com"
        smtpuser = "sistema.lpm"
        smtppassword = "lambdaproject"
        self.session = smtplib.SMTP(smtpserver, 587)
        self.session.starttls()
        self.session.ehlo()
        self.session.login(smtpuser, smtppassword)
        self.session.starttls()

    def enviar_mail(self, to, text):
        me = "sistema.lpm@gmail.com"
        msg = MIMEText(text)

        msg['Subject'] = u"Recuperación de contraseña"
        msg['From'] = me
        msg['To'] = to
    
        self.session.sendmail(me, [you], msg.as_string())

    def quit(self):
        self.session.quit()
