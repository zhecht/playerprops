
import time
import json
import random
import unicodedata
import nodriver as uc
import argparse

def convert365Team(team):
	team = team.lower()
	t = team.split(" ")[0]
	if t == "arz":
		return "ari"
	elif t == "ny":
		if "giants" in team:
			return "nyg"
		return "nyj"
	elif t == "la":
		if "rams" in team:
			return "lar"
		return "lac"
	elif t == "wsh":
		return "was"
	return t

def convert365NHLTeam(team):
	team = team.lower()
	t = team.split(" ")[0]
	if t == "ny":
		if "rangers" in team:
			return "nyr"
		elif "island" in team:
			return "nyi"
		return "nj"
	elif t == "uta":
		return "utah"
	elif t == "mon":
		return "mtl"
	elif t == "cal":
		return "cgy"
	elif t == "vgs":
		return "vgk"
	elif t == "win":
		return "wpg"
	elif t == "clb":
		return "cbj"
	elif t == "nas":
		return "nsh"
	return t

def convertMGMNHLTeam(team):
	team = team.lower()
	if team == "blues":
		return "stl"
	elif team == "kraken":
		return "sea"
	elif team == "bruins":
		return "bos"
	elif team == "panthers":
		return "fla"
	elif team == "blackhawks":
		return "chi"
	elif team == "utah hockey club":
		return "utah"
	elif team == "canadiens":
		return "mtl"
	elif team == "maple leafs":
		return "tor"
	elif team == "rangers":
		return "nyr"
	elif team == "penguins":
		return "pit"
	elif team == "jets":
		return "wpg"
	elif team == "oilers":
		return "edm"
	elif team == "flames":
		return "cgy"
	elif team == "canucks":
		return "van"
	elif team == "avalanche":
		return "col"
	elif team == "golden knights":
		return "vgk"
	elif team == "devils":
		return "nj"
	elif team == "kings":
		return "la"
	elif team == "sabres":
		return "buf"
	elif team == "red wings":
		return "det"
	elif team == "islanders":
		return "nyi"
	elif team == "senators":
		return "ott"
	elif team == "stars":
		return "dal"
	elif team == "wild":
		return "min"
	elif team == "sharks":
		return "sj"
	elif team == "lightning":
		return "tb"
	elif team == "hurricanes":
		return "car"
	elif team == "flyers":
		return "phi"
	return team

def convertMGMTeam(team):
	team = team.lower()[:3]
	if team == "buc":
		return "tb"
	elif team == "fal":
		return "atl"
	elif team == "jet":
		return "nyj"
	elif team == "vik":
		return "min"
	elif team == "pan":
		return "car"
	elif team == "bea":
		return "chi"
	elif team == "rav":
		return "bal"
	elif team == "ben":
		return "cin"
	elif team == "dol":
		return "mia"
	elif team == "pat":
		return "ne"
	elif team == "bro":
		return "cle"
	elif team == "com":
		return "was"
	elif team == "col":
		return "ind"
	elif team == "jag":
		return "jax"
	elif team == "bil":
		return "buf"
	elif team == "tex":
		return "hou"
	elif team == "rai":
		return "lv"
	elif team == "bro":
		return "den"
	elif team == "car":
		return "ari"
	elif team == "49e":
		return "sf"
	elif team == "pac":
		return "gb"
	elif team == "ram":
		return "lar"
	elif team == "gia":
		return "nyg"
	elif team == "sea":
		return "sea"
	elif team == "cow":
		return "dal"
	elif team == "ste":
		return "pit"
	elif team == "sai":
		return "no"
	elif team == "chi":
		return "kc"
	elif team == "tit":
		return "ten"
	elif team == "lio":
		return "det"
	elif team == "cha":
		return "lac"
	elif team == "eag":
		return "phi"

def convertTeam(team):
	team = team.lower()
	t = team[:3]
	if t == "kan":
		return "kc"
	elif t == "los":
		if "chargers" in team:
			return "lac"
		return "lar"
	elif t == "gre":
		return "gb"
	elif t == "san":
		return "sf"
	elif t == "tam":
		return "tb"
	elif t == "las":
		return "lv"
	elif t == "jac":
		return "jax"
	elif t == "new":
		if "giants" in team:
			return "nyg"
		elif "jets" in team:
			return "nyj"
		elif "saints" in team:
			return "no"
		return "ne"
	return t

def convertNHLTeam(team):
	team = team.lower()
	t = team[:3]
	if t == "was":
		return "wsh"
	elif t == "cal":
		return "cgy"
	elif t == "col" and "columbus" in team:
		return "cbj"
	elif t == "flo":
		return "fla"
	elif t == "los":
		return "la"
	elif t == "nas":
		return "nsh"
	elif t == "mon":
		return "mtl"
	elif t == "new":
		if "rangers" in team:
			return "nyr"
		elif "island" in team:
			return "nyi"
		return "nj"
	elif t == "san":
		return "sj"
	elif t == "tam":
		return "tb"
	elif t == "st.":
		return "stl"
	elif t == "veg":
		return "vgk"
	elif t == "win":
		return "wpg"
	elif t == "uta":
		return "utah"
	return t

def strip_accents(text):
	try:
		text = unicode(text, 'utf-8')
	except NameError: # unicode is a default on python 3
		pass

	text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode("utf-8")

	return str(text)

