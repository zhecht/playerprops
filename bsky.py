
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

CHAR_LIMIT = 280

def bvpReport():
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
	post = ""
	m,d = map(str, datetime.now().strftime("%b %-d").split(" "))
	hdr = f"HRs vs {m} {d}{getSuffix(int(d))} SP (sorted by avg)\n\n"
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

				p = f"{row} HR (.{thresh}+) => {', '.join(ps)}\n\n"
				if len(post)+len(p) >= CHAR_LIMIT:
					posts.append(post)
					post = ""
				post += p

			ps = []
			for p in players:
				if p[0] not in seen:
					ps.append(p[0])
			p = f"{row} HR (<.250) => {', '.join(ps)}\n\n"
			if len(post)+len(p) >= CHAR_LIMIT:
				posts.append(post)
				post = ""
			post += p
		else:
			post += f"{row} HRs => {', '.join([x[0] for x in players])}\n\n"
	posts.append(post)

	for post in posts:
		print(f"{hdr}{post}")
	
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

def dailyReport(date):
	if not date:
		date = str(datetime.now())[:10]
	with open("static/dailyev/feed.json") as fh:
		feed = json.load(fh)

	with open("static/mlb/schedule.json") as fh:
		schedule = json.load(fh)

	allFeed = []
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

def batterReport():
	date = str(datetime.now())[:10]
	with open("static/dailyev/feed.json") as fh:
		feed = json.load(fh)

	with open("static/mlb/schedule.json") as fh:
		schedule = json.load(fh)

	with open("static/baseballreference/roster.json") as fh:
		rosters = json.load(fh)

	with open("static/dailyev/odds.json") as fh:
		odds = json.load(fh)

	players = []
	for team in rosters:
		for player in rosters[team]:
			players.append(player)

	with open("static/dailyev/ev.json") as fh:
		ev = json.load(fh)

	allFeed = []
	for day in [1,2]:
		dt = str(datetime.now() - timedelta(days=day))[:10]
		games = [x["game"] for x in schedule[dt]]
		with open(f"static/splits/mlb_feed/{dt}.json") as fh:
			feed = json.load(fh)
		for game in games:
			allFeed.extend(feed[game])

	homers = [x for x in allFeed if x["result"] == "Home Run"]
	near = [x for x in allFeed if x["result"] != "Home Run" and x["hr/park"] and x["hr/park"].split("/")[0] != "0"]

	post = "Almost Homers last game\n\n"
	teams = [team for team in [game for game in games]]
	print(teams)
	for game in games:
		for team in game.split(" @ "):

			rows = [x for x in near if x["team"] == team]
			s = []
			for row in rows:
				player = row["player"].split(" ")[-1].title()
				n,d = map(int, row["hr/park"].split("/"))
				s.append(f"{player} {row['dist']} ft")
			if s:
				post += f"{team.upper()}: {', '.join(s)}\n\n"

	print(post)

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
	#bvpReport()
	batterReport()

	#postHomer({'player': 'aaron judge', 'game': 'ari @ nyy', 'hr/park': '14/30', 'pa': '6', 'dt': '2025-04-03 19:20:50', 'img': 'https://www.mlbstatic.com/team-logos/147.svg', 'team': 'nyy', 'in': '1', 'result': 'Home Run', 'evo': '112.1', 'la': '22', 'dist': '394'})