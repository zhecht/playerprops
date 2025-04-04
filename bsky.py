
from datetime import datetime,timedelta
from subprocess import call
from bs4 import BeautifulSoup as BS
from atproto import AsyncClient, Client
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

def dailyReport():
	date = str(datetime.now())[:10]

	with open(f"static/dailyev/odds.json") as fh:
		data = json.load(fh)

	with open(f"static/mlb/lineups.json") as fh:
		lineups = json.load(fh)

	with open(f"static/mlb/schedule.json") as fh:
		schedule = json.load(fh)

	with open(f"static/baseballreference/leftOrRight.json") as fh:
		leftOrRight = json.load(fh)

	with open(f"static/baseballreference/bvp.json") as fh:
		bvpData = json.load(fh)

	with open(f"static/baseballreference/roster.json") as fh:
		roster = json.load(fh)

	homers = {}
	for game in data:
		away, home = map(str, game.split(" @ "))
		for player in data[game]:
			team, opp = home, away
			if player in roster.get(away, {}):
				team, opp = away, home
			elif player not in roster.get(home, {}):
				continue

			bvp = pitcher = ""
			try:
				pitcher = lineups[opp]["pitcher"]
				pitcherLR = leftOrRight[opp].get(pitcher, "")
				bvpStats = bvpData[team][player+' v '+pitcher]
				hrs = bvpStats["hr"]
				avg = round(bvpStats["h"] / bvpStats["ab"], 3)
				
				if hrs:
					homers.setdefault(hrs, [])
					homers[hrs].append((avg, player))
				#bvp = f"{bvpStats['h']}-{bvpStats['ab']}, {bvpStats['hr']} HR"
			except:
				pass


	posts = []
	post = f"{datetime.now().strftime("%b %-d")} ({len(schedule[date])} games)\n\n"
	post += f"HR vs Pitcher (sorted by avg)\n"
	for row in sorted(homers, reverse=True):
		players = [(x[1].split(" ")[-1].title(), x[0]) for x in sorted(homers[row], reverse=True)]

		if row == 1:
			seen = {}
			for thresh in [750, 500, 250]:
				ps = []
				for p in players:
					if p[1] >= thresh / 1000 and p[0] not in seen:
						ps.append(p[0])
						seen[p[0]] = 1

				p = f"{row} (0.{thresh}+) => {', '.join(ps)}\n"
				if len(post)+len(p) >= 300:
					posts.append(post)
					post = ""
				post += p

			ps = []
			for p in players:
				if p[0] not in seen:
					ps.append(p[0])
			p = f"{row} (<0.250) => {', '.join(ps)}\n"
			if len(post)+len(p) >= 300:
				posts.append(post)
				post = ""
			post += p
		else:
			post += f"{row} => {', '.join([x[0] for x in players])}\n"
	posts.append(post)

	for post in posts:
		print(post)
	
	if False:
		client = Client()
		import p
		client.login("zhecht7@gmail.com", p.BSKY_PASSWORD)
		print(posts[0])
		parent = client.send_post(text=posts[0])

		if len(posts) > 1:
			client.send_post(posts[1], reply_to={
				"parent": {"uri": parent.uri, "cid": parent.cid},
				"root": {"uri": parent.uri, "cid": parent.cid}
			})

def yesterdayReport():
	date = str(datetime.now())[:10]
	with open("static/dailyev/feed.json") as fh:
		feed = json.load(fh)

	with open("static/mlb/schedule.json") as fh:
		schedule = json.load(fh)

	allFeed = []
	for day in [1,2]:
		dt = str(datetime.now() - timedelta(days=day))[:10]
		games = [x["game"] for x in schedule[date]]
		for game in games:
			allFeed.extend(feed[game])
	homers = [x for x in allFeed if x["result"] == "Home Run"]
	near = [x for x in allFeed if x["result"] != "Home Run" and x["hr/park"] and x["hr/park"].split("/")[0] != "0"]

	post = f"{datetime.strptime(date, "%Y-%m-%d").strftime("%b %-d")}: {len(homers)} HRs ({round(len(homers) / len(games), 2)} per game)\n\n"
	for game in games:
		for team in game.split(" @ "):
			rows = ", ".join([y["player"].split(" ")[-1].title() for y in [x for x in homers if x["team"] == team]])
			if rows:
				post += f"{team.upper()}: {rows}\n"

	nearPost = f"{len(near)} almost HRs\n\n"
	for game in games:
		for team in game.split(" @ "):
			rows = [x for x in near if x["team"] == team]
			s = []
			for row in rows:
				player = row["player"].split(" ")[-1].title()
				n,d = map(int, row["hr/park"].split("/"))
				s.append(f"{player} {row['dist']} ft")
			if s:
				nearPost += f"{team.upper()}: {', '.join(s)}\n"

	if False:
		client = Client()
		import p
		client.login("zhecht7@gmail.com", p.BSKY_PASSWORD)
		print(post)
		parent = client.send_post(text=post)
		client.send_post(nearPost[:300], reply_to={
			"parent": {"uri": parent.uri, "cid": parent.cid},
			"root": {"uri": parent.uri, "cid": parent.cid}
		})

# 🚀⚾🚀 Aaron Judge
#   🏟️ ▾1 ARI @ NYY
# 399 ft | 19 Parks
def postHomer(data): 
	icon = "▴" if data["game"].startswith(data["team"]) else "▾"
	post = f"""🚀⚾🚀 {data["player"].title()} DINGER
 🏟️ {icon}{data["in"]} {data["game"].upper()}
{data["dist"]} ft | {data["hr/park"].split("/")[0]} Parks
	"""
	
	client = Client()
	import p
	client.login("zhecht7@gmail.com", p.BSKY_PASSWORD)
	print(post)
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

	dailyReport()

	#postHomer({'player': 'aaron judge', 'game': 'ari @ nyy', 'hr/park': '14/30', 'pa': '6', 'dt': '2025-04-03 19:20:50', 'img': 'https://www.mlbstatic.com/team-logos/147.svg', 'team': 'nyy', 'in': '1', 'result': 'Home Run', 'evo': '112.1', 'la': '22', 'dist': '394'})