def parsePlayer(player):
	player = strip_accents(player).lower().replace(".", "").replace("'", "").replace("-", " ").replace(" jr", "").replace(" sr", "").replace(" iv", "").replace(" iii", "").replace(" ii", "")
	return player

data = {}
props = {}
async def write365(sport=None):
	if not sport:
		sport == "nfl"
	# start with multi
	url = "https://www.oh.bet365.com/?_h=CfVWPHD5idsD_8dFdjBYcw%3D%3D&btsffd=1#/AC/B12/C20426855/D47/E120593/F47/N7/"
	if sport == "nhl":
		url = "https://www.oh.bet365.com/?_h=p2hqPA35Yw8_tTyHi3apXA%3D%3D&btsffd=1#/AC/B17/C20836572/D43/E170563/F43/N6/"

	browser = await uc.start(no_sandbox=True)
	page = await browser.get(url)

	await page.wait_for(selector=".srb-MarketSelectionButton-selected")

	reject = await page.query_selector(".ccm-CookieConsentPopup_Reject")
	await reject.mouse_click()

	btns = await page.query_selector_all(".srb-MarketSelectionButton")
	for btnIdx in range(0, len(btns)):
		btn = btns[btnIdx]
		await page.wait_for(selector=".srb-MarketSelectionButton-selected")
		if btnIdx != 0:
			await btn.scroll_into_view()
			await btn.mouse_click()
		#print(btn.text_all)
		await page.wait_for(selector=".srb-MarketSelectionButton-selected")
		btns = await page.query_selector_all(".srb-MarketSelectionButton")
		prop = await page.query_selector(".srb-MarketSelectionButton-selected")
		prop = prop.text.lower()
		
		if prop in props:
			continue
		props[prop] = True

		alt = False
		if "touchdown scorers" in prop:
			if "multi" in prop:
				prop = "2+td"
			else:
				prop = "attd"
		elif "goalscorers" in prop:
			if "multi" in prop:
				continue
			prop = "atgs"
		else:
			if "milestones" in prop:
				alt = True
			if "power play" in prop:
				continue
			prop = prop.replace("player ", "").replace("to record a ", "").replace(" and ", "+").replace(" milestones", "").replace("passing", "pass").replace("rushing", "rush").replace("receiving", "rec").replace("receptions", "rec").replace("reception", "rec").replace("points", "pts").replace("assists", "ast").replace("interceptions", "int").replace("completions", "cmp").replace("attempts", "att").replace("shots on goal", "sog").replace("blocked shots", "bs").replace("yards", "yd").replace("touchdowns", "td").replace(" + ", "+").replace(" ", "_")
			if prop == "longest_pass_completion":
				prop = "longest_pass"
			elif prop == "longest_rush_attempt":
				prop = "longest_rush"
			elif prop == "rush+rec_yd":
				prop = "rush+rec"
			elif prop == "sack":
				prop = "sacks"

		if True:
			for c in ["src-FixtureSubGroupWithShowMore_Closed", "src-FixtureSubGroup_Closed", "src-HScrollFixtureSubGroupWithBottomBorder_Closed"]:
				divs = await page.query_selector_all("."+c)

				for div in divs:
					await div.scroll_into_view()
					await div.mouse_click()
					time.sleep(round(random.uniform(0.9, 1.25), 2))

			links = await page.query_selector_all(".msl-ShowMore_Link")

			for el in links:
				await el.scroll_into_view()
				await el.mouse_click()
				time.sleep(round(random.uniform(0.9, 1.25), 2))
		
		divs = await page.query_selector_all(".gl-MarketGroupPod")
		for div in divs:
			game = await div.query_selector(".src-FixtureSubGroupButton_Text")
			try:
				away, home = map(str, game.text.split(" @ "))
			except:
				continue
			if sport == "nhl":
				away = convert365NHLTeam(away)
				home = convert365NHLTeam(home)
			else:
				away = convert365Team(away)
				home = convert365Team(home)

			game = f"{away} @ {home}"
			if game not in data:
				data[game] = {}

			players = await div.query_selector_all(".srb-ParticipantLabelWithTeam_Name")
			cols = await div.query_selector_all(".gl-Market_General")

			if alt:
				for col in cols[1:]:
					line = await col.query_selector("div")
					line = str(float(line.text) - 0.5)
					odds = await col.query_selector_all(".gl-Participant_General")
					for player, odds in zip(players, odds):
						player = parsePlayer(player.text)
						odds = odds.text
						if not odds:
							continue
						if prop not in data[game]:
							data[game][prop] = {}
						if player not in data[game][prop]:
							data[game][prop][player] = {}
						if line in data[game][prop][player]:
							continue
						data[game][prop][player][line] = odds
				continue

			odds1 = await cols[1].query_selector_all(".gl-Participant_General")
			if len(cols) > 2:
				odds2 = await cols[2].query_selector_all(".gl-Participant_General")
			else:
				odds2 = []
			odds3 = await cols[-1].query_selector_all(".gl-Participant_General")

			for idx, p in enumerate(players):
				p = parsePlayer(p.text)
				try:
					o1 = await odds1[idx].query_selector_all("span")
					o1 = o1[-1].text
					o2 = ""
					if odds2:
						o2 = await odds2[idx].query_selector_all("span")
					o3 = await odds3[idx].query_selector_all("span")
				except:
					continue
				try:
					o2 = o2[-1].text
				except:
					o2 = ""
				try:
					o3 = o3[-1].text
				except:
					o3 = ""

				if prop not in data[game]:
					data[game][prop] = {}
					if prop == "2+td":
						data[game]["3+td"] = {}
					elif prop == "attd":
						data[game]["ftd"] = {}
						data[game]["ltd"] = {}
					elif prop == "atgs":
						data[game]["fgs"] = {}

				if prop == "2+td":
					data[game][prop][p] = o1
					if o3:
						data[game]["3+td"][p] = o3
				elif prop == "attd":
					if o2:
						data[game][prop][p] = o2
					data[game]["ftd"][p] = o1
					if o3:
						data[game]["ltd"][p] = o3
				elif prop == "atgs":
					if o2:
						data[game][prop][p] = o2
					data[game]["fgs"][p] = o1
				else:
					if p not in data[game][prop]:
						data[game][prop][p] = {}
					if prop == "sacks":
						line = "0.5"
					else:
						line = await odds1[idx].query_selector_all("span")
						line = line[-2].text
					data[game][prop][p][line] = f"{o1}/{o2}"

	with open(f"static/{sport}/bet365.json", "w") as fh:
		json.dump(data, fh, indent=4)

	#time.sleep(50)
	browser.stop()

