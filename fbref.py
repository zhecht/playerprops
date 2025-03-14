import argparse
import json
import os
import random
import time
import nodriver as uc

from controllers.shared import *
from datetime import datetime, timedelta

async def writeMatches(date=None):
	with open("static/soccer/schedule.json") as fh:
		schedule = json.load(fh)
	with open("static/soccer/links.json") as fh:
		links = json.load(fh)

	if not date:
		date = str(datetime.now())[:10]

	schedule[date] = {}

	url = f"https://fbref.com/en/matches/{date}"
	browser = await uc.start(no_sandbox=True)
	page = await browser.get(url)

	await page.wait_for(selector="td[data-stat=match_report]")

	reports = await page.query_selector_all("td[data-stat=match_report]")
	for report in reports:
		league = report.parent.parent.children[0].children[0].children[0].href.split("/")[-1].lower().replace("-", " ").replace(" stats", "")
		if league not in links:
			links[league] = {}
		if league not in schedule[date]:
			schedule[date][league] = []

		for td in report.parent.children:
			if "home_team" in td.attributes:
				homeLink = td.children[0]
			elif "away_team" in td.attributes:
				awayLink = td.children[-1]
				break

		try:
			home = convertSoccer(homeLink.href.split("/")[-1].lower().replace("-", " ").replace(" stats", ""))
			away = convertSoccer(awayLink.href.split("/")[-1].lower().replace("-", " ").replace(" stats", ""))
		except:
			continue
		game = f"{home} v {away}"
		schedule[date][league].append(game)
		links[league][home] = homeLink.href
		links[league][away] = awayLink.href

	browser.stop()

	with open("static/soccer/schedule.json", "w") as fh:
		json.dump(schedule, fh, indent=4)

	with open("static/soccer/links.json", "w") as fh:
		json.dump(links, fh, indent=4)

async def writePlayerStats(playerUrl, browser=None):
	#https://fbref.com/en/players/82518f62/matchlogs/2024-2025/Bruno-Guimaraes-Match-Logs
	if not browser:
		browser = await uc.start(no_sandbox=True)
	try:
		page = await browser.get(playerUrl)
		await page.wait_for(selector="#matchlogs_all")
	except:
		return

	rows = await page.query_selector_all("#matchlogs_all tbody tr")
	data = {}
	for row in rows:
		if "class" in row.attributes:
			continue
		for td in row.children:
			dataStatIdx = td.attributes.index("data-stat")
			stat = td.attributes[dataStatIdx+1]
			if stat in ["round", "match_report"]:
				continue
			if stat not in data:
				data[stat] = []

			try:
				if stat in ["team", "opponent"]:
					value = td.children[-1].text
				else:
					value = td.text
			except:
				value = td.text
			data[stat].append(strip_accents(value))

	for stat in data:
		data[stat] = ",".join(data[stat])

	return data


