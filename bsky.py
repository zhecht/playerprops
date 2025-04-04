
from datetime import datetime,timedelta
from subprocess import call
from bs4 import BeautifulSoup as BS
from atproto import Client
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

from controllers.shared import *

# 300 char limit

def dailyReport(date):
	if not date:
		date = str(datetime.now())[:10]
	with open("static/dailyev/feed.json") as fh:
		feed = json.load(fh)

	with open("static/mlb/schedule.json") as fh:
		schedule = json.load(fh)

	games = [x["game"] for x in schedule[date]]
	allFeed = []
	for game in games:
		allFeed.extend(feed[game])
	homers = [x for x in allFeed if x["result"] == "Home Run"]

	post = f"{datetime.strptime(date, "%Y-%m-%d").strftime("%b %-d")}: {len(homers)} HRs ({round(len(homers) / len(games), 2)} per game)\n\n"
	for game in games:
		post += f"{game.upper()}: \n"

	"""
	10 HRs Apr 3 (2.00 per Game)

	ARI @ NYY: Chisholm, Grisham, Judge
	HOU @ MIN: Pena, Walker
	COL @ PHI: Schwarber
	BOS @ BAL: Casas, Campbell, Mullins, Bregman
	"""

#{'player': 'aaron judge', 'game': 'ari @ nyy', 'hr/park': '14/30', 'pa': '6', 'dt': '2025-04-03 19:20:50', 'img': 'https://www.mlbstatic.com/team-logos/147.svg', 'team': 'nyy', 'in': '1', 'result': 'Home Run', 'evo': '112.1', 'la': '22', 'dist': '394'}
def postHomer(data): 
	# Aaron Judge DINGER | ARI @ NYY | 394 ft | 14 Parks
	# Aaron Judge DINGER | ARI @ NYY ▼4 | 394 ft | 14 Parks
	icon = "▲" if data["game"].startswith(data["team"]) else "▼"
	post = f"""{data["player"].title()} DINGER | {data["game"].upper()} {icon}{data["in"]} | {data["dist"]} ft | {data["hr/park"].split("/")[0]} Parks
	"""
	
	client = Client() #AsyncClient
	import p
	client.login("intersectinglines7@gmail.com", p.BSKY_PASSWORD)
	client.send_post(text=post)

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("--threads", type=int, default=7)
	parser.add_argument("--team", "-t")
	parser.add_argument("--date", "-d")
	parser.add_argument("--sport")
	parser.add_argument("--nhl", action="store_true")
	parser.add_argument("--mlb", action="store_true")
	parser.add_argument("-u", "--update", action="store_true")
	parser.add_argument("--run", action="store_true")
	parser.add_argument("--schedule", action="store_true")
	parser.add_argument("--stats", action="store_true")

	args = parser.parse_args()

	#dailyReport(args.date)

	postHomer({'player': 'aaron judge', 'game': 'ari @ nyy', 'hr/park': '14/30', 'pa': '6', 'dt': '2025-04-03 19:20:50', 'img': 'https://www.mlbstatic.com/team-logos/147.svg', 'team': 'nyy', 'in': '1', 'result': 'Home Run', 'evo': '112.1', 'la': '22', 'dist': '394'})