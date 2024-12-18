
import time
import json
import random
import unicodedata
import nodriver as uc
import argparse

def convertCollege(team):
	team = strip_accents(team.lower())
	team = team.replace(".", "").replace("'", "").replace("-", " ")
	j = {
		"uconn": "connecticut",
		"florida international": "fiu",
		"indiana u": "indiana",
		"miami fl": "miami",
		"miami (fl)": "miami",
		"miami (oh)": "miami oh",
		"penn": "pennsylvania",
		"nc greensboro": "unc greensboro",
		"st johns": "saint johns",
		"saint josephs": "st josephs",
		"md baltimore": "umbc",
		"wv mountaineers": "west virginia",
		"va commonwealth": "vcu"
	}
	if team.endswith(" u"):
		return team[:-2]
	elif team.endswith(" st"):
		return team[:-3]+" state"
	return j.get(team, team)

def convertSoccer(team):
	team = team.lower().replace("-", " ")
	team = team.replace("munchen", "munich")
	j = {
		"stade brest": "brest",
		"girona fc": "girona",
		"inter milan": "inter",
		"rb leipzig": "leipzig",
		"bayer leverkusen": "leverkusen",
		"paris st-g": "paris st germain",
		"psg": "paris st germain",
		"psv eindhoven": "psv",
		"fc salzburg": "salzburg",
		"rb salzburg": "salzburg",
		"red bull salzburg": "salzburg",
		"shakhtar donetsk": "shakhtar",
		"sporting": "sporting lisbon"
	}
	return j.get(team, team)

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

def convert365NBATeam(team):
	team = team.lower()
	t = team.split(" ")[0]
	if t == "la":
		if "lakers" in team:
			return "lal"
		return "lac"
	elif t == "uta":
		return "utah"
	elif t == "was":
		return "wsh"
	elif t == "pho":
		return "phx"
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
	elif t == "was":
		return "wsh"
	elif t == "lac":
		return "la"
	return t

def convertMGMNBATeam(team):
	team = team.lower()
	if team == "knicks":
		return "ny"
	elif team == "celtics":
		return "bos"
	elif team == "timberwolves":
		return "min"
	elif team == "lakers":
		return "lal"
	elif team == "pacers":
		return "ind"
	elif team == "pistons":
		return "det"
	elif team == "bucks":
		return "mil"
	elif team == "76ers":
		return "phi"
	elif team == "cavaliers":
		return "cle"
	elif team == "raptors":
		return "tor"
	elif team == "magic":
		return "orl"
	elif team == "heat":
		return "mia"
	elif team == "nets":
		return "bkn"
	elif team == "hawks":
		return "atl"
	elif team == "bulls":
		return "chi"
	elif team == "pelicans":
		return "no"
	elif team == "hornets":
		return "cha"
	elif team == "rockets":
		return "hou"
	elif team == "grizzlies":
		return "mem"
	elif team == "jazz":
		return "utah"
	elif team == "suns":
		return "phx"
	elif team == "clippers":
		return "lac"
	elif team == "warriors":
		return "gs"
	elif team == "trail blazers":
		return "por"
	elif team == "wizards":
		return "wsh"
	elif team == "spurs":
		return "sa"
	elif team == "mavericks":
		return "dal"
	elif team == "thunder":
		return "okc"
	elif team == "nuggets":
		return "den"
	elif team == "kings":
		return "sac"
	return team

def convertMGMNHLTeam(team):
	team = team.lower()
	if team == "blues":
		return "stl"
	elif team == "capitals":
		return "wsh"
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
	elif team == "predators":
		return "nsh"
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

def convertNBATeam(team):
	team = team.lower()
	t = team[:3]
	if t == "was":
		return "wsh"
	elif t == "los":
		if "clippers" in team:
			return "lac"
		return "lal"
	elif t == "new":
		return "ny"
	elif t == "okl":
		return "okc"
	elif t == "san":
		return "sa"
	elif t == "was":
		return "wsh"
	elif t == "pho":
		return "phx"
	elif t == "gol":
		return "gs"
	elif t == "bro":
		return "bkn"
	elif t == "uta":
		return "utah"
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
	if player == "jadeney":
		return "jaden ivey"
	elif player.startswith("sebastian aho"):
		return "sebastian aho"
	elif player == "alex sarr":
		return "alexandre sarr"
	elif player == "mitchell marner":
		return "mitch marner"
	elif player == "alexander nylander":
		return "alex nylander"
	elif player == "nicolas claxton":
		return "nic claxton"
	return player

data = {}
props = {}

async def write365(sport=None, keep=None):
	data = {}
	if not sport:
		sport == "nfl"
	# start with multi
	urls = ["https://www.oh.bet365.com/?_h=CfVWPHD5idsD_8dFdjBYcw%3D%3D&btsffd=1#/AC/B12/C20426855/D47/E120593/F47/N7/", "https://www.oh.bet365.com/?_h=CfVWPHD5idsD_8dFdjBYcw%3D%3D&btsffd=1#/AC/B12/C20426855/D47/E120591/F47/"]
	if sport == "nhl":
		urls = ["https://www.oh.bet365.com/?_h=p2hqPA35Yw8_tTyHi3apXA%3D%3D&btsffd=1#/AC/B17/C20836572/D43/E170563/F43/N6/", "https://www.oh.bet365.com/?_h=utS-cSv5dnUh0yF1fiHydA%3D%3D&btsffd=1#/AC/B17/C20836572/D43/E170348/F43/"]
	elif sport == "nba":
		urls = ["https://www.oh.bet365.com/?_h=2t7rH-j5aYaLEGrY6urXTQ%3D%3D&btsffd=1#/AC/B18/C20604387/D43/E181379/F43/N43/"]
	elif sport == "soccer":
		urls = ["https://www.oh.bet365.com/?_h=nElNnPL5dnUh0trxLWRXBw%3D%3D&btsffd=1#/AC/B1/C1/D1002/G45/J99/Q1/F^24/N8/", "https://www.oh.bet365.com/?_h=nElNnPL5dnUh0trxLWRXBw%3D%3D&btsffd=1#/AC/B1/C1/D1002/G10202/J99/Q1/F^24/N6/"]

	if keep:
		with open(f"static/{sport}/bet365.json") as fh:
			data = json.load(fh)

	browser = None
	for urlIdx, url in enumerate(urls):
		if urlIdx == 0:
			browser = await uc.start(no_sandbox=True)
		page = await browser.get(url)

		await page.wait_for(selector=".srb-MarketSelectionButton-selected")

		reject = await page.query_selector(".ccm-CookieConsentPopup_Reject")
		if reject:
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
			if "td scorers" in prop:
				if "multi" in prop:
					prop = "2+td"
				else:
					prop = "attd"
			elif "goalscorers" in prop:
				if "multi" in prop:
					continue
				prop = "atgs"
			elif sport == "nba":
				if "milestones" in prop or prop in ["assists"]:
					alt = True
				prop = prop.replace("player ", "").replace(" and ", "+").replace(" & ", "+").replace(", ", "+").replace(" o/u", "").replace(" milestones", "").replace("points", "pts").replace("assists", "ast").replace("rebounds", "reb").replace("steals", "stl").replace("blocks", "blk").replace("turnovers", "to").replace("threes made", "3ptm").replace("double double", "double_double").replace("triple double", "triple_double").replace(" ", "_")
				if prop == "ast+reb":
					prop = "reb+ast"
				if prop in ["pts_low", "pts_high"]:
					prop = "pts"
			elif prop == "both teams to score":
				prop = "btts"
			elif prop == "alternative total goals":
				prop = "total"
			else:
				if "milestones" in prop or (sport == "nfl" and "o/u" not in prop):
					alt = True
				if "power play" in prop or prop == "player to score or assist":
					continue
				prop = prop.replace("player ", "").replace("to record a ", "").replace(" and ", "+").replace(" o/u", "").replace(" milestones", "").replace("passing", "pass").replace("rushing", "rush").replace("receiving", "rec").replace("receptions", "rec").replace("reception", "rec").replace("points", "pts").replace("assists", "ast").replace("interceptions", "int").replace("completions", "cmp").replace("attempts", "att").replace("shots on goal", "sog").replace("blocked shots", "bs").replace("yards", "yd").replace("touchdowns", "td").replace(" + ", "+").replace(" ", "_")
				if prop == "longest_pass_completion":
					prop = "longest_pass"
				elif prop == "longest_rush_attempt":
					prop = "longest_rush"
				elif prop == "rush+rec_yd":
					prop = "rush+rec"
				elif prop == "sack":
					prop = "sacks"

				if sport == "soccer":
					if prop == "ast":
						prop = "assist"
					else:
						prop = f"player_{prop}"
					
					if prop == "player_shots_on_target":
						alt = True

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
				sep = "v" if sport == "soccer" else "@"
				try:
					away, home = map(str, game.text.lower().split(f" {sep} "))
				except:
					continue
				if sport == "nhl":
					away = convert365NHLTeam(away)
					home = convert365NHLTeam(home)
				elif sport == "nba":
					away = convert365NBATeam(away)
					home = convert365NBATeam(home)
				elif sport == "nfl":
					away = convert365Team(away)
					home = convert365Team(home)
				elif sport == "soccer":
					away = convertSoccer(away)
					home = convertSoccer(home)

				game = f"{away} {sep} {home}"
				if game not in data:
					data[game] = {}

				#if game != "girona v liverpool":
				#	continue

				q = ".srb-ParticipantLabelWithTeam_Name"
				if prop == "total":
					q = ".srb-ParticipantLabelCentered_Name"
				players = await div.query_selector_all(q)
				cols = await div.query_selector_all(".gl-Market_General")

				if prop != "sacks" and alt:
					for col in cols[1:]:
						line = await col.query_selector("div")
						if not line:
							continue
						if not line.text.endswith("5"):
							line = str(float(line.text) - 0.5)
						else:
							line = line.text
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

				if prop == "total":
					if "total" not in data[game]:
						data[game]["total"] = {}
					overs = await cols[1].query_selector_all(".gl-Participant_General")
					unders = await cols[2].query_selector_all(".gl-Participant_General")
					x = await cols[4].query_selector_all(".gl-Participant_General")
					overs.extend(x)
					x = await cols[5].query_selector_all(".gl-Participant_General")
					unders.extend(x)

					for idx, p in enumerate(players):
						data[game]["total"][p.text] = f"{overs[idx].text}/{unders[idx].text}"

					continue


				try:
					odds1 = await cols[1].query_selector_all(".gl-Participant_General")
				except:
					continue
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

					#print(game, o1, o2, o3)

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
						if o3:
							data[game][prop][p] = o3
						data[game]["ftd"][p] = o1
						if o2:
							data[game]["ltd"][p] = o2
					elif prop == "atgs":
						if o3:
							data[game][prop][p] = o3
						data[game]["fgs"][p] = o1
					else:
						if p not in data[game][prop]:
							data[game][prop][p] = {}
						if prop == "sacks":
							line = "0.5"
						else:
							line = await odds1[idx].query_selector_all("span")
							try:
								line = line[-2].text
							except:
								continue
						ou = f"{o1}/{o2}".replace("/SP", "")
						data[game][prop][p][line] = ou

			if sport == "nhl" and prop == "atgs":
				break
			elif sport == "nfl" and prop == "attd":
				break
			elif sport == "soccer" and prop == "total":
				break

			with open(f"static/{sport}/bet365.json", "w") as fh:
				json.dump(data, fh, indent=4)

		with open(f"static/{sport}/bet365.json", "w") as fh:
			json.dump(data, fh, indent=4)

	with open(f"static/{sport}/bet365.json", "w") as fh:
		json.dump(data, fh, indent=4)

	#time.sleep(50)
	browser.stop()

