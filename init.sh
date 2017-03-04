#! /bin/bash
#
# project init script
# ini parser from https://github.com/albfan/bash-ini-parser
#

render_template() {
    setting_file=$1
    input_file=$2
    output_file=$3
    cfg_parser $setting_file
    cfg_section_postgres
    cfg_section_pgweb
    cfg_section_redis
    cfg_section_scrapy
    cfg_section_proxy
    sed -e "s@{POSTGRES_USER}@$POSTGRES_USER@g" \
    -e "s@{POSTGRES_PASSWORD}@$POSTGRES_PASSWORD@g" \
    -e "s@{POSTGRES_DB}@$POSTGRES_DB@g" \
    -e "s@{PGDATA}@$PGDATA@g" \
    -e "s@{PGWEB_PORT}@$PGWEB_PORT@g" \
    -e "s@{REDISDATA}@$REDISDATA@g" \
    -e "s@{PROXY_ADDRESS}@$PROXY_ADDRESS@g" \
    -e "s@{PROXY_PORT}@$PROXY_PORT@g" \
    -e "s@{PROXY_TYPE}@$PROXY_TYPE@g" \
    -e "s@{WORK_DIR}@$WORK_DIR@g" $input_file > $output_file
}

. script/bash-ini-parser

render_template settings.cfg docker-compose.yml.in docker-compose.yml
