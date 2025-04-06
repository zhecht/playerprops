
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

def bvpReport(date):
	if not date:
		date = str(datetime.now())[:10]

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
	games = [x["game"] for x in schedule[date]]
	times = [x["start"] for x in schedule[date]]
	for t, game in zip(times, games):
		away, home = map(str, game.split(" @ "))
		awayPitcher, homePitcher = lineups[away]["pitcher"], lineups[home]["pitcher"]
		players = list(roster[away].keys()) + list(roster[home].keys())
		#homers = []
		for player in players:
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
				
				#if hrs:
				#	homers.append(f"""{player.split(" ")[-1].title()} ({hrs})""")
			except:
				pass


		# 1:07 pm NYY @ DET: Stroman v Skubal
		#	Mountcastle (3)
		if False:
			print(f"""{game.upper()}: {awayPitcher.split(" ")[-1].title()} v {homePitcher.split(" ")[-1].title()} ({t})
	{", ".join(homers)}
""")

	posts = []
	post = ""
	m,d = map(str, datetime.strptime(date, "%Y-%m-%d").strftime("%b %-d").split(" "))
	hdr = f"HRs vs {m} {d}{getSuffix(int(d))} SP (sorted by avg)\n\n"
	for row in sorted(homers, reverse=True):
		players = [(x[1].split(" ")[-1].title(), x[0]) for x in sorted(homers[row], reverse=True)]

		if row == 1:
			seen = {}
			for thresh in [333]:
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
			p = f"{row} HR (<.333) => {', '.join(ps)}\n\n"
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
	with open(f"static/splits/mlb_feed/{date}.json") as fh:
		feed = json.load(fh)

	with open("static/mlb/schedule.json") as fh:
		schedule = json.load(fh)

	allFeed = []
	games = [x["game"] for x in schedule[date]]
	for game in games:
		allFeed.extend(feed[game])

	# 📈🚀📉💲🤑
	homers = [x for x in allFeed if x["result"] == "Home Run"]
	near = [x for x in allFeed if x["result"] != "Home Run" and x["hr/park"] and x["hr/park"].split("/")[0] != "0"]

	test = """Apr 4th Summary

31 Homers (2.21 per game) 📈
	Longest: Matt Olson 434 ft
	Hardest: Riley Greene 114.3 Exit Velo

Almost Homers

Sweeney 411 ft, Marte 410 ft, Siri 409 ft, Bailey 402 ft, Morel 402 ft
"""

	longest = sorted([x for x in homers if x["dist"]], key=lambda k: int(k["dist"]), reverse=True)[0]
	#hardest = sorted([(int(x["evo"] or 0), x) for x in homers], reverse=True)[0][1]
	almostRows = [x for x in sorted(near, key=lambda x: int(x["hr/park"].split("/")[0] or 0), reverse=True)]
	almost10 = [f"""{x["player"].title()}""" for x in almostRows if x["hr/park"] and int(x["hr/park"].split("/")[0]) >= 10]
	almost = [f"""{x["player"].title()}""" for x in almostRows if x["hr/park"] and 1 < int(x["hr/park"].split("/")[0] or "0") < 10]
	m,d = map(str, datetime.now().strftime("%b %-d").split(" "))
	post = f"""{m} {d}{getSuffix(int(d))} Summary

{len(homers)} HRs ({round(len(homers) / len(games), 2)} per game)
	Longest: {longest["player"].title()} {longest["dist"]} ft
	
Almost Homers

10+ parks => {", ".join(almost10[:20])}

<10 parks => {", ".join(almost[:20])}
"""
	print(post)
	for game in games:
		for team in game.split(" @ "):
			rows = ", ".join([y["player"].split(" ")[-1].title() for y in [x for x in homers if x["team"] == team]])
			if rows:
				post += f"{team.upper()}: {rows}\n"


def batterReport():

	data = []
	for team in os.listdir("static/splits/mlb/"):
		with open(f"static/splits/mlb_feed/{team}") as fh:
			feed = json.load(fh)

		for player in feed:
			keys = sorted(feed[player].keys(), reverse=True)
			

	exit()

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
	near = [x for x in allFeed if x["result"] != "Home Run" and x["hr/park"] and int(x["hr/park"].split("/")[0]) > 2]

	
	teams = []
	for game in games:
		for team in game.split(" @ "):
			teams.append(team)

	post = "Almost Homers last game\n\n"
	postLength = len(post)
	print(post)
	for team in sorted(teams):
		rows = [x for x in near if x["team"] == team]
		s = []
		for row in rows:
			player = row["player"].split(" ")[-1].title()
			n,d = map(int, row["hr/park"].split("/"))
			s.append(f"{player} {row['dist']} ft")
			#s.append(f"{player}")

		if s:
			p = f"{team.upper()}: {', '.join(s)}"
			postLength += len(p)
			if postLength >= CHAR_LIMIT:
				print("-"*20)
				postLength = 0
			print(p)
			post += f"{p}\n"

	#print(post)

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("--threads", type=int, default=7)
	parser.add_argument("--team", "-t")
	parser.add_argument("--date", "-d")
	parser.add_argument("--sport")
	parser.add_argument("--report", action="store_true")
	parser.add_argument("--bvp", action="store_true")
	parser.add_argument("--daily", action="store_true")

	args = parser.parse_args()

	#dailyReport(args.date)
	if args.bvp:
		bvpReport(args.date)
	if args.report:
		batterReport()
	if args.daily:
		dailyReport(args.date)

	#postHomer({'player': 'aaron judge', 'game': 'ari @ nyy', 'hr/park': '14/30', 'pa': '6', 'dt': '2025-04-03 19:20:50', 'img': 'https://www.mlbstatic.com/team-logos/147.svg', 'team': 'nyy', 'in': '1', 'result': 'Home Run', 'evo': '112.1', 'la': '22', 'dist': '394'})