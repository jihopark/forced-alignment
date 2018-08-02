# https://github.com/readbeyond/aeneas
DIRECTORY=example

for i in $DIRECTORY/*.wav; do
    extension="${i##*.}"
    filename="${i%.*}"
    python -m aeneas.tools.execute_task \
        ${filename}.wav \
        ${filename}.txt \
        "task_language=eng|os_task_file_format=json|is_text_type=plain" \
        ${filename}.json
done