async def writeESPN(sport=None):
	if not sport:
		sport = "nfl"

	url = "https://espnbet.com/sport/football/organization/united-states/competition/nfl"
	if sport == "ncaaf":
		url = "https://espnbet.com/sport/football/organization/united-states/competition/ncaaf"
	elif sport == "nhl":
		url = "https://espnbet.com/sport/hockey/organization/united-states/competition/nhl"
	data = {}

	if False:
		with open("static/nfl/espn.json") as fh:
			data = json.load(fh)

	browser = await uc.start(no_sandbox=True)
	page = await browser.get(url)

	#document.querySelectorAll("section")[0].querySelectorAll("article")
	await page.wait_for(selector="article")
	section = await page.query_selector("section")
	articles = await section.query_selector_all("article")

	for articleIdx in range(len(articles)):
		article = articles[articleIdx]
		if "LIVE" in article.text_all:
			continue
		if "Today" not in article.text_all:
			break
			pass
		teams = await article.query_selector_all(".text-primary")
		if sport == "nfl":
			away = convert365Team(teams[0].text)
			home = convert365Team(teams[-1].text)
		elif sport == "nhl":
			away = convert365NHLTeam(teams[0].text)
			home = convert365NHLTeam(teams[-1].text)
		else:
			away = teams[0].text.lower()
			if away.startswith("("):
				away = away.split(") ")[-1]
			home = teams[-1].text.lower()
			if home.startswith("("):
				home = home.split(") ")[-1]
		game = f"{away} @ {home}"

		if game in data:
			continue

		data[game] = {}
		print(game)

		btn = await article.query_selector("button")
		await btn.click()
		await page.wait_for(selector="div[data-testid='away-team-card']")

		tabs = await page.query_selector_all("button[data-testid=tablist-carousel-tab]")

		for tabIdx in range(len(tabs)):
			#if tabs[tabIdx].text_all.lower() not in ["lines", "player props", "td scorers"]:
			if tabs[tabIdx].text_all.lower() not in ["player props", "td scorers"]:
				continue
			await tabs[tabIdx].click()
			time.sleep(1.5)
			await page.wait_for(selector="button[data-testid=tablist-carousel-tab][aria-selected=true]")

			details = await page.query_selector_all("details")
			players = {}
			for detailIdx in range(len(details)):
				detail = details[detailIdx]
				prop = await detail.query_selector("h2")
				try:
					prop = prop.text.lower()
				except:
					print(game, "skip")
					continue

				skip = 2
				player = ""

				if prop == "moneyline":
					prop = "ml"
				elif prop == "match spread":
					prop = "spread"
				elif prop == "total points":
					prop = "total"
				elif prop == "to score a touchdown":
					prop = "attd"
					skip = 3
				elif "first goalscorer" in prop:
					prop = "fgs"
					skip = 1
				elif prop == "player total goals":
					prop = "atgs"
					skip = 3
				elif prop == "player total shots on goal":
					prop = "sog"
				elif prop == "player saves":
					prop = "saves"
				elif prop == "player points":
					prop = "pts"
				elif prop == "player total assists":
					prop = "ast"
					skip = 3
				elif prop == "player total blocked shots":
					prop = "bs"
					skip = 3
				elif "first touchdown scorer" in prop:
					if "power hour" in prop:
						continue
					if prop != "first touchdown scorer":
						prop = "team_ftd"
					else:
						prop = "ftd"
					skip = 1
					if sport == "ncaaf":
						skip = 3
				elif prop.startswith("1st half touchdown scorer"):
					player = parsePlayer(prop.split("(")[1].split(")")[0])
					last = player.split(" ")
					player = player.split(" ")[0][0]+" "+last[-1]
					prop = "1h_attd"
					skip = 1
					if sport == "ncaaf":
						skip = 3
				elif "(" in prop and "(o/u)" not in prop:
					if "1st half" in prop or "1st quarter" in prop:
						continue
					player = parsePlayer(prop.split("(")[1].split(")")[0])
					last = player.split(" ")
					player = player.split(" ")[0][0]+" "+last[-1]
					prop = prop.split(" (")[0].replace(" + ", "+").replace("passing", "pass").replace("rushing", "rush").replace("receptions", "rec").replace("reception", "rec").replace("receiving", "rec").replace("attempts", "att").replace("interceptions thrown", "int").replace("completions", "cmp").replace("completion", "cmp").replace("completed passes", "pass_cmp").replace("yards", "yd").replace("touchdown scorer", "attd").replace("touchdowns", "td").replace("tds", "td").replace(" ", "_")
					if "+" in prop:
						prop = prop.split("_")[0]
					elif prop == "longest_pass_cmp":
						prop = "longest_pass"
					skip = 1
					if prop == "int":
						skip = 3
				elif sport != "nhl" and prop.startswith("player"):
					if prop == "player total sacks":
						continue
					prop = prop.replace("player total ", "").replace("player ", "").replace(" + ", "+").replace(" (o/u)", "").replace("points", "pts").replace("field goals made", "fgm").replace("extra pts made", "xp").replace("passing", "pass").replace("rushing", "rush").replace("receptions", "rec").replace("reception", "rec").replace("receiving", "rec").replace("attempts", "att").replace("interceptions thrown", "int").replace("interceptions", "int").replace("completions", "cmp").replace("completion", "cmp").replace("yards", "yd").replace("touchdowns", "td").replace("tds", "td").replace("assists", "ast").replace("defensive", "def").replace(" ", "_")
					if prop == "def_tackles+ast":
						prop = "tackles+ast"
					elif "+" in prop:
						prop = prop.split("_")[0]
					elif prop == "longest_pass_cmp":
						prop = "longest_pass"
					elif prop == "def_int":
						skip = 1
				else:
					continue

				if prop in ["1h_attd", "2h_attd"]:
					continue

				if "open" not in detail.attributes:
					summary = await detail.query_selector("summary")
					await summary.click()
					#await detail.wait_for(selector="button")

				if prop not in data[game]:
					data[game][prop] = {}

				sections = [detail]
				if prop == "tackles+ast" or prop == "int":
					sections = await detail.query_selector_all("div[aria-label='']")

				player = ""
				for section in sections:
					btns = await section.query_selector_all("button")
					if prop == "tackles+ast" or prop == "int":
						player = await section.query_selector("header")
						player = parsePlayer(player.text)
					for btnIdx in range(0, len(btns), skip):
						if btns[btnIdx].text == "See All Lines":
							continue
						if prop != "int" and "disabled" in btns[btnIdx].attributes and skip != 3:
							continue
						ou = ""
						if prop != "int":
							i = btnIdx
							if sport in ["ncaaf", "nhl"] and skip == 3:
								i += 1
							over = await btns[i].query_selector_all("span")
							ou = over[1].text
							if skip != 1:
								try:
									under = await btns[i+1].query_selector_all("span")
									ou += "/"+under[1].text
								except:
									continue

						ou = ou.replace("Even", "+100")
						if prop == "ml":
							data[game][prop] = ou
						elif prop in ["atgs", "fgs", "ast"]:
							player = btns[btnIdx].text.split(" Total")[0]
							player = parsePlayer(player)
							if prop == "atgs":
								last = player.split(" ")
								p = player.split(" ")[0][0]+" "+last[-1]
								players[p] = player
							data[game][prop][player] = ou
						elif prop in ["bs"]:
							player = btns[btnIdx].text.split(" Total")[0]
							line = await btns[btnIdx+1].query_selector("span")
							line = line.text.split(" ")[1]
							player = parsePlayer(player)
							if player not in data[game][prop]:
								data[game][prop][player] = {}
							data[game][prop][player][line] = ou
						elif "ftd" in prop or (prop == "attd" and skip == 3):
							if skip == 3:
								player = btns[btnIdx].text.split(" To Score")[0].split(" First")[0]
								player = parsePlayer(player)
							else:
								player = await btns[btnIdx].query_selector("span")
								player = parsePlayer(player.text)
							last = player.split(" ")
							player = player.split(" ")[0][0]+" "+last[-1]
							data[game][prop][player] = ou
						elif prop == "def_int":
							player = await btns[btnIdx].query_selector("span")
							player = parsePlayer(player.text)
							last = player.split(" ")
							player = player.split(" ")[0][0]+" "+last[-1]
							data[game][prop][player] = {}
							data[game][prop][player]["0.5"] = ou
						elif prop == "int":
							j = btnIdx + 1
							if len(btns) <= 4:
								skip = 2
								j = btnIdx
							line = await btns[j].query_selector("span")
							line = line.text.split(" ")[1]
							ou = await btns[j].query_selector_all("span")
							ou = ou[1].text+"/"
							under = await btns[j+1].query_selector_all("span")
							ou += under[1].text
							data[game][prop][player] = {}
							data[game][prop][player][line] = ou.replace("Even", "+100")
						else:
							line = await btns[btnIdx].query_selector("span")
							line = line.text
							if "+" in line:
								line = str(float(line.replace("+", "")) - 0.5)
							else:
								line = line.split(" ")[1]

							if skip == 2 and prop != "tackles+ast":
								p = await btns[btnIdx].parent.parent.parent.query_selector("header")
								if p:
									player = parsePlayer(p.text)
								last = player.split(" ")
								try:
									player = player.split(" ")[0][0]+" "+last[-1]
								except:
									continue
							if player in players:
								player = players[player]
							if player not in data[game][prop]:
								data[game][prop][player] = {}
							data[game][prop][player][line] = ou

		with open(f"static/{sport}/espn.json", "w") as fh:
			json.dump(data, fh, indent=4)

		page = await browser.get(url)
		await page.wait_for(selector="article")
		section = await page.query_selector("section")
		articles = await section.query_selector_all("article")

	with open(f"static/{sport}/espn.json", "w") as fh:
		json.dump(data, fh, indent=4)
	browser.stop()