async def writeESPN(sport=None, keep=None):
	if not sport:
		sport = "nfl"

	url = "https://espnbet.com/sport/football/organization/united-states/competition/nfl"
	if sport == "ncaaf":
		url = "https://espnbet.com/sport/football/organization/united-states/competition/ncaaf"
	elif sport == "nhl":
		url = "https://espnbet.com/sport/hockey/organization/united-states/competition/nhl"
	elif sport in ["nba", "ncaab"]:
		url = f"https://espnbet.com/sport/basketball/organization/united-states/competition/{sport}"
	elif sport == "soccer":
		url = "https://espnbet.com/sport/soccer/organization/international-clubs/competition/uefa-champions-league"
	data = {}

	if keep:
		with open(f"static/{sport}/espn.json") as fh:
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
		if sport != "nfl" and "Today" not in article.text_all:
			break
			pass
		teams = await article.query_selector_all(".text-primary")
		if sport == "nfl":
			away = convert365Team(teams[0].text)
			home = convert365Team(teams[-1].text)
		elif sport == "nhl":
			away = convert365NHLTeam(teams[0].text)
			home = convert365NHLTeam(teams[-1].text)
		elif sport == "nba":
			away = convert365NBATeam(teams[0].text)
			home = convert365NBATeam(teams[-1].text)
		elif sport == "soccer":
			away = convertSoccer(teams[0].text)
			home = convertSoccer(teams[-1].text)
		else:
			away = teams[0].text.lower()
			if away.startswith("("):
				away = away.split(") ")[-1]
			away = convertCollege(away)
			home = teams[-1].text.lower()
			if home.startswith("("):
				home = home.split(") ")[-1]
			home = convertCollege(home)
		sep = "v" if sport == "soccer" else "@"
		game = f"{away} {sep} {home}"

		if game in data:
			continue

		data[game] = {}
		print(game)

		btn = await article.query_selector("button")
		await btn.click()
		await page.wait_for(selector="div[data-testid='away-team-card']")

		tabs = await page.query_selector_all("button[data-testid=tablist-carousel-tab]")

		for tabIdx in range(len(tabs)):
			if sport == "soccer" and tabs[tabIdx].text_all.lower() not in ["lines", "game props", "player props"]:
				continue

			if sport != "soccer" and tabs[tabIdx].text_all.lower() not in ["player props", "td scorers"]:
				continue
			await tabs[tabIdx].click()
			if sport == "nba":
				time.sleep(5)
			else:
				time.sleep(1.5)
			await page.wait_for(selector="button[data-testid=tablist-carousel-tab][aria-selected=true]")

			details = await page.query_selector_all("details")
			players = {}
			for detailIdx in range(len(details)):
				detail = details[detailIdx]
				prop = await detail.query_selector("h2")
				#print(prop)
				try:
					prop = prop.text.lower()
				except:
					print(game, "skip")
					continue

				prefix = ""
				if "first half" in prop:
					prefix = "1h_"
				elif "second half" in prop:
					prefix = "2h_"

				skip = 2
				player = mainLine = ""

				if prop == "moneyline":
					prop = "ml"
				elif prop == "match spread" or prop == "2-way handicap":
					prop = "spread"
				elif prop == "total points" or prop == "total goals":
					prop = "total"
				elif prop == "to score a touchdown":
					prop = "attd"
					skip = 3
				elif prop == "player total touchdowns":
					prop = "attd"
					skip = 1
				elif "first goalscorer" in prop:
					prop = "fgs"
					skip = 1
				elif prop == "anytime goalscorer":
					prop = "atgs"
					skip = 1
				elif prop == "player to score a header":
					prop = "header"
					skip = 1
				elif prop == "total shots":
					prop = "game_shots"
					skip = 1
				elif prop == "total tackles":
					prop = "game_tackles"
					skip = 1
				elif prop == "total passes":
					prop = "game_passes"
					skip = 1
				elif prop == "total shots on target":
					prop = "game_shots_on_target"
					skip = 1
				elif tabs[tabIdx].text_all.lower() == "game props" and (prop.endswith("total shots on target") or prop.endswith("total shots") or prop.endswith("total tackles") or prop.endswith("total passes")):
					skip = 1
					suffix = prop.split(" total ")[-1].replace(" ", "_")

					if convertSoccer(prop.split(" total ")[0]) == game.split(" v ")[0]:
						prop = "home"
					elif convertSoccer(prop.split(" total ")[0]) == game.split(" v ")[-1]:
						prop = "away"
					else:
						continue

					prop = f"{prop}_{suffix}"
				elif prop.endswith("total shots on target") or prop.endswith("total shots") or prop.endswith("total tackles") or prop.endswith("total passes"):
					player = parsePlayer(prop.split(" total ")[0])
					prop = prop.split(" total ")[-1].replace(" ", "_")
					prop = f"player_{prop}"
					skip = 1
				elif sport == "soccer" and (prop == "player 1+ assists" or prop == "player 2+ assists"):
					mainLine = str(float(prop.split(" ")[1].replace("+", "")) - 0.5)
					prop = "assist"
					skip = 1
				elif prop.startswith("1st") and prop.endswith("goalscorer"):
					prop = "fgs"
					if prop != "1st goalscorer":
						prop = "team_fgs"
						#continue
					skip = 1
				elif prop == "both teams to score":
					prop = "btts"
				elif prop == "draw no bet":
					prop = "dnb"
				elif sport == "soccer" and prop.endswith("total goals"):
					team = convertSoccer(prop.split(" total")[0])
					if team == game.split(" v ")[0]:
						prop = "home_total"
					elif team == game.split(" v ")[-1]:
						prop = "away_total"
					else:
						continue
				elif "corners" in prop:
					if "minutes" in prop:
						continue
					if convertSoccer(prop.split(" team")[0].split(" total")[0].split("half ")[-1]) == game.split(" v ")[0]:
						prop = "home_corners"
					elif convertSoccer(prop.split(" team")[0].split(" total")[0].split("half ")[-1]) == game.split(" v ")[-1]:
						prop = "away_corners"
					elif prop.endswith("total corners"):
						prop = "corners"
					else:
						continue
				elif sport == "soccer":
					#if prop.endswith("total goals"):
					#	prop = "total"
					continue
				elif prop == "player total goals":
					prop = "atgs"
					skip = 3
				elif prop == "player total shots on goal":
					prop = "sog"
				elif prop == "player saves":
					prop = "saves"
					skip = 3
				elif prop == "player points":
					prop = "pts"
				elif prop.startswith("longest"):
					prop = prop.replace("reception", "rec").replace("pass completion", "pass").replace(" ", "_")
					skip = 1
				elif prop == "player total points":
					prop = "pts"
					if sport == "ncaab":
						skip = 3
				elif prop == "player total rebounds":
					prop = "reb"
					if sport == "ncaab":
						skip = 3
				elif prop == "player total assists":
					prop = "ast"
					if sport in ["nhl", "ncaab"]:
						skip = 3
				elif sport in ["nba", "ncaab"] and prop.startswith("player"):
					if "first" in prop or "1st" in prop:
						continue
					ou = False
					if "o/u" in prop:
						ou = True
					prop = prop.replace("player total ", "").replace(" o/u", "").replace("player to record a ", "").replace(", ", "+").replace(" and ", "+").replace("points", "pts").replace("rebounds", "reb").replace("assists", "ast").replace("blocks", "blk").replace("steals", "stl").replace("3-pointers made", "3ptm").replace("3-pointers attempted", "3pta").replace("free throws made", "ftm").replace("field goals made", "fgm").replace("field goals attempted", "fga").replace("turnovers", "to").replace(" ", "_")
					if ou and prop in ["pts", "reb", "ast", "3ptm"]:
						skip = 2
					else:
						skip = 3

					if prop in ["3pta", "fgm", "fga", "ftm"]:
						continue
				elif sport == "ncaab" and " total " in prop:
					player = parsePlayer(prop.split(" total ")[0])
					prop = prop.split(" total ")[-1].replace(", ", "+").replace(" and ", "+").replace("points", "pts").replace("rebounds", "reb").replace("assists", "ast").replace("blocks", "blk").replace("steals", "stl").replace("3-pointers made", "3ptm").replace("turnovers", "to").replace(" ", "_")
					skip = 1
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
					if prop == "player total sacks" or prop == "player total defensive interceptions" or "1st half" in prop or "1st quarter" in prop:
						continue
					prop = prop.replace("player total ", "").replace("player ", "").replace(" + ", "+").replace(" (o/u)", "").replace("points", "pts").replace("field goals made", "fgm").replace("extra pts made", "xpm").replace("passing", "pass").replace("rushing", "rush").replace("receptions", "rec").replace("reception", "rec").replace("receiving", "rec").replace("attempts", "att").replace("interceptions thrown", "int").replace("interceptions", "int").replace("completions", "cmp").replace("completion", "cmp").replace("yards", "yd").replace("touchdowns", "td").replace("tds", "td").replace("assists", "ast").replace("defensive", "def").replace(" ", "_")
					if prop == "def_tackles+ast":
						prop = "tackles+ast"
					elif "+" in prop:
						prop = prop.split("_")[0]
					elif prop == "longest_pass_cmp":
						prop = "longest_pass"
					elif prop == "def_int":
						skip = 1
				elif prop == "rushing + receiving yards":
					prop = "rush+rec"
					skip = 1
				elif sport == "nfl" and prop.startswith("total"):
					prop = prop.replace("total ", "").replace(" + ", "+").replace("passing", "pass").replace("rushing", "rush").replace("receptions", "rec").replace("reception", "rec").replace("receiving", "rec").replace("attempts", "att").replace("interceptions thrown", "int").replace("interceptions", "int").replace("completions", "cmp").replace("completion", "cmp").replace("yards", "yd").replace("touchdowns", "td").replace("tds", "td").replace("assists", "ast").replace("defensive", "def").replace(" ", "_")
					if "_" in prop and "+" in prop:
						prop = prop.split("_")[0]
					elif prop == "completed_passes":
						prop = "pass_cmp"
					elif prop == "passes_attempted":
						prop = "pass_att"

					if prop.endswith("_"):
						prop = prop[:-1]
					skip = 1
				else:
					continue

				if sport == "soccer":
					prop = f"{prefix}{prop}"

				if prop in ["1h_attd", "2h_attd"]:
					continue

				if prop == "ast+reb":
					prop = "reb+ast"

				if "open" not in detail.attributes:
					summary = await detail.query_selector("summary")
					await summary.click()
					#await detail.wait_for(selector="button")

				if prop not in data[game]:
					data[game][prop] = {}

				sections = [detail]
				if prop == "tackles+ast" or prop == "int" or (sport in ["nba", "ncaab"] and prop in ["pts", "reb", "ast"]):
					sections = await detail.query_selector_all("div[aria-label='']")

				for section in sections:
					btns = await section.query_selector_all("button")
					if prop == "tackles+ast" or prop == "int":
						player = await section.query_selector("header")
						player = parsePlayer(player.text)
					for btnIdx in range(0, len(btns), skip):
						if btns[btnIdx].text == "See All Lines":
							continue
						if "disabled" in btns[btnIdx].attributes and skip != 3:
							continue
						ou = ""
						i = btnIdx
						if sport != "nfl" and skip == 3:
							i += 1
						if i >= len(btns):
							continue
						try:
							over = await btns[i].query_selector_all("span")
							ou = over[1].text
						except:
							continue
						if skip != 1:
							try:
								under = await btns[i+1].query_selector_all("span")
								ou += "/"+under[1].text
							except:
								continue

						ou = ou.replace("Even", "+100")
						if prop in ["ml", "btts", "dnb"]:
							data[game][prop] = ou
						elif "ftd" in prop:
							player = await btns[btnIdx].query_selector("span")
							player = parsePlayer(player.text)
							last = player.split(" ")
							player = player.split(" ")[0][0]+" "+last[-1]
							data[game][prop][player] = ou
						elif prop.startswith("player_"):
							line = await btns[btnIdx].query_selector("span")
							if not line:
								continue
							line = str(float(line.text.replace("+", "")) - 0.5)
							if player not in data[game][prop]:
								data[game][prop][player] = {}
							data[game][prop][player][line] = ou
						elif sport == "soccer" and tabs[tabIdx].text_all.lower() == "game props" and skip == 1:
							line = await btns[btnIdx].query_selector("span")
							line = line.text.split(" ")[-1]
							data[game][prop][line] = ou
						elif sport == "soccer" and skip == 1:
							player = await btns[btnIdx].query_selector("span")
							player = parsePlayer(player.text)
							if mainLine:
								if player not in data[game][prop]:
									data[game][prop][player] = {}
								data[game][prop][player][mainLine] = ou
							else:
								data[game][prop][player] = ou
						elif sport == "soccer" and skip == 2:
							line = await btns[btnIdx].query_selector("span")
							line = line.text.split(" ")[-1]
							data[game][prop][line] = ou
						elif sport == "nfl" and skip == 1:
							player = await btns[btnIdx].parent.parent.query_selector("th")
							player = parsePlayer(player.text)
							last = player.split(" ")
							player = player.split(" ")[0][0]+" "+last[-1]
							if player not in data[game][prop]:
								data[game][prop][player] = {}
							line = btns[btnIdx].parent.attributes
							idIdx = line.index("id")
							line = str(float(line[idIdx+1].split("-")[-1].replace("+","")) - 0.5)
							#print(prop, player, line, ou)
							data[game][prop][player][line] = ou
						elif sport == "nhl" and prop in ["atgs", "fgs", "ast"]:
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
						elif prop == "def_int":
							player = await btns[btnIdx].query_selector("span")
							player = parsePlayer(player.text)
							last = player.split(" ")
							player = player.split(" ")[0][0]+" "+last[-1]
							data[game][prop][player] = {}
							data[game][prop][player]["0.5"] = ou
						else:
							line = ""
							if prop not in ["double_double", "triple_double"]:
								line = await btns[i].query_selector("span")
								if not line:
									continue
								line = line.text
								try:
									if "+" in line:
										line = str(float(line.replace("+", "")) - 0.5)
									else:
										line = line.split(" ")[1]
								except:
									continue

							if skip == 2 and prop != "tackles+ast":
								p = await btns[btnIdx].parent.parent.parent.query_selector("header")
								if p:
									player = parsePlayer(p.text)
								last = player.split(" ")
								try:
									player = player.split(" ")[0][0]+" "+last[-1]
								except:
									continue
							elif sport in ["nba", "ncaab", "nhl"] and skip == 3:
								player = parsePlayer(btns[btnIdx].text.lower().split(" total ")[0].split(" to record")[0])
								if sport == "nba":
									last = player.split(" ")
									player = player.split(" ")[0][0]+" "+last[-1]

							#print(player, prop, line, ou)

							if player in players:
								player = players[player]
							if player not in data[game][prop]:
								data[game][prop][player] = {}
							if prop in ["double_double", "triple_double"]:
								data[game][prop][player] = ou
							elif sport == "nfl" and line in data[game][prop][player]:
								over = int(data[game][prop][player][line])
								if "/" in ou and over > int(ou.split("/")[0]):
									data[game][prop][player][line] = str(over)+"/"+ou.split("/")[-1]
								else:
									data[game][prop][player][line] = ou
							else:
								data[game][prop][player][line] = ou


			with open(f"static/{sport}/espn.json", "w") as fh:
				json.dump(data, fh, indent=4)

		with open(f"static/{sport}/espn.json", "w") as fh:
			json.dump(data, fh, indent=4)

		page = await browser.get(url)
		await page.wait_for(selector="article")
		section = await page.query_selector("section")
		articles = await section.query_selector_all("article")

	with open(f"static/{sport}/espn.json", "w") as fh:
		json.dump(data, fh, indent=4)
	browser.stop()

