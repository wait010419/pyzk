# -*- coding: utf-8 -*-
# -*- coding: gbk -*-
import os
import sys
import time
import datetime
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from pypinyin import lazy_pinyin
from zk import ZK, const

class Attendance_Send(object):
    def __init__(self, mail_host="smtp-host", mail_user="user",mail_pass="pass_word",sender_email="sender_email"):
        self.mail_host=mail_host
        self.mail_user=mail_user
        self.mail_pass=mail_pass
        self.sender=sender_email
        self.login_status=0

    def login(self):
        self.session = smtplib.SMTP(self.mail_host)
        self.session.login(self.mail_user, self.mail_pass)
        self.login_status=1

    def send_email(self,receivers, subject, content):
        self.receivers = receivers  
        self.msg = MIMEText(content)
        #self.msg = MIMEText('<html><h1>Test completed,Test results are as follows:{}</h1></html>'.format(content),'html')
        self.msg['Subject'] = subject
        self.msg['From'] = self.sender
        self.msg['To'] = Header(receivers[0])
        #self.msg['Time'] = Header(datetime.datetime.today().strftime('%Y-%m-%d  %H:%M:%S'))
        self.session.sendmail(self.sender, self.receivers, self.msg.as_string())

    def logout(self):
        self.session.quit()
        self.login_status=0

conn = None
zk = ZK('zk_ip', port=4370)
students = ['user_name']  #user name
days = 1 #record days
base_dir = os.getcwd()

try:
    timeToday = datetime.datetime.today()
    if int(timeToday.strftime('%w')) == 0 or int(timeToday.strftime('%w')) >= 6:
        print ("today is not workday!!!")
        exit()
    #timeToday = datetime.datetime(2019,5,13,9,9,9)

    conn = zk.connect()

    print ('Disabling device ...')
    conn.disable_device()

    print ('--- Get User ---')
    inicio = time.time()
    users = conn.get_users()
    final = time.time()
    print ('took {:.3f}[s]'.format(final - inicio))

    print ('--- Get Attendance ---')
    inicio = time.time()
    attendance = conn.get_attendance()
    final = time.time()
    print ('took {:.3f}[s]'.format(final - inicio))

    print ('Enabling device ...')
    conn.enable_device()

    #update user dict
    students_dict={}
    for user in users:
        if user.name in students:
            print (user.user_id + ':' + user.name)
            students_dict[user.user_id] = user.name

    #display attendance
    att_send = Attendance_Send()
    for std in students:
        print()
        message=''
        timeToday = datetime.datetime.today()
        cnt = days
        while cnt > 0:
            if int(timeToday.strftime('%w')) == 0 or int(timeToday.strftime('%w')) >= 6:
                cnt -= 1;
                timeToday = timeToday+datetime.timedelta(days=-1)
                continue;

            timeWorkOn = datetime.datetime(timeToday.year, timeToday.month, timeToday.day, 9,1,0)
            timeWorkOff = datetime.datetime(timeToday.year, timeToday.month, timeToday.day, 18,0,0)
            if int(timeToday.strftime('%w'))  == 1:
                timeWorkOff = timeWorkOff+datetime.timedelta(days=-3)
            else:
                timeWorkOff = timeWorkOff+datetime.timedelta(days=-1)
            tswon = time.mktime(time.strptime(timeWorkOn.strftime('%Y-%m-%d %H:%M:%S'), "%Y-%m-%d %H:%M:%S"))
            tswoff = time.mktime(time.strptime(timeWorkOff.strftime('%Y-%m-%d %H:%M:%S'), "%Y-%m-%d %H:%M:%S"))

            std_id = list(students_dict.keys())[list(students_dict.values()).index(std)] 
            workon = None
            workoff = None
            for att in attendance:
                if att.user_id == std_id:
                    timeStr = time.strptime(att.timestamp.strftime('%Y-%m-%d %H:%M:%S'), "%Y-%m-%d %H:%M:%S")
                    timestamp = time.mktime(timeStr)
                    if timestamp > tswoff and timestamp < (tswoff + 9*3600):
                        workoff = att.timestamp
                    if timestamp < tswon and timestamp > (tswon - 3*3600) and not workon:
                        workon = att.timestamp
                        #print ("ATT {:>2}: uid:{:>3}, user_name:{:>5} t: {}, w:{}".format(i, att.uid, 
                        #    students_dict[att.user_id], att.timestamp, att.timestamp.strftime('%w')))

            if workon:
                print("{} work on at {}".format(students_dict[std_id],workon))
                #message=message+"{} work on at {}\r\n".format(students_dict[std_id],workon)
            else:
                print("\033[31m{} do not work on {}\033[0m".format(students_dict[std_id],timeWorkOn.strftime('%Y-%m-%d')))
                message=message+"{} do not work on {}\r\n".format(students_dict[std_id],timeWorkOn.strftime('%Y-%m-%d'))

            if workoff:
                print("{} work off at {}".format(students_dict[std_id],workoff))
                #message=message+"{} work off at {}\r\n".format(students_dict[std_id],workoff)
            else:
                print("\033[31m{} do not work off {}\033[0m".format(students_dict[std_id],timeWorkOff.strftime('%Y-%m-%d')))
                message=message+"{} do not work off {}\r\n".format(students_dict[std_id],timeWorkOff.strftime('%Y-%m-%d'))

            cnt -= 1;
            timeToday = timeToday+datetime.timedelta(days=-1)
        if message != '':
            if att_send.login_status == 0:
                att_send.login()
            att_send.send_email(['receiver_email'], 'attedance-'+datetime.datetime.today().strftime('%Y-%m-%d'), message)
    if att_send.login_status == 1:
        att_send.logout()



except Exception as e:
    print ("Process terminate : {}".format(e))
finally:
    if conn:
        conn.disconnect()