async def writeMGM(sport=None):
	if not sport:
		sport = "nfl"
	url = "https://sports.mi.betmgm.com/en/sports/football-11/betting/usa-9/nfl-35"
	if sport == "ncaaf":
		url = "https://sports.mi.betmgm.com/en/sports/football-11/betting/usa-9/college-football-211"
	elif sport == "nhl":
		url = "https://sports.mi.betmgm.com/en/sports/hockey-12/betting/usa-9/nhl-34"

	browser = await uc.start(no_sandbox=True)
	page = await browser.get(url)

	await page.wait_for(selector="ms-six-pack-event")
	events = await page.query_selector_all("ms-six-pack-event")

	for eventIdx in range(len(events)):
		event = events[eventIdx]


		if "Today" not in event.text_all and "starting in" not in event.text_all.lower() and "p1" not in event.text_all.lower() and "p2" not in event.text_all.lower() and "p3" not in event.text_all.lower():
			break
			pass
		teams = await event.query_selector_all(".participant")
		if sport == "ncaaf":
			away = teams[0].text.strip().lower()
			home = teams[1].text.strip().lower()
		elif sport == "nhl":
			away = convertMGMNHLTeam(teams[0].text.strip())
			home = convertMGMNHLTeam(teams[1].text.strip())
		else:
			away = convertMGMTeam(teams[0].text.strip())
			home = convertMGMTeam(teams[1].text.strip())
		game = f"{away} @ {home}"

		if game in data:
			continue

		#print(game)
		data[game] = {}

		a = await event.query_selector("a")
		await a.click()

		await page.wait_for(selector=".event-details-pills-list")
		li = await page.query_selector_all(".event-details-pills-list button")
		if "All" in li[-1].text:
			await li[-1].click()

		cutoff = await page.query_selector_all(".option-group-column:nth-child(1) ms-option-panel")
		cutoff = len(cutoff)
		groups = await page.query_selector_all(".option-group-column")
		for groupIdx, group in enumerate(groups):
			if not group:
				continue
			panels = await group.query_selector_all("ms-option-panel")
			for panelIdx, panel in enumerate(panels):
				prop = await panel.query_selector(".market-name")
				prop = prop.text.lower()
				#print(panelIdx, prop)

				multProps = False
				if prop == "first td scorer":
					prop = "ftd"
				elif prop == "anytime td scorer":
					prop = "attd"
				elif prop == "anytime goalscorer":
					prop = "atgs"
				elif prop == "first goalscorer":
					prop = "fgs"
				elif prop == "player shots":
					prop = "sog"
				elif prop == "player assists":
					prop = "ast"
				elif prop == "player blocked shots":
					prop = "bs"
				elif prop == "player points":
					prop = "pts"
				elif prop == "player to score 2+ tds":
					prop = "2+td"
				elif prop == "player to score 3+ tds":
					prop = "3+td"
				elif prop.endswith(": first touchdown scorer"):
					prop = "team_ftd"
				elif prop in ["rushing props", "defensive props", "quarterback props", "receiving props", "kicking props"]:
					multProps = True
				else:
					continue

				if not multProps and prop not in data[game]:
					data[game][prop] = {}

				up = await panel.query_selector(".theme-up")
				if not up:
					up = await panel.query_selector(".clickable")
					await up.click()
					try:
						await page.wait_for(selector=f".option-group-column:nth-child({groupIdx+1}) ms-option-panel:nth-child({panelIdx+1}) .option")
					except:
						continue

				show = await panel.query_selector(".show-more-less-button")
				if show and show.text_all == "Show More":
					await show.click()

				if multProps:
					lis = await panel.query_selector_all("li")
					for liIdx, li in enumerate(lis):
						a = await li.query_selector("a")
						await a.click()
						try:
							await page.wait_for(selector=f".option-group-column:nth-child({groupIdx+1}) ms-option-panel:nth-child({panelIdx+1}) li:nth-child({liIdx+1}).active")
						except:
							continue
						prop = a.text.lower().replace("receiving", "rec").replace("rushing", "rush").replace("passing", "pass").replace("yards", "yd").replace("receptions made", "rec").replace("reception", "rec").replace("extra points made", "xp").replace("points", "pts").replace("field goals made", "fgm").replace("points", "pts").replace("longest pass completion", "longest_pass").replace("completions", "cmp").replace("completion", "cmp").replace("attempts", "att").replace("touchdowns", "td").replace("assists", "ast").replace("defensive interceptions", "def_int").replace("interceptions thrown", "int").replace(" ", "_")
						if prop == "rush+rec_yd":
							prop = "rush+rec"
						elif prop == "pass+rush_yd":
							prop = "pass+rush"

						if "1st" in prop:
							continue

						if prop not in data[game]:
							data[game][prop] = {}

						players = await panel.query_selector_all(".attribute-key")
						odds = await panel.query_selector_all("ms-option")
						for playerIdx, player in enumerate(players):
							player = parsePlayer(player.text.split(" (")[0])
							if player not in data[game][prop]:
								data[game][prop][player] = {}
							line = await odds[playerIdx*2].query_selector(".name")
							if not line:
								continue
							line = line.text.strip().split(" ")[-1]
							over = await odds[playerIdx*2].query_selector(".value")
							under = await odds[playerIdx*2+1].query_selector(".value")
							data[game][prop][player][line] = over.text
							if under:
								data[game][prop][player][line] += "/" + under.text

				elif prop in ["pts", "ast", "sog", "bs"]:
					players = await panel.query_selector_all(".attribute-key")
					odds = await panel.query_selector_all(".value")
					for playerIdx, player in enumerate(players):
						player = parsePlayer(player.text.split(" (")[0])
						line = await odds[playerIdx*2].parent.query_selector(".name")
						line = line.text.strip().split(" ")[-1]
						ou = odds[playerIdx*2].text+"/"+odds[playerIdx*2+1].text
						if prop == "ast":
							data[game][prop][player] = ou
						else:
							data[game][prop][player] = {
								line: ou
							}
				else:
					odds = await panel.query_selector_all(".value")
					players = await panel.query_selector_all(".attribute-key")
					for player, odd in zip(players, odds):
						player = parsePlayer(player.text.split(" (")[0])
						if "defense" in player and sport == "nfl":
							player = player.split(" ")[0]

						if prop in ["attd", "ftd", "2+td", "3+td", "team_ftd", "atgs", "fgs"]:
							data[game][prop][player] = odd.text

		page = await browser.get(url)
		await page.wait_for(selector="ms-six-pack-event")
		events = await page.query_selector_all("ms-six-pack-event")

	with open(f"static/{sport}/mgm.json", "w") as fh:
		json.dump(data, fh, indent=4)
	browser.stop()


