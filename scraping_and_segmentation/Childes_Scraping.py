
#1. Go to all folders
#2. Go to all subsections
#3. Find all .cha website
#4. Scrape the sentence: span name = "utterance"
#5. Scrape the timestamp: beg and end
#6. Chop down the sentences


import selenium
from selenium import webdriver
import urllib.request
from urllib.request import urlretrieve
from bs4 import BeautifulSoup
import re
import time
import random
from pydub import AudioSegment
#from settings import *
import os

def get_all_cha_page(sub_sec, dr):
	dr.get(sub_sec)
	ps = dr.page_source
	ps = BeautifulSoup(ps, "html.parser")
	cha_list = ps.find("div", {"id":"left"}).find("ul", {"id":"navlist"}).findAll("li")

	path_list = ps.find("div", {"id":"left"}).find("div", {"id":"nav"}).findAll("a", recursive=False)
	path = ""
	print(len(path_list))
	for p in path_list:
		print(p)
		if p.find(text=True) != None:
			path = path + str(p.find(text=True))
	print(path)

	for cha in cha_list:
		if cha.a.img.attrs['src'] == "style/images/audio.png":
			url = cha.a.attrs['href']
			print(url)
			label = cha.a.find(text=True).strip()[:-4]
			print(path + label)
			cha_url_label_dict[url] = path + label;

def deal_with_one_cha_page(url, label):

	beg_list = []
	end_list = []
	sentence_list = []

	def download_audio_file(url):
		path = "/Users/ida/Desktop/" + label
		try: 
			os.makedirs(path)
		except:
			print("Directory already exists.")
		urlretrieve(url, path + "/audio.mp4")

	def get_beg_end(ps):
		utterance_secs = ps.find("div", {"id":"transcript"}).findAll("span", {"name":"utterance"})
		for sec in utterance_secs:

			line = sec.find(text=True, recursive=False).strip()
			sentence_list.append(line)
			beg_list.append(int(sec['beg']))
			end_list.append(int(sec['end']))


	def split_sentences():
		path = "/Users/ida/Desktop/" + label
		sound = AudioSegment.from_file(path + "/audio.mp4")

		path_t = path + "/sentences_audio/"
		try: 
			os.makedirs(path_t)
		except:
			print("Directory already exists.")

		for i in range(len(beg_list)):
			beg = beg_list[i]
			end = end_list[i]
			sent = sound[beg:end]
			try:
				sent.export(path_t + "id_{}_{}_to_{}.mp4".format(i, beg, end), format="mp4")
			except:
				print("Sentence" + str(i) + "in total list can't be saved as audio")

			
	def save_sent_as_txt():
		with open(label + '/sentence_text.txt', 'w') as filehandle:
			for i in range(len(sentence_list)):
				try:
					s = sentence_list[i]
					s = re.sub('[^0-9a-zA-Z\'.,!?;\s]+', '', s)
					filehandle.write('%s\n' %s)
				except:
					filehandle.write("Sentence " + str(i) + " not available\n")
				

	dr.get(url)
	ps = dr.page_source
	ps = BeautifulSoup(ps, "html.parser")
	audio_url = ps.find("div", {"id":"media"}).audio.source.attrs["src"]
	
	download_audio_file(audio_url)
	get_beg_end(ps)
	split_sentences()
	save_sent_as_txt()


Gleason1 = "https://childes.talkbank.org/browser/index.php?url=Eng-NA/Gleason/Dinner/"
Gleason2 = "https://childes.talkbank.org/browser/index.php?url=Eng-NA/Gleason/Father/"
Gleason3 = "https://childes.talkbank.org/browser/index.php?url=Eng-NA/Gleason/Mother/"

url_list = [Gleason1, Gleason2, Gleason3]


cha_url_label_dict = dict()
dr = webdriver.PhantomJS()

for u in url_list:
	get_all_cha_page(u, dr)

for url in cha_url_label_dict:
	deal_with_one_cha_page(url, cha_url_label_dict[url])
