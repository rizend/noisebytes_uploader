#!/bin/bash

title=$1
author=$2
input=$3
newfile=$4
tempdir="./temp"

shopt -s nullglob

# select an outro video
outrovideos=(./processor_assets/Outro\ Videos/*)
outrovideo=${outrovideos[$[$RANDOM % ${#outrovideos[@]}]]}
echo Outro Video: $outrovideo

outrosongs=(./processor_assets/Outro\ Songs/*)
outrosongdir=${outrosongs[$[$RANDOM % ${#outrosongs[@]}]]}
outrosong="${outrosongdir}/song.wav"
outrosongtitle="${outrosongdir}/title.txt"
outrosongartist="${outrosongdir}/artist.txt"
echo "Outro song file: ${outrosong}"
echo "Outro song title: ${outrosongtitle}"
echo "Outro song artist: ${outrosongartist}"

filename=${input%.*}
ext=${input##${filename}}
inaudio="${tempdir}/${filename}.a.wav"
invideo="${tempdir}/${filename}.v.mp4"
inaudiocorrected="${tempdir}/${filename}.a.corrected.wav"
invideocorrected="${tempdir}/${filename}.v.corrected.mp4"
inputcorrected="${tempdir}/${filename}.corrected.mp4"
outro="${tempdir}/${filename}.outro.mp4"
main="${tempdir}/${filename}.main.mp4"





ffmpeg \
-i "${input}" \
-max_muxing_queue_size 1024 \
-r 30 \
-filter_complex "[0:a] anull [audio]" \
-map "[audio]" "${inaudio}"

adur=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "${inaudio}")



ffmpeg \
-i "${input}" \
-max_muxing_queue_size 1024 \
-r 30 \
-filter_complex "[0:v] null [video]" \
-map "[video]" "${invideo}"

vdur=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "${invideo}")

vratio=$(echo "${adur} / ${vdur}" | bc -l)



ffmpeg \
-i "./processor_assets/Intro.mp4" \
-i "./processor_assets/Inter Static.mp4" \
-i "${inaudio}" \
-i "${invideo}" \
-loop 1 -i "./processor_assets/Lower Third.png" \
-i "./processor_assets/Inter Static.mp4" \
-i "${outrovideo}" \
-i "./processor_assets/Outro Blurb.wav" \
-i "${outrosong}" \
-i "./processor_assets/Outro Static.mp4" \
-filter_complex "
[0:a] anull [introa] ;
[0:v] null [introv] ;

[1:a] anull [introstatica] ;
[1:v] null [introstaticv] ;

[2] anull [maina] ;

[3:v] setpts=${vratio}*PTS [contentv] ;

[4] scale=1280/720 ,
    setsar=1/1,
    drawtext=fontfile=./processor_assets/FiraCode-Bold.ttf:text=${title}:fontcolor=#FFFFFF:fontsize=55:x=230:y=570 ,
    drawtext=fontfile=./processor_assets/FiraCode-Regular.ttf:text=${author}:fontcolor=#FFFFFF:fontsize=45:x=230:y=630 ,
    fade=in:0:30 ,
    fade=out:180:30
    [lowerthird] ;

[5:a] anull [interstatica] ;
[5:v] null [interstaticv] ;

[6:v] null [outrov] ;

[7] anull [outroblurba] ;

[8] anull [outrosonga] ;

[9:a] anull [outrostatica] ;
[9:v] null [outrostaticv] ;

[outroblurba][outrosonga] amerge [outroa] ;

[contentv][lowerthird] overlay=format=rgb:eof_action=pass [mainv] ;

[introa][introstatica][maina][interstatica][outroa][outrostatica] concat=n=6:v=0:a=1 [outa] ;
[introv][introstaticv][mainv][interstaticv][outrov][outrostaticv] concat=n=6:v=1:a=0 [outv]" \
-map "[outv]" -map "[outa]" "${newfile}"


rm "${inaudio}"
rm "${invideo}"