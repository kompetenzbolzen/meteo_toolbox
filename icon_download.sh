#!/bin/bash

# http://opendata.dwd.de/weather/nwp/icon-d2/grib/00/t/icon-d2_germany_regular-lat-lon_pressure-level_2023080200_000_1000_t.grib2.bz2

# <BASE>/<RUN>/<PARAMETER>/icon-d2_regular-lat-lon_pressure-level_<INIT>_<OFFSET>_<LEVEL>_<PARAMETER>

# Detect latest with
# curl https://opendata.dwd.de/weather/nwp/content.log.bz2 | bzip2 -d

function get_latest_run() {
	# Allow up to 3hours for DWD to upload the new model run. We also want UTC
	export TZ=UTC
	local corrected_date=$(date -d "$(date '+%Y-%m-%d %H:%M:%S') 3 hours ago"  '+%Y-%m-%d %H:%M:%S')
	local current_hour=$(date -d "$corrected_date" +%H)
	local run_hour=$(( (current_hour/6) * 6 ))

	RUN=$(printf "%02d" $run_hour)
	DATE=$(date -d "$corrected_date" +%Y%m%d)

	echo Selecting run $RUN - $DATE
}


NPROC=$(nproc)

#OUTDIR=dwd_icon-d2
OUTDIR=dwd_icon-eu
#MODEL=icon-d2
#MODEL_LONG=icon-d2_germany
MODEL=icon-eu
MODEL_LONG=icon-eu_europe
BASE="https://opendata.dwd.de/weather/nwp"

get_latest_run
#RUN="00"
#DATE=$(date +%Y%m%d)

# In ICON-EU, the parameter name in the filename is in caps.
# This is a stupid fix for a stupid problem.
PARAMETER_FILENAME_CAPS=yes

PARAMETERS=( "t" "relhum" "u" "v" "fi" )
# tot_prec and cape_ml/cin_ml is in 15min intervals and screws with xygrib
PARAMETERS_SINGLE_LEVEL=( "pmsl" )
PRESSURE_LEVELS=( "1000" "975" "950" "850" "700" "600" "500" "400" "300" "250" "200" )
OFFSETS=( "000" "003" "006" "009" "012" "015" "018" "024" "027" "030" "033" "036"  "039" "042" "045" "048" )

mkdir -p $OUTDIR

for OFFSET in "${OFFSETS[@]}"; do
	for PARAMETER in "${PARAMETERS[@]}"; do
		for LEVEL in "${PRESSURE_LEVELS[@]}"; do
			while [ $(pgrep -c -P$$) -gt $NPROC ]; do
				sleep 1
			done

			if [ "$PARAMETER_FILENAME_CAPS" = "yes" ]; then
				PARAMETER2=${PARAMETER^^}
			else
				PARAMETER2=${PARAMETER}
			fi

			URL="$BASE/$MODEL/grib/$RUN/$PARAMETER/${MODEL_LONG}_regular-lat-lon_pressure-level_${DATE}${RUN}_${OFFSET}_${LEVEL}_${PARAMETER2}.grib2.bz2"
			BNAME=$(basename "$URL")
			echo Getting "$BNAME"
			( wget -q --directory-prefix=$OUTDIR  "$URL" || echo FAILED: "$BNAME" ) &

		done
	done

	for PARAMETER in "${PARAMETERS_SINGLE_LEVEL[@]}"; do
			while [ $(pgrep -c -P$$) -gt $NPROC ]; do
				sleep 1
			done

			if [ "$PARAMETER_FILENAME_CAPS" = "yes" ]; then
				PARAMETER2=${PARAMETER^^}
			else
				PARAMETER2=${PARAMETER}
			fi

			URL="$BASE/$MODEL/grib/$RUN/$PARAMETER/${MODEL_LONG}_regular-lat-lon_single-level_${DATE}${RUN}_${OFFSET}_2d_${PARAMETER2}.grib2.bz2"
			BNAME=$(basename "$URL")
			echo Getting "$BNAME"
			( wget -q --directory-prefix=$OUTDIR  "$URL" || echo FAILED: "$BNAME" ) &
	done
done

while [ $(pgrep -c -P$$) -gt 0 ]; do
	sleep 1
done

echo Done downloading. Decompressing...

for F in $OUTDIR/*.grib2.bz2; do
	while [ $(pgrep -c -P$$) -gt $NPROC ]; do
		sleep 1
	done

	bzip2 -df "$F" &
done

rm -f $OUTDIR/combined.grib2

grib_copy $OUTDIR/*.grib2 $OUTDIR/combined.grib2 || exit 1
rm -f $OUTDIR/icon*.grib2

echo Done.
