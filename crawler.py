from urllib.parse import urlparse
from queue import Queue
import threading
from requests import Session
from bs4 import BeautifulSoup

from  lucernefestival_crawler_functions import get_event_list as get_event_list_lucernefestival
from  lucernefestival_crawler_functions import parse_event_list as parse_event_list_lucernefestival


class EventCrawler:
    def __init__(self, url):
        self.url = url
        self.url_base =  urlparse(self.url).hostname
        self.url_scheme =  urlparse(self.url).scheme
        self._supported_methods = ["www.lucernefestival.ch"]
        self._supported_method_functions = {"www.lucernefestival.ch": 
                                    {
                                    "get_event_list": self._get_event_list_of_lucernefestival,
                                    "parse_event_list": self._parse_event_list_of_lucernefestival,
                                    }
                                }
        self._event_list = None
        self._get_event_list = None
        self._parse_event_list = None
        self.concurrent_threads = None
        self._data = []

    def _is_supported(self):
        if self.url_base in self._supported_methods:
            return True 
        else:
            return False

    def crawl(self, **kwargs):
        if not self._is_supported():
            raise ValueError(f"This url is not supported!\nPlease include the internet protocol,e.g. http https, in url.\nSupported urls: {self._supported_methods}")
        self._get_event_list   = self._supported_method_functions[f"{self.url_base}"]["get_event_list"]
        self._parse_event_list = self._supported_method_functions[f"{self.url_base}"]["parse_event_list"]

        self._get_event_list()
        self._parse_event_list(**kwargs)
        return self._data


        

    def _get_event_list_of_lucernefestival(self):
        self._event_list = get_event_list_lucernefestival(self.url)
        return 

    def _parse_event_list_of_lucernefestival(self, expanded_details=False):
        def _parser(expanded_details, queue, thread_no):
            while True:
                event = queue.get()
                self._data.append(parse_event_list_lucernefestival(expanded_details, event, self.url))
                queue.task_done()
        
        queue = Queue()

        concurrent_threads = 1 if expanded_details else 8
        concurrent_threads = self.concurrent_threads if self.concurrent_threads else concurrent_threads
        for itr in range(concurrent_threads):
            worker = threading.Thread(target=_parser, args=(expanded_details, queue, itr))
            worker.daemon = True
            worker.start()

        for event in self._event_list:
            queue.put(event)
        queue.join()


ecrawler_summer = EventCrawler("https://www.lucernefestival.ch/en/program/summer-festival-22")
print(ecrawler_summer.crawl(expanded_details=False))

# ecrawler_spring = EventCrawler("https://www.lucernefestival.ch/en/program/mendelssohn-festival-22")
# print(ecrawler_spring.crawl(expanded_details=True))
