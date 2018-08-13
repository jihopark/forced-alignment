#!/bin/sh
if [ "$#" -ne 1 ]; then
    echo "Error: Please pass the directory of the dataset as parameter"
    exit
fi

DIRECTORY=$1
echo processing directory: $DIRECTORY
for d in $DIRECTORY/* ; do
    for child_name in $d/*; do
        shopt -s nullglob
        for f in $child_name/sentences_audio/*.mp4; do
            filename="${f%.*}"
            ffmpeg -i ${filename}.mp4 -ar 16000 -ac 1 ${filename}.wav
        done
    done
done
