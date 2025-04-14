import argparse
import json
import math
import os
import random
import queue
import re
import time
import nodriver as uc
import requests
import subprocess
import threading
import multiprocessing
from pdf2image import convert_from_path
import pytesseract
from PIL import Image

from bs4 import BeautifulSoup as BS
from controllers.shared import *
from datetime import datetime, timedelta

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

q = queue.Queue()
locks = {}
for book in ["fd", "dk", "cz", "espn", "mgm", "kambi", "b365"]:
	locks[book] = threading.Lock()
#lock = threading.Lock()

def devig(evData, player="", ou="575/-900", finalOdds=630, prop="hr", dinger=False, book=""):
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

	if dinger:
		# 70% conversion * 40% (2.1 HR/game = 2.1*$5/$25)
		fairVal = min(x, mult, add)
		x = 0.2856
		# 80% conversion * 42% (2.1 HR/game = 2.1*$5/$25)
		x = .336

		# for DK, 70% * (32 HR/tue = $32 / $20)
		#x = 1.12
		# for DK No Sweat, 70% * $10/ $20 bet
		x = 0.7
		ev = ((100 * (finalOdds / 100 + 1)) * fairVal - 100 + (100 * x))
		ev = round(ev, 1)

	evData.setdefault(player, {})
	if book:
		evData[player][f"{book}_ev"] = ev
		evData[player][f"{book}_fairVal"] = fairVal
		evData[player][f"{book}_implied"] = implied
	else:
		evData[player][f"fairVal"] = fairVal
		evData[player][f"implied"] = implied
		evData[player][f"ev"] = ev

def writeCirca(date):
	if not date:
		date = str(datetime.now())[:10]
	with open("static/mlb/schedule.json") as fh:
		schedule = json.load(fh)

	writeHistorical(date, book="circa")

	games = [x["game"] for x in schedule[date]]
	teamGame = {}
	for game in games:
		a,h = map(str, game.split(" @ "))
		teamGame[a] = game
		teamGame[h] = game

	dt = datetime.now().strftime("%Y-%-m-%-d")
	file = f"MLB Props - {dt}.pdf"
	pages = convert_from_path(f"/mnt/c/Users/zhech/Downloads/MLB Props - {dt}.pdf")
	data = nested_dict()

	for page in pages:
		page.save("out.png", "PNG")
		img = Image.open("out.png")
		bottom = 2200
		top = 400
		#w,h = img.size
		# l,t,r,b
		playersImg = img.crop((0,top,400,bottom))
		text = pytesseract.image_to_string(playersImg).split("\n")

		players = []
		for player in text:
			if "(" not in player:
				continue
			team = convertMLBTeam(player.split(")")[0].split("(")[-1])
			if team == "art":
				team = "ari"
			elif team == "nyn":
				team = "nym"
			elif team == "nil":
				team = "mil"
			game = teamGame.get(team, "")
			player = parsePlayer(player.lower().split(" (")[0])
			players.append((player, game))

		# strikeouts
		#i = img.crop((770,1230,1035,1320))
		#print(pytesseract.image_to_string(i).split("\n"))

		oversImg = img.crop((540,top,600,bottom))
		undersImg = img.crop((685,top,760,bottom))
		oversArr = pytesseract.image_to_string(oversImg).split("\n")
		undersArr = pytesseract.image_to_string(undersImg).split("\n")
		overs = []
		for over in oversArr:
			o = re.search(r"\d{3,4}", over)
			if not o:
				continue
			overs.append(over)
		unders = []
		for under in undersArr:
			o = re.search(r"\d{3,4}", under)
			if not o:
				continue
			unders.append(under)
		
		for p,o,u in zip(players, overs, unders):
			data[p[-1]][p[0]]["circa"] = f"{o}/{u}"

	with open("static/dingers/circa.json", "w") as fh:
		json.dump(data, fh, indent=4)

def mergeCirca():
	with open("static/dingers/circa.json") as fh:
		circa = json.load(fh)
	with open("static/mlb/circa-main.json") as fh:
		circaMain = json.load(fh)


	for game in circa:
		for player in circa[game]:
			circaMain.setdefault(game, {})
			circaMain[game].setdefault("hr", {})
			circaMain[game]["hr"][player] = circa[game][player]["circa"]

	with open("static/mlb/circa.json", "w") as fh:
		json.dump(circaMain, fh, indent=4)

async def getESPNLinks(date):
	browser = await uc.start(no_sandbox=True)
	url = "https://espnbet.com/sport/baseball/organization/united-states/competition/mlb"
	page = await browser.get(url)
	await page.wait_for(selector="article")
	html = await page.get_content()

	games = {}
	soup = BS(html, "html.parser")
	for article in soup.select("article"):
		if not article.find("h3") or " @ " not in article.find("h3").text:
			continue
		if date == str(datetime.now())[:10] and "Today" not in article.text:
			continue
		elif date != str(datetime.now())[:10] and datetime.strftime(datetime.strptime(date, "%Y-%m-%d"), "%b %d") not in article.text:
			continue

		away, home = map(str, article.find("h3").text.split(" @ "))
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
	writeHistorical(str(datetime.now())[:10], book)
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
		try:
			await page.wait_for(selector="div[data-testid='away-team-card']")
		except:
			q.task_done()
			continue
		html = await page.get_content()
		soup = BS(html, "html.parser")

		for detail in soup.find_all("details"):
			if not detail.text.startswith("Player Total Home Runs Hit"):
				continue
			for article in detail.find_all("article"):
				if not article.find("header"):
					continue
				player = parsePlayer(article.find("header").text)
				last = player.split(" ")
				p = player[0][0]+". "+last[-1]
				player = playerMap.get(p, player)

				over = article.find("button").find_all("span")[-1].text
				under = article.find_all("button")[-1].find_all("span")[-1].text
				if "0.5" in over or "0.5" in under:
					continue
				data[game][player][book] = over+"/"+under

		try:
			updateData(book, data)
		except:
			print("espn fail", data)
		q.task_done()
	browser.stop()

