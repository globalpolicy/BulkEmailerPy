import smtplib
import sqlite3

# crafts the SMTP data to be sent
def make_smtp_data(sender_email, recipient, subject_text, email_text):
    # SMTP headers and their corresponding values need to be specified as plain ASCII string:
    smtp_raw_data = """\
    From: %s
    To: %s
    Subject: %s

    %s
    """ % (sender_email, recipient, subject_text, email_text)
    return smtp_raw_data


# actual function for sending emails
def send_mail(sender_email, passcode, subject_text, email_text, recipients_sqlitedb_filepath, is_warmup_email,
              email_limit):
    """
    Sends email. If the is_warmup_email flag is False, email will be sent only to those recipients for whom the 'warmedup' and the 'processed' fields are set to 1 and 0 respectively in the database. This means you must first call this method with the is_warmup_email parameter set to True. Similarly, if the is_warmup_email parameter is set to True, email is sent to all recipients whose 'warmedup' field value is 0.

    :param sender_email: Email id used to authenticate to the SMTP server. This will be visible to the recipient. If using Yahoo, provide the full address e.g. somename@yahoo.com
    :param passcode: Password of the email id used to authenticate to the SMTP server. If a Yahoo id is used in the 'sender' parameter, this should be a so-called 'app password'
    :param subject_text: Subject text. Only single line.
    :param email_text: The message body. Can be multi line.
    :param recipients_sqlitedb_filepath: Path of the sqlite db file containing the recipient emails. Three columns needed of the schema:  CREATE TABLE "Emails" (	"email"	TEXT UNIQUE,	"processed"	INTEGER NOT NULL DEFAULT 0,	"warmedup"	INTEGER NOT NULL DEFAULT 0,	PRIMARY KEY("email")    );
    :param is_warmup_email: True if this mail is supposed to be a warm-up mail for anti-anti-spam.
    :param email_limit: The maximum number of emails that will be sent (0 for no limit). Can be useful to avoid being rate-limited. Different smtp providers have different limits.
    :return: The number of recipients to whom the email was sent successfully.
    """
    if sender_email.__contains__('gmail.com'):
        conn = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        # conn.set_debuglevel(1) # this lets us see in the console window what conversation's happening between the server and our program

    elif sender_email.__contains__('yahoo.com'):
        conn = smtplib.SMTP_SSL('smtp.mail.yahoo.com', 465)
        # conn.set_debuglevel(1)

    elif sender_email.__contains__('outlook.com'):
        conn = smtplib.SMTP('smtp-mail.outlook.com', 587)
        # conn.set_debuglevel(1)
        conn.ehlo()
        conn.starttls()

    else:
        return

    conn.ehlo()
    conn.login(sender_email, passcode)

    db = sqlite3.connect(recipients_sqlitedb_filepath)

    if is_warmup_email:
        select_query = "SELECT email FROM Emails WHERE warmedup=0"
    else:
        select_query = "SELECT email FROM Emails WHERE processed=0 and warmedup=1"

    cursor = db.execute(select_query)

    success_count = 0  # counter for successful email sends
    for row in cursor:
        recipient = row[0]

        error_times = 0
        successfully_sent = False  # flag for testing if the current recipient was successfully sent
        while error_times < 10 and not successfully_sent:
            try:
                conn.sendmail(sender_email, recipient, make_smtp_data(sender_email, recipient, subject_text,
                                                                      email_text))

                successfully_sent = True  # if code lands here, it was a successful send
                success_count = success_count + 1

                # update the database accordingly
                if is_warmup_email:
                    update_query = "UPDATE Emails SET warmedup=1 WHERE email='" + recipient + "'"
                else:
                    update_query = "UPDATE Emails SET processed=1 WHERE email='" + recipient + "'"
                db.execute(update_query)
                db.commit()  # write the changes to the db file right away

                print("[", success_count, "]: Email sent to " + recipient + " successfully!")
            except Exception as e:
                error_times = error_times + 1
                print(e.__class__, "occurred for ", "[", recipient, "]")

        # stop if we've tried too many times
        if error_times == 10:
            break

        # stop if we've reached the specified email limit
        if success_count == email_limit:
            break

    conn.quit()  # close the SMTP connection
    db.close()  # close the database connection

    return success_count