async def writeMGM(sport=None, keep=None):
	if not sport:
		sport = "nfl"
	url = "https://sports.mi.betmgm.com/en/sports/football-11/betting/usa-9/nfl-35"
	if sport == "ncaaf":
		url = "https://sports.mi.betmgm.com/en/sports/football-11/betting/usa-9/college-football-211"
	elif sport == "nhl":
		url = "https://sports.mi.betmgm.com/en/sports/hockey-12/betting/usa-9/nhl-34"
	elif sport == "nba":
		url = "https://sports.mi.betmgm.com/en/sports/basketball-7/betting/usa-9/nba-6004"
	elif sport == "ncaab":
		url = "https://sports.mi.betmgm.com/en/sports/basketball-7/betting/usa-9/college-264"

	data = {}
	if keep:
		with open(f"static/{sport}/mgm.json") as fh:
			data = json.load(fh)

	browser = await uc.start(no_sandbox=True)
	page = await browser.get(url)

	await page.wait_for(selector="ms-six-pack-event")
	events = await page.query_selector_all("ms-six-pack-event")

	for eventIdx in range(len(events)):
		event = events[eventIdx]

		if sport != "nfl" and "Today" not in event.text_all and "starting in" not in event.text_all.lower() and "p1" not in event.text_all.lower() and "p2" not in event.text_all.lower() and "p3" not in event.text_all.lower():
			if sport == "nhl" and eventIdx == 0:
				pass
			elif sport == "ncaab":
				continue
			else:
				break
				pass
		teams = await event.query_selector_all(".participant")
		if sport.startswith("ncaa"):
			away = convertCollege(teams[0].text.strip().lower())
			home = convertCollege(teams[1].text.strip().lower())
		elif sport == "nhl":
			away = convertMGMNHLTeam(teams[0].text.strip())
			home = convertMGMNHLTeam(teams[1].text.strip())
		elif sport == "nba":
			away = convertMGMNBATeam(teams[0].text.strip())
			home = convertMGMNBATeam(teams[1].text.strip())
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
				if not prop:
					continue
				prop = prop.text.lower()
				#print(panelIdx, prop)

				multProps = False
				alt = False
				if prop == "first td scorer":
					prop = "ftd"
				elif prop == "anytime td scorer":
					prop = "attd"
				elif prop == "anytime goalscorer":
					prop = "atgs"
				elif prop == "first goalscorer":
					prop = "fgs"
				elif prop == "goalie saves":
					prop = "saves"
				elif prop == "player shots":
					prop = "sog"
				elif prop == "player assists":
					prop = "ast"
				elif prop == "player rebounds":
					prop = "reb"
				elif prop == "player steals":
					prop = "stl"
				elif prop == "player blocks":
					prop = "blk"
				elif prop == "player three-pointers":
					prop = "3ptm"
				elif prop == "double-double":
					prop = "double_double"
				elif prop == "triple-double":
					prop = "triple_double"
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
				elif prop.startswith("alternate player"):
					prop = prop.split(" ")[-1].replace("points", "pts").replace("rebounds", "reb").replace("assists", "ast").replace("three-pointers", "3ptm")
					alt = True
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

				if alt:
					lis = await panel.query_selector_all("li")
					for liIdx, li in enumerate(lis):
						a = await li.query_selector("a")
						await a.click()
						try:
							await page.wait_for(selector=f".option-group-column:nth-child({groupIdx+1}) ms-option-panel:nth-child({panelIdx+1}) li:nth-child({liIdx+1}).active")
						except:
							continue

						line = await li.query_selector(".title")
						line = str(float(line.text.replace("+", "")) - 0.5)
						if prop not in data[game]:
							data[game][prop] = {}

						players = await panel.query_selector_all(".attribute-key")
						odds = await panel.query_selector_all("ms-option")
						for playerIdx, player in enumerate(players):
							player = parsePlayer(player.text.split(" (")[0])
							if player not in data[game][prop]:
								data[game][prop][player] = {}
							over = await odds[playerIdx].query_selector(".value")
							if not over:
								continue
							if line not in data[game][prop][player]:
								data[game][prop][player][line] = over.text

				elif multProps:
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
							if not over:
								continue
							data[game][prop][player][line] = over.text
							if under:
								data[game][prop][player][line] += "/" + under.text

				elif sport == "nba":
					players = await panel.query_selector_all(".attribute-key")
					odds = await panel.query_selector_all(".option-pick")
					for playerIdx, player in enumerate(players):
						player = parsePlayer(player.text.split(" (")[0])
						try:
							line = await odds[playerIdx*2].query_selector(".name")
							line = line.text.strip().split(" ")[-1]
						except:
							continue
						
						try:
							ov = await odds[playerIdx*2].query_selector(".value")
							un = await odds[playerIdx*2+1].query_selector(".value")
						except:
							continue
						if ov:
							ou = ov.text
							if un:
								ou += "/"+un.text
							if prop in ["double_double", "triple_double"]:
								data[game][prop][player] = ou
							else:
								if player not in data[game][prop]:
									data[game][prop][player] = {}
								data[game][prop][player][line] = ou
				elif prop in ["pts", "ast", "reb", "sog", "bs"]:
					players = await panel.query_selector_all(".attribute-key")
					odds = await panel.query_selector_all(".value")
					for playerIdx, player in enumerate(players):
						player = parsePlayer(player.text.split(" (")[0])
						line = await odds[playerIdx*2].parent.query_selector(".name")
						line = line.text.strip().split(" ")[-1]
						ou = odds[playerIdx*2].text+"/"+odds[playerIdx*2+1].text
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

	with open(f"static/{sport}/mgm.json", "w") as fh:
		json.dump(data, fh, indent=4)
	browser.stop()

