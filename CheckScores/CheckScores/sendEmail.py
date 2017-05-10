import os
import smtplib
import ConfigParser

path = os.path.dirname(os.path.abspath(__file__))

#pull configs from a config file
config = ConfigParser.ConfigParser()
config.read(path + "/config.ini")
fromaddr = config.get('email','fromaddr')
toaddr = config.get('email','toaddr')
svr = config.get('email','svr')
euser = config.get('email','euser')
epasswd = config.get('email','epasswd')


# called to send a passed message
def sendMessage(msg) :
    
    server = smtplib.SMTP(svr)
    server.ehlo()
    server.starttls()
    server.login(euser,epasswd)
    server.sendmail(fromaddr, toaddr, msg)
    server.quit()