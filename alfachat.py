import requests

def send_sms_to(sms_config, number, text):
    url = "https://www.smsout.de/client/sendsms.php?Username={0}&Password={1}&SMSTo={2}&SMSType=V1&SMSText={3}"
    return requests.get(url.format(sms_config[0], sms_config[1], number, text))