async def write365(loop):
	book = "365"

	writeHistorical(str(datetime.now())[:10], book)

	browser = await uc.start(no_sandbox=True)
	url = "https://www.oh.bet365.com/?_h=uvJ7Snn5ImZN352O9l7rPQ%3D%3D&btsffd=1#/AC/B16/C20525425/D43/E160301/F43/N2/"
	page = await browser.get(url)

	await page.wait_for(selector=".srb-MarketSelectionButton-selected")	
	reject = await page.query_selector(".ccm-CookieConsentPopup_Reject")
	if reject:
		await reject.mouse_click()

	if True:
		for c in ["src-FixtureSubGroup_Closed"]:
			divs = await page.query_selector_all("."+c)

			for div in divs:
				await div.scroll_into_view()
				await div.mouse_click()
				#time.sleep(round(random.uniform(0.9, 1.25), 2))
				time.sleep(round(random.uniform(0.4, 0.9), 2))

	while True:
		players = await page.query_selector_all(".gl-Participant_General")
		data = nested_dict()
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
				data[game][player][book] += "/"+odds

		with open("static/dingers/updated_b365", "w") as fh:
			fh.write(str(datetime.now()))
		with open("static/dingers/b365.json", "w") as fh:
			json.dump(data, fh, indent=4)

		if not loop:
			break

	browser.stop()
	
async def writeDK(loop):
	book = "dk"
	browser = await uc.start(no_sandbox=True)
	url = "https://sportsbook.draftkings.com/leagues/baseball/mlb?category=batter-props&subcategory=home-runs"
	page = await browser.get(url)

	try:
		await page.wait_for(selector=".sportsbook-event-accordion__wrapper")
	except:
		print("element not found")
		return


	while True:
		data = nested_dict()
		gameDivs = await page.query_selector_all(".sportsbook-event-accordion__wrapper")
		for gameDiv in gameDivs:
			game = gameDiv.children[0].children[1].text_all
			if " @ " not in game and " at " not in game:
				continue
			away, home = map(str, game.replace(" at ", " @ ").split(" @ "))
			game = f"{convertMLBTeam(away)} @ {convertMLBTeam(home)}"

			odds = await gameDiv.query_selector_all("button[data-testid='sb-selection-picker__selection-0']")
			for oIdx, odd in enumerate(odds):
				player = parsePlayer(odd.parent.parent.parent.parent.parent.children[0].text.split(" (")[0])
				ou = odd.text_all.split(" ")[-1]
				if ou.endswith("+"):
					continue
				data[game][player][book] = ou


		with open("static/dingers/updated_dk", "w") as fh:
			fh.write(str(datetime.now()))
		with open("static/dingers/dk.json", "w") as fh:
			json.dump(data, fh, indent=4)

		if not loop:
			break

		time.sleep(5)
		#time.sleep(60 * 10)

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
		if not parent:
			continue
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
	writeHistorical(date, book)
	while True:
		data = nested_dict()

		(game, url) = q.get()
		if url is None:
			q.task_done()
			break

		page = await browser.get(url)
		try:
			await page.wait_for(selector=".event-details-pills-list")
		except:
			q.task_done()
			continue

		#show = await page.query_selector(".option-group-column:nth-of-type(2) .option-panel .show-more-less-button")
		#if show:
		#	await show.click()
		
		foundPanel = None
		panels = await page.query_selector_all(".option-panel")
		for panel in panels:
			if "Batter home runs" in panel.text_all:
				up = await panel.query_selector("svg[title=theme-up]")
				if not up:
					up = await panel.query_selector(".clickable")
					await up.click()

				show = await panel.query_selector(".show-more-less-button")
				if show and show.text_all == "Show More":
					await show.click()
					await show.scroll_into_view()
					time.sleep(0.75)
				foundPanel = panel
				break

		if not foundPanel:
			q.task_done()
			continue
		else:
			html = await page.get_content()
			soup = BS(html, "html.parser")

		panel = None
		players = []
		odds = []
		for p in soup.select(".option-panel"):
			if "Batter home runs" in p.text:
				players = p.select(".attribute-key")
				odds = p.select("ms-option")
				break

		#players = panel.select(".attribute-key")
		#odds = panel.select("ms-option")

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

		try:
			updateData(book, data)
		except:
			print(data)
			pass
		q.task_done()

	browser.stop()

def updateData(book, data):
	file = f"static/dingers/{book}.json"
	with locks[book]:
		d = {}
		if os.path.exists(file):
			with open(file) as fh:
				d = json.load(fh)
		d.update(data)
		with open(file, "w") as fh:
			json.dump(d, fh, indent=4)

async def writeBR(date):
	url = "https://mi.betrivers.com/?page=sportsbook&group=1000093616&type=playerprops"
	browser = await uc.start(no_sandbox=True)
	page = await browser.get(url)

	res = {}
	await page.wait_for(selector="article")
	articles = await page.query_selector_all("article")

	for article in articles:
		if "live" in article.text_all.lower():
			continue
		await article.scroll_into_view()
		if "Show more" in article.text_all:
			spans = await article.query_selector_all("span")
			for span in spans:
				if span.text == "Show more":
					await span.scroll_into_view()
					await span.parent.mouse_click()
					time.sleep(0.2)
					break

	time.sleep(10)
	html = await page.get_content()
	soup = BS(html, "lxml")

	with open("out.html", "w") as fh:
		fh.write(html)
		
	browser.stop()
	return res

async def getFDLinks(date):
	browser = await uc.start(no_sandbox=True)
	url = "https://mi.sportsbook.fanduel.com/navigation/mlb"
	page = await browser.get(url)
	await page.wait_for(selector="span[role=link]")

	html = await page.get_content()
	soup = BS(html, "lxml")
	links = soup.select("span[role=link]")

	for link in links:
		if link.text == "More wagers":
			t = link.find_previous("a").parent.find("time")
			url = link.find_previous("a").get("href")
			game = " ".join(url.split("/")[-1].split("-")[:-1])
			away, home = map(str, game.split(" @ "))
			game = f"{convertMLBTeam(away)} @ {convertMLBTeam(home)}"
			games[game] = f"https://mi.sportsbook.fanduel.com{url}?tab=batter-props"

	browser.stop()
	return games

def runFD():
	uc.loop().run_until_complete(writeFD())

