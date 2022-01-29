# lucernefestival.ch event crawler
This snippet of code scrapes events from lucernefestival.ch and saves them into a database.  

## Usage
An easy way to run this code is to startup containers for `postgres` service and `crawler.py`. First, you should have `docker` installed on your system. Then, run the command `docker-compose up` to have the defined services in `docker-compose.yml` running.  
Access postgres database `musical_events` by the command `psql -h '0.0.0.0' -p 5432 -U postgres` with the password `1234`.  
These tables should be in the musical_events database:  
 
Schema | Name | Type | Owner
--- | --- | --- | ---
public | event | table | postgres
public | event_detail | table | postgres
