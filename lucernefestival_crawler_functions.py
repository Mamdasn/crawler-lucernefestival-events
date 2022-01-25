from requests import Session
from bs4 import BeautifulSoup
from urllib.parse import urlparse

def get_event_list(url):
    event_list = None
    with Session() as session:
        page_data = session.get(url)
        page_data_html_parsed = BeautifulSoup(page_data.content, 'html.parser')
        events_list_section = page_data_html_parsed.html.body.find('div', {'class': 'list', 'id': 'event-list'})
        event_list = events_list_section.find_all('div', {'class': 'entry', 'id': True, 'data-date': True})
    return event_list

def parse_event_list(expanded_details, event, url):
        # date
        date = event['data-date']
        # time
        time_of_day = event.find('span', {'class': 'time'}).string.strip()
        # location
        location = event.find('p', {'class': 'location'}).get_text().strip()
        # title
        title = event.find('p', {'class': 'surtitle'}).get_text().strip()
        # image link
        image_link = event.find('div', {'class': 'image'})['style'].split(' ')[1][4:-1]
        
        works = None
        artists = None
        
        if not expanded_details:
            # works
            works = event.find('p', {'class': 'subtitle'})
            ## remove sponsor section from works
            sponsor = event.find('span', {'class': 'sponsor'})
            if sponsor: sponsor.extract()
            works = works.text.strip().replace(" |", ";")
            # artists
            artists = event.find('div', {'class': 'event-info'}).a.get_text().strip().replace(" |", ";")
        else:
            # extracting works and artists in more details
            url_base =  urlparse(url).hostname
            url_scheme =  urlparse(url).scheme
            event_url = f"{url_scheme}://{url_base}/{event.find('div', {'class': 'event-info'}).a['href']}"
            with Session() as inner_session:
                event_page_data = inner_session.get(event_url)
                event_page_data_parsed = BeautifulSoup(event_page_data.content, 'html.parser')
                artists_musical_pieces = event_page_data_parsed.find('div', {'class': 'artists-musical-pieces'})
                musical_pieces = artists_musical_pieces.find_all('div', {'class': 'musical-piece'})
                musical_pieces = artists_musical_pieces.find_all('div', {'class': 'with-spaces'}) if musical_pieces==[] else musical_pieces
                
                for musical_piece in musical_pieces:
                    for child in musical_piece.children:
                        work_detail = child.get_text().strip() if child.get_text() else None
                        if work_detail:
                            works = f"{works}{'; ' if child.name == 'strong' else ' '}{work_detail}" if works else work_detail

                artists_section = artists_musical_pieces.find_all('div', {'class': 'artist'})
                for artist_section in artists_section:
                    for child in artist_section.children:
                        artist_detail = child.get_text().strip() if child.get_text() else None
                        if artist_detail:
                            artists = f"{artists}{'; ' if child.name == 'strong' else ' '}{artist_detail if child.name == 'strong' else f'({artist_detail})'}" if artists else artist_detail
        
        return {"date": date, "time": time_of_day, "location": location, "title": title, "artists": artists, "works": works, "image link": image_link}
                