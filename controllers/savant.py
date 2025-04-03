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
	data = nested_dict()

	#tab = await page.query_selector("#tab_splits")
	#await tab.click()

	#el = await page.query_selector("#splits-season-mlb")
	#await el.click()

	html = await page.get_content()
	soup = BS(html, "html.parser")

	year = "2025"

	tables = ["#date-platoon-mlb", "#order-splits-mlb"]

	for tableId in tables:
		table = soup.select(tableId)[0]
		hdrs = [th.text.lower() for th in table.select("th")]
		for tr in table.select("tbody tr"):
			j = {}
			for hdr, td in zip(hdrs, tr.select("td")):
				if hdr in ["team", "lg"]:
					continue
				try:
					j[hdr] = int(td.text.strip() or 0)
				except:
					try:
						j[hdr] = float(td.text.strip())
					except:
						j[hdr] = td.text.strip().lower()

			t = j["type"]
			del j["type"]
			data[player][year][t] = j.copy()

	browser.stop()

	path = f"static/splits/mlb_savant/{team}.json"
	d = {}
	if os.path.exists(path):
		with open(path) as fh:
			d = json.load(fh)
	merge_dicts(d, data, forceReplace=True)
	with open(f"static/splits/mlb_savant/{team}.json", "w") as fh:
		json.dump(d, fh)

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("--player")
	args = parser.parse_args()

	uc.loop().run_until_complete(writeSplits(args.player))