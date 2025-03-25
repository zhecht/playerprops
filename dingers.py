import argparse
import json
import math
import os
import random
import queue
import time
import nodriver as uc
import subprocess
import threading
import multiprocessing

from bs4 import BeautifulSoup as BS
from controllers.shared import *
from datetime import datetime, timedelta

q = queue.Queue()
lock = threading.Lock()

def devig(evData, player="", ou="575/-900", finalOdds=630, prop="hr", sharp=False):
	impliedOver = impliedUnder = 0
	over = int(ou.split("/")[0])
	if over > 0:
		impliedOver = 100 / (over+100)
	else:
		impliedOver = -1*over / (-1*over+100)

	bet = 100
	profit = finalOdds / 100 * bet
	if finalOdds < 0:
		profit = 100 * bet / (finalOdds * -1)

	if "/" not in ou:
		u = 1.07 - impliedOver
		if u >= 1:
			#print(player, ou, finalOdds, impliedOver)
			return
		if over > 0:
			under = int((100*u) / (-1+u))
		else:
			under = int((100 - 100*u) / u)
	else:
		under = int(ou.split("/")[1])

	if under > 0:
		impliedUnder = 100 / (under+100)
	else:
		impliedUnder = -1*under / (-1*under+100)

	x = impliedOver
	y = impliedUnder
	while round(x+y, 8) != 1.0:
		k = math.log(2) / math.log(2 / (x+y))
		x = x**k
		y = y**k

	dec = 1 / x
	if dec >= 2:
		fairVal = round((dec - 1)  * 100)
	else:
		fairVal = round(-100 / (dec - 1))
	#fairVal = round((1 / x - 1)  * 100)
	implied = round(x*100, 2)
	#ev = round(x * (finalOdds - fairVal), 1)

	#multiplicative 
	mult = impliedOver / (impliedOver + impliedUnder)
	add = impliedOver - (impliedOver+impliedUnder-1) / 2

	evs = []
	for method in [x, mult, add]:
		ev = method * profit + (1-method) * -1 * bet
		ev = round(ev, 1)
		evs.append(ev)

	ev = min(evs)

	evData.setdefault(player, {})
	evData[player][f"fairVal"] = fairVal
	evData[player][f"implied"] = implied
	evData[player][f"ev"] = ev

async def getESPNLinks(date):
	browser = await uc.start(no_sandbox=True)
	url = "https://espnbet.com/sport/baseball/organization/united-states/competition/mlb"
	page = await browser.get(url)
	await page.wait_for(selector="article")
	html = await page.get_content()

	games = {}
	soup = BS(html, "html.parser")
	for article in soup.select("article"):
		if " @ " not in article.get("aria-label"):
			continue
		if datetime.strftime(datetime.strptime(date, "%Y-%m-%d"), "%b %d") not in article.text:
			continue

		away, home = map(str, article.get("aria-label").split(" @ "))
		eventId = article.find("div").find("div").get("id").split("|")[1]
		away, home = convertMLBTeam(away), convertMLBTeam(home)
		game = f"{away} @ {home}"
		games[game] = f"{url}/event/{eventId}/section/player_props"

	browser.stop()
	return games

def runESPN(rosters):
	uc.loop().run_until_complete(writeESPN(rosters))

async def writeESPN(rosters):
	book = "espn"
	browser = await uc.start(no_sandbox=True)

	while True:
		data = nested_dict()
		(game, url) = q.get()
		if url is None:
			q.task_done()
			break

		playerMap = {}
		away, home = map(str, game.split(" @ "))
		for team in [away, home]:
			for player in rosters.get(team, {}):
				last = player.split(" ")
				p = player[0][0]+". "+last[-1]
				playerMap[p] = player

		page = await browser.get(url)
		await page.wait_for(selector="div[data-testid='away-team-card']")
		html = await page.get_content()
		soup = BS(html, "html.parser")

		for detail in soup.find_all("details"):
			if not detail.text.startswith("Player Total Home Runs Hit"):
				continue
			for article in detail.find_all("article"):
				player = parsePlayer(article.find("header").text)
				last = player.split(" ")
				p = player[0][0]+". "+last[-1]
				player = playerMap.get(p, player)

				over = article.find("button").find_all("span")[-1].text
				under = article.find_all("button")[-1].find_all("span")[-1].text
				data[game][player][book] = over+"/"+under

		updateData(data)
		q.task_done()
	browser.stop()