async def writeNCAABFD(keep):
	url = f"https://sportsbook.fanduel.com/navigation/ncaab"
	if False:
		url += "?tab=top-25"
	browser = await uc.start(no_sandbox=True)
	page = await browser.get(url)

	await page.wait_for(selector="#main ul")

	data = {}
	if keep:
		with open(f"static/ncaab/fanduelLines.json") as fh:
			data = json.load(fh)

	links = await page.query_selector_all("#main ul")
	if "Men's College Basketball Odds" in links[1].text_all:
		links = await links[1].query_selector_all("li")
	else:
		links = await links[2].query_selector_all("li")
	linkIdx = -1
	while True:
		linkIdx += 1
		if "half" in links[linkIdx].text_all.lower() or "overtime" in links[linkIdx].text_all.lower():
			continue

		if "MON" in links[linkIdx].text_all or "TUE" in links[linkIdx].text_all or "WED" in links[linkIdx].text_all or "THU" in links[linkIdx].text_all or "FRI" in links[linkIdx].text_all or "SAT" in links[linkIdx].text_all or "SUN" in links[linkIdx].text_all:
			break

		teams = await links[linkIdx].query_selector_all("span[role=text]")
		if not teams:
			continue
		away = convertCollege(teams[0].text)
		home = convertCollege(teams[1].text)
		game = f"{away} @ {home}"

		if game in data:
			continue

		link = await links[linkIdx].query_selector("span[role=link]")
		await link.parent.click()
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
		away = convertCollege(away)
		home = convertCollege(home)
		game = f"{away} @ {home}"

		if game in data:
			continue

		data[game] = {}

		for tabIdx in range(len(tabs)):
			try:
				tab = tabs[tabIdx]
			except:
				continue
			await page.wait_for(selector="div[data-test-id=ArrowAction]")

			if tab.text.lower() not in ["popular", "player points", "player threes", "player rebounds", "player assists", "player combos", "player defense"]:
			#if tab.text.lower() not in ["popular"]:
				continue

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
				alt = False

				if "1st half" in label or "first half" in label:
					prefix = "1h_"
				elif "2nd half" in label or "second half" in label:
					prefix = "2h_"
				elif "1st quarter" in label:
					prefix = "1q_"

				if label == "game lines":
					prop = "lines"
				else:
					if label.startswith("to score") and label.endswith("points"):
						prop = "pts"
						mainLine = str(float(label.split(" ")[-2].replace("+", "")) - 0.5)
						skip = 1
					elif label.endswith("+ made threes"):
						prop = "3ptm"
						mainLine = str(float(label.split(" ")[0].replace("+", "")) - 0.5)
						skip = 1
					elif label.startswith("to record") and label.endswith("rebounds"):
						prop = "reb"
						mainLine = str(float(label.split(" ")[-2].replace("+", "")) - 0.5)
						skip = 1
					elif label.startswith("to record") and label.endswith("assists"):
						prop = "ast"
						mainLine = str(float(label.split(" ")[-2].replace("+", "")) - 0.5)
						skip = 1
					elif label.startswith("to record") and label.endswith("steals"):
						prop = "stl"
						mainLine = str(float(label.split(" ")[-2].replace("+", "")) - 0.5)
						skip = 1
					elif label.startswith("to record") and label.endswith("blocks"):
						prop = "blk"
						mainLine = str(float(label.split(" ")[-2].replace("+", "")) - 0.5)
						skip = 1
					elif label.endswith("total points"):
						prop = "pts"
					elif label.endswith("total rebounds"):
						prop = "reb"
					elif label.endswith("total assists"):
						prop = "ast"
					elif label.endswith("total points + assists"):
						prop = "pts+ast"
					elif label.endswith("total points + rebounds"):
						prop = "pts+reb"
					elif label.endswith("total points + rebounds + assists"):
						prop = "pts+reb+ast"
					elif label.endswith("total rebounds + assists"):
						prop = "reb+ast"
					elif label.endswith("made threes"):
						mainLine = str(float(label.split(" ")[0].replace("+", "")) - 0.5)
						prop = "3ptm"
						skip = 1
					elif " - alt" in label:
						alt = True
						skip = 1
						player = parsePlayer(label.split(" - ")[0].split(" (")[0])
						prop = label.split("alternate total ")[-1].split("alt ")[-1].replace("assists", "ast").replace("points", "pts").replace("rebounds", "reb").replace("threes", "3ptm").replace(" + ", "+").replace(" ", "_")
					else:
						continue

				prop = f"{prefix}{prop}"

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
				bs = []
				for btn in btns:
					if "aria-label" in btn.attributes:
						bs.append(btn)
				btns = bs
				start = 1

				if "..." in btns[1].text:
					start += 1

				#if "aria-label" not in btns[start].attributes:
				#	start += 1

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

					try:
						fields = label.split(", ")
						line = fields[-2]
						odds = fields[-1].split(" ")[0]
					except:
						continue

					if skip == 1:
						if mainLine:
							player = parsePlayer(fields[1].split(" (")[0])
							line = mainLine
						elif alt:
							line = fields[1].split(" ")[-1]
						else:
							line = fields[-2]

						player = player.split(" (")[0]
						if player not in data[game][prop]:
							data[game][prop][player] = {}
						if line in data[game][prop][player]:
							if alt:
								if " under " in fields[1].lower():
									if "/" not in data[game][prop][player][line]:
										data[game][prop][player][line] += "/"+odds
								else:
									ov = data[game][prop][player][line].split("/")[0]
									un = ""
									if "/" in ov:
										un = data[game][prop][player][line].split("/")[1]
									if int(odds) > int(ov):
										data[game][prop][player][line].split("/")[-1]
										data[game][prop][player][line] = f"{odds}"
										if un and "/" not in data[game][prop][player][line]:
											data[game][prop][player][line] += f"/{un}"
							continue
						data[game][prop][player][line] = odds
					else:
						line = fields[-2]
						player = parsePlayer(fields[0].lower().split(" (")[0])
						if player not in data[game][prop]:
							data[game][prop][player] = {}
						data[game][prop][player][line] = odds
						if i+1 < len(btns) and "unavailable" not in btns[i+1].attributes[labelIdx]:
							try:
								data[game][prop][player][line] += "/"+btns[i+1].attributes[labelIdx].split(", ")[-1]
							except:
								continue
			

		with open(f"static/ncaab/fanduelLines.json", "w") as fh:
			json.dump(data, fh, indent=4)

		page = await browser.get(url)

		await page.wait_for(selector="#main ul")

		links = await page.query_selector_all("#main ul")
		if "Men's College Basketball Odds" in links[1].text_all:
			links = await links[1].query_selector_all("li")
		else:
			links = await links[2].query_selector_all("li")
		linkIdx = -1

	with open(f"static/ncaab/fanduelLines.json", "w") as fh:
		json.dump(data, fh, indent=4)
	browser.stop()

