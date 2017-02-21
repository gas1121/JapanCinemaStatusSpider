#JapanCinemaStatusSpider

## Usage
- make sure python3 is installed
- create init.json and follow example.json to set up options and environments variables
- run init.py to initialize project
- run `(sudo) docker-compose build scrapy(scrapy-vps)`
- run `(sudo) docker-compose run scrapy(scrapy-vps) /bin/sh`

## TODO list
- [x] build cinemas data table(to handle when single session is full)
- [ ] crawl target cinema list from movie page
- [x] support multiple movie and cinema
- [ ] Better command line support for spider
- [ ] Support json configuration file and bash script
- [x] Connect to database 
- [x] Data select program
- [ ] Add template and Env for security
- [x] Duplicate session in database
- [ ] Add cron table
- [ ] Add support for windows docker
- [ ] Add support for Appveyor and TravisCI