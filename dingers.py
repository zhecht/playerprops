import argparse
import json
import math
import os
import random
import time
import nodriver as uc
import threading
import multiprocessing

from bs4 import BeautifulSoup as BS
from controllers.shared import *
from datetime import datetime, timedelta

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

async def writeESPN(data, browser):
	book = "espn"
	close = False
	if not browser:
		close = True
		browser = await uc.start(no_sandbox=True)

	with open(f"static/dailyev/odds.json") as fh:
		oldData = json.load(fh)
	players = {}
	for game in oldData:
		for player in oldData[game]:
			last = player.split(" ")
			p = player[0][0]+". "+last[-1]
			players[p] = player

	url = "https://espnbet.com/sport/baseball/organization/united-states/competition/mlb/event/6a1344e6-8f85-4272-a1bf-9bb6f3f7527c/section/player_props"
	game = "lad @ chc"
	page = await browser.get(url)
	await page.wait_for(selector="div[data-testid='away-team-card']")

	html = await page.get_content()
	soup = BS(html, "lxml")

	for detail in soup.find_all("details"):
		if not detail.text.startswith("Player Total Home Runs Hit"):
			continue
		for article in detail.find_all("article"):
			player = parsePlayer(article.find("header").text)
			last = player.split(" ")
			p = player[0][0]+". "+last[-1]
			player = players.get(p, player)

			over = article.find("button").find_all("span")[-1].text
			under = article.find_all("button")[-1].find_all("span")[-1].text
			data[game][player][book] = over+"/"+under

	if close:
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

async def writeMGM(data, browser):
	book = "mgm"
	close = False
	if not browser:
		close = True
		browser = await uc.start(no_sandbox=True)

	game = "lad @ chc"
	data.setdefault(game, {})

	url = "https://sports.mi.betmgm.com/en/sports/events/los-angeles-dodgers-at-chicago-cubs-neutral-venu-17080709"
	page = await browser.get(url)

	await page.wait_for(selector=".event-details-pills-list")
	panel = await page.query_selector(".option-group-column:nth-of-type(2) .option-panel")
	show = await panel.query_selector(".show-more-less-button")
	if show:
		await show.click()
		await show.scroll_into_view()
		time.sleep(0.5)

	players = await panel.query_selector_all(".attribute-key")
	odds = await panel.query_selector_all("ms-option")

	for idx, player in enumerate(players):
		player = parsePlayer(player.text.strip().split(" (")[0])
		over = await odds[idx*2].query_selector(".value")
		under = await odds[idx*2+1].query_selector(".value")
		if not over:
			continue
		ou = over.text
		if under:
			ou += "/"+under.text

		data[game].setdefault(player, {})
		data[game][player][book] = ou

	if close:
		browser.stop()

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

async def writeCZ(token=None):
	outfile = "outDingersCZ"
	if not token:
		url = f"https://sportsbook.caesars.com/us/mi/bet/"
		browser = await uc.start(no_sandbox=True)
		exit()

	url = "https://api.americanwagering.com/regions/us/locations/mi/brands/czr/sb/v3/sports/baseball/events/schedule?competitionIds=04f90892-3afa-4e84-acce-5b89f151063d"
	os.system(f"curl '{url}' --compressed -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0' -H 'Accept: */*' -H 'Accept-Language: en-US,en;q=0.5' -H 'Accept-Encoding: gzip, deflate, br' -H 'Referer: https://sportsbook.caesars.com/' -H 'content-type: application/json' -H 'X-Unique-Device-Id: 8478f41a-e3db-46b4-ab46-1ac1a65ba18b' -H 'X-Platform: cordova-desktop' -H 'X-App-Version: 7.13.2' -H 'x-aws-waf-token: {token}' -H 'Origin: https://sportsbook.caesars.com' -H 'Connection: keep-alive' -H 'Sec-Fetch-Dest: empty' -H 'Sec-Fetch-Mode: cors' -H 'Sec-Fetch-Site: cross-site' -H 'TE: trailers' -o {outfile}")

def writeKambi(data):
	book = "kambi"
	outfile = "outDailyKambi"

	url = "https://eu-offering-api.kambicdn.com/offering/v2018/pivuslarl-lbr/listView/baseball/mlb/all/all/matches.json?lang=en_US&market=US"
	os.system(f"curl -k \"{url}\" -o {outfile}")
	
	with open(outfile) as fh:
		j = json.load(fh)

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
				#
				#team = teamIds[betOffer["outcomes"][0]["eventParticipantId"]]

				data.setdefault(game, {})
				data[game].setdefault(player, {})
				data[game][player][book] = f"{over}/{under}"

	with open(f"static/dailyev/odds.json", "w") as fh:
		json.dump(data, fh, indent=4)

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
		bvp = json.load(fh)

	with open(f"static/baseballreference/roster.json") as fh:
		roster = json.load(fh)

	with open(f"static/mlbprops/lineups.json") as fh:
		lineups = json.load(fh)

	evData = {}

	for game in data:
		away, home = map(str, game.split(" @ "))
		for player in data[game]:
			opp = away
			team = home
			if player in roster[away]:
				opp = home
				team = away

			try:
				pitcher = lineups[opp]["pitching"]
				bvpStats = bvp[team][player+' v '+pitcher]
			except:
				pitcher = ""

			avgOver = []
			avgUnder = []
			highest = 0
			evBook = ""
			books = data[game][player].keys()

			if len(books) < 2:
				continue
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
			
			evData[player]["player"] = player
			evData[player]["game"] = game
			evData[player]["book"] = evBook
			evData[player]["line"] = highest
			evData[player]["avg"] = ou
			evData[player]["prop"] = "hr"
			evData[player]["bookOdds"] = {b: o for b, o in zip(books, oddsArr)}

	with open("static/dailyev/ev.json", "w") as fh:
		json.dump(evData, fh, indent=4)

	with open("static/dailyev/evArr.json", "w") as fh:
		json.dump([value for key, value in evData.items()], fh, indent=4)

	#with open("static/mlb/evArr.json", "w") as fh:
	#	json.dump([value for key, value in evData.items()], fh, indent=4)

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

	args = parser.parse_args()

	if args.feed:
		uc.loop().run_until_complete(writeFeed(args.date, args.loop))
	elif args.fd:
		uc.loop().run_until_complete(writeOne("fd"))
	elif args.mgm:
		uc.loop().run_until_complete(writeOne("mgm"))
	elif args.dk:
		uc.loop().run_until_complete(writeOne("dk"))
	elif args.bet365:
		uc.loop().run_until_complete(writeOne("365"))
	elif args.espn:
		uc.loop().run_until_complete(writeOne("espn"))
	elif args.cz:
		uc.loop().run_until_complete(writeCZ(args.token))
	elif args.kambi:
		writeKambi()

	if args.update:
		writeAll()

	if args.ev:
		writeEV()
	if args.print:
		printEV()

	if args.commit:
		commitChanges()

	if True:
		with open("static/mlb/caesars.json") as fh:
			cz = json.load(fh)
		with open("static/mlb/pinnacle.json") as fh:
			pn = json.load(fh)
		with open("static/dailyev/odds.json") as fh:
			data = json.load(fh)

		for book, d in zip(["cz", "pn"], [cz, pn]):
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