async def writeFDFromBuilder(date, loop):
	book = "fd"
	with open("static/mlb/schedule.json") as fh:
		schedule = json.load(fh)

	if date not in schedule:
		print("Date not in schedule")
		return

	games = [x["game"] for x in schedule[date]]
	teamMap = {}
	for game in games:
		for t in game.split(" @ "):
			teamMap[t] = game

	url = "https://sportsbook.fanduel.com/navigation/mlb?tab=parlay-builder"
	browser = await uc.start(no_sandbox=True)
	page = await browser.get(url)
	try:
		await page.wait_for(selector="div[role=button][aria-selected=true]")
	except:
		print("tab not found")
		return
	tab = await page.query_selector("div[role=button][aria-selected=true]")
	if tab.text == "Parlay Builder":
		arrow = await page.query_selector("div[data-testid=ArrowAction]")
		await arrow.click()
		await page.wait_for(selector="div[aria-label='Show more']")
		mores = await page.query_selector_all("div[aria-label='Show more']")
		for more in mores:
			await more.click()
		time.sleep(1)
	else:
		print("parlay builder not found")
		return

	while True:
		html = await page.get_content()

		gameStarted = {}
		for gameData in schedule[date]:
			dt = datetime.strptime(gameData["start"], "%I:%M %p")
			dt = int(dt.strftime("%H%M"))
			gameStarted[gameData["game"]] = int(datetime.now().strftime("%H%M")) > dt

		writeHistorical(date, book, gameStarted)
		writeFDFromBuilderHTML(html, teamMap, date, gameStarted)
		if not loop:
			break
		
		time.sleep(5)
		#time.sleep(60 * 10)

	browser.stop()

def writeFDFromBuilderHTML(html, teamMap, date, gameStarted):
	soup = BS(html, "html.parser")
	btns = soup.select("div[role=button]")

	data = nested_dict()
	dingerData = nested_dict()
	currGame = ""
	for btn in btns:
		label = btn.get("aria-label")
		if not label:
			continue
		if not label.startswith("To Hit A Home Run"):
			continue
		player = parsePlayer(label.split(", ")[1])
		odds = label.split(" ")[-1]

		try:
			team = btn.parent.parent.parent.find_all("img")[1]

			if "/team/" not in team.get("src"):
				continue
			team = convertMLBTeam(team.get("src").split("/")[-1].replace(".png", "").replace("_", " "))
			game = teamMap.get(team, currGame)
		except:
			game = currGame

		if "unavailable" in odds:
			continue

		currGame = game
		if gameStarted[game]:
			continue
		dingerData[game][player]["fd"] = odds
		data[game]["hr"][player] = odds
		

	with open("static/dingers/updated_fd", "w") as fh:
		fh.write(str(datetime.now()))
	with open("static/dingers/fd.json", "w") as fh:
		json.dump(dingerData, fh, indent=4)
	with open("static/mlb/fanduel.json") as fh:
		d = json.load(fh)
	merge_dicts(d, data, forceReplace=True)
	with open("static/mlb/fanduel.json", "w") as fh:
		json.dump(d, fh, indent=4)

async def writeFD():
	book = "fd"
	browser = await uc.start(no_sandbox=True)

	while True:
		data = nested_dict()

		(game, url) = q.get()
		if url is None:
			q.task_done()
			break

		page = await browser.get(url)
		await page.wait_for(selector="div[role=button][aria-selected=true]")

		tab = await page.query_selector("div[role=button][aria-selected=true]")
		if tab.text != "Batter Props":
			q.task_done()
			continue

		el = await page.query_selector("div[aria-label='Show more']")
		if el:
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

			data[game][player][book] = labelSplit[-1]

		updateData(book, data)
		q.task_done()

	browser.stop()

async def writeCZ(date, token=None):
	book = "cz"
	outfile = "outDingersCZ"
	if False and not token:
		await writeCZToken()

	with open("token") as fh:
		token = fh.read()

	writeHistorical(date, book)

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

		with open(outfile) as fh:
			data = json.load(fh)

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

	with open("static/dingers/updated_cz", "w") as fh:
		fh.write(str(datetime.now()))
	updateData(book, res)

def writeKambi(date):
	book = "kambi"
	outfile = "outDailyKambi"

	url = "https://eu-offering-api.kambicdn.com/offering/v2018/pivuslarl-lbr/listView/baseball/mlb/all/all/matches.json?lang=en_US&market=US"
	os.system(f"curl -s \"{url}\" -o {outfile}")
	
	with open(outfile) as fh:
		j = json.load(fh)

	data = nested_dict()
	writeHistorical(date, book)

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
		os.system(f"curl -s \"{url}\" -o {outfile}")

		with open(outfile) as fh:
			j = json.load(fh)

		for betOffer in j["betOffers"]:
			label = betOffer["criterion"]["label"].lower()
			#print(label)
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

	updateData(book, data)