async def write365(data, browser):
	book = "365"
	close = False
	if not browser:
		close = True
		browser = await uc.start(no_sandbox=True)
	url = "https://www.oh.bet365.com/?_h=uvJ7Snn5ImZN352O9l7rPQ%3D%3D&btsffd=1#/AC/B16/C20525425/D43/E160301/F43/N2/"
	page = await browser.get(url)

	await page.wait_for(selector=".srb-MarketSelectionButton-selected")	

	reject = await page.query_selector(".ccm-CookieConsentPopup_Reject")
	if reject:
		await reject.mouse_click()

	players = await page.query_selector_all(".gl-Participant_General")
	for player in players:
		game = player.parent.parent.parent.parent.children[0].children[0].children[0].text
		game = convertMLBTeam(game.split(" @ ")[0])+" @ "+convertMLBTeam(game.split(" @ ")[-1])

		attrs = player.attributes
		labelIdx = attrs.index("aria-label")
		label = attrs[labelIdx+1].lower().strip()

		player = parsePlayer(label.split("  0.5")[0].replace("over ", "").replace("under ", ""))
		odds = label.split(" ")[-1]
		
		data.setdefault(game, {})
		data[game].setdefault(player, {})

		if label.startswith("over"):
			data[game][player][book] = odds
		else:
			#data[game][player].setdefault(book, "-/")
			data[game][player][book] += "/"+odds

	if close:
		browser.stop()
	
async def writeDK(data, browser):
	book = "dk"
	close = False
	if not browser:
		close = True
		browser = await uc.start(no_sandbox=True)
	url = "https://sportsbook.draftkings.com/leagues/baseball/mlb?category=batter-props&subcategory=home-runs"
	page = await browser.get(url)

	await page.wait_for(selector=".sportsbook-event-accordion__wrapper")
	gameDivs = await page.query_selector_all(".sportsbook-event-accordion__wrapper")
	for gameDiv in gameDivs:
		game = gameDiv.children[0].children[1].text_all
		if " @ " not in game and " at " not in game:
			continue
		away, home = map(str, game.replace(" at ", " @ ").split(" @ "))
		game = f"{convertMLBTeam(away)} @ {convertMLBTeam(home)}"
		data.setdefault(game, {})

		odds = await gameDiv.query_selector_all("button[data-testid='sb-selection-picker__selection-0']")
		for oIdx, odd in enumerate(odds):
			player = parsePlayer(odd.parent.parent.parent.parent.parent.children[0].text.split(" (")[0])
			ou = odd.text_all.split(" ")[-1]
			data[game].setdefault(player, {})
			data[game][player][book] = ou

	if close:
		browser.stop()

async def getMGMLinks(date):
	browser = await uc.start(no_sandbox=True)
	url = "https://sports.mi.betmgm.com/en/sports/baseball-23/betting/usa-9/mlb-75"
	page = await browser.get(url)
	await page.wait_for(selector="ms-prematch-timer")
	html = await page.get_content()

	games = {}
	soup = BS(html, "html.parser")
	for t in soup.select("ms-prematch-timer"):
		if "Today" in t.text or "Starting" in t.text:
			d = str(datetime.now())[:10]
		elif "Tomorrow" in t.text:
			d = str(datetime.now() + timedelta(days=1))[:10]
		else:
			m,d,y = map(int, t.text.split(" ")[0].split("/"))
			d = f"20{y}-{m:02}-{d:02}"

		if d != date:
			continue

		parent = t.find_previous("ms-six-pack-event")
		a = parent.find("a")
		teams = parent.select(".participant")
		away, home = convertMGMMLBTeam(teams[0].text.strip()), convertMGMMLBTeam(teams[1].text.strip())
		game = f"{away} @ {home}"
		games[game] = "https://sports.betmgm.com"+a.get("href")

	browser.stop()
	return games

def runMGM():
	uc.loop().run_until_complete(writeMGM())

