import requests
from bs4 import BeautifulSoup

baselink = 'https://www.lucernefestival.ch'
link = f'{baselink}/en/program/summer-festival-22'

needed_data = {}

with requests.Session() as session:
    page_data = session.get(link)
    page_data_parsed = BeautifulSoup(page_data.content, 'html.parser')

    events_list_section = page_data_parsed.html.body.find('div', {'class': 'list', 'id': 'event-list'})
    events_list = events_list_section.find_all('div', {'class': 'entry', 'id': True, 'data-date': True})
    
    for i in range(len(events_list)):
        
        ## date, time, location, title, artists, works and image link
        
        #date
        date = events_list[i]['data-date']
        # time
        time = events_list[i].find('span', {'class': 'time'}).string.strip()

        print('-'*90)

        # location
        location = events_list[i].find('p', {'class': 'location'}).get_text().strip()

        # title
        title = events_list[i].find('p', {'class': 'surtitle'}).get_text().strip()

        # # artists
        # artists = ", ".join(title.split(' | ')[1:]) if len(title.split(' | ')) > 1 else title

        # image link
        image_link = events_list[i].find('div', {'class': 'image'})['style'].split(' ')[1][4:-1]


        
        # extracting works and artists
        event_url = f"{baselink}/{events_list[i].find('div', {'class': 'event-info'}).a['href']}"
        works = None
        artists = None
        with requests.Session() as inner_session:
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

            
            artists_sec = artists_musical_pieces.find_all('div', {'class': 'artist'})
            for artist_sec in artists_sec:
                for child in artist_sec.children:
                    artist_detail = child.get_text().strip() if child.get_text() else None
                    if artist_detail:
                        artists = f"{artists}{'; ' if child.name == 'strong' else ' '}{artist_detail if child.name == 'strong' else f'({artist_detail})'}" if artists else artist_detail

        ## date, time, location, title, artists, works and image link

        print(f"date:\t\t{date}")
        print(f"time:\t\t{time}")
        print(f"location:\t\t{location}")
        print(f"title:\t\t{title}")
        print(f"artists:\t\t{artists}")
        print(f"works:\t\t{works}")
        print(f"image link:\t\t{image_link}")
        

            
                