def writeFeed(date, yearArg):
	if not date:
		date = str(datetime.now())[:10]
	with open(f"static/mlb/schedule.json") as fh:
		schedule = json.load(fh)

	base = f"https://baseballsavant.mlb.com/gamefeed?date="
	dates = [date]
	
	if yearArg:
		seasonStarts = {
			"2025": [datetime(2025,3,28), datetime.now()],
			"2024": [datetime(2024,3,20), datetime(2024,9,30)],
			"2023": [datetime(2023,3,30), datetime(2023,10,1)],
			"2022": [datetime(2022,4,7), datetime(2022,10,5)],
			"2021": [datetime(2021,4,1), datetime(2021,10,3)],
			"2020": [datetime(2020,7,23), datetime(2020,9,27)],
			"2019": [datetime(2019,3,28), datetime(2019,9,29)],
			"2018": [datetime(2018,3,29), datetime(2018,9,30)],
			"2017": [datetime(2017, 4, 2), datetime(2017, 10, 1)],
			"2016": [datetime(2016, 4, 3), datetime(2016, 10, 2)],
			"2015": [datetime(2015, 4, 5), datetime(2015, 10, 4)],
		}
		seasonStarts = {yearArg: seasonStarts[yearArg]}
		print(seasonStarts.keys())
		dates = []
		for y in seasonStarts:
			start_dt = seasonStarts[y][0]
			d = [(start_dt + timedelta(days=i)).strftime("%Y-%m-%d")
					for i in range((seasonStarts[y][1] - start_dt).days + 1)]
			dates.extend(d)

	driver = webdriver.Firefox()

	for dt in dates:
		date = dt
		sameYear = int(date.split("-")[0]) == datetime.now().year
		driver.get(f"{base}{dt}")
		#time.sleep(0.5)
		try:
			element = WebDriverWait(driver, 10).until(
				EC.presence_of_element_located((By.CSS_SELECTOR, "#allMetrics th"))
			)
		except:
			continue
		time.sleep(1.5)

		soup = BS(driver.page_source, "html.parser")
		allTable = soup.find("div", id="allMetrics")
		hdrs = [th.text.lower() for th in allTable.find_all("th")]
		data = nested_dict()
		starts = {}
		gameIdxs = {}
		liveGames = 0
		if date in schedule:
			for gameIdx, game in enumerate(schedule[date]):
				starts[game["game"]] = game["start"]
				gameIdxs[game["game"]] = gameIdx
				if game["start"] and game["start"] != "LIVE" and game["start"] != "Postponed":
					dt = datetime.strptime(game["start"], "%I:%M %p")
					dt = int(dt.strftime("%H%M"))
					if dt <= int(datetime.now().strftime("%H%M")):
						liveGames += 1

		#print(dt, len(hdrs))
		data["all"] = {k: v.text.strip() for k,v in zip(hdrs,allTable.find_all("td")) if k}
		data["all"]["liveGames"] = liveGames
		#data["all"]["totGames"] = len(soup.find_all("div", class_="game-container"))

		for div in soup.find_all("div", class_="game-container"):
			away = div.find("div", class_="team-left")
			home = div.find("div", class_="team-right")
			away = convertMLBTeam(away.text.strip())
			home = convertMLBTeam(home.text.strip())
			game = f"{away} @ {home}"

			if "POSTPONED" in div.text:
				continue
			data["all"]["totGames"] = data["all"].get("totGames", 0) + 1
			if (date == "2025-03-18" or date == "2025-03-19") and "lad" not in game:
				continue
			if (date == "2024-03-20" or date == "2024-03-21") and "lad" not in game:
				continue

			if game in data:
				game += "-gm2"

			data[game] = []
			table = div.find("div", class_="mini-ev-table")
			if not table or not table.find("tbody"):
				continue
			for tr in table.find("tbody").find_all("tr"):
				tds = tr.find_all("td")
				player = parsePlayer(tds[1].text.strip())
				#print(player)
				#pitcher = parsePlayer(tds[4].text.strip())
				img = tr.find("img").get("src")
				team = convertSavantLogoId(img.split("/")[-1].replace(".svg", ""))
				hrPark = tds[-1].text.strip()

				pa = tds[2].text.strip()
				j = {
					"player": player,
					#"pitcher": pitcher,
					"game": game,
					"gameIdx": gameIdxs.get(game, 0),
					"hr/park": hrPark,
					"pa": pa,
					"dt": "",
					"img": img,
					"team": team,
					"start": starts.get(game, "")
				}
				i = 3
				for hdr in ["in", "result", "evo", "la", "dist"]:
					j[hdr] = tds[i].text.strip()
					i += 1

				data[game].append(j)
		writeFeedSplits(date, data, sameYear)
	
	driver.close()

	if yearArg:
		base = f"static/splits/mlb_feed/{yearArg}"
		os.system(f"zip -r {base}/logs.zip {base}/ -i {base}/{yearArg}-*")
		os.system(f"rm {base}/{yearArg}-*")

def writeFeedSplits(date, data, sameYear):
	year = date.split("-")[0]
	base = f"static/splits/mlb_feed" if sameYear else f"static/splits/mlb_feed/{year}"
	if not os.path.exists(base):
		os.mkdir(base)

	with open(f"{base}/{date}.json", "w") as fh:
		json.dump(data, fh)

	yearData = nested_dict()
	if os.path.exists(f"static/splits/mlb_feed/{year}.json"):
		with open(f"static/splits/mlb_feed/{year}.json") as fh:
			yearData = json.load(fh)

	yearData[date] = data["all"]
	with open(f"static/splits/mlb_feed/{year}.json", "w") as fh:
		json.dump(yearData, fh)

	allFeed = []
	splits = nested_dict()
	for game in data:
		if game == "all":
			continue
		elif date in ["2025-03-18", "2025-03-19"] and "lad" not in game:
			continue #preseason
		for playData in data[game]:
			splits[playData["team"]][playData["player"]][f"{date}-{playData['pa'].zfill(2)}"] = {
				"hr/park": playData["hr/park"],
				"pa": playData["pa"],
				"in": playData["in"],
				"result": playData["result"],
				"evo": playData["evo"],
				"la": playData["la"],
				"dist": playData["dist"],
			}

	for team in splits:
		j = nested_dict()
		try:
			pass
			with open(f"{base}/{team}.json") as fh:
				j.update(json.load(fh))
		except:
			pass

		for player in splits[team]:
			for key in splits[team][player]:
				j[player][key] = splits[team][player][key]
		with open(f"{base}/{team}.json", "w") as fh:
			json.dump(j, fh)

def writeHot():
	CUTOFF = 12
	with open("static/baseballreference/roster.json") as fh:
		roster = json.load(fh)
	trends = []
	for team in roster:
		with open(f"static/splits/mlb_feed/{team}.json") as fh:
			feed = json.load(fh)
		for player in feed:
			bip = []
			evos = []
			for key in sorted(feed[player]):
				if int(feed[player][key]["dist"] or "0") == 0:
					continue
				feed[player][key]["dt"] = "-".join(key.split("-")[:-1])
				bip.append(int(feed[player][key]["dist"]))
				evos.append(float(feed[player][key]["evo"] or "0"))

			if len(bip) < CUTOFF:
				continue

			regression = linearRegression(range(min(CUTOFF, len(bip))), bip[-CUTOFF:])
			evo_regression = linearRegression(range(min(CUTOFF, len(evos))), evos[-CUTOFF:])
			trends.append({
				"team": team, "player": player,
				"slope": regression["slope"],
				"predictedY": regression["predicted_y"],
				"y": bip[-CUTOFF:],
				"evoPredictedY": evo_regression["predicted_y"],
				"evoY": evos[-CUTOFF:],
			})

	trends.sort(key=lambda k: k["slope"], reverse=True)
	with open("static/mlb/trends.json", "w") as fh:
		json.dump(trends, fh)

def fixFeed():
	#for year in range(2015,2026):
	for year in range(2020,2025):
		year = str(year)
		totals = nested_dict()
		for team in os.listdir(f"static/splits/mlb_feed/{year}/"):
			if team == "logs.zip" or "-" in team:
				continue
			with open(f"static/splits/mlb_feed/{year}/{team}") as fh:
				feed = json.load(fh)
			for player in feed:
				for play in feed[player]:
					if feed[player][play]["result"] == "Home Run":
						y,m,d,pa = map(str, play.split("-"))
						dt = f"{y}-{m}-{d}"
						totals[dt].setdefault("hr", 0)
						totals[dt]["hr"] += 1
			
		with open(f"static/splits/mlb_feed/{year}.json") as fh:
			yearData = json.load(fh)

		for dt in yearData:
			allHr = int(yearData[dt]["hr"])
			if allHr != totals.get(dt, {}).get("hr", 0):
				#print(dt, allHr, totals[dt]["hr"])
				yearData[dt]["hr"] = max(allHr, totals.get(dt, {}).get("hr", 0))

		with open(f"static/splits/mlb_feed/{year}.json", "w") as fh:
			json.dump(yearData, fh)