async def writeMGM():
	book = "mgm"
	browser = await uc.start(no_sandbox=True)

	while True:
		data = nested_dict()

		(game, url) = q.get()
		if url is None:
			q.task_done()
			break

		page = await browser.get(url)
		await page.wait_for(selector=".event-details-pills-list")

		show = await page.query_selector(".option-group-column:nth-of-type(2) .option-panel .show-more-less-button")
		if show:
			await show.click()

		html = await page.get_content()
		soup = BS(html, "html.parser")
		panel = soup.select(".option-group-column:nth-of-type(2) .option-panel")[0]
		if panel.select(".market-name")[0].text.strip() != "Batter home runs":
			q.task_done()
			continue
		players = panel.select(".attribute-key")
		odds = panel.select("ms-option")

		for i, player in enumerate(players):
			player = parsePlayer(player.text.strip().split(" (")[0])
			over = odds[i*2].select(".value")
			under = odds[i*2+1].select(".value")
			if not over:
				continue
			ou = over[0].text
			if under:
				ou += "/"+under[0].text

			data[game][player][book] = ou

		updateData(data)
		q.task_done()

	browser.stop()

def updateData(data):
	file = "static/dailyev/odds.json"
	with lock:
		with open(file) as fh:
			d = json.load(fh)
		merge_dicts(d, data, forceReplace=True)
		with open(file, "w") as fh:
			json.dump(d, fh, indent=4)

async def writeFDPage(data, page):
	book = "fd"
	await page.wait_for(selector="h1")
	game = await page.query_selector("h1")
	game = game.text.lower().replace(" odds", "")
	away, home = map(str, game.split(" @ "))
	awayFull, homeFull = away, home
	game = f"{convertMLBTeam(away)} @ {convertMLBTeam(home)}"
	data.setdefault(game, {})

	navs = await page.query_selector_all("nav")
	tabs = await navs[-1].query_selector_all("a")
	for tab in tabs:
		if tab.text == "Batter Props":
			await tab.click()
			await page.wait_for(selector="div[data-test-id=ArrowAction]")
			break

	els = await page.query_selector_all("div[aria-label='Show more']")
	for el in els:
		await el.click()

	btns = await page.query_selector_all("div[role=button]")
	for btn in btns:
		try:
			labelIdx = btn.attributes.index("aria-label")
		except:
			continue
		labelSplit = btn.attributes[labelIdx+1].lower().split(", ")
		if "selection unavailable" in labelSplit[-1] or labelSplit[0].startswith("tab ") or len(labelSplit) <= 1:
			continue

		player = parsePlayer(labelSplit[1])

		data[game].setdefault(player, {})
		data[game][player][book] = labelSplit[-1]

async def writeFD(data, browser):
	close = False
	if not browser:
		close = True
		browser = await uc.start(no_sandbox=True)
	url = f"https://sportsbook.fanduel.com/navigation/mlb"
	page = await browser.get(url)

	await page.wait_for(selector="span[role=link]")
	links = await page.query_selector_all("span[role=link]")

	for link in links:
		if link.text == "More wagers":
			await link.parent.click()
			break

	await writeFDPage(data, page)

	if close:
		browser.stop()