async def writeStats(leagueArg, teamArg):
	with open("static/soccer/links.json") as fh:
		links = json.load(fh)

	with open("static/soccer/roster.json") as fh:
		roster = json.load(fh)

	leagueArg = leagueArg.replace("-", " ")
	teamArg = teamArg.replace("-", " ")
	if leagueArg not in links or teamArg not in links[leagueArg]:
		return

	leaguePath = leagueArg.replace('-', ' ').replace(' ', '_')
	teamPath = teamArg.replace('-', ' ').replace(' ', '_')
	stats = {}
	if not os.path.exists(f"static/soccer/stats/{leaguePath}"):
		os.mkdir(f"static/soccer/stats/{leaguePath}")

	path = f"static/soccer/stats/{leaguePath}/{teamPath}.json"
	if os.path.exists(path):
		with open(path) as fh:
			stats = json.load(fh)
	else:
		stats = {}

	url = f"https://fbref.com{links[leagueArg][teamArg]}"
	browser = await uc.start(no_sandbox=True)

	if False:
		stats["teamStats"] = {}
		stats["teamStatsAgainst"] = {}

		for type in ["shooting", "keeper", "passing", "passing_types", "defense"]:
			for i in range(2):
				key = "teamStats"
				if i == 1:
					key += "Against"
					a = await page.query_selector_all(".switcher a")
					await a[-1].mouse_click()
					time.sleep(0.1)

				link = links[leagueArg][teamArg]
				firstLink = "/".join(link.split("/")[:-1])
				url = f"https://fbref.com{firstLink}/2024-2025/matchlogs/all_comps/{type}/{link.split('/')[-1].replace('Stats', 'Match-Logs-All-Competitions')}"
				page = await browser.get(url)
				time.sleep(0.5)

				try:
					await page.wait_for(selector="#matchlogs_for")
				except:
					continue

				table = await page.query_selector("#matchlogs_for")
				tr = await table.query_selector_all("thead tr")
				hdrs = await tr[-1].query_selector_all("th")
				hdrs_ = []
				for hdr in hdrs:
					try:
						statIdx = hdr.attributes.index("data-stat")
					except:
						continue
					hdrs_.append(hdr.attributes[statIdx+1])
				hdrs = hdrs_
				rows = await table.query_selector_all("tbody tr")
				for row in rows:
					if row.children[0].children[0].tag != "a":
						continue
					for hdr, col in zip(hdrs, row.children):
						if hdr in ["start_time", "comp", "round", "attendance", "captain", "formation", "opp formation", "match_report", "notes"]:
							continue
						if hdr in ["date", "dayofweek", "venue", "result", "goals_for", "goals_against", "opponent"] and type != "shooting":
							continue
						if hdr not in stats[key]:
							stats[key][hdr] = []
						#if type == "passing":
						#	print(key, hdr, col.text_all)
						#	exit()
						stats[key][hdr].append(col.text_all)

		for hdr in stats["teamStats"]:
			stats["teamStats"][hdr] = ",".join(stats["teamStats"][hdr])
			stats["teamStatsAgainst"][hdr] = ",".join(stats["teamStatsAgainst"][hdr])

		with open(path, "w") as fh:
			json.dump(stats, fh, indent=4)

	#browser.stop()
	#return

	url = f"https://fbref.com{links[leagueArg][teamArg]}"
	#browser = await uc.start(no_sandbox=True)
	page = await browser.get(url)
	await page.wait_for(selector="#all_stats_standard")
	players = await page.query_selector_all("#all_stats_standard th[data-stat=player]")
	#print(url, len(players))
	for playerIdx, player in enumerate(players[1:]):
		# matches played
		try:
			if int(player.parent.children[4].text) == 0:
				continue
		except:
			continue
		playerLink = player.children[0].href
		if not playerLink:
			continue
		name = playerLink.split("/")[-1].lower().replace("-", " ")
		player = parsePlayer(name)
		if player in stats:
			#continue
			pass

		#print(player)

		if player not in stats:
			stats[player] = {}
		if player not in roster:
			roster[player] = []
		if teamArg not in roster[player]:
			roster[player].append(teamArg)

		playerUrl = f"https://fbref.com/en/players/{playerLink.split('/')[-2]}/matchlogs/2024-2025/{playerLink.split('/')[-1]}-Match-Logs"
		j = await writePlayerStats(playerUrl, browser)
		if j:
			stats[player] = j.copy()

		with open(path, "w") as fh:
			json.dump(stats, fh, indent=4)

		with open("static/soccer/roster.json", "w") as fh:
			json.dump(roster, fh, indent=4)

		page = await browser.get(url)
		await page.wait_for(selector="th[data-stat=player]")
		players = await page.query_selector_all("#all_stats_standard th[data-stat=player]")
		time.sleep(round(random.uniform(0.3, 0.7), 2))

	browser.stop()

	with open(path, "w") as fh:
		json.dump(stats, fh, indent=4)

	with open("static/soccer/roster.json", "w") as fh:
		json.dump(roster, fh, indent=4)


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("--date", "-d")
	parser.add_argument("--team", "-t")
	parser.add_argument("--league", "-l")
	parser.add_argument("--matches", action="store_true")
	parser.add_argument("--all", action="store_true")
	parser.add_argument("--stats", action="store_true")
	parser.add_argument("--today", action="store_true")

	args = parser.parse_args()

	if args.matches:
		uc.loop().run_until_complete(writeMatches(args.date))

	if args.stats:
		if args.today or args.all:
			with open("static/soccer/schedule.json") as fh:
				schedule = json.load(fh)
			today = str(datetime.now())[:10]
			if args.date:
				today = args.date
			for league in schedule[today]:
				for game in schedule[today][league]:
					for team in game.split(" v "):
						print(league, team)
						if team == "milan":
							#continue
							pass
						uc.loop().run_until_complete(writeStats(league, team))
		else:
			uc.loop().run_until_complete(writeStats(args.league, args.team))

	#uc.loop().run_until_complete(writePlayerStats("https://fbref.com/en/players/82518f62/matchlogs/2024-2025/Bruno-Guimaraes-Match-Logs"))

