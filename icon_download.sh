#!/bin/bash

# http://opendata.dwd.de/weather/nwp/icon-d2/grib/00/t/icon-d2_germany_regular-lat-lon_pressure-level_2023080200_000_1000_t.grib2.bz2

# <BASE>/<RUN>/<PARAMETER>/icon-d2_regular-lat-lon_pressure-level_<INIT>_<OFFSET>_<LEVEL>_<PARAMETER>

OUTDIR=dwd_icon-d2
MODEL=icon-d2
MODEL_LONG=icon-d2_germany
BASE="http://opendata.dwd.de/weather/nwp"

RUN="00"
PARAMETERS=( "t" "relhum" "u" "v" "fi" )
# tot_prec and cape_ml/cin_ml is in 15min intervals and screws with xygrib
PARAMETERS_SINGLE_LEVEL=( "w_ctmax" )
PRESSURE_LEVELS=( "1000" "975" "950" "850" "700" "600" "500" "400" "300" "250" "200" )
OFFSETS=( "000" "003" "006" "009" "012" "015" "018" "024" )
DATE=$(date +%Y%m%d)

mkdir -p $OUTDIR

echo -n > "$OUTDIR/index.txt"

for OFFSET in "${OFFSETS[@]}"; do
	for PARAMETER in "${PARAMETERS[@]}"; do
		for LEVEL in "${PRESSURE_LEVELS[@]}"; do
			URL="$BASE/$MODEL/grib/$RUN/$PARAMETER/${MODEL_LONG}_regular-lat-lon_pressure-level_${DATE}${RUN}_${OFFSET}_${LEVEL}_${PARAMETER}.grib2.bz2"
			BNAME=$(basename "$URL")
			echo Getting "$URL"
			echo "${BNAME%.bz2}" >> $OUTDIR/index.txt
			wget -q --directory-prefix=$OUTDIR  "$URL" || echo FAILED!

		done
	done

	for PARAMETER in "${PARAMETERS_SINGLE_LEVEL[@]}"; do
			URL="$BASE/$MODEL/grib/$RUN/$PARAMETER/${MODEL_LONG}_regular-lat-lon_single-level_${DATE}${RUN}_${OFFSET}_2d_${PARAMETER}.grib2.bz2"
			BNAME=$(basename "$URL")
			echo Getting "$URL"
			echo "${BNAME%.bz2}" >> $OUTDIR/index.txt
			wget -q --directory-prefix=$OUTDIR  "$URL" || echo FAILED!
	done
done

echo Done downloading. Decompressing...

for F in $OUTDIR/*.grib2.bz2; do
	bzip2 -df "$F"
done

rm -f $OUTDIR/combined.grib2

grib_copy $OUTDIR/*.grib2 $OUTDIR/combined.grib2 || exit 1
rm -f $OUTDIR/icon*.grib2

echo Done.
