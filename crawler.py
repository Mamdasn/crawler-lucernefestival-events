from urllib.parse import urlparse
from queue import Queue
import threading
from requests import Session
from bs4 import BeautifulSoup

from  lucernefestival import Lucernefestival_grabber, Lucernefestival_postgres


class EventCrawler:
    def __init__(self, url, save_to_database=False):
        self.url = url
        self.url_base =  urlparse(self.url).hostname
        self.url_scheme =  urlparse(self.url).scheme
        self._supported_methods = ["www.lucernefestival.ch"]
        self._supported_method_functions = {"www.lucernefestival.ch": 
                                    {
                                    "get_event_list": self._get_event_list_of_lucernefestival,
                                    "parse_event_list": self._parse_event_list_of_lucernefestival,
                                    "write_to_database": Lucernefestival_postgres.write_to_database,
                                    }
                                }
        self._save_to_database = save_to_database
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



    def _get_event_list_of_lucernefestival(self):
        self._event_list = Lucernefestival_grabber.get_event_list(self.url)
        return 


    def _parse_event_list_of_lucernefestival(self, expanded_details=False):
        def _parser(expanded_details, queue, thread_no):
            while True:
                event = queue.get()
                self._data.append(Lucernefestival_grabber.parse_event_list(expanded_details, event, self.url))
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
        return

    def crawl(self, **kwargs):
        if not self._is_supported():
            raise ValueError(f"This url is not supported!\nPlease include the internet protocol,e.g. http https, in url.\nSupported urls: {self._supported_methods}")
        self._get_event_list   = self._supported_method_functions[f"{self.url_base}"]["get_event_list"]
        self._parse_event_list = self._supported_method_functions[f"{self.url_base}"]["parse_event_list"]

        self._get_event_list()
        self._parse_event_list(**kwargs)

        if self._save_to_database:
            write_to_database = self._supported_method_functions[f"{self.url_base}"]["write_to_database"]
            write_to_database(self._data)

        return self._data


ecrawler_summer = EventCrawler("https://www.lucernefestival.ch/en/program/summer-festival-22", save_to_database=False)
data = ecrawler_summer.crawl(expanded_details=True)


# ecrawler_spring = EventCrawler("https://www.lucernefestival.ch/en/program/mendelssohn-festival-22")
# print(ecrawler_spring.crawl(expanded_details=True))