def writeMonths():
	monthData = nested_dict()
	data = nested_dict()
	for year in range(2015,2026):
		year = str(year)
		with open(f"static/splits/mlb_feed/{year}.json") as fh:
			yearData = json.load(fh)
		dts = sorted(yearData)
		for dt in dts:
			if yearData[dt]["totGames"] == 0:
				continue
			y,m,d = map(str, dt.split("-"))
			try:
				hr = int(yearData[dt]["hr"])
			except:
				hr = 0
			hr_g = round(hr / yearData[dt]["totGames"], 2)
			monthData.setdefault(m, {"hr": [], "g": [], "hr/g": [], "dt": []})
			monthData[m]["hr"].append(hr)
			monthData[m]["g"].append(yearData[dt]["totGames"])
			monthData[m]["hr/g"].append(round(hr / yearData[dt]["totGames"], 2))
			monthData[m]["dt"].append(dt)

			if dt == "2025-04-06":
				print(hr)
			data.setdefault(year, {"hr": [], "g": [], "hr/g": [], "dt": []})
			data[year]["hr"].append(hr)
			data[year]["g"].append(yearData[dt]["totGames"])
			data[year]["hr/g"].append(round(hr / yearData[dt]["totGames"], 2))
			data[year]["dt"].append(dt)

	with open("static/splits/mlb_feed/feed_xy.json", "w") as fh:
		json.dump(data, fh)

async def writeBVP(date):
	with open(f"static/baseballreference/bvp.json") as fh:
		bvp = json.load(fh)
	#bvp = nested_dict()

	url = f"https://swishanalytics.com/optimus/mlb/batter-vs-pitcher-stats?date={date}"
	browser = await uc.start(no_sandbox=True)
	page = await browser.get(url)

	await page.wait_for(selector=".batter-name")
	html = await page.get_content()

	#with open("out.html", "w") as fh:
	#	fh.write(html)

	soup = BS(html, "html.parser")
	hdrs = []
	for row in soup.find("tr").find_all("th"):
		hdrs.append(row.text.lower())

	for row in soup.select(".stat-table tr"):
		tds = row.find_all("td")
		team = convertMGMTeam(tds[0].find("img").get("src").split("/")[-1].replace(".png", ""))
		player = parsePlayer(tds[0].find("span").text.strip())
		pitcher = parsePlayer(tds[1].find("span").text.strip())

		j = {}
		for hdr, col in zip(hdrs[2:], tds[2:]):
			try:
				j[hdr] = int(col.text)
			except:
				try:
					j[hdr] = float(col.text)
				except:
					j[hdr] = col.text
		bvp.setdefault(team, {})
		bvp[team][f"{player} v {pitcher}"] = j

	with open("static/baseballreference/bvp.json", "w") as fh:
		json.dump(bvp, fh, indent=4)

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