async def writeSoccerFD(keep, league):
	url = f"https://sportsbook.fanduel.com/soccer"
	if league:
		url += "?tab=featured"
	browser = await uc.start(no_sandbox=True)
	page = await browser.get(url)
	time.sleep(1)

	await page.wait_for(selector="#main ul")

	data = {}
	if keep:
		with open(f"static/soccer/fanduelLines.json") as fh:
			data = json.load(fh)

	links = await page.query_selector_all("#main ul")
	if "More wagers" in links[1].text_all:
		links = await links[1].query_selector_all("li")
	else:
		links = await links[2].query_selector_all("li")
	linkIdx = -1
	while True:
		linkIdx += 1
		if "half" in links[linkIdx].text_all.lower() or "overtime" in links[linkIdx].text_all.lower():
			continue

		if "MON" in links[linkIdx].text_all or "TUE" in links[linkIdx].text_all or "WED" in links[linkIdx].text_all or "THU" in links[linkIdx].text_all or "FRI" in links[linkIdx].text_all or "SAT" in links[linkIdx].text_all or "SUN" in links[linkIdx].text_all:
			pass

		teams = await links[linkIdx].query_selector_all("span[role=text]")
		if not teams:
			continue
		away = teams[0].text.lower()
		home = teams[1].text.lower()
		away = convertSoccer(away)
		home = convertSoccer(home)
		game = f"{away} v {home}"

		if game in data:
			continue

		link = await links[linkIdx].query_selector("span[role=link]")
		await link.parent.click()
		await page.wait_for(selector="a[aria-selected=true]")

		nav = await page.query_selector_all("nav")
		nav = nav[-1]
		tabs = await nav.query_selector_all("a")

		game = await page.query_selector("h1")
		game = game.text.lower().replace(" odds", "")
		away, home = map(str, game.split(" v "))
		away = convertSoccer(away)
		home = convertSoccer(home)
		game = f"{away} v {home}"

		if game in data:
			continue

		data[game] = {}

		for tabIdx in range(len(tabs)):
			try:
				tab = tabs[tabIdx]
			except:
				continue
			await page.wait_for(selector="div[data-test-id=ArrowAction]")

			if tab.text.lower() not in ["goal scorer", "goals", "team props", "half", "shots on target", "shots", "assists", "corners", "saves"]:
			#if tab.text.lower() not in ["corners"]:
				continue

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
				skip = 1
				player = False
				alt = False

				if "1st half" in label or "first half" in label:
					prefix = "1h_"
				elif "2nd half" in label or "second half" in label:
					prefix = "2h_"

				if label == "game lines":
					prop = "lines"
				elif label == "anytime goalscorer":
					prop = "atgs"
				elif label == "to score or assist":
					prop = "score_or_assist"
				elif label == "anytime assist":
					prop = "assist"
				elif "total corners" in label:
					skip = 2
					mainLine = label.split(" ")[-1]
					prop = "corners"
					if not label.startswith("total"):
						prop = f"{label.split(' ')[0]}_corners"
				elif label.endswith("shots on target") or label.endswith("shots"):
					if "headed" in label:
						continue
					prop = "shots"
					if "target" in label:
						prop = "shots_on_target"
					if label.startswith("match"):
						prop = f"game_{prop}"
					elif label.startswith("player"):
						mainLine = str(float(label.split(" ")[3]) - 0.5)
						prop = f"player_{prop}"
					elif label.startswith("team"):
						skip = 2
						mainLine = str(float(label.split(" ")[3]) - 0.5)
						prop = f"team_{prop}"
				elif label.startswith("2 way spread"):
					mainLine = label.split(" ")[-2]
					if "away team" in label:
						mainLine = str(float(mainLine) * -1)
					skip = 2
					prop = "spread"
				elif label.startswith("both teams to score"):
					if "&" in label:
						continue
					prop = "btts"
					skip = 2
				elif "over/under" in label and label.endswith("goals"):
					mainLine = label.split(" ")[-2]
					skip = 2
					prop = "total"
					if label.startswith("home team"):
						prop = "home_total"
					elif label.startswith("away team"):
						prop = "away_total"
				else:
					continue

				prop = f"{prefix}{prop}"

				if not prop:
					continue

				path = await arrow.query_selector("svg[data-test-id=ArrowActionIcon]")
				path = await path.query_selector("path")
				if prop != "lines" and path.attributes[1].split(" ")[0] != "M.147":
					await arrow.click()

				el = await div.query_selector("div[aria-label='Show more']")
				if el:
					await el.click()

				if prop != "lines" and prop not in data[game]:
					data[game][prop] = {}

				btns = await div.query_selector_all("div[role=button]")
				bs = []
				for btn in btns:
					if "aria-label" in btn.attributes:
						bs.append(btn)
				btns = bs
				start = 1

				if "..." in btns[1].text:
					start += 1

				#if "aria-label" not in btns[start].attributes:
				#	start += 1

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

					try:
						fields = label.split(", ")
						line = fields[-2]
						odds = fields[-1].split(" ")[0]
					except:
						continue

					ou = odds
					if skip != 1:
						try:
							under = btns[i+1].attributes[labelIdx].split(", ")[-1].split(" ")[0]
							ou += f"/{int(under)}"
						except:
							pass

					if prop.split("_")[-1] in ["btts"]:
						data[game][prop] = ou
					elif prop in ["team_shots_on_target", "team_shots"]:
						suffix = prop.replace("team_", "")
						if f"away_{suffix}" not in data[game]:
							data[game][f"away_{suffix}"] = {}
						if f"home_{suffix}" not in data[game]:
							data[game][f"home_{suffix}"] = {}
						if "/" not in ou:
							continue
						data[game][f"home_{suffix}"][mainLine] = fields[-1]
						data[game][f"away_{suffix}"][mainLine] = btns[i+1].attributes[labelIdx].split(", ")[-1]
					elif mainLine:
						if prop.startswith("player"):
							player = parsePlayer(fields[1])
							if player not  in data[game][prop]:
								data[game][prop][player] = {}
							data[game][prop][player][mainLine] = ou
						else:
							data[game][prop][mainLine] = ou
					elif prop.startswith("game_shots"):
						line = str(float(fields[-2].split(" ")[0]) - 0.5)
						data[game][prop][line] = ou
					else:
						player = parsePlayer(line)
						data[game][prop][player] = ou
			

		with open(f"static/soccer/fanduelLines.json", "w") as fh:
			json.dump(data, fh, indent=4)

		page = await browser.get(url)

		await page.wait_for(selector="#main ul")

		links = await page.query_selector_all("#main ul")
		if "More wagers" in links[1].text_all:
			links = await links[1].query_selector_all("li")
		else:
			links = await links[2].query_selector_all("li")
		linkIdx = -1

	with open(f"static/soccer/fanduelLines.json", "w") as fh:
		json.dump(data, fh, indent=4)
	browser.stop()

