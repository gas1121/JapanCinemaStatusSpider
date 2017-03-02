#JapanCinemaStatusSpider

## Usage
- make sure python3 is installed
- create init.json and follow example.json to set up options and environments variables
- run init.py to initialize project
- run `(sudo) docker-compose build scrapy(scrapy-vps)`
- run `(sudo) docker-compose run scrapy(scrapy-vps) /bin/sh`

## TODO list
- [x] build cinemas data table(to handle when single session is full)
- [x] support multiple movie and cinema
- [ ] Better command line support for spider
- [x] Support configuration file and bash script
- [x] Connect to database 
- [x] Data select program
- [x] Add template and Env for security
- [x] Duplicate session in database
- [ ] Add cron table
- [ ] Add support for windows docker
- [ ] Add support for Appveyor and TravisCI
- [ ] Add redis as cache
- [x] Handle database when crawling multiple companies and times
- [x] Use json api instead of html page directly
- [ ] run multiple time to ensure all record is crawled
 - [x] database support multiple times
 - [ ] pre filter request for crawled session
- [ ] spider command line bool option problem