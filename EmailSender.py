from email.message import EmailMessage
import ssl 
import smtplib

subject='check out this email'
body="email body"

class MailSender:
    __password='uiro zcjz krve jjxh'
    __email_sender='flaviusandrei07@gmail.com'

    def send_email(self,email_destinatie,subiect,body):
        em=EmailMessage()
        em['From']=self.__email_sender
        em['To']=email_destinatie
        em['Subject']=subiect
        em.set_content(body)

        context=ssl.create_default_context()

        with smtplib.SMTP_SSL('smtp.gmail.com',465,context=context) as smtp:
            smtp.login(__email_sender,__password)
            smtp.sendmail(__email_sender,email_destinatie,em.as_string())