def writeStatsPage(date):
	if not date:
		date = str(datetime.now())[:10]
	lastYear = str(datetime.now().year - 1)
	with open(f"static/baseballreference/roster.json") as fh:
		roster = json.load(fh)

	with open(f"static/baseballreference/bvp.json") as fh:
		bvpData = json.load(fh)

	with open(f"static/baseballreference/leftOrRight.json") as fh:
		leftOrRight = json.load(fh)

	with open(f"static/mlb/schedule.json") as fh:
		schedule = json.load(fh)

	
	headers = {"Accept": "application/vnd.github.v3.raw"}
	
	url = "https://api.github.com/repos/zhecht/lines/contents/static/mlb/lineups.json"
	response = requests.get(url, headers=headers)
	lineups = response.json()

	url = "https://api.github.com/repos/zhecht/lines/contents/static/mlb/weather.json"
	response = requests.get(url, headers=headers)
	weather = response.json()

	# bbref
	with open(f"static/baseballreference/advanced.json") as fh:
		advanced = json.load(fh)

	with open(f"static/baseballreference/expected.json") as fh:
		expected = json.load(fh)

	with open(f"static/baseballreference/rankings.json") as fh:
		rankings = json.load(fh)

	with open(f"static/baseballreference/parkFactors.json") as fh:
		parkFactors = json.load(fh)

	teamGame = {}
	opps = {}
	for game in schedule[date]:
		a,h = map(str, game["game"].split(" @ "))
		teamGame[a] = game
		teamGame[h] = game
		opps[a] = h
		opps[h] = a

	prop = "hr"
	line = 0.5
	lastAB = 0

	data = []
	sortData = {}
	for team in roster:
		with open(f"static/splits/mlb_feed/{team}.json") as fh:
			feed = json.load(fh)
		with open(f"static/splits/mlb/{team}.json") as fh:
			teamStats = json.load(fh)
		with open(f"static/splits/mlb_historical/{team}.json") as fh:
			teamStatsHist = json.load(fh)

		game = opp = stadiumRank = opp = pitcher = pitcherLR = ""
		oppRank = oppRankClass = ""
		if team not in teamGame:
			#continue
			pass

		start = ""
		gameWeather = {}
		try: # game info
			game = teamGame[team]["game"]
			start = teamGame[team]["start"]
			away,home = map(str, game.split(" @ "))
			opp = opps[team]
			oppRankings = rankings[opp].get(f"opp_{prop}")
			pitcher = lineups[opp]["pitcher"]
			pitcherLR = leftOrRight[opp].get(pitcher, "")
			gameWeather = weather.get(game, {})

			if home in parkFactors:
				stadiumRank = parkFactors[home]["hrRank"]

			if oppRankings:
				oppRank = oppRankings["rankSuffix"]
				oppRankClass = oppRankings["rankClass"]
		except:
			pass

		pitcherSummary = ""
		babip = ""
		if pitcher in advanced:
			p = pitcher
			pitcherSummary = f"{advanced[p]['p_era']} ERA, {advanced[p]['batting_avg']} AVG, {advanced[p]['xba']} xAVG, {babip} BABIP, {advanced[p]['slg_percent']} SLG, {advanced[p]['xslg']} xSLG, {advanced[p]['woba']} WOBA, {advanced[p]['xwoba']} xWOBA, {advanced[p]['barrel_batted_rate']}% Barrel Batted"

		for player in roster[team]:
			try:
				order = lineups[team]["batters"].index(player)+1
			except:
				order = "-"
			bvpStats = bvpData[team].get(player+' v '+pitcher, {})
			bvp = ""
			bvpHR = bvpAvg = 0
			if bvpStats and bvpStats["ab"]:
				#bvp = f"{bvpStats['h']}-{bvpStats['ab']}, {bvpStats['hr']} HR, {bvpStats['rbi']} RBI, {bvpStats['so']} SO"
				bvp = f"{bvpStats['h']}-{bvpStats['ab']}, {bvpStats['hr']} HR"
				bvpHR = bvpStats["hr"]
				if bvpStats["ab"]:
					bvpAvg = bvpStats["h"] / bvpStats["ab"]

			savantData = expected[team].get(player, {})
			feedKeys = sorted(feed.get(player, {}).keys())
			evos = [feed[player][k]["evo"] for k in [k for k in feedKeys]]
			dists = [feed[player][k]["dist"] for k in [k for k in feedKeys]]
			hrParks = [feed[player][k]["hr/park"].split("/")[0] for k in [k for k in feedKeys]]
			results = [feed[player][k]["result"] for k in [k for k in feedKeys]]

			#if player == "shohei ohtani":
			#	print(player, results, evos, dists, hrParks)
			over100 = over300ft = 0
			if len(dists[-lastAB:]):
				over300ft = round(len([x for x in dists[-lastAB:] if x and int(x) >= 300]) * 100 / len(dists[-lastAB:]))
				sortData.setdefault("dist", [])
				sortData["dist"].append((over300ft, player))

				over100 =round( len([x for x in evos[-lastAB:] if x and float(x) >= 100]) * 100 / len(evos[-lastAB:]))
				sortData.setdefault("evo", [])
				sortData["evo"].append((over100, player))

			playerStats = teamStats.get(player, {})
			dtSplits, logs, awayHomeSplits, playerYears = [], [], [], []
			hitRate = hitRateL10 = hitRateLYR = totGames = 0
			if playerStats:
				dtSplits = playerStats["dt"]
				awayHomeSplits = playerStats["awayHome"]
				totGames = len(dtSplits)
				logs = playerStats.get(prop, [])

				if totGames:
					hitRate = round(len([x for x in logs if x > line]) * 100 / totGames)
					hitRateL10 = round(len([x for x in logs[-10:] if x > line]) * 100 / min(totGames, 10))

			playerStatsHist = teamStatsHist.get(player, {})
			playerYears = sorted(list(playerStatsHist.keys()), reverse=True)
			if lastYear in playerStatsHist:
				playerStatsHist = playerStatsHist[lastYear]
			else:
				playerStatsHist = {}
			dtSplitsLYR, logsLYR = [], []
			if playerStatsHist:
				dtSplitsLYR = playerStatsHist["date"]
				totGamesLYR = len(dtSplitsLYR)
				logsLYR = playerStatsHist.get(prop, [])

				if totGamesLYR:
					hitRateLYR = round(len([x for x in logsLYR if x > line]) * 100 / totGamesLYR)

			data.append({
				"player": player, "team": team, "opp": opp,
				"game": game, "start": start,
				"bvp": bvp, "pitcher": pitcher, "pitcherSummary": pitcherSummary,
				"bvpHR": bvpHR, "bvpAvg": bvpAvg,
				"order": order,
				"prop": prop, "line": line, "book": "", "bookOdds": {},
				"ba": savantData.get("ba", "-"), "xba": savantData.get("est_ba", "-"),
				"feed": {
					"evo": [float(x or 0.0) for x in evos],
					"dist": [int(x or 0) for x in dists],
					"hr/park": hrParks,
					"result": results, "keys": feedKeys
				},
				"logs": logs, "dtSplits": dtSplits, "awayHomeSplits": awayHomeSplits,
				"hitRate": hitRate, "hitRateL10": hitRateL10, "hitRateLYR": hitRateLYR,
				"oppRank": oppRank, "oppRankClass": oppRankClass,
				"weather": gameWeather, "stadiumRank": stadiumRank,
				"100-evo": over100, "300-ft": over300ft,
				"playerYears": playerYears
			})

	if False:
		print(sorted(sortData["evo"], reverse=True)[:50])
		print(f"""💥 Leaders in 100+ MPH Hit Balls (L12 AB) 💥

{", ".join([shortName(x[1]) for x in sorted(sortData["evo"], reverse=True)[:50]])}
""")

		print(sorted(sortData["dist"], reverse=True)[:50])
		print(f"""🚀 Leaders in 300ft Hit Balls (L12 AB) 🚀

{", ".join([shortName(x[1]) for x in sorted(sortData["dist"], reverse=True)[:50]])}
""")

	with open(f"static/mlb/stats.json", "w") as fh:
		json.dump(data, fh)

