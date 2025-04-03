from datetime import datetime,timedelta
from subprocess import call
from bs4 import BeautifulSoup as BS
import math
import json
import os
import re
import argparse
import unicodedata
import time
import csv
from glob import glob
import nodriver as uc

try:
	from shared import *
except:
	from controllers.shared import *


async def writeSplits(player):
	with open("static/baseballreference/expected.json") as fh:
		expected = json.load(fh)

	team = playerId = ""
	for t in expected:
		if player in expected[t]:
			team = t
			playerId = expected[t][player]["entity_id"]
			break

	if not team:
		print("Not found in expected")

	url = f"https://baseballsavant.mlb.com/savant-player/{playerId}"

	browser = await uc.start(no_sandbox=True)

	page = await browser.get(url)
	await page.wait_for(selector=".table-savant")
	html = await page.get_content()
	soup = BS(html, "html.parser")

	data = nested_dict()
	year = "2025"

	table = soup.select("#date-platoon-mlb")[0]
	hdrs = [th.text.lower() for th in table.select("th")]
	for tr in table.select("tbody tr"):
		for hdr, td in zip(hdrs, tr.select("td")):
			if hdr in ["team", "lg"]:
				continue
			data[player][year]["leftRight"][hdr] = td.text

	browser.stop()
	with open(f"static/splits/mlb_savant/{team}", "w") as fh:
		json.dump(data, fh, indent=4)

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("--player")
	args = parser.parse_args()

	uc.loop().run_until_complete(writeSplits(args.player))