import os
import re
import string

def load_transcription_file(path):
    regex = re.compile('[%s]' % re.escape(string.punctuation))

    text_file_path = path + "sentence_text.txt"
    print("\nLoading %s" % text_file_path)
    assert os.path.isfile(text_file_path)

    texts = []
    with open(text_file_path, "r") as f:
        i = 0
        for line in f:
            s = line.rstrip().split("\t")
			# remove numbers
            clean_s = filter(lambda x: not x.isdigit(),
								regex.sub('', s[1]).split())
			# remove non speech
            clean_s = filter(lambda x: x not in ["laughs", "coughs", "giggles"], clean_s)

			# replace 'xxx' or 'xx' (unknown) with 'aa'
            clean_s = ["aa" if s in ["xxx","xx","yyy","yy"] else s for s in clean_s]
            clean_s = " ".join(clean_s).lower()
            texts.append((i, s[0], clean_s.rstrip()))
            i += 1
    return texts
