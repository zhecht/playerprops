
from flask import *
from datetime import datetime,timedelta
from subprocess import call
from bs4 import BeautifulSoup as BS
import json
import os
import re
import argparse
import unicodedata
import time
import csv
from twilio.rest import Client
from glob import glob

mlbdraft_blueprint = Blueprint('mlbdraft', __name__, template_folder='views')

def strip_accents(text):
	try:
		text = unicode(text, 'utf-8')
	except NameError: # unicode is a default on python 3 
		pass

	text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode("utf-8")

	return str(text)

def parsePlayer(player):
	return strip_accents(player).lower().replace(".", "").replace("'", "").replace("-", " ").replace(" jr", "").replace(" iii", "").replace(" ii", "")

def writeSavant():

	with open("static/mlb/percentiles.json") as fh:
		percentiles = json.load(fh)

	with open("static/baseballreference/advanced.json") as fh:
		advanced = json.load(fh)

	for player in advanced:
		savantId = advanced[player]["player_id"]
		url = f"https://baseballsavant.mlb.com/savant-player/{player.replace(' ', '-')}-{savantId}"
		outfile = "outdraft"
		time.sleep(0.2)
		os.system(f"curl {url} -o {outfile}")

		soup = BS(open(outfile, 'rb').read(), "lxml")

		percentiles[player] = {}

		data = "{}"
		for script in soup.findAll("script"):
			if not script.string:
				continue
			if "serverVals" in script.string:
				m = re.search(r"statcast: \[(.*?)\],", script.string)
				if m:
					data = m.group(1).replace("false", "False").replace("true", "True").replace("null", "None")
					data = f"[{data}]"
					break

		data = eval(data)

		for row in data:
			if row["year"] == "2023":
				for hdr in row:
					if hdr.startswith("percent_rank") and row[hdr] and "unrounded" not in hdr:
						percentiles[player][hdr] = row[hdr]

	with open("static/mlb/percentiles.json", "w") as fh:
		json.dump(percentiles, fh, indent=4)

def writePitchers():
	pitchers = []
	with open("static/mlb/fantasypros_pitchers.csv") as fh:
		reader = csv.reader(fh, delimiter=",")
		for idx, row in enumerate(reader):
			if idx == 0 or len(row) < 3:
				continue

			if float(row[3]) >= 100:
				pitchers.append(parsePlayer(row[0]))

	with open("static/mlb/pitchers.json", "w") as fh:
		json.dump(pitchers, fh, indent=4)

@mlbdraft_blueprint.route('/getMLBDraft')
def getmlbdraft_route():
	with open("static/mlb/percentiles.json") as fh:
		percentiles = json.load(fh)

	with open("static/baseballreference/advanced.json") as fh:
		advanced = json.load(fh)

	res = []
	for player in percentiles:
		savantId = advanced[player]["player_id"]
		j = {"player": player.title(), "savantId": savantId}
		for stat in percentiles[player]:
			s = stat.replace("percent_rank_", "")
			j[s] = percentiles[player][stat]
		res.append(j)

	return jsonify(res)

@mlbdraft_blueprint.route('/mlbdraft')
def mlbdraft_route():

	return render_template("mlbdraft.html")

if __name__ == "__main__":

	#writePitchers()
	writeSavant()