async def writeFD(sport=None):
	if not sport:
		sport = "nfl"
	url = f"https://sportsbook.fanduel.com/navigation/{sport}"

	browser = await uc.start(no_sandbox=True)
	page = await browser.get(url)

	await page.wait_for(selector="span[role=link]")
	links = await page.query_selector_all("span[role=link]")

	for link in links:
		if link.text == "More wagers":
			await link.parent.click()
			break

	await page.wait_for(selector="h1")

	h1 = await page.query_selector("h1")
	h1 = await h1.parent.query_selector("div")
	await h1.click()

	await page.wait_for(selector="div[role=dialog]")
	links = await page.query_selector_all("div[role=dialog] a")
	capture = False

	data = {}
	if capture:
		with open("static/nfl/fanduelLines.json") as fh:
			data = json.load(fh)

	for linkIdx in range(len(links)):

		h1 = await page.query_selector("h1")
		h1 = await h1.parent.query_selector("div")
		await h1.mouse_click()

		await page.wait_for(selector="div[role=dialog]")
		links = await page.query_selector_all("div[role=dialog] a")

		titleIdx = links[linkIdx].attributes.index("title")
		title = links[linkIdx].attributes[titleIdx+1]
		sp = title.lower().split(" @ ")
		if " at " in title.lower():
			sp = title.lower().split(" at ")
		away, home = map(str, sp)
		if sport == "nfl":
			away = convertTeam(away)
			home = convertTeam(home)
		elif sport == "nhl":
			away = convertNHLTeam(away)
			home = convertNHLTeam(home)
		game = f"{away} @ {home}"

		if sport == "nfl" and "Thursday" in links[linkIdx].text_all:
			break
			pass

		if sport == "nhl" and ("Monday" in links[linkIdx].text_all or "Tuesday" in links[linkIdx].text_all or "Wednesday" in links[linkIdx].text_all or "Thursday" in links[linkIdx].text_all or "Friday" in links[linkIdx].text_all or "Saturday" in links[linkIdx].text_all or "Sunday" in links[linkIdx].text_all):
			break

		if "live" in links[linkIdx].text_all:
			continue

		if game in data:
			continue
			pass

		if sport == "nfl":
			if linkIdx > 15:
				break

		if False:
			if game == "miami ohio @ toledo":
				capture = True
			if not capture:
				continue

		await links[linkIdx].click()
		await page.wait_for(selector="a[aria-selected=true]")

		nav = await page.query_selector_all("nav")
		nav = nav[-1]
		tabs = await nav.query_selector_all("a")

		game = await page.query_selector("h1")
		game = game.text.lower().replace(" odds", "")
		sp = game.split(" @ ")
		if " at " in game:
			sp = game.split(" at ")
		away, home = map(str, sp)
		awayFull, homeFull = away, home
		if sport == "nfl":
			away = convertTeam(away)
			home = convertTeam(home)
		elif sport == "nhl":
			away = convertNHLTeam(away)
			home = convertNHLTeam(home)
		game = f"{away} @ {home}"

		data[game] = {}

		for tabIdx in range(len(tabs)):
			try:
				tab = tabs[tabIdx]
			except:
				continue
			await page.wait_for(selector="div[data-test-id=ArrowAction]")

			if sport == "nhl":
				if tab.text.lower() not in ["popular", "goals", "shots", "points/assists"]:
				#if tab.text.lower() not in ["points/assists"]:
					continue
			else:
				if tab.text.lower() not in ["popular", "td scorer props", "passing props", "receiving props", "rushing props"]:
				#if tab.text.lower() not in ["popular"]:
					continue
			if tab.text.lower() != "popular" or sport == "nhl":
				await tab.scroll_into_view()
				await tab.mouse_click()
				await page.wait_for(selector="div[data-test-id=ArrowAction]")
				nav = await page.query_selector_all("nav")
				nav = nav[-1]
				tabs = await nav.query_selector_all("a")

			arrows = await page.query_selector_all("div[data-test-id=ArrowAction]")

			for arrowIdx, arrow in enumerate(arrows):
				label = arrow.text.lower()
				div = arrow.parent.parent.parent

				prop = prefix = fullPlayer = player = mainLine = ""
				skip = 2
				player = False

				if "1st half" in label or "first half" in label:
					prefix = "1h_"
				elif "2nd half" in label or "second half" in label:
					prefix = "2h_"
				elif "1st quarter" in label:
					prefix = "1q_"

				if label == "game lines":
					prop = "lines"
				elif label == "any time goal scorer":
					prop = "atgs"
					skip = 1
				elif label.endswith("total goals"):
					if "alternate" in label:
						continue
					if awayFull in label or homeFull in label:
						continue
					prop = "atgs"
				elif label == "first goal scorer":
					prop = "fgs"
					skip = 1
				elif label == "first home team goal scorer" or label == "first away team goal scorer":
					prop = "team_fgs"
					skip = 1
				elif label == "touchdown scorers":
					prop = "attd"
					data[game]["ftd"] = {}
					skip = 3
					if sport == "ncaaf":
						skip = 2
				elif label == "1st team touchdown scorer":
					prop = "team_ftd"
					skip = 1
				elif label == "to score 2+ touchdowns":
					prop = "2+td"
					skip = 1
				elif label == "to score 3+ touchdowns":
					prop = "3+td"
					skip = 1
				elif label == "anytime 1st half td scorer" or label == "anytime 2nd half td scorer":
					prop = "attd"
					skip = 1
				elif "kicking points" in label:
					prop = "kicking_pts"
				elif label == "player to record a sack":
					prop = "sacks"
					skip = 1
				elif label == "player to record an interception":
					prop = "def_int"
					skip = 1
				elif sport == "nhl" and label.startswith("player"):
					if label.endswith("shots on goal"):
						prop = "sog"
						mainLine = str(float(label.split(" ")[1].replace("+", "")) - 0.5)
						skip = 1
					elif label.endswith("assists"):
						prop = "ast"
						mainLine = str(float(label.split(" ")[1].replace("+", "")) - 0.5)
						skip = 1
					elif label.endswith("points"):
						if "powerplay" in label:
							continue
						prop = "pts"
						mainLine = str(float(label.split(" ")[1].replace("+", "")) - 0.5)
						skip = 1
					else:
						continue
				elif label.endswith("shots on goal"):
					if "period" in label:
						continue
					prop = "sog"
				elif label.startswith("player"):
					if "to record" in label or "specials" in label:
						continue
					prop = label.replace("player total ", "").replace("player ", "").replace("passing", "pass").replace("rushing", "rush").replace("receiving", "rec").replace("receptions", "rec").replace("reception", "rec").replace("completions", "cmp").replace("attempts", "att").replace("assists", "ast").replace("yds", "yd").replace("tds", "td").replace(" + ", "+").replace(" ", "_")
				elif " - alt" in label:
					skip = 1
					fullPlayer = label.split(" -")[0]
					player = parsePlayer(label.split(" -")[0].split(" (")[0])
					prop = label.split("alt ")[1].replace("passing", "pass").replace("rushing", "rush").replace("receiving", "rec").replace("total receptions", "rec").replace("receptions", "rec").replace("reception", "rec").replace("yds", "yd").replace("tds", "td").replace(" + ", "+").replace(" ", "_")
				elif " - passing + rushing yds" in label:
					prop = "pass+rush"
				else:
					continue

				prop = f"{prefix}{prop}"

				if prop == "rush+rec_yd":
					prop = "rush+rec"
				elif prop == "pass+rush_yd":
					prop = "pass+rush"

				if not prop:
					continue

				path = await arrow.query_selector("svg[data-test-id=ArrowActionIcon]")
				path = await path.query_selector("path")
				if prop != "lines" and path.attributes[1].split(" ")[0] != "M.147":
					await arrow.click()
					#await div.wait_for(selector="div[role=button]")
					#await div.wait_for(selector="div[aria-label='Show more']")

				el = await div.query_selector("div[aria-label='Show more']")
				if el:
					await el.click()
					#await div.wait_for("div[aria-label='Show less']")

				if prop != "lines" and prop not in data[game]:
					data[game][prop] = {}

				btns = await div.query_selector_all("div[role=button]")
				start = 1

				if "..." in btns[1].text:
					start += 1

				if prop == "lines":
					btns = btns[1:]
					idx = btns[1].attributes.index("aria-label")
					label = btns[1].attributes[idx+1]
					if "unavailable" not in label:
						data[game]["ml"] = label.split(", ")[2].split(" ")[0]+"/"+btns[4].attributes[idx+1].split(", ")[2].split(" ")[0]

					label = btns[0].attributes[1]
					if "unavailable" not in label:
						line = label.split(", ")[2]
						data[game]["spread"] = {}
						data[game]["spread"][float(line.replace("+", ""))] = label.split(", ")[3].split(" ")[0]+"/"+btns[3].attributes[1].split(", ")[3].split(" ")[0]
					line = btns[2].attributes[1].split(", ")[3].split(" ")[1]
					data[game]["total"] = {}
					data[game]["total"][line] = btns[2].attributes[1].split(", ")[4].split(" ")[0]+"/"+btns[5].attributes[1].split(", ")[4].split(" ")[0]
					continue

				for i in range(start, len(btns), skip):
					btn = btns[i]
					#print(i, start, skip, btn.attributes)
					if "data-test-id" in btn.attributes or "aria-label" not in btn.attributes:
						continue

					labelIdx = btn.attributes.index("aria-label") + 1
					label = btn.attributes[labelIdx]
					if "Show more" in label or "Show less" in label or "unavailable" in label:
						continue

					fields = label.split(", ")
					line = fields[1].split(" ")[1]
					odds = fields[-1].split(" ")[0]

					if prop == "kicking_pts":
						player = parsePlayer(arrow.text.lower().split(" total ")[0])
						data[game][prop][player] = {}
						data[game][prop][player][fields[2]] = odds + "/" + btns[i+1].attributes[labelIdx].split(", ")[3]
					elif prop in ["3+td", "2+td", "team_ftd", "1h_attd", "2h_attd"]:
						player = parsePlayer(fields[1].split(" (")[0])
						if sport == "nfl" and "defense" in player:
							continue
							player = convertTeam(player)
						if player:
							data[game][prop][player] = odds
					elif prop == "attd":
						if sport == "ncaaf" and "first" not in div.text_all.lower():
							skip = 1
						player = parsePlayer(fields[1].split(" (")[0])
						if sport == "nfl" and "defense" in player:
							continue
							player = convertTeam(player)
						data[game][prop][player] = odds
						#print(player, odds, btns[i+1].attributes)
						if skip != 1:
							data[game]["ftd"][player] = btns[i+1].attributes[labelIdx].split(", ")[2]
					elif prop in ["atgs", "fgs", "pts", "ast", "sog", "team_fgs"]:
						player = parsePlayer(fields[1].split(" (")[0].split(" - ")[0])
						if mainLine:
							if player not in data[game][prop]:
								data[game][prop][player] = {}
							data[game][prop][player][mainLine] = odds
						else:
							if prop in ["pts", "sog", "ast"]:
								line = fields[-2]

							if skip == 1:
								data[game][prop][player] = odds
							elif prop == "atgs":
								if player in data[game][prop] and int(data[game][prop][player]) > int(odds):
									data[game][prop][player] += "/"+btns[i+1].attributes[labelIdx].split(", ")[-1]
								else:
									data[game][prop][player] = odds+"/"+btns[i+1].attributes[labelIdx].split(", ")[-1]
							else:
								if player in data[game][prop] and line in data[game][prop][player] and int(data[game][prop][player][line].split("/")[0]) > int(odds.split("/")[0]):
									data[game][prop][player][line] += "/"+btns[i+1].attributes[labelIdx].split(", ")[-1]
								else:
									if player not in data[game][prop]:
										data[game][prop][player] = {}
									data[game][prop][player][line] = odds+"/"+btns[i+1].attributes[labelIdx].split(", ")[-1]
					elif skip == 1:
						# alts
						x = 0
						if prop in ["pass_td", "rec"] or "+" in prop:
							x = 1
						elif "+" not in fields[0]:
							x = 1
						if prop == "sacks" or prop == "def_int":
							player = parsePlayer(fields[1].split(" to Record")[0].split(" (")[0])
							line = "0.5"
						else:
							line = fields[x].lower().replace(fullPlayer+" ", "").split(" ")[0].replace("+", "")
							line = str(float(line) - 0.5)
						if player not in data[game][prop]:
							data[game][prop][player] = {}
						if line in data[game][prop][player]:
							continue
						data[game][prop][player][line] = odds
					elif prop == "pass+rush":
						player = parsePlayer(fields[0].split(" (")[0].split(" -")[0])
						if player not in data[game][prop]:
							data[game][prop][player] = {}
						line  = fields[2]
						data[game][prop][player][line] = odds+"/"+btns[i+1].attributes[labelIdx].split(", ")[3].split(" ")[0]
					else:
						player = parsePlayer(fields[0].split(" (")[0])
						if player not in data[game][prop]:
							data[game][prop][player] = {}
						data[game][prop][player][line] = odds+"/"+btns[i+1].attributes[labelIdx].split(", ")[2].split(" ")[0]
			

		with open(f"static/{sport}/fanduelLines.json", "w") as fh:
			json.dump(data, fh, indent=4)
	with open(f"static/{sport}/fanduelLines.json", "w") as fh:
		json.dump(data, fh, indent=4)
	browser.stop()

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("--bet365", action="store_true")
	parser.add_argument("--fd", action="store_true")
	parser.add_argument("--espn", action="store_true")
	parser.add_argument("--mgm", action="store_true")
	parser.add_argument("--team", "-t")
	parser.add_argument("--sport")

	args = parser.parse_args()

	if args.bet365:
		uc.loop().run_until_complete(write365(args.sport))

	if args.fd:
		uc.loop().run_until_complete(writeFD(args.sport))

	if args.espn:
		uc.loop().run_until_complete(writeESPN(args.sport))

	if args.mgm:
		uc.loop().run_until_complete(writeMGM(args.sport))
