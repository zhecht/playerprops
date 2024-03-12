
from datetime import datetime,timedelta
from subprocess import call
from bs4 import BeautifulSoup as BS
import json
import os
import re
import argparse
import unicodedata
import time
from twilio.rest import Client
from glob import glob

def writeSavant():

	with open("static/mlb/percentiles.json") as fh:
		percentiles = json.load(fh)

	with open("static/baseballreference/advanced.json") as fh:
		advanced = json.load(fh)

	for player in ["pablo lopez"]:
		savantId = advanced[player]["player_id"]
		url = f"https://baseballsavant.mlb.com/savant-player/{player.replace(' ', '-')}-{savantId}"
		outfile = "outdraft"
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

if __name__ == "__main__":

	writeSavant()