def writeEV(date, dinger, silent=False):
	if not date:
		date = str(datetime.now())[:10]

	data = {}
	updated = {}
	for book in ["fd", "espn", "dk", "cz", "b365", "mgm", "pn", "circa"]:
		path = f"static/dingers/{book}.json"
		if os.path.exists(path):
			with open(path) as fh:
				d = json.load(fh)
			merge_dicts(data, d)

		upd = f"static/dingers/updated_{book}"
		if os.path.exists(upd):
			with open(upd) as fh:
				j = fh.read()
			updated[book] = j
		else:
			updated[book] = ""

	with open("updated.json") as fh:
		u = json.load(fh)
	u["dingers"] = updated
	with open("updated.json", "w") as fh:
		json.dump(u, fh, indent=4)

	with open(f"static/dailyev/odds.json", "w") as fh:
		json.dump(data, fh, indent=4)

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

	with open(f"static/mlb/schedule.json") as fh:
		schedule = json.load(fh)

	gameTimes = {}
	gameStarted = {}
	for gameData in schedule[date]:
		if gameData["start"] == "LIVE":
			gameStarted[gameData["game"]] = True
		else:
			dt = datetime.strptime(gameData["start"], "%I:%M %p")
			dt = int(dt.strftime("%H%M"))
			gameTimes[gameData["game"]] = dt
			gameStarted[gameData["game"]] = int(datetime.now().strftime("%H%M")) > dt

	evData = {}

	for game in data:
		if not game:
			continue
		away, home = map(str, game.split(" @ "))
		if game not in gameTimes:
			continue
		gameStart = gameTimes[game]
		gameWeather = weather.get(game, {})
		awayStats = {}
		homeStats = {}

		if date == str(datetime.now())[:10] and gameStarted[game]:
			continue
			pass

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
				order = lineups[team]["batters"].index(player)+1
			except:
				order = "-"

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
				if "/" in odds and book not in ["kambi", "espn"]:
				#if "/" in odds and book not in ["kambi", "pn"]:
				#if "/" in odds:
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
			if "dk" in books:
				#if evBook == "dk" and player in evData:
				#	evData[player]["dk_ev"] = evData[player]["ev"]
				#else:
				devig(evData, player, ou, int(data[game][player]["dk"]), book="dk-sweat", dinger=True)
				devig(evData, player, ou, int(data[game][player]["dk"]), book="dk")
				pass
			if "espn" in books:
				devig(evData, player, ou, int(data[game][player]["espn"].split("/")[0]), book="espn")

			if "mgm" in books:
				devig(evData, player, ou, int(data[game][player]["mgm"].split("/")[0]), book="mgm")
				o = int(data[game][player]["mgm"].split("/")[0])
				o = convertAmericanOdds(1 + (convertDecOdds(o) - 1) * 1.20)
				devig(evData, player, ou, o, book="mgm-20")

				if "circa" in books:
					devig(evData, player, data[game][player]["circa"], o, book="mgm-20-vs-circa")
			if "fd" in books:
				devig(evData, player, ou, int(data[game][player]["fd"]), book="fd")
				fd = int(data[game][player]["fd"])
				fd = convertAmericanOdds(1 + (convertDecOdds(fd) - 1) * 1.50)
				devig(evData, player, ou, fd, book="fd-50")
			if "circa" in books:
				devig(evData, player, data[game][player]["circa"], highest, book="vs-circa")
			if "365" in books:
				devig(evData, player, data[game][player]["365"], highest, book="vs-365")

			if player not in evData:
				continue
			elif evData[player]["ev"] > 0 and not silent:
				print(f"{player} {evBook} +{highest}, FV={evData[player]['fairVal']}")

			try:
				j = ph[team][player]["2024"]
				pinchHit = f"{j['ph']} PH / {j['g']} G"
			except:
				pinchHit = ""
			
			evData[player]["player"] = player
			evData[player]["pitcher"] = "" if not pitcher else f"{pitcher} ({pitcherLR})"
			evData[player]["game"] = game
			evData[player]["team"] = team
			evData[player]["weather"] = gameWeather
			evData[player]["book"] = evBook
			evData[player]["line"] = highest
			evData[player]["ou"] = ou
			evData[player]["prop"] = "hr"
			evData[player]["bvp"] = bvp
			evData[player]["lastHR"] = lastHR
			evData[player]["ph"] = pinchHit
			evData[player]["order"] = order
			evData[player]["start"] = gameStart
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
		game = tds[1].text.lower().strip().replace("\u00a0", " ").replace("  ", " ").replace("az", "ari").replace("cws", "chw")
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
			try:
				leftRight = "L" if table.find_all("span", class_="starting-lineups__pitcher-pitch-hand")[idx].text == "LHP" else "R"
			except:
				leftRight = ""
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

async def writeOne(book):
	#with open(f"static/dailyev/odds.json") as fh:
	#	data = json.load(fh)
	data = nested_dict()

	browser = await uc.start(no_sandbox=True)
	if book == "fd":
		await writeFD(data, browser)
	elif book == "dk":
		await writeDK(data, browser)
	elif book == "mgm":
		await writeMGM(data, browser)
	elif book == "espn":
		await writeESPN(data, browser)
	elif book == "kambi":
		writeKambi(data)

	browser.stop()

	if True:
		with locks[book]:
			old = {}
			if os.path.exists(f"static/dingers/{book}.json"):
				with open(f"static/dingers/{book}.json") as fh:
					old = json.load(fh)
			old.update(data)
			with open(f"static/dingers/{book}.json", "w") as fh:
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
		elif book == "fd":
			thread = threading.Thread(target=runFD, args=())
		thread.start()
		threads.append(thread)

	for game in games:
		url = games[game]
		q.put((game,url))

	q.join()

	with open(f"static/dingers/updated_{book}", "w") as fh:
		fh.write(str(datetime.now()))

	for _ in range(totThreads):
		q.put((None,None))
	for thread in threads:
		thread.join()