async def writeFD(sport=None, keep=None, league=None):
	if not sport:
		sport = "nfl"
	url = f"https://sportsbook.fanduel.com/navigation/{sport}"

	if sport == "ncaab":
		await writeNCAABFD(keep)
		exit()
	elif sport == "soccer":
		await writeSoccerFD(keep, league)
		exit()

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

	data = {}
	if keep:
		with open(f"static/{sport}/fanduelLines.json") as fh:
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
		elif sport == "nba":
			away = convertNBATeam(away)
			home = convertNBATeam(home)
		elif sport == "ncaab":
			away = convertCollege(away)
			home = convertCollege(home)
		game = f"{away} @ {home}"

		if sport == "nfl" and "Thursday" in links[linkIdx].text_all:
			break
			pass

		if sport != "nfl" and ("Monday" in links[linkIdx].text_all or "Tuesday" in links[linkIdx].text_all or "Wednesday" in links[linkIdx].text_all or "Thursday" in links[linkIdx].text_all or "Friday" in links[linkIdx].text_all or "Saturday" in links[linkIdx].text_all or "Sunday" in links[linkIdx].text_all):
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
		elif sport == "nba":
			away = convertNBATeam(away)
			home = convertNBATeam(home)
		elif sport == "ncaab":
			away = convertCollege(away)
			home = convertCollege(home)
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
					continue
			elif sport in ["nba", "ncaab"]:
				if tab.text.lower() not in ["popular", "player points", "player threes", "player rebounds", "player assists", "player combos", "player defense"]:
				#if tab.text.lower() not in ["popular"]:
					continue
			else:
				if tab.text.lower() not in ["popular", "td scorer props", "passing props", "receiving props", "rushing props"]:
				#if tab.text.lower() not in ["popular"]:
					continue
			if tab.text.lower() != "popular" or sport in ["nhl", "nba", "ncaab"]:
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
				alt = False

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
					if "alternate" in label or "period" in label:
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
				elif label == "to record a double double":
					prop = "double_double"
					skip = 1
				elif label == "to record a triple double":
					prop = "triple_double"
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
					if "to record" in label or "specials" in label or "performance" in label or "featured" in label:
						continue
					prop = label.replace("player total ", "").replace("player ", "").replace("passing", "pass").replace("rushing", "rush").replace("receiving", "rec").replace("receptions", "rec").replace("reception", "rec").replace("completions", "cmp").replace("attempts", "att").replace("assists", "ast").replace("points", "pts").replace("rebounds", "reb").replace("made threes", "3ptm").replace("steals", "stl").replace("blocks", "blk").replace("yds", "yd").replace("tds", "td").replace(" + ", "+").replace(" ", "_")
				elif " - alt" in label:
					if sport != "nba":
						skip = 1
					alt = True
					fullPlayer = label.split(" -")[0]
					player = parsePlayer(label.split(" -")[0].split(" (")[0])
					prop = label.split("alternate total ")[-1].split("alt ")[-1].replace("passing", "pass").replace("rushing", "rush").replace("receiving", "rec").replace("total receptions", "rec").replace("receptions", "rec").replace("reception", "rec").replace("assists", "ast").replace("points", "pts").replace("rebounds", "reb").replace("threes", "3ptm").replace("yds", "yd").replace("tds", "td").replace(" + ", "+").replace(" ", "_")
				elif " - passing + rushing yds" in label:
					prop = "pass+rush"
				elif sport in ["nba", "ncaab"]:
					if label.startswith("to score") and label.endswith("points"):
						prop = "pts"
						mainLine = str(float(label.split(" ")[-2].replace("+", "")) - 0.5)
						skip = 1
					elif label.endswith("+ made threes"):
						prop = "3ptm"
						mainLine = str(float(label.split(" ")[0].replace("+", "")) - 0.5)
						skip = 1
					elif label.startswith("to record") and label.endswith("rebounds"):
						prop = "reb"
						mainLine = str(float(label.split(" ")[-2].replace("+", "")) - 0.5)
						skip = 1
					elif label.startswith("to record") and label.endswith("assists"):
						prop = "ast"
						mainLine = str(float(label.split(" ")[-2].replace("+", "")) - 0.5)
						skip = 1
					elif label.startswith("to record") and label.endswith("steals"):
						prop = "stl"
						mainLine = str(float(label.split(" ")[-2].replace("+", "")) - 0.5)
						skip = 1
					elif label.startswith("to record") and label.endswith("blocks"):
						prop = "blk"
						mainLine = str(float(label.split(" ")[-2].replace("+", "")) - 0.5)
						skip = 1
					elif label.endswith(") total points"):
						prop = "pts"
					elif label.endswith(") total rebounds"):
						prop = "reb"
					elif label.endswith(") total assists"):
						prop = "ast"
					elif label.endswith(") total points + assists"):
						prop = "pts+ast"
					elif label.endswith(") total points + rebounds"):
						prop = "pts+reb"
					elif label.endswith(") total points + rebounds + assists"):
						prop = "pts+reb+ast"
					elif label.endswith(") total rebounds + assists"):
						prop = "reb+ast"
					else:
						continue
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
				bs = []
				for btn in btns:
					if "aria-label" in btn.attributes:
						bs.append(btn)
				btns = bs
				start = 1

				if "..." in btns[1].text:
					start += 1

				#if "aria-label" not in btns[start].attributes:
				#	start += 1

				if alt and prop == "reb+ast":
					skip = 1

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

					try:
						fields = label.split(", ")
						line = fields[1].split(" ")[1]
						odds = fields[-1].split(" ")[0]
					except:
						continue

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
						if skip != 1 and "unavailable" not in btns[i+1].attributes[labelIdx]:
							data[game]["ftd"][player] = btns[i+1].attributes[labelIdx].split(", ")[2]
					elif sport == "nhl" and prop in ["atgs", "fgs", "pts", "ast", "sog", "team_fgs"]:
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
									try:
										data[game][prop][player] = odds+"/"+btns[i+1].attributes[labelIdx].split(", ")[-1]
									except:
										pass
							else:
								if player in data[game][prop] and line in data[game][prop][player] and int(data[game][prop][player][line].split("/")[0]) > int(odds.split("/")[0]):
									data[game][prop][player][line] += "/"+btns[i+1].attributes[labelIdx].split(", ")[-1]
								else:
									if player not in data[game][prop]:
										data[game][prop][player] = {}
									data[game][prop][player][line] = odds+"/"+btns[i+1].attributes[labelIdx].split(", ")[-1]
					elif prop in ["double_double", "triple_double"]:
						player = parsePlayer(fields[1].split(" (")[0])
						data[game][prop][player] = odds
					elif skip == 1 and prop == "reb+ast":
						player = parsePlayer(fields[0].split(" - alt")[0])
						if "reb + ast" in player:
							player = player.replace("   alt reb + ast", "")
						line = fields[1].split(" ")[-1]
						if player not in data[game][prop]:
							data[game][prop][player] = {}
						if line in data[game][prop][player]:
							continue
						data[game][prop][player][line] = odds
					elif sport == "ncaab" and skip == 1:
						if mainLine:
							player = parsePlayer(fields[1].split(" (")[0])
							line = mainLine
						elif alt:
							line = fields[1].split(" ")[-1]
						else:
							line = fields[-2]

						player = player.split(" (")[0]
						if player not in data[game][prop]:
							data[game][prop][player] = {}
						if line in data[game][prop][player]:
							if alt:
								if " under " in fields[1].lower():
									if "/" not in data[game][prop][player][line]:
										data[game][prop][player][line] += "/"+odds
								else:
									ov = data[game][prop][player][line].split("/")[0]
									un = ""
									if "/" in ov:
										un = data[game][prop][player][line].split("/")[1]
									if int(odds) > int(ov):
										data[game][prop][player][line].split("/")[-1]
										data[game][prop][player][line] = f"{odds}"
										if un and "/" not in data[game][prop][player][line]:
											data[game][prop][player][line] += f"/{un}"
							continue
						data[game][prop][player][line] = odds
					elif skip == 1:
						# alts
						x = 0
						if prop in ["pass_td", "rec"] or "+" in prop:
							x = 1
						elif "+" not in fields[0]:
							x = 1
						if mainLine:
							player = parsePlayer(fields[1])
							line = mainLine
						elif prop == "sacks" or prop == "def_int":
							player = parsePlayer(fields[1].split(" to Record")[0].split(" (")[0])
							line = "0.5"
						else:
							line = fields[x].lower().replace(fullPlayer+" ", "").split(" ")[0].replace("+", "")
							line = str(float(line) - 0.5)

						player = player.split(" (")[0]
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
						if sport == "nba" and alt:
							line = fields[1].split(" ")[0]
						elif sport == "ncaab":
							line = fields[-2]
						player = parsePlayer(fields[0].lower().split(" (")[0].split(" - alt")[0])
						if player not in data[game][prop]:
							data[game][prop][player] = {}
						data[game][prop][player][line] = odds
						if i+1 < len(btns) and "unavailable" not in btns[i+1].attributes[labelIdx]:
							try:
								if sport == "ncaab":
									data[game][prop][player][line] += "/"+btns[i+1].attributes[labelIdx].split(", ")[-1]
								else:
									data[game][prop][player][line] += "/"+btns[i+1].attributes[labelIdx].split(", ")[2].split(" ")[0]
							except:
								continue
			

		with open(f"static/{sport}/fanduelLines.json", "w") as fh:
			json.dump(data, fh, indent=4)
	with open(f"static/{sport}/fanduelLines.json", "w") as fh:
		json.dump(data, fh, indent=4)
	browser.stop()

