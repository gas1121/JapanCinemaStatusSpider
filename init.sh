#! /bin/bash
#
# project init script
# ini parser from https://github.com/albfan/bash-ini-parser
#

. script/bash-ini-parser
cfg_parser init.cfg
#cfg_section_postgres
#$POSTGRES_DB