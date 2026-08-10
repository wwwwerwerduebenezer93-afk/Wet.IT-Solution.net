"""Email/SMS verification delivery with safe development fallbacks."""
import os,smtplib
from email.message import EmailMessage
import requests

def send_email_code(email,code):
    host=os.getenv("SMTP_HOST")
    if not host: return False
    msg=EmailMessage(); msg["Subject"]="UCC CodeMentor AI verification code"; msg["From"]=os.getenv("SMTP_FROM","no-reply@codementor.local"); msg["To"]=email; msg.set_content(f"Your verification code is {code}. It expires in 10 minutes.")
    port=int(os.getenv("SMTP_PORT","587")); user=os.getenv("SMTP_USER"); password=os.getenv("SMTP_PASSWORD")
    with smtplib.SMTP(host,port,timeout=12) as server:
        if os.getenv("SMTP_TLS","1")=="1": server.starttls()
        if user: server.login(user,password or "")
        server.send_message(msg)
    return True

def send_sms_code(phone,code):
    url=os.getenv("SMS_API_URL"); key=os.getenv("SMS_API_KEY")
    if not url: return False
    response=requests.post(url,headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"},json={"to":phone,"message":f"UCC CodeMentor AI verification code: {code}. Expires in 10 minutes."},timeout=12)
    response.raise_for_status(); return True

