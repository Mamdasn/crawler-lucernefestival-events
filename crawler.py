from urllib.parse import urlparse
from queue import Queue
import threading
from requests import Session
from bs4 import BeautifulSoup

from  lucernefestival import LucernefestivalGrabber, LucernefestivalPostgres


class EventCrawler:
    def __init__(self, method):
        self.url = None
        self._supported_methods = method

    @property
    def _url_base(self):
        return urlparse(self.url).hostname

    def _is_supported(self):
        if self._url_base in self._supported_methods:
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
    
    def crawl(self, url, number_of_threads=1, save_to_database=True, **kwargs):
        self.url = url
        if not self._is_supported():
            raise ValueError(f"This url is not supported!\nPlease include the internet protocol,e.g. http https, in url.\nSupported urls: {[k for k in self._supported_methods]}")
        
        get_event_list   = self._supported_methods[f"{self._url_base}"]["get_event_list"]
        parse_event_list = self._supported_methods[f"{self._url_base}"]["parse_event_list"]

        event_list = get_event_list(self.url)
        concurrent_threads = number_of_threads
        data = self._run_in_parallel(parse_event_list, event_list, concurrent_threads, **kwargs)

        if save_to_database:
            print("Writing/Updating data in database")
            write_to_database = self._supported_methods[f"{self._url_base}"]["write_to_database"]
            write_response = write_to_database(data)
            if write_response:
                print("Writing/Updating data in database is done.")
            else:
                print("There seems to be a problem with your database.")

        return data


# Define a method
method = {"www.lucernefestival.ch": 
            {
            "get_event_list": LucernefestivalGrabber.get_event_list,
            "parse_event_list": LucernefestivalGrabber.parse_event_list,
            "write_to_database": LucernefestivalPostgres.write_to_database,
            }
        }
ecrawler_summer = EventCrawler(method)

print("Scraping data from lucernefestival.ch")
url = "https://www.lucernefestival.ch/en/program/summer-festival-22"
data = ecrawler_summer.crawl(url, number_of_threads=8, save_to_database=True, expanded_details=True)
print("Scraping data finished.")


# ecrawler_spring = EventCrawler("https://www.lucernefestival.ch/en/program/mendelssohn-festival-22")
# print(ecrawler_spring.crawl(expanded_details=True))




