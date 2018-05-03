#!/bin/bash

title=$1
author=$2
file=$3
newfile=$4

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



ffmpeg \
-i "./processor_assets/Intro - VHS Test Pattern (small).mov" \
-i "./processor_assets/Inter Static.mov" \
-i "${file}" \
-loop 1 -i "./processor_assets/Lower Third.png" \
-i "./processor_assets/Inter Static.mov" \
-i "${outrovideo}" \
-i "./processor_assets/Outro Blurb.mp3" \
-i "${outrosong}" \
-i "./processor_assets/Outro Static.mov" \
-filter_complex "
[0:v] scale=1280:720,setsar=1:1 [introv] ;
[0:a] anull [introa] ;

[1:v] scale=1280:720,setsar=1:1 [introstaticv] ;
[1:a] anull [introstatica] ;

[2:v] scale=1280:720,setsar=1:1 [contentv] ;
[2:a] anull [maina] ;

[3] scale=1280:720 ,
    drawtext=fontfile=./processor_assets/FiraCode-Bold.ttf:text=${title}:fontcolor=#FFFFFF:fontsize=55:x=230:y=570 ,
    drawtext=fontfile=./processor_assets/FiraCode-Regular.ttf:text=${author}:fontcolor=#FFFFFF:fontsize=45:x=230:y=630 ,
    fade=in:0:30 ,
    fade=out:180:30
    [lower] ;

[4:v] scale=1280:720,setsar=1:1 [outrostaticv] ;
[4:a] anull [outrostatica] ;

[5:v] scale=1280:720 ,
      drawtext=fontfile=./processor_assets/FiraCode-Regular.ttf:text='Thank you for watching!':fontcolor=#FFFFFF:fontsize=50:box=1:boxcolor=#00000088:x=25:y=25 ,
      drawtext=fontfile=./processor_assets/FiraCode-Regular.ttf:text='If you liked this video':fontcolor=#FFFFFF:fontsize=50:box=1:boxcolor=#00000088:x=25:y=85 ,
      drawtext=fontfile=./processor_assets/FiraCode-Regular.ttf:text='please consider supporting':fontcolor=#FFFFFF:fontsize=50:box=1:boxcolor=#00000088:x=25:y=145 ,
      drawtext=fontfile=./processor_assets/FiraCode-Regular.ttf:text='Noisebridge by going to':fontcolor=#FFFFFF:fontsize=50:box=1:boxcolor=#00000088:x=25:y=205 ,
      drawtext=fontfile=./processor_assets/FiraCode-Bold.ttf:text='patreon.com/noisebridge':fontcolor=#FFFFFF:fontsize=75:box=1:boxcolor=#00000088:x=25:y=265 ,
      drawtext=fontfile=./processor_assets/FiraCode-Regular.ttf:text='and signing up for a':fontcolor=#FFFFFF:fontsize=50:box=1:boxcolor=#00000088:x=25:y=355 ,
      drawtext=fontfile=./processor_assets/FiraCode-Regular.ttf:text='monthly donation!':fontcolor=#FFFFFF:fontsize=50:box=1:boxcolor=#00000088:x=25:y=415 ,
      drawtext=fontfile=./processor_assets/FiraCode-Regular.ttf:text='Song Credit':fontcolor=#FFFFFF:fontsize=20:box=1:boxcolor=#00000088:x=25:y=580,
      drawtext=fontfile=./processor_assets/FiraCode-Regular.ttf:textfile=${outrosongtitle}:fontcolor=#FFFFFF:fontsize=30:box=1:boxcolor=#00000088:x=25:y=610,
      drawtext=fontfile=./processor_assets/FiraCode-Regular.ttf:textfile=${outrosongartist}:fontcolor=#FFFFFF:fontsize=30:box=1:boxcolor=#00000088:x=25:y=650
      [outrov] ;

[6] anull [outroblurba] ;

[7] anull [outrosonga] ;

[outroblurba][outrosonga] amerge [outroa] ;

[8:v] scale=1280:720,setsar=1:1 [outrostatic2v] ;
[8:a] anull [outrostatic2a] ;



[contentv][lower] overlay=format=rgb:eof_action=pass [mainv] ;
[introv][introstaticv][mainv][outrostaticv][outrov][outrostatic2v] concat=n=6:v=1:a=0 [outv] ;
[introa][introstatica][maina][outrostatica][outroa][outrostatic2a] concat=n=6:v=0:a=1 [outa]" \
-map "[outv]" -map "[outa]" "${newfile}"