async def writeSoccerDK(keep):
	url = "https://sportsbook.draftkings.com/leagues/soccer/champions-league"
	data = {}
	if keep:
		with open(f"static/soccer/draftkings.json") as fh:
			data = json.load(fh)

	browser = await uc.start(no_sandbox=True)
	page = await browser.get(url)
	time.sleep(1)

	await page.wait_for(selector="div[role=tablist]")

	tablist = await page.query_selector("div[role=tablist]")
	mainTabs = await tablist.query_selector_all("a")

	for mainIdx, mainTab in enumerate(mainTabs):
		if mainTab.text.lower() not in ["game lines", "goalscorer props", "shots/assists props", "corners"]:
		#if mainTab.text.lower() not in ["corners"]:
			continue

		await mainTab.click()
		await page.wait_for(selector=".sportsbook-event-accordion__wrapper")

		tabs = await page.query_selector_all("div[role=tablist]")
		tabs = await tabs[-1].query_selector_all("a")

		for tabIdx, tab in enumerate(tabs):
			prop = tab.text.lower().split(" (")[0]

			if tabIdx != 0:
				await tab.click()
				await page.wait_for(selector=".sportsbook-event-accordion__wrapper")

			skip = 2
			alt = False

			if prop.startswith("alt"):
				alt = True

			prefix = ""
			if "1st half" in prop:
				prefix = "1h_"
			elif "2nd half" in prop:
				prefix = "2h_"

			if prop == "moneyline":
				prop = "ml"
				continue
			elif prop == "draw no bet":
				prop = "dnb"
			elif prop == "total goals":
				prop = "total"
			elif prop == "spread":
				prop = "spread"
			elif prop == "goalscorer":
				prop = "atgs"
			elif prop == "to score or give assist":
				prop = "score_or_assist"
			elif prop == "to score a header":
				prop = "header"
			elif "total corners" in prop:
				if "3" in tab.text or "odd/even" in prop:
					continue
				prop = "corners"
			elif prop == "total team corners":
				prop = "team_corners"
			elif prop.startswith("player"):
				prop = prop.replace(" ", "_")
				if prop == "player_assists":
					prop = "assist"
			else:
				continue

			prop = f"{prefix}{prop}"

			gameDivs = await page.query_selector_all(".sportsbook-event-accordion__wrapper")
			for gameDiv in gameDivs:
				game = await gameDiv.query_selector(".sportsbook-event-accordion__title-wrapper")
				teams = await gameDiv.query_selector_all(".sportsbook-event-accordion__title-logo")

				if prop in ["spread", "total"]:
					more = await gameDiv.query_selector(".view-more__button span")
					await more.mouse_click()
				try:
					altIdx = teams[0].attributes.index("alt")
				except:
					continue
				
				away = teams[0].attributes[altIdx+1].lower().replace("-logo", "")
				home = teams[1].attributes[altIdx+1].lower().replace("-logo", "")
				t = await gameDiv.query_selector(".sportsbook-event-accordion__date")
				#if "tomorrow" not in t.text_all.lower() and "today" not in t.text_all.lower():
				if "today" not in t.text_all.lower():
					continue

				away = convertSoccer(away)
				home = convertSoccer(home)
				game = f"{away} v {home}"

				#if game != "girona v liverpool":
				#	continue

				if game not in data:
					data[game] = {}

				if prop not in data[game]:
					data[game][prop] = {}

				#data[game][prop] = {}

				if "ml" in prop:
					odds = await gameDiv.query_selector_all(".sportsbook-odds")
				elif prop in ["dnb"]:
					odds = await gameDiv.query_selector_all(".sportsbook-odds")
					data[game][prop] = odds[0].text.replace("\u2212", "-")
					if len(odds) > 1:
						data[game][prop] += "/"+odds[1].text.replace("\u2212", "-")
				elif prop == "team_corners":
					divs = await gameDiv.query_selector_all(".component-29")
					for div in divs:
						team = await div.query_selector(".sportsbook-row-name")
						team = convertSoccer(team.text.lower().split(":")[0])
						btns = await div.query_selector_all("div[role=button]")
						line = btns[0].text_all.split(" ")[-2]
						over = btns[0].text_all.split(" ")[-1].replace("\u2212", "-")
						under = btns[1].text_all.split(" ")[-1].replace("\u2212", "-")
						awayHome = "away"
						if team == game.split(" v ")[0]:
							awayHome = "home"
						p = f"{awayHome}_corners"
						if p not in data[game]:
							data[game][p] = {}
						data[game][p][line] = f"{over}/{under}"
				elif prop in ["spread", "total"] or "corners" in prop:
					q = ".view-more"
					if "corners" in prop:
						q = "ul"
					btns = await gameDiv.query_selector_all(f"{q} div[role=button]")
					for i in range(0, len(btns), 2):
						line = btns[i].text_all.split(" ")[-2]
						over = btns[i].text_all.split(" ")[-1].replace("\u2212", "-")
						under = btns[i+1].text_all.split(" ")[-1].replace("\u2212", "-")
						data[game][prop][line] = f"{over}/{under}"
				elif prop in ["score_or_assist", "header"]:
					btns = await gameDiv.query_selector_all("ul div[role=button]")
					for btn in btns:
						player = await btn.query_selector("span")
						if not player:
							continue
						player = parsePlayer(player.text)
						odds = await btn.query_selector(".sportsbook-odds")
						data[game][prop][player] = odds.text.replace("\u2212", "-")
				elif prop == "atgs":
					divs = await gameDiv.query_selector_all(".scorer-7__body")
					for div in divs:
						player = await div.query_selector(".scorer-7__player")
						if not player:
							continue
						player = parsePlayer(player.text.strip())
						btns = await div.query_selector_all("div[role=button]")
						data[game][prop][player] = btns[-1].text.replace("\u2212", "-")
				elif prop.startswith("player") or prop == "assist":
					divs = await gameDiv.query_selector_all(".component-29")
					for div in divs:
						line = await div.query_selector("span")
						line = str(float(line.text.split(" ")[3]) - 0.5)
						btns = await div.query_selector_all("div[role=button]")
						for btn in btns:
							player = await btn.query_selector("span")
							if not player:
								continue
							player = parsePlayer(player.text_all)
							odds = await btn.query_selector(".sportsbook-odds")

							if player not in data[game][prop]:
								data[game][prop][player] = {}
							data[game][prop][player][line] = odds.text.replace("\u2212", "-")
				else:
					rows = await gameDiv.query_selector_all(".sportsbook-table__body tr")
					for row in rows:
						tds = await row.query_selector_all("td")
						player = await row.query_selector("span")
						if not player:
							continue
						player = parsePlayer(player.text)

						if player not in data[game][prop]:
							try:
								data[game][prop][player] = {}
							except:
								continue

						line = await tds[0].query_selector(".sportsbook-outcome-cell__line")
						if not line:
							continue
						line = line.text
						odds = await tds[0].query_selector(".sportsbook-odds")
						under = await tds[1].query_selector(".sportsbook-odds")
						if line in data[game][prop][player]:
							over = data[game][prop][player][line]
							if "/" in over:
								continue
							if int(over) < int(odds.text.replace("\u2212", "-")):
								over = odds.text.replace("\u2212", "-")
							data[game][prop][player][line] = over+"/"+under.text.replace("\u2212", "-")
						else:
							data[game][prop][player][line] = odds.text.replace("\u2212", "-")
							if under:
								data[game][prop][player][line] += "/"+under.text.replace("\u2212", "-")
		
			if prop in ["btts", "2h_corners", "assist"]:
				break

			with open(f"static/soccer/draftkings.json", "w") as fh:
				json.dump(data, fh, indent=4)

		with open(f"static/soccer/draftkings.json", "w") as fh:
			json.dump(data, fh, indent=4)
	with open(f"static/soccer/draftkings.json", "w") as fh:
		json.dump(data, fh, indent=4)
	browser.stop()

