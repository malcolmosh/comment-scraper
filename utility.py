import requests
from requests import HTTPError
def base_header():
    headers = \
    {
        "Accept-Language": "en-US,en;q=0.5",\
        "Accept-Encoding":"gzip, deflate, br",\
        "Connection":"close",\
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:84.0) Gecko/20100101 Firefox/84.0"
    }
    return headers

class Message():
    def error(self, msg):
        print('Error: \n', msg)
    
    def warn(self, msg):
        print('Warn: \n', msg)

    def info(self, msg):
        print('Info: \n', msg)

    def debug(self, msg):
        print('Debug: \n', msg)