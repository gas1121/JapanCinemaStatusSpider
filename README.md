#JapanCinemaStatusSpider
Spider for movie booking status of major cinemas in japan.Program support toho's cinema currently.

## Features
- only need docker installed and with no dependencies
- database support
- dockerized for different parts like scrapy,phantomjs,postgres etc. 
- time scheduled job support
- support mirror if need
- support proxy for scrapy spider


## Usage
- make sure docker and docker-compose is installed.
- use default configuration in **settings.cfg** or change setting as you like.
- run **init.sh** on linux platform or **init.ps1** on windows platform to generate **docker-compose.yml** file.
- run `(sudo) docker-compose build scrapy(scrapy-vps)` to build spider image
- run `(sudo) docker-compose up -d scrapy` to start spider container, it will automatically start crawling data on setted time.
- alternatively, you can run `(sudo) docker-compose run scrapy /bin/sh` to start shell in spider's container and then run `scrapy crawl toho_v2` to start spider manually.
- you can use `(sudo) docker-compose run psql` to query result in database or use web interface by `(sudo) docker-compose up -d pgweb` and then visit **http://localhost:80**.
- you can also run `(sudo) docker-compose run scrapy /bin/sh` to visit spider container and run **data_handler.py** to get crawl result.

## Customize
#### Modify schedule time
We use [schedule](http://schedule.readthedocs.io/en/latest/]) library to schedule our spider, you can modify **run.py** to change schedule time following **schedule** library's documentation.
#### Use mirror
Just use **scrapy** container instead of **scrapy-vps**

## TODO list
- [x] Better command line support for spider
- [ ] Add support for windows docker
- [ ] Add support for Appveyor and TravisCI
- [ ] Add redis as cache
- [ ] Use information sites:
 - [x] http://eiga.com
 - [ ] http://cinema.pia.co.jp
 - [ ] http://movie.walkerplus.com
 - [x] http://movies.yahoo.co.jp
 - [ ] http://www.entermeitele.net/roadshow/theater/
 - [ ] http://cinema.co.jp/theater/list
 - [ ] https://movie.jorudan.co.jp/theater/
 - [ ] https://movieticket.jp/
- [ ] run multiple time to ensure all record is crawled
 - [x] database support multiple times
 - [ ] pre filter request for crawled showing(by cinema crawled showing count)
- [ ] spider command line bool option problem
- [ ] filter locked seat data
- [ ] add more stand alone cinema crawler
