[![Build Status](https://travis-ci.org/gas1121/JapanCinemaStatusSpider?branch=dev)](https://travis-ci.org/gas1121/JapanCinemaStatusSpider) [![Coverage Status](https://coveralls.io/repos/github/gas1121/JapanCinemaStatusSpider/badge.svg?branch=dev)](https://coveralls.io/github/gas1121/JapanCinemaStatusSpider?branch=dev)

# JapanCinemaStatusSpider
A scrapy project to crawl movie booking data from several cinema company chains.

## Feature
- Crawl cinema data from several movie web portals.
- Crawl movie booking data.
- All in docker container, easy to use
- support proxy include socks5


## Usage
- set docker compose variables or use default
- build **crawler** image
- TODO run **crawler** service in **docker-compose** to start spider
- you can use **psql** or **pgweb** in service in **docker-compose** file to visit database
- you can also use **data_handler.py** in spider image to get crawl result.

## Customize
#### Modify schedule time
We use [schedule](http://schedule.readthedocs.io/en/latest/]) to schedule our spider work, you can modify **run.py** to change schedule time following its documentation.
#### Use mirror
Set docker compose's environment variable use_mirror to **1**

## Useful sites
Here is a list of useful site and some of them is used by this spider
- movie web portals in japan:
 - [x] http://eiga.com
 - [ ] http://cinema.pia.co.jp
 - [x] http://movie.walkerplus.com
 - [x] http://movies.yahoo.co.jp
 - [ ] http://www.entermeitele.net/roadshow/theater/
 - [ ] http://cinema.co.jp/theater/list
 - [ ] https://movie.jorudan.co.jp/theater/
 - [ ] https://movieticket.jp/
- total seat counts(from walkerplus 20170412) 616119
- cinema company chains have total seats over 5000:
 - [x] Aeon 140138
 - [x] Toho 114395+2705
 - [x] United/Cineplex 67377-2383
 - [x] Movix 47996+2141+2564
 - [x] 109 31544
 - [x] kinezo 28051+1324+1986
 - [x] korona 17688
 - [x] cinemasunshine 17477
 - [ ] cinemax 8618
 - [ ] startheaters 6650
 - [x] forum 6500
 - [ ] humax 5064
- small cinema company chains:
 - [ ] xyst cinema 3760 5
 - [ ] sugai-dinos 3181 4
 - [ ] jollios 3031 2(+1 TOHO)
 - [ ] ttcg 2662 9
 - [ ] j-max 2361 2
- big single cinemas:
 - [ ] チネチッタ 3208
 - [ ] シネマイクスピアリ 3152
 - [ ] 札幌シネマフロンティア 2705
 - [ ] ミッドランドスクエアシネマ 2284
 - [ ] 立川シネマシティ 2244
 - [ ] シネプラザサントムーン 2004
 - [ ] アースシネマズ姫路 1989
 - [ ] シネシティザート 1921
 - [ ] あべのアポロシネマ 1842
 - [ ] セントラルシネマ宮崎 1821
 - [ ] ミッドランドシネマ名古屋空港 1811
 - [ ] プレビ劇場ISESAKICINEMA 1669
 - [ ] 千葉京成ローザ10 1657
 - [ ] シネティアラ21 1501
 - [ ] シネマハーヴェストウォーク 1489
 - [ ] テアトルサンク 1485
 - [ ] セントラルシネマ大牟田 1400
 - [ ] シネックスマーゴ 1389
 - [ ] 長野グランドシネマズ 1365
 - [ ] 松本シネマライツ 1358
 - [ ] シアターフォルテ 1256
 - [ ] 福山駅前シネマモード1・2,福山エーガル8シネマズ 1220
 - [ ] 布施ラインシネマ 1145
 - [ ] シネマヴィレッジ8・イオン柏 1124
 - [ ] 佐久アムシネマ 1035
 - [ ] シネマ・リオーネ古川 1010

## TODO list
- [ ] move some command line options to zookeeper to allow spider change config
- [ ] some request missing when run multiple spiders concurrently
- [ ] cookie issue with somne spiders(aeon united)
- [ ] Better integration with scrapy cluster
- [ ] Destribution support
- [x] Better command line support for spider
- [ ] Filter locked seat data
- [ ] Add more stand alone cinema's crawler
- [ ] Handle showings selecting seat freely
- [ ] Use other spider library for support of schedule and web ui
 - [x] schedule
 - [ ] web ui