async def writeCZ(date, token=None):
	book = "cz"
	outfile = "outDingersCZ"
	if False and not token:
		await writeCZToken()

	with open("token") as fh:
		token = fh.read()

	url = "https://api.americanwagering.com/regions/us/locations/mi/brands/czr/sb/v3/sports/baseball/events/schedule?competitionIds=04f90892-3afa-4e84-acce-5b89f151063d"
	os.system(f"curl -s '{url}' --compressed -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0' -H 'Accept: */*' -H 'Accept-Language: en-US,en;q=0.5' -H 'Accept-Encoding: gzip, deflate, br' -H 'Referer: https://sportsbook.caesars.com/' -H 'content-type: application/json' -H 'X-Unique-Device-Id: 8478f41a-e3db-46b4-ab46-1ac1a65ba18b' -H 'X-Platform: cordova-desktop' -H 'X-App-Version: 7.13.2' -H 'x-aws-waf-token: {token}' -H 'Origin: https://sportsbook.caesars.com' -H 'Connection: keep-alive' -H 'Sec-Fetch-Dest: empty' -H 'Sec-Fetch-Mode: cors' -H 'Sec-Fetch-Site: cross-site' -H 'TE: trailers' -o {outfile}")
	try:
		with open(outfile) as fh:
			data = json.load(fh)
	except:
		await writeCZToken()
		with open("token") as fh:
			token = fh.read()
		os.system(f"curl -s '{url}' --compressed -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0' -H 'Accept: */*' -H 'Accept-Language: en-US,en;q=0.5' -H 'Accept-Encoding: gzip, deflate, br' -H 'Referer: https://sportsbook.caesars.com/' -H 'content-type: application/json' -H 'X-Unique-Device-Id: 8478f41a-e3db-46b4-ab46-1ac1a65ba18b' -H 'X-Platform: cordova-desktop' -H 'X-App-Version: 7.13.2' -H 'x-aws-waf-token: {token}' -H 'Origin: https://sportsbook.caesars.com' -H 'Connection: keep-alive' -H 'Sec-Fetch-Dest: empty' -H 'Sec-Fetch-Mode: cors' -H 'Sec-Fetch-Site: cross-site' -H 'TE: trailers' -o {outfile}")

	with open(outfile) as fh:
		data = json.load(fh)

	games = []
	for event in data["competitions"][0]["events"]:
		if str(datetime.strptime(event["startTime"], "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=4))[:10] != date:
			continue
			pass
		games.append(event["id"])

	res = nested_dict()
	for gameId in games:
		url = f"https://api.americanwagering.com/regions/us/locations/mi/brands/czr/sb/v3/events/{gameId}"
		os.system(f"curl -s '{url}' --compressed -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0' -H 'Accept: */*' -H 'Accept-Language: en-US,en;q=0.5' -H 'Accept-Encoding: gzip, deflate, br' -H 'Referer: https://sportsbook.caesars.com/' -H 'content-type: application/json' -H 'X-Unique-Device-Id: 8478f41a-e3db-46b4-ab46-1ac1a65ba18b' -H 'X-Platform: cordova-desktop' -H 'X-App-Version: 7.13.2' -H 'x-aws-waf-token: {token}' -H 'Origin: https://sportsbook.caesars.com' -H 'Connection: keep-alive' -H 'Sec-Fetch-Dest: empty' -H 'Sec-Fetch-Mode: cors' -H 'Sec-Fetch-Site: cross-site' -H 'TE: trailers' -o {outfile}")
		game = data["name"].lower().replace("|", "").replace(" at ", " @ ")
		if "@" not in game:
			continue
		away, home = map(str, game.split(" @ "))
		game = f"{convertMLBTeam(away)} @ {convertMLBTeam(home)}"
		
		for market in data["markets"]:
			if "name" not in market or market["active"] == False:
				continue
			prop = market["name"].lower().replace("|", "").split(" (")[0]
			if prop != "player to hit a home run":
				continue

			for selection in market["selections"]:
				try:
					ou = str(selection["price"]["a"])
				except:
					continue
				player = parsePlayer(selection["name"].replace("|", ""))
				res[game][player][book] = ou

	updateData(res)


def writeKambi(date):
	book = "kambi"
	outfile = "outDailyKambi"

	url = "https://eu-offering-api.kambicdn.com/offering/v2018/pivuslarl-lbr/listView/baseball/mlb/all/all/matches.json?lang=en_US&market=US"
	os.system(f"curl -s \"{url}\" -o {outfile}")
	
	with open(outfile) as fh:
		j = json.load(fh)

	data = nested_dict()

	eventIds = {}
	for event in j["events"]:
		game = event["event"]["name"].lower()
		if " vs " in game:
			away, home = map(str, game.split(" vs "))
		else:
			away, home = map(str, game.split(" @ "))
		game = f"{convertMLBTeam(away)} @ {convertMLBTeam(home)}"
		if game in eventIds:
			continue
			#pass
		eventIds[game] = event["event"]["id"]

	for game in eventIds:
		eventId = eventIds[game]
		teamIds = {}
		
		time.sleep(0.3)
		url = f"https://eu-offering-api.kambicdn.com/offering/v2018/pivuslarl-lbr/betoffer/event/{eventId}.json"
		os.system(f"curl -k \"{url}\" -o {outfile}")

		with open(outfile) as fh:
			j = json.load(fh)

		for betOffer in j["betOffers"]:
			label = betOffer["criterion"]["label"].lower()
			if not teamIds and "Handicap" in label:
				for row in betOffer["outcomes"]:
					team = convertMLBTeam(row["label"].lower())
					#teamIds[row["participantId"]] = team
					#data[team] = {}
			elif "to hit a home run" in label:
				player = strip_accents(betOffer["outcomes"][0]["participant"])
				try:
					last, first = map(str, player.lower().split(", "))
					player = f"{first} {last}"
				except:
					player = player.lower()
				player = parsePlayer(player)
				over = betOffer["outcomes"][0]["oddsAmerican"]
				under = betOffer["outcomes"][1]["oddsAmerican"]
				data[game][player][book] = f"{over}/{under}"

	updateData(data)

async def writeFeed(date, loop):
	if not date:
		date = str(datetime.now())[:10]
	url = f"https://baseballsavant.mlb.com/gamefeed?date={date}"
	browser = await uc.start(no_sandbox=True)
	page = await browser.get(url)

	await page.wait_for(selector=".container-open")
	"""
	await page.wait_for(selector=".container-open")
	o = await page.query_selector(".container-open")
	await o.mouse_click()
	time.sleep(0.5)
	await page.wait_for(selector="#nav-buttons")
	nav = await page.query_selector("#nav-buttons")
	await nav.children[3].click()
	time.sleep(1)
	"""

	with open("static/dailyev/feed_times.json") as fh:
		times = json.load(fh)

	i = 0
	while True:
		html = await page.get_content()
		with open(f"static/dailyev/feed.html", "w") as fh:
			fh.write(html)
		parseFeed(times)
		i += 1

		if not loop:
			break
		
		time.sleep(1)
		if i >= 10:
			commitChanges()
			i = 0

	browser.stop()

def parseESPN(espnLines):
	with open("static/baseballreference/roster.json") as fh:
		roster = json.load(fh)

	with open(f"static/mlb/espn.json") as fh:
		espn = json.load(fh)

	players = {}
	for team in roster:
		players[team] = {}
		for player in roster[team]:
			first = player.split(" ")[0][0]
			last = player.split(" ")[-1]
			players[team][f"{first} {last}"] = player

	for game in espn:
		espnLines[game] = {}
		for prop in espn[game]:
			if prop == "hr":
				espnLines[game][prop] = {}
				away, home = map(str, game.split(" @ "))
				for p in espn[game][prop]:
					if p not in players[away] and p not in players[home]:
						continue
					if p in players[away]:
						player = players[away][p]
					else:
						player = players[home][p]
					
					if type(espn[game][prop][p]) is str:
						espnLines[game][prop][player] = espn[game][prop][p]
					else:
						espnLines[game][prop][player] = espn[game][prop][p].copy()

def parseFeed(times):
	soup = BS(open("static/dailyev/feed.html", 'rb').read(), "lxml")
	data = {}
	allTable = soup.find("div", id="allMetrics")
	hdrs = [th.text.lower() for th in allTable.find_all("th")]
	data["all"] = {k: v.text.strip() for k,v in zip(hdrs,allTable.find_all("td")) if k}
	for div in soup.find_all("div", class_="game-container"):
		away = div.find("div", class_="team-left")
		home = div.find("div", class_="team-right")
		away = convertMLBTeam(away.text.strip())
		home = convertMLBTeam(home.text.strip())
		game = f"{away} @ {home}"
		data[game] = []
		if game not in times:
			times[game] = {}
		table = div.find("div", class_="mini-ev-table")
		if not table:
			continue
		for tr in table.find("tbody").find_all("tr"):
			tds = tr.find_all("td")
			player = parsePlayer(tds[1].text.strip())
			img = tds[0].find("img").get("src")
			if tds[4].text.strip() != "Home Run":
				#continue
				pass

			pa = tds[2].text.strip()
			dt = times[game].get(pa, str(datetime.now()))
			times[game][pa] = dt
			j = {
				"player": player,
				"hr/park": tds[-1].text.strip(),
				"pa": pa,
				"dt": dt,
				"img": img
			}
			i = 3
			for hdr in ["in", "result", "evo", "la", "dist"]:
				j[hdr] = tds[i].text.strip()
				i += 1
			data[game].append(j)

	with open("static/dailyev/feed.json", "w") as fh:
		json.dump(data, fh, indent=4)
	with open("static/dailyev/feed_times.json", "w") as fh:
		json.dump(times, fh, indent=4)

def writeEV():
	with open(f"static/dailyev/odds.json") as fh:
		data = json.load(fh)

	with open(f"static/baseballreference/bvp.json") as fh:
		bvpData = json.load(fh)

	with open(f"static/baseballreference/ph.json") as fh:
		ph = json.load(fh)

	with open(f"static/baseballreference/roster.json") as fh:
		roster = json.load(fh)

	with open(f"static/baseballreference/leftOrRight.json") as fh:
		leftOrRight = json.load(fh)

	with open(f"static/dailyev/weather.json") as fh:
		weather = json.load(fh)

	with open(f"static/mlb/lineups.json") as fh:
		lineups = json.load(fh)

	with open(f"updated.json") as fh:
		updated = json.load(fh)
	updated["dingers"] = str(datetime.now())
	with open(f"updated.json", "w") as fh:
		json.dump(updated, fh, indent=4)

	evData = {}

	for game in data:
		away, home = map(str, game.split(" @ "))
		gameWeather = weather.get(game, {})
		awayStats = {}
		homeStats = {}

		if os.path.exists(f"static/splits/mlb/{away}.json"):
			with open(f"static/splits/mlb/{away}.json") as fh:
				awayStats = json.load(fh)
		if os.path.exists(f"static/splits/mlb/{home}.json"):
			with open(f"static/splits/mlb/{home}.json") as fh:
				homeStats = json.load(fh)

		for player in data[game]:
			opp = away
			team = home
			playerStats = {}
			if player in roster.get(away, {}):
				opp = home
				team = away
				playerStats = awayStats.get(player, {})
			elif player in roster.get(home, {}):
				playerStats = homeStats.get(player, {})
			else:
				continue

			bvp = pitcher = ""
			try:
				pitcher = lineups[opp]["pitcher"]
				pitcherLR = leftOrRight[opp].get(pitcher, "")
				bvpStats = bvpData[team][player+' v '+pitcher]
				bvp = f"{bvpStats['h']}-{bvpStats['ab']}, {bvpStats['hr']} HR"
			except:
				pass

			try:
				hrs = [(i, x) for i, x in enumerate(playerStats["hr"]) if x]
				lastHR = len(playerStats["hr"]) - hrs[-1][0]
				lastHR = f"{lastHR} Games"
			except:
				lastHR = ""

			avgOver = []
			avgUnder = []
			highest = 0
			evBook = ""
			books = data[game][player].keys()

			if "fd" not in books:
				#continue
				pass
			oddsArr = []
			for book in books:
				odds = data[game][player][book]
				oddsArr.append(odds)
				over = odds.split("/")[0]
				highest = max(highest, int(over))
				if highest == int(over):
					evBook = book
				avgOver.append(convertImpOdds(int(over)))
				if "/" in odds:
					avgUnder.append(convertImpOdds(int(odds.split("/")[-1])))

			if avgOver:
				avgOver = float(sum(avgOver) / len(avgOver))
				avgOver = convertAmericanFromImplied(avgOver)
			else:
				avgOver = "-"
			if avgUnder:
				avgUnder = float(sum(avgUnder) / len(avgUnder))
				avgUnder = convertAmericanFromImplied(avgUnder)
			else:
				avgUnder = "-"

			ou = f"{avgOver}/{avgUnder}"
			if ou == "-/-" or ou.startswith("-/") or ou.startswith("0/"):
				continue

			if ou.endswith("/-") or ou.endswith("/0"):
				ou = ou.split("/")[0]

			devig(evData, player, ou, highest)
			if "365" in books:
				#devig(evData, player, ou, highest)
				pass

			if player not in evData:
				continue

			try:
				j = ph[team][player]["2024"]
				pinchHit = f"{j['ph']} PH / {j['g']} G"
			except:
				pinchHit = ""
			
			evData[player]["player"] = player
			evData[player]["pitcher"] = "" if not pitcher else f"{pitcher} ({pitcherLR})"
			evData[player]["game"] = game
			evData[player]["weather"] = gameWeather
			evData[player]["book"] = evBook
			evData[player]["line"] = highest
			evData[player]["avg"] = ou
			evData[player]["prop"] = "hr"
			evData[player]["bvp"] = bvp
			evData[player]["lastHR"] = lastHR
			evData[player]["ph"] = pinchHit
			evData[player]["bookOdds"] = {b: o for b, o in zip(books, oddsArr)}

	with open("static/dailyev/ev.json", "w") as fh:
		json.dump(evData, fh, indent=4)

	with open("static/dailyev/evArr.json", "w") as fh:
		json.dump([value for key, value in evData.items()], fh, indent=4)

def printEV():
	with open(f"static/dailyev/ev.json") as fh:
		evData = json.load(fh)

	l = ["EV (AVG)", "EV (365)", "Game", "Player", "IN", "FD", "AVG", "bet365", "DK", "MGM", "CZ", "Kambi"]
	output = "\t".join(l) + "\n"
	for row in sorted(evData.items(), key=lambda item: item[1]["ev"], reverse=True):
		l = [row[-1]["ev"], "", row[-1]["game"].upper(), row[0].title(), ""]
		for book in ["fd", "avg", "365", "dk", "mgm", "cz", "kambi"]:
			if book in row[-1]["bookOdds"]:
				l.append(f"'{row[-1]['bookOdds'][book]}")
			else:
				l.append("")
		output += "\t".join([str(x) for x in l]) + "\n"

	with open("static/dailyev/ev.csv", "w") as fh:
		fh.write(output)

sharedData = {}
def runThread(book):
	uc.loop().run_until_complete(writeOne(book))

async def writeWeather(date):
	browser = await uc.start(no_sandbox=True)
	url = f"https://swishanalytics.com/mlb/weather?date={date}"
	page = await browser.get(url)

	await page.wait_for(selector=".weather-overview-table")
	html = await page.get_content()
	soup = BS(html, "html.parser")

	weather = nested_dict()
	for row in soup.select(".weatherClick"):
		tds = row.select("small")
		game = tds[1].text.lower().strip().replace("\u00a0", " ").replace("  ", " ")
		wind = tds[2].text
		gameId = row.get("id")
		weather[game]["wind"] = wind.replace("\u00a0", " ").replace("  ", " ").strip()

		extra = soup.find("div", id=f"{gameId}Row")
		time, stadium = map(str, soup.find("div", id=f"{gameId}Row").select(".desktop-hide")[0].text.split(" | "))
		weather[game]["time"] = time
		weather[game]["stadium"] = stadium
		for row in extra.find("tbody").find_all("tr"):
			hdr = row.find("td").text.lower()
			tds = row.select(".gametime-hour small")
			if not tds:
				tds = row.select(".gametime-hour")
			
			weather[game][hdr] = [x.text.strip().replace("\u00b0", "") for x in tds][1]
			if hdr == "wind dir":
				transform = row.find("img").get("style").split("; ")[-1]
				weather[game]["transform"] = [x.get("style").split("; ")[-1] for x in row.select(".gametime-hour img:nth-of-type(1)")][1]


	with open("static/dailyev/weather.json", "w") as fh:
		json.dump(weather, fh, indent=4)

def writeLineups(date):
	if not date:
		date = str(datetime.now())[:10]

	with open(f"static/baseballreference/leftOrRight.json") as fh:
		leftOrRight = json.load(fh)

	url = f"https://www.mlb.com/starting-lineups/{date}"
	result = subprocess.run(["curl", url], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

	soup = BS(result.stdout, "html.parser")

	pitchers = {}
	for table in soup.find_all("div", class_="starting-lineups__matchup"):
		player = parsePlayer(table.find("a").text.strip())

	data = {}
	for table in soup.select(".starting-lineups__matchup"):
		for idx, which in enumerate(["away", "home"]):
			try:
				team = table.find("div", class_=f"starting-lineups__teams--{which}-head").text.strip().split(" ")[0].lower().replace("az", "ari").replace("cws", "chw")
			except:
				continue

			if team in data:
				continue
			
			pitcher = parsePlayer(table.find_all("div", class_="starting-lineups__pitcher-name")[idx].text.strip())
			leftRight = "L" if table.find_all("span", class_="starting-lineups__pitcher-pitch-hand")[idx].text == "LHP" else "R"
			leftOrRight[team][pitcher] = leftRight
			data[team] = {"pitcher": pitcher, "batters": []}
			for player in table.find("ol", class_=f"starting-lineups__team--{which}").find_all("li"):
				try:
					player = parsePlayer(player.find("a").text.strip())
				except:
					player = parsePlayer(player.text)

				data[team]["batters"].append(player)

	#for row in plays:
	#	if row[-1] in data and len(data[row[-1]]) > 1:
	#		if row[0] not in data[row[-1]]:
	#			print(row[0], "SITTING!!")

	with open(f"static/mlb/lineups.json", "w") as fh:
		json.dump(data, fh, indent=4)

	with open(f"static/baseballreference/leftOrRight.json", "w") as fh:
		json.dump(leftOrRight, fh, indent=4)


def writeAll():

	threads = []
	for b in ["fd", "dk", "365", "mgm", "kambi"]:
		thread = threading.Thread(target=runThread, args=(b,))
		threads.append(thread)
		thread.start()

	for thread in threads:
		thread.join()

	writeEV()
	printEV()

async def writeOne(book):
	#with open(f"static/dailyev/odds.json") as fh:
	#	data = json.load(fh)
	data = nested_dict()

	browser = await uc.start(no_sandbox=True)
	if book == "fd":
		await writeFD(data, browser)
	elif book == "dk":
		await writeDK(data, browser)
	elif book == "365":
		await write365(data, browser)
	elif book == "mgm":
		await writeMGM(data, browser)
	elif book == "espn":
		await writeESPN(data, browser)
	elif book == "kambi":
		writeKambi(data)

	browser.stop()
	with lock:
		with open(f"static/dailyev/odds.json") as fh:
			old = json.load(fh)
		merge_dicts(old, data, forceReplace=True)
		with open(f"static/dailyev/odds.json", "w") as fh:
			json.dump(old, fh, indent=4)

def runThreads(book, games, totThreads):
	threads = []
	with open("static/baseballreference/roster.json") as fh:
		roster = json.load(fh)
	for _ in range(totThreads):
		if book == "mgm":
			thread = threading.Thread(target=runMGM, args=())
		elif book == "espn":
			thread = threading.Thread(target=runESPN, args=(roster,))
		thread.start()
		threads.append(thread)

	for game in games:
		url = games[game]
		q.put((game,url))

	q.join()

	for _ in range(totThreads):
		q.put((None,None))
	for thread in threads:
		thread.join()

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("--sport")
	parser.add_argument("--token")
	parser.add_argument("--commit", action="store_true")
	parser.add_argument("--date", "-d")
	parser.add_argument("--print", "-p", action="store_true")
	parser.add_argument("--update", "-u", action="store_true")
	parser.add_argument("--bet365", action="store_true")
	parser.add_argument("--espn", action="store_true")
	parser.add_argument("--cz", action="store_true")
	parser.add_argument("--dk", action="store_true")
	parser.add_argument("--fd", action="store_true")
	parser.add_argument("--mgm", action="store_true")
	parser.add_argument("--kambi", action="store_true")
	parser.add_argument("--feed", action="store_true")
	parser.add_argument("--keep", action="store_true")
	parser.add_argument("--ev", action="store_true")
	parser.add_argument("--loop", action="store_true")
	parser.add_argument("--lineups", action="store_true")
	parser.add_argument("--weather", action="store_true")
	parser.add_argument("--threads", type=int, default=5)

	args = parser.parse_args()

	games = {}
	date = args.date
	if not date:
		date = str(datetime.now())[:10]

	if args.feed:
		uc.loop().run_until_complete(writeFeed(args.date, args.loop))
	elif args.fd:
		uc.loop().run_until_complete(writeOne("fd"))
	elif args.mgm:
		games = uc.loop().run_until_complete(getMGMLinks(date))
		#games['mil @ nyy'] = 'https://sports.betmgm.com/en/sports/events/milwaukee-brewers-at-new-york-yankees-16837616'
		runThreads("mgm", games, min(args.threads, len(games)))
	elif args.dk:
		uc.loop().run_until_complete(writeOne("dk"))
	elif args.bet365:
		uc.loop().run_until_complete(writeOne("365"))
	elif args.espn:
		games = uc.loop().run_until_complete(getESPNLinks(date))
		#games['mil @ nyy'] = 'https://espnbet.com/sport/baseball/organization/united-states/competition/mlb/event/b353fbf4-02ef-409b-8327-58fb3b0b1fa9/section/player_props'
		runThreads("espn", games, min(args.threads, len(games)))
	elif args.cz:
		uc.loop().run_until_complete(writeCZ(date, args.token))
	elif args.kambi:
		writeKambi(date)

	if args.weather:
		uc.loop().run_until_complete(writeWeather(date))

	if args.lineups:
		writeLineups(args.date)

	if args.update:
		writeAll()

	if args.ev:
		writeEV()
	if args.print:
		printEV()

	if args.commit:
		commitChanges()

	if True:
		with open("static/mlb/pinnacle.json") as fh:
			pn = json.load(fh)
		with open("static/dailyev/odds.json") as fh:
			data = json.load(fh)

		for book, d in zip(["pn"], [pn]):
			for game in d:
				if "hr" in d[game]:
					for player in d[game]["hr"]:
						data.setdefault(game, {})
						data[game].setdefault(player, {})
						if book == "pn":
							data[game][player][book] = d[game]["hr"][player]["0.5"]
						else:
							data[game][player][book] = d[game]["hr"][player]

		with open("static/dailyev/odds.json", "w") as fh:
			json.dump(data, fh, indent=4)