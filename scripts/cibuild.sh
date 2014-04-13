#!/bin/bash
#
#  cibuild.sh
#

if [ -z "$GEOIP2_FILE" ]; then
  echo "Downloading geoip2 database"
  if [ ! -f GeoLite2-City.mmdb.gz ]; then
    curl -o GeoLite2-City.mmdb.gz 'http://geolite.maxmind.com/download/geoip/database/GeoLite2-City.mmdb.gz'
  fi
  gunzip GeoLite2-City.mmdb.gz
  export GEOIP2_FILE=$PWD/GeoLite2-City.mmdb
fi

make test
