from urllib.parse import urlparse
from queue import Queue
import threading
from numpy import number
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
                                    "get_event_list": Lucernefestival_grabber.get_event_list,
                                    "parse_event_list": Lucernefestival_grabber.parse_event_list,
                                    "write_to_database": Lucernefestival_postgres.write_to_database,
                                    }
                                }
        self._save_to_database = save_to_database
        self._event_list = None
        self.concurrent_threads = None
        self._data = []

    def _is_supported(self):
        if self.url_base in self._supported_methods:
            return True 
        else:
            return False

    @staticmethod
    def _run_in_parallel(parser, input_data, number_of_threads, **kwargs):
        data = []
        def _parser(queue, thread_no, **kwargs):
            while True:
                event = queue.get()
                data.append(parser(event, **kwargs))
                queue.task_done()

        queue = Queue()

        for itr in range(number_of_threads):
            worker = threading.Thread(target=_parser, args=(queue, itr), kwargs=kwargs)
            worker.daemon = True
            worker.start()

        for event in input_data:
            queue.put(event)

        queue.join()
        return data

    def crawl(self, number_of_threads=1, **kwargs):
        if not self._is_supported():
            raise ValueError(f"This url is not supported!\nPlease include the internet protocol,e.g. http https, in url.\nSupported urls: {self._supported_methods}")
        
        get_event_list   = self._supported_method_functions[f"{self.url_base}"]["get_event_list"]
        parse_event_list = self._supported_method_functions[f"{self.url_base}"]["parse_event_list"]

        self._event_list = get_event_list(self.url)
        self.concurrent_threads = number_of_threads
        self._data = self._run_in_parallel(parse_event_list, self._event_list, self.concurrent_threads, **kwargs)

        if self._save_to_database:
            print("Writing/Updating data in database")
            write_to_database = self._supported_method_functions[f"{self.url_base}"]["write_to_database"]
            write_response = write_to_database(self._data)
            if write_response:
                print("Writing/Updating data in database is done.")
            else:
                print("There seems to be a problem with your database.")

        return self._data


ecrawler_summer = EventCrawler("https://www.lucernefestival.ch/en/program/summer-festival-22", save_to_database=True)
print("Scraping data from lucernefestival.ch")
data = ecrawler_summer.crawl(number_of_threads=8, expanded_details=True)
# print(data)
print("Scraping data finished.")

# ecrawler_spring = EventCrawler("https://www.lucernefestival.ch/en/program/mendelssohn-festival-22")
# print(ecrawler_spring.crawl(expanded_details=True))




