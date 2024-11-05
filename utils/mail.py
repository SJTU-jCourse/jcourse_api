import smtplib
import ssl
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

def send_mail_inner(sender, sender_alias, sender_pwd, recipient_list, subject, body, host, port, is_use_ssl):
    try:
        message = MIMEMultipart('alternative')
        message['Subject'] = Header(subject, 'UTF-8')
        message['From'] = formataddr([sender_alias, sender])
        message['To'] = ",".join(recipient_list)
        to_addr_list = recipient_list

        mime_text = MIMEText(body)
        message.attach(mime_text)

        if is_use_ssl:
            context = ssl.create_default_context()
            context.set_ciphers('DEFAULT')
            client = smtplib.SMTP_SSL(host, port, context=context)
        else:
            client = smtplib.SMTP(host, port)

        client.login(sender, sender_pwd)
        client.sendmail(sender, to_addr_list, message.as_string())
        client.quit()

        print('Send email success!')
    except smtplib.SMTPConnectError as e:
        print('Send email failed,connection error:', e.smtp_code, e.smtp_error)
    except smtplib.SMTPAuthenticationError as e:
        print('Send email failed,smtp authentication error:', e.smtp_code, e.smtp_error)
    except smtplib.SMTPSenderRefused as e:
        print('Send email failed,sender refused:', e.smtp_code, e.smtp_error)
    except smtplib.SMTPRecipientsRefused as e:
        print('Send email failed,recipients refused:', e.recipients)
    except smtplib.SMTPDataError as e:
        print('Send email failed,smtp data error:', e.smtp_code, e.smtp_error)
    except smtplib.SMTPException as e:
        print('Send email failed,smtp exception:', str(e))
    except Exception as e:
        print('Send email failed,other error:', str(e))
