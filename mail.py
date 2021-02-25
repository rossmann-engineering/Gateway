import logging
import config as cfg
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

def send_mail(address, filename = None, body = None):


    config = cfg.Config.getConfig()

    if not 'emailfromaddress' in config or not 'smtphost' in config or not 'smtpport':
        return

    fromaddr = config['emailfromaddress']
    toaddr = address

    logging.info("Send Mail to {0}".format(toaddr))

    # instance of MIMEMultipart
    msg = MIMEMultipart()

    # storing the senders email address
    msg['From'] = fromaddr

    # storing the receivers email address
    msg['To'] = toaddr

    # storing the subject
    msg['Subject'] = "Message from Gateway"


    # string to store the body of the mail
    if filename is not None:
        body = 'Attached the Register logfile of your Gateway"'
    else:
        body = body

    # attach the body with the msg instance
    msg.attach(MIMEText(body, 'plain'))

    # open the file to be sent
    #filename = "File_name_with_extension"
    if filename is not None:
        attachment = open(filename, "rb")

        # instance of MIMEBase and named as p
        p = MIMEBase('application', 'octet-stream')

        # To change the payload into encoded form
        p.set_payload((attachment).read())

        # encode into base64
        encoders.encode_base64(p)

        p.add_header('Content-Disposition', "attachment; filename= %s" % 'registerlogdata.csv')

        # attach the instance 'p' to instance 'msg'
        msg.attach(p)

    # creates SMTP session
    s = smtplib.SMTP(host=config['smtphost'], port=int(config['smtpport']))


    # start TLS for security
    if bool(config.get('smtpenabletls', True)):
        s.starttls()

    # Authentication
    if 'smtpusername' in config:
        s.login(config['smtpusername'], config.get("smtppassword", ''))

    # Converts the Multipart msg into a string
    text = msg.as_string()

    # sending the mail
    s.sendmail(fromaddr, toaddr, text)

    # terminating the session
    s.quit()

if __name__ == "__main__":
    send_mail('info@rossmann-engineering.de', body='test')