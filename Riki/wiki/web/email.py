import sqlite3
import smtplib
import time


def email():
    t = int(get_time())
    if t == 0:
        conn = sqlite3.connect('Database/database.db')
        cursor = conn.cursor()
        cursor.execute("select username from Users where featured  = ?", (1,))
        user_name = cursor.fetchall()
        cursor.execute("select email from Users where featured  = ?", (1,))
        user_email = cursor.fetchall()
        names = string(user_name)
        emails = string(user_email)
        conn.commit()
        conn.close()
        i = 0
        for address in emails:
            smtp(address, names[i])
            i = i+1


def get_time():
    t = time.localtime()
    current = time.strftime("%H%M%S", t)
    return current


def string(old_list):
    new_list = []
    for e in old_list:
        s = ' '.join(e)
        new_list.append(s)
    return new_list


def smtp(to, name):
    gmail_user = 'realmikiwiki@gmail.com'
    gmail_password = 'mikiwiki1'

    sent_from = gmail_user
    subject = 'Featured Page'
    body = 'Hey %s, check out this cool page. \n http://127.0.0.1:5000/feature/\n' % name

    email_text = """\
    From: %s
    To: %s
    Subject: %s

    %s
    """ % (sent_from, to, subject, body)

    try:
        s = smtplib.SMTP_SSL(host='smtp.gmail.com', port=465)
        s.ehlo()
        s.login(gmail_user, gmail_password)
        s.sendmail(sent_from, to, email_text)
        s.close()
    except:
        print('Something went wrong')
