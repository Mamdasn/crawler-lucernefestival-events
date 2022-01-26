from requests import Session
from bs4 import BeautifulSoup
from urllib.parse import urlparse

import psycopg2
from config import config

class Lucernefestival_grabber():
    
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
            time_of_day = event.find('span', {'class': 'time'}).string.strip().replace('.', ':')
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
            
            return {"date": date, "time": time_of_day, "location": location, "title": title, "artists": artists, "works": works, "image_link": image_link}


class Lucernefestival_postgres():

    def write_to_database(data):
        """ create tables in the PostgreSQL database and insert data into it"""

        def _insert_event(
                    cursor,
                    date = None, 
                    time = None, 
                    location = None, 
                    title = None, 
                    artists = None, 
                    works = None, 
                    image_link = None):
                    """ 

                    insert a new event into the event and event_detail tables 
                    
                    """
                    
                    sql_event_detail = """INSERT INTO event_detail (artists, date, time, image_link, location, works)
                            VALUES(%s, %s::DATE, %s::TIME, %s, %s, %s) ON CONFLICT (artists, date, time) DO UPDATE 
                            SET works = EXCLUDED.works, image_link = EXCLUDED.image_link, location = EXCLUDED.location 
                            RETURNING id;"""
                    sql_event = """INSERT INTO event (title, date, time, event_detail_id)
                                        VALUES(%s, %s::DATE, %s::TIME, %s) ON CONFLICT (event_detail_id) DO NOTHING RETURNING id;"""
                    
                    cursor.execute(sql_event_detail, (artists, date, time, image_link, location, works,))
                    event_detail_id = cursor.fetchone()
                    if event_detail_id: 
                        event_detail_id = event_detail_id[0]
                        cursor.execute(sql_event, (title, date, time, event_detail_id))

        check_existence = """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_name = 'event'
            );
            """
        create_commands = (
            """
            CREATE TABLE event_detail (
                id BIGSERIAL NOT NULL PRIMARY KEY,
                artists VARCHAR(400) NOT NULL,
                date DATE NOT NULL,
                time TIME NOT NULL,
                image_link VARCHAR(400),
                location VARCHAR(400),
                works VARCHAR,
                UNIQUE(artists, date, time)
            )
            """,
            """
            CREATE TABLE event (
                id BIGSERIAL NOT NULL PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                date DATE NOT NULL,
                time TIME NOT NULL,
                event_detail_id BIGINT REFERENCES event_detail(id),
                UNIQUE(event_detail_id)
            )
            """
            )

        try:
            # read the connection parameters from config file
            params = config()
            conn = psycopg2.connect(**params)
            cursor = conn.cursor()
            # check existence of tables
            cursor.execute(check_existence)
            tables_already_exist = cursor.fetchone()[0]
            
            if not tables_already_exist:
                # create tables
                for create_command in create_commands:
                    cursor.execute(create_command)
            
            for d in data:
                _insert_event(cursor=cursor, **d)
        
            cursor.close()
            conn.commit()
            if conn is not None:
                conn.close()
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
            return False
        return True

        
    