def writeOdds():
	with open(f"static/mlb/bet365.json") as fh:
		bet365Lines = json.load(fh)

	with open(f"static/mlb/kambi.json") as fh:
		kambiLines = json.load(fh)

	with open(f"static/mlb/pinnacle.json") as fh:
		pnLines = json.load(fh)

	with open(f"static/mlb/mgm.json") as fh:
		mgmLines = json.load(fh)

	with open(f"static/mlb/fanduel.json") as fh:
		fdLines = json.load(fh)

	with open(f"static/mlb/draftkings.json") as fh:
		dkLines = json.load(fh)

	with open(f"static/mlb/caesars.json") as fh:
		czLines = json.load(fh)

	with open(f"static/mlb/espn.json") as fh:
		espnLines = json.load(fh)

	lines = {
		"pn": pnLines,
		"kambi": kambiLines,
		"mgm": mgmLines,
		"fd": fdLines,
		"dk": dkLines,
		"cz": czLines,
		"espn": espnLines,
		"365": bet365Lines
	}

	data = nested_dict()
	for book in lines:
		d = lines[book]
		for game in d:
			if "hr" in d[game]:
				for player in d[game]["hr"]:
					if book in ["fd", "cz", "kambi"]:
						data[game][player][book] = d[game]["hr"][player]
					elif "0.5" in d[game]["hr"][player]:
						data[game][player][book] = d[game]["hr"][player]["0.5"]

	with open("static/dailyev/odds.json", "w") as fh:
		json.dump(data, fh, indent=4)

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("--sport")
	parser.add_argument("--token")
	parser.add_argument("--commit", action="store_true")
	parser.add_argument("--tmrw", action="store_true")
	parser.add_argument("--yest", action="store_true")
	parser.add_argument("--date", "-d")
	parser.add_argument("--year")
	parser.add_argument("--print", "-p", action="store_true")
	parser.add_argument("--update", "-u", action="store_true")
	parser.add_argument("--bvp", action="store_true")
	parser.add_argument("--bet365", action="store_true")
	parser.add_argument("--espn", action="store_true")
	parser.add_argument("--cz", action="store_true")
	parser.add_argument("--dk", action="store_true")
	parser.add_argument("--br", action="store_true")
	parser.add_argument("--fd", action="store_true")
	parser.add_argument("--mgm", action="store_true")
	parser.add_argument("--kambi", action="store_true")
	parser.add_argument("--feed", action="store_true")
	parser.add_argument("--keep", action="store_true")
	parser.add_argument("--ev", action="store_true")
	parser.add_argument("--loop", action="store_true")
	parser.add_argument("--lineups", action="store_true")
	parser.add_argument("--weather", action="store_true")
	parser.add_argument("--dinger", action="store_true")
	parser.add_argument("--threads", type=int, default=5)
	parser.add_argument("--scrape", action="store_true")
	parser.add_argument("--clear", action="store_true")
	parser.add_argument("--stats", action="store_true")
	parser.add_argument("--circa", action="store_true")
	parser.add_argument("--months", action="store_true")
	parser.add_argument("--merge-circa", action="store_true")
	parser.add_argument("--fix-feed", action="store_true")
	parser.add_argument("--hot", action="store_true")

	args = parser.parse_args()

	if args.clear:
		for book in ["fd", "espn", "dk", "cz", "b365", "mgm", "pn", "circa"]:
			path = f"static/dingers/{book}.json"
			with open(path, "w") as fh:
				json.dump({}, fh)
		with open("static/dailyev/odds.json", "w") as fh:
			json.dump({}, fh)

	games = {}
	date = args.date
	if args.tmrw:
		date = str(datetime.now() + timedelta(days=1))[:10]
	elif args.yest:
		date = str(datetime.now() - timedelta(days=1))[:10]
	elif not date:
		date = str(datetime.now())[:10]

	if args.bvp:
		uc.loop().run_until_complete(writeBVP(date))

	if args.feed:
		writeFeed(date, args.year)
	elif args.fix_feed:
		fixFeed()
	elif args.months:
		writeMonths()
	elif args.hot:
		writeHot()
	elif args.fd:
		#games = uc.loop().run_until_complete(getFDLinks(date))
		#games["mil @ nyy"] = "https://mi.sportsbook.fanduel.com/baseball/mlb/milwaukee-brewers-@-new-york-yankees-34146634?tab=batter-props"
		#runThreads("fd", games, min(args.threads, len(games)))
		uc.loop().run_until_complete(writeFDFromBuilder(date, args.loop))
	elif args.mgm:
		games = uc.loop().run_until_complete(getMGMLinks(date))
		#games['det @ lad'] = 'https://sports.mi.betmgm.com/en/sports/events/detroit-tigers-at-los-angeles-dodgers-17081448'
		runThreads("mgm", games, min(args.threads, len(games)))
	elif args.dk:
		uc.loop().run_until_complete(writeDK(args.loop))
	elif args.br:
		uc.loop().run_until_complete(writeBR(date))
	elif args.bet365:
		uc.loop().run_until_complete(write365(args.loop))
	elif args.espn:
		games = uc.loop().run_until_complete(getESPNLinks(date))
		#games['mil @ nyy'] = 'https://espnbet.com/sport/baseball/organization/united-states/competition/mlb/event/b353fbf4-02ef-409b-8327-58fb3b0b1fa9/section/player_props'
		runThreads("espn", games, min(args.threads, len(games)))
	
	if args.cz:
		uc.loop().run_until_complete(writeCZ(date, args.token))
	if args.kambi:
		writeKambi(date)
	if args.circa:
		writeCirca(date)
	if args.merge_circa:
		mergeCirca()

	if args.weather:
		uc.loop().run_until_complete(writeWeather(date))

	if args.lineups:
		writeLineups(date)

	if args.update:
		date = args.date
		if not date:
			date = str(datetime.now())[:10]

		while True:
			writeEV(date, args.dinger)
			printEV()
			#for book in ["weather", "lineups", "cz", "dk", "bet365", "fd", "espn", "mgm"]:
			for book in ["weather", "lineups", "cz", "bet365", "espn", "mgm"]:
			#for book in ["espn", "mgm"]:
				subprocess.Popen(["python", "dingers.py", f"--{book}", "-d", date])
			subprocess.Popen(["python", "controllers/mlb.py", f"--pn", "-d", date])

			if not args.loop:
				break

			# every 10m
			time.sleep(60 * 5)
			print(datetime.now())
			writeEV(date, args.dinger)
			printEV()
			if args.commit:
				commitChanges()

		"""
		uc.loop().run_until_complete(writeWeather(date))
		writeLineups(args.date)
		uc.loop().run_until_complete(writeCZ(date, args.token))
		print("kambi")
		writeKambi(date)
		print("dk")
		uc.loop().run_until_complete(writeOne("dk"))
		print("365")
		uc.loop().run_until_complete(writeOne("365"))
		"""

	if args.commit and args.loop:
		while True:
			if args.ev:
				writeEV(date, args.dinger, silent=True)
			if args.print:
				printEV()
			commitChanges()

			time.sleep(5)
			#time.sleep(60 * 10)

	if args.ev:
		writeEV(date, args.dinger)
	if args.print:
		printEV()

	if args.stats:
		writeStatsPage(date)

	if args.scrape:
		writeOdds()

	if args.commit:
		commitChanges()

	if False:
		data = []
		plays = [("aaron judge", 230), ("eugenio suarez", 470), ("shohei ohtani", 285), ("francisco lindor", 440), ("brandon nimmo", 630), ("mark vientos", 450), ("juan soto", 350), ("pete alonso", 350), ("byron buxton", 470), ("corbin carroll", 540)]
		with open("static/dailyev/ev.json") as fh:
			ev = json.load(fh)
		for player, odds in plays:
			evData = {}
			if player in ev:
				devig(evData, player, ev[player]["ou"], odds)
				betEV = evData[player]["ev"]
				if "circa" in ev[player]["bookOdds"]:
					evData = {}
					devig(evData, player, ev[player]["bookOdds"]["circa"], odds)
					circaEV = evData[player]["ev"]
			else:
				betEV = circaEV = ""
			data.append({
				"book": "fd",
				"sport": "mlb",
				"player": player,
				"prop": "hr",
				"odds": odds,
				"ev": ev.get(player, {}),
				"betEV": betEV,
				"circaEV": circaEV,
			})

		with open("plays.json", "w") as fh:
			json.dump(data, fh, indent=4)