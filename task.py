from lxml import etree
import sys, requests, json, os, argparse, random, time, mysql.connector, hashlib, dateutil.parser
from requests.models import Response
from utility import Message, base_header
from requests import HTTPError
from bs4 import BeautifulSoup
from mysql.connector import errorcode
from urllib.parse import urlparse
from utility import Message, MySQL
from CommentScraper import CommentScraper

class CommentScraperTask(MySQL):
    def __init__(self, DBHost='localhost', DBPort=3306, DBUser='root', DBPassword='root', DBName='mysql', outputPath=None) -> None:
        super().__init__(host=DBHost, port=DBPort, user=DBUser, password=DBPassword, database=DBName)
        self.url = None
        self.dateHash = None
        self.status = 0
        self.errMsg = None
        self.scraper = CommentScraper()
        self.outputPath = outputPath

    def request_task(self):
        self.success = True
        self.errMsg = None
        self.DBCon.autocommit = False
        requestSQL1 = \
        """
        SELECT url, date_hash FROM url_queue WHERE status = 0 LIMIT 1 FOR UPDATE SKIP LOCKED;
        """
        requestSQL2 = \
        """
        UPDATE url_queue SET status = 1 WHERE url = %(url)s;
        """
        self.DBCursor.execute(requestSQL1)
        row = self.DBCursor.fetchone()
        if row is None:
            ret = False
        else:
            self.url = row['url']
            self.dateHash = row['date_hash']
            self.DBCursor.execute(requestSQL2, {'url': self.url})
            self.status = 1
            ret = True
        self.DBCon.commit()
        self.DBCon.autocommit = True
        return ret

    def error(self, msg):
        self.errMsg = msg
        return super().error(msg)

    def perform_task(self):
        self.scraper.load_comments(self.url, self.outputPath, self.dateHash + '.json')
        if os.path.exists(os.path.join(self.outputPath, self.dateHash + '.json')):
            self.status = 2
            self.errMsg = None
        else:
            self.status = -1

    def complete_task(self):
        completeSQL = "UPDATE url_queue SET status = %(status)s, error_message = %(errMsg)s WHERE url = %(url)s;"
        self.DBCursor.execute(completeSQL, {'url': self.url, 'status': self.status, 'errMsg': self.errMsg})
        self.info('Finish article {}.'.format(self.url))
    
    def run_once(self):
        if self.request_task():
            self.perform_task()
            self.complete_task()

    def run(self):
        while 1:
            if self.request_task():
                self.perform_task()
                self.complete_task()
            else:
                self.info('No more task, I am going to sleep for 30 minutes.')
                cnt = 30
                while cnt > 0:
                    self.debug('Sleeping, wake up in {} minutes.'.format(cnt))
                    time.sleep(60)
                    cnt -= 1


if __name__ == "__main__":
    t = CommentScraperTask(DBName='comment-crawler', outputPath='D:/request-based-comment-crawler/comment')
    t.run()