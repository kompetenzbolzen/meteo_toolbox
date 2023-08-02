#!/bin/bash

# http://opendata.dwd.de/weather/nwp/icon-d2/grib/00/t/icon-d2_germany_regular-lat-lon_pressure-level_2023080200_000_1000_t.grib2.bz2

# <BASE>/<RUN>/<PARAMETER>/icon-d2_regular-lat-lon_pressure-level_<INIT>_<OFFSET>_<LEVEL>_<PARAMETER>

OUTDIR=dwd_icon-d2
MODEL=icon-d2
MODEL_LONG=icon-d2_germany
BASE="http://opendata.dwd.de/weather/nwp"

RUN="00"
PARAMETERS=( "t" )
PRESSURE_LEVELS=( "1000" "975" "950" "850" "700" "600" "500" "400" "300" "250" "200" )
OFFSETS=( "000" )
DATE=$(date +%Y%m%d)

mkdir -p $OUTDIR

echo -n > "$OUTDIR/index.txt"

for PARAMETER in ${PARAMETERS[@]}; do
	for OFFSET in ${OFFSETS[@]}; do
		for LEVEL in ${PRESSURE_LEVELS[@]}; do
			URL="$BASE/$MODEL/grib/$RUN/$PARAMETER/${MODEL_LONG}_regular-lat-lon_pressure-level_${DATE}${RUN}_${OFFSET}_${LEVEL}_${PARAMETER}.grib2.bz2"
			BNAME=$(basename "$URL")
			echo Getting "$URL"
			echo "$BNAME" >> $OUTDIR/index.txt
			wget -q --directory-prefix=$OUTDIR  "$URL"

		done
	done
done

echo Done downloading. Decompressing...

for F in $OUTDIR/*.grib2.bz2; do
	bzip2 -df "$F"
done

echo Done.