async def writeDK(sport=None, keep=None, propArg=None):
	if not sport:
		sport = "nfl"

	if sport in ["nba", "ncaab"]:
		url = f"https://sportsbook.draftkings.com/leagues/basketball/{sport}"
	elif sport == "nhl":
		url = "https://sportsbook.draftkings.com/leagues/hockey/nhl"
	elif sport == "soccer":
		await writeSoccerDK(keep)
		exit()
	else:
		url = "https://sportsbook.draftkings.com/leagues/football/nfl"

	data = {}
	if keep or propArg:
		with open(f"static/{sport}/draftkings.json") as fh:
			data = json.load(fh)

	browser = await uc.start(no_sandbox=True)
	page = await browser.get(url)
	time.sleep(1)

	await page.wait_for(selector="div[role=tablist]")

	tablist = await page.query_selector("div[role=tablist]")
	mainTabs = await tablist.query_selector_all("a")
	data = {}

	for mainIdx, mainTab in enumerate(mainTabs):
		if sport in ["nba", "ncaab"]:
			if mainTab.text.lower() not in ["player points", "player rebounds", "player assists", "player threes", "player combos", "player defense"]:
				continue
		elif sport == "nhl":
			if mainTab.text.lower() not in ["goalscorer", "shots on goal", "points", "assists", "blocks", "goalie props"]:
				continue
		else:
			if mainTab.text.lower() not in ["td scorers", "passing props", "rushing props", "receiving props", "d/st props"]:
				continue

		await mainTab.click()
		await page.wait_for(selector=".sportsbook-event-accordion__wrapper")


		tabs = await page.query_selector_all("div[role=tablist]")
		tabs = await tabs[-1].query_selector_all("a")

		for tabIdx, tab in enumerate(tabs):
			prop = tab.text.lower()
			if "most" in prop or "- 1q" in prop or "- 1st q" in prop or "- h2h" in prop or "race to" in prop or "x+ yards" in prop:
				continue

			if sport == "nhl" and prop not in ["goalscorer", "shots on goal", "shots on goal o/u", "points", "points o/u", "assists", "assists o/u", "blocks o/u", "saves o/u"]:
				continue
			if mainTab.text.lower() == "td scorers" and prop not in ["td scorer", "player not to score"]:
				continue

			if tabIdx != 0:
				await tab.click()
				await page.wait_for(selector=".sportsbook-event-accordion__wrapper")

			skip = 1
			alt = False
			if "o/u" in prop or mainTab.text.lower() == "d/st props":
				skip = 2

			if prop.startswith("alt"):
				alt = True

			prop = prop.split(" (")[0].replace("player ", "").replace(" o/u", "").replace("alt ", "").replace("passing", "pass").replace("receiving", "rec").replace("rushing", "rush").replace("attempts", "att").replace("receptions", "rec").replace("reception", "rec").replace("completions", "pass_cmp").replace("completion", "cmp").replace("tds", "td").replace("yards", "yd").replace("points", "pts").replace("rebounds", "reb").replace("assists", "ast").replace("threes", "3ptm").replace("blocks", "blk").replace("turnovers", "to").replace("steals", "stl").replace("shots on goal", "sog").replace("goalscorer", "atgs").replace(" + ", "+").replace(" ", "_")
			if prop == "double-double":
				prop = "double_double"
			elif prop == "triple-double":
				prop = "triple_double"
			elif prop == "ast+reb":
				prop = "reb+ast"
			elif sport == "nhl" and prop == "blk":
				prop = "bs"
			elif prop == "rush+rec_yd":
				prop = "rush+rec"

			if propArg and prop != propArg:
				continue

			gameDivs = await page.query_selector_all(".sportsbook-event-accordion__wrapper")
			for gameDiv in gameDivs:
				game = await gameDiv.query_selector(".sportsbook-event-accordion__title-wrapper")
				teams = await gameDiv.query_selector_all(".sportsbook-event-accordion__title-logo")

				try:
					altIdx = teams[0].attributes.index("alt")
				except:
					continue
				if sport == "ncaab":
					away = convertCollege(game.text_all.lower().split(" at ")[0])
					home = convertCollege(game.text_all.lower().split(" at ")[-1])
				elif sport == "nba":
					away = convert365NBATeam(teams[0].attributes[altIdx+1].split(" ")[0])
					home = convert365NBATeam(teams[1].attributes[altIdx+1].split(" ")[0])
				elif sport == "nhl":
					away = convert365NHLTeam(teams[0].attributes[altIdx+1])
					home = convert365NHLTeam(teams[1].attributes[altIdx+1])
				else:
					away = convert365Team(teams[0].attributes[altIdx+1].split(" ")[0])
					if away == "nyj" and "giants" in teams[0].attributes[altIdx+1]:
						away = "nyg"
					home = convert365Team(teams[1].attributes[altIdx+1].split(" ")[0])
					if home == "nyj" and "giants" in teams[1].attributes[altIdx+1]:
						home = "nyg"

				if " logo " in away:
					away = away.split(" logo ")[0]
				if " logo " in home:
					home = home.split(" logo ")[0]
				game = f"{away} @ {home}"

				if game not in data:
					data[game] = {}

				#if keep and prop in data[game]:
				#	continue

				#print(mainTab.text, prop, tab.text)

				if mainTab.text.lower() != "td scorer":
					if prop not in data[game]:
						data[game][prop] = {}

				if prop == "atgs":
					divs = await gameDiv.query_selector_all(".component-18")
					if "anytime goalscorer" not in divs[-1].text_all.lower():
						continue
					btns = await divs[-1].query_selector_all("div[role=button]")
					for btn in btns:
						odds = await btn.query_selector(".sportsbook-odds")
						if not odds:
							continue
						attrIdx = btn.attributes.index("aria-label")
						player = parsePlayer(btn.attributes[attrIdx+1].strip())
						data[game][prop][player] = odds.text.replace("\u2212", "-")
				elif tab.text.lower() == "td scorer":
					if "attd" not in data[game]:
						data[game]["attd"] = {}

					divs = await gameDiv.query_selector_all(".component-18")
					if len(divs) < 2:
						continue
					if "anytime td scorer" not in divs[-2].text_all.lower():
						continue
					btns = await divs[-2].query_selector_all("div[role=button]")
					for btn in btns:
						odds = await btn.query_selector(".sportsbook-odds")
						if not odds:
							continue
						attrIdx = btn.attributes.index("aria-label")
						player = parsePlayer(btn.attributes[attrIdx+1].strip())
						#print(player, odds.text)
						data[game]["attd"][player] = odds.text.replace("\u2212", "-")
				elif tab.text.lower() == "player not to score":
					btns = await gameDiv.query_selector_all("ul div[role=button]")
					for btn in btns:
						odds = await btn.query_selector(".sportsbook-odds")
						if not odds:
							continue
						attrIdx = btn.attributes.index("aria-label")
						player = parsePlayer(btn.attributes[attrIdx+1].strip())
						if player in data[game]["attd"] and "/" not in data[game]["attd"][player]:
							data[game]["attd"][player] += "/"+odds.text.replace("\u2212", "-")
				elif sport == "ncaab" or (sport == "nba" and skip == 1):
					players = await gameDiv.query_selector_all(".side-rail-name")
					odds = await gameDiv.query_selector_all(".sb-selection-picker__selection--focused")
					for player, odd in zip(players, odds):
						player = parsePlayer(player.text)
						spans = await odd.query_selector_all("span")
						if not spans:
							continue
						line = str(float(spans[0].text.replace("+", "")) - 0.5)
						data[game][prop][player] = {
							line: spans[-1].text
						}
				elif skip == 1 or alt:
					divs = await gameDiv.query_selector_all(".component-29")
					for div in divs:
						player = await div.query_selector("p")
						if not player:
							continue
						player = parsePlayer(player.text_all.lower().split(" alt ")[0].split(" points")[0].split(" rebounds")[0].split(" assists")[0].split(" three")[0].split(" blocks")[0].split(" steals")[0].split(" alternate")[0])

						if player not in data[game][prop]:
							data[game][prop][player] = {}

						outcomes = await div.query_selector_all("div[role=button]")
						for outcomeIdx in range(0, len(outcomes), skip):
							outcome = outcomes[outcomeIdx]
							spans = await outcome.query_selector_all("span")
							if len(spans) == 0:
								continue
							if skip == 1:
								try:
									line = str(float(spans[0].text.replace("+", "")) - 0.5)
								except:
									continue
							else:
								line = await outcome.query_selector(".sportsbook-outcome-cell__line")
								if not line:
									continue
								line = line.text

							odds = spans[-1].text.replace("\u2212", "-")
							data[game][prop][player][line] = odds
							if skip == 2:
								under = await outcomes[outcomeIdx+1].query_selector(".sportsbook-odds")
								if under:
									data[game][prop][player][line] += "/"+under.text.replace("\u2212", "-")
				else:
					rows = await gameDiv.query_selector_all(".sportsbook-table__body tr")
					for row in rows:
						tds = await row.query_selector_all("td")
						player = await row.query_selector("span")
						if not player:
							continue
						player = parsePlayer(player.text)

						if player not in data[game][prop]:
							try:
								data[game][prop][player] = {}
							except:
								continue

						line = await tds[0].query_selector(".sportsbook-outcome-cell__line")
						if not line:
							continue
						line = line.text
						odds = await tds[0].query_selector(".sportsbook-odds")
						under = await tds[1].query_selector(".sportsbook-odds")
						if line in data[game][prop][player]:
							over = data[game][prop][player][line]
							if "/" in over:
								continue
							if int(over) < int(odds.text.replace("\u2212", "-")):
								over = odds.text.replace("\u2212", "-")
							data[game][prop][player][line] = over+"/"+under.text.replace("\u2212", "-")
						else:
							data[game][prop][player][line] = odds.text.replace("\u2212", "-")
							if under:
								data[game][prop][player][line] += "/"+under.text.replace("\u2212", "-")


			if prop in ["saves"]:
				break
		
		with open(f"static/{sport}/draftkings.json", "w") as fh:
			json.dump(data, fh, indent=4)
	with open(f"static/{sport}/draftkings.json", "w") as fh:
		json.dump(data, fh, indent=4)
	browser.stop()


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("--bet365", action="store_true")
	parser.add_argument("--fd", action="store_true")
	parser.add_argument("--espn", action="store_true")
	parser.add_argument("--mgm", action="store_true")
	parser.add_argument("--dk", action="store_true")
	parser.add_argument("--keep", action="store_true")
	parser.add_argument("--team", "-t")
	parser.add_argument("--prop", "-p")
	parser.add_argument("--sport")
	parser.add_argument("--league")

	args = parser.parse_args()

	if args.bet365:
		uc.loop().run_until_complete(write365(args.sport, args.keep))

	if args.fd:
		uc.loop().run_until_complete(writeFD(args.sport, args.keep, args.league))

	if args.espn:
		uc.loop().run_until_complete(writeESPN(args.sport, args.keep))

	if args.mgm:
		uc.loop().run_until_complete(writeMGM(args.sport, args.keep))

	if args.dk:
		uc.loop().run_until_complete(writeDK(args.sport, args.keep, args.prop))
