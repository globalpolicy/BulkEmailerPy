# BulkEmailerPy
A Python 3 script to send emails to multiple recipients via SMTP

# How it works
The function `send_mail` reads the recipients' email addresses from a specified sqlite database file having the schema:

```CREATE TABLE "Emails" ("email"	TEXT UNIQUE,	"processed"	INTEGER NOT NULL DEFAULT 0,	"warmedup"	INTEGER NOT NULL DEFAULT 0,	PRIMARY KEY("email"));```

The `email` field is self-descriptive. `warmedup` however requires some discussion:

>## Warm-up email
>The `send_mail` function is designed to work around the concept of "warm-up emails". 
>The basic idea is this: if you directly send an email containing suspicious keywords or more importantly, external links, the recipient's email client is likely going to flag it as spam. 
>To mitigate this, you first send an innocuous email free of any spam-detection triggers - this is the "warm-up email". 
>
>After some time, preferably a couple of minutes, follow up with the actual email you intend to send.
>The rationale is that the recipient's client will build a reputation for your email adress based on that first-contact email you sent - the warm-up email, and treat your subsequent email(s) with more leniency.

So, the `warmedup` field indicates whether a warm-up email has already been sent to the recipient (`1` for True, `0` for False).

You would first call the `send_mail` function to send warm-up emails to a specified number of recipients from your database by setting the penultimate parameter to `True`:

>```sent_number = send_mail('some.id@outlook.com', 'LOGIN_PASSWORD/APP_PASSWORD', 'Some subject text', 'Some innocent email message.', 'sqlite_database_file_path', True, 50)```

The last parameter by the way is the batch size - the number of recipients you want the email sent to back-to-back. You may want to change it up depending on the SMTP server you're using (at the time of this writing, Yahoo's servers typically block you at around the 15 mark).

Once this function returns, it will have updated the `warmedup` field of the database to `1` for all the recipients to whom the email has been successfully sent.

You then wait a couple of minutes then call it again as:

>```sent_number = send_mail('some.id@outlook.com', 'LOGIN_PASSWORD/APP_PASSWORD', 'Some subject text', 'Your intended email message.', 'sqlite_database_file_path', False, 50)```

Notice that the penultimate parameter is now set to `False` meaning this is now the follow-up email. So, the function is now going to send your new email message to only those recipients whose `warmedup` value is set to `1` and `processed` value is set to `0`. 

Once the function returns, the `processed` field will have been set to `1` for all those recipients to whom the second email has been successfully sent.

So, in the end, both the `warmedup` and the `processed` fields are going to be end up being `1` for those recipients to whom the intended email message was successfully sent.
