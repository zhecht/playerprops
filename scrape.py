
import time
import json
import random
import unicodedata
import nodriver as uc
import argparse
import threading
import queue
from bs4 import BeautifulSoup as BS

from controllers.shared import convertSoccer, parsePlayer, strip_accents, convertMLBTeam, nested_dict, merge_dicts
from datetime import datetime, timedelta

q = queue.Queue()
lock = threading.Lock()

def convertCollege(team):
	team = strip_accents(team.lower())
	team = team.replace(".", "").replace("'", "").replace("(", "").replace(")", "").replace("-", " ")
	team = team.replace(" and ", "&").replace(" & ", "&")
	j = {
		"albany ny": "albany",
		"ark pine bluff": "arkansas pine bluff",
		"alcorn": "alcorn state",
		"boston": "boston university",
		"cal baptist": "california baptist",
		"central conn state": "central connecticut state",
		"central conn": "central connecticut state",
		"uconn": "connecticut",
		"coll charleston": "charleston",
		"charlotte 49ers": "charlotte",
		"citadel": "the citadel",
		"college of charleston": "charleston",
		"e kentucky": "eastern kentucky",
		"etsu": "east tennessee state",
		"florida international": "fiu",
		"gw colonials": "george washington",
		"gw revolutionaries": "george washington",
		"ga southern": "georgia southern",
		"grambling": "grambling state",
		"indiana u": "indiana",
		"purdue fort wayne": "ipfw",
		"iu indy": "iupui",
		"lafayette college": "lafayette",
		"long island": "liu",
		"long island university": "liu",
		"loyola il": "loyola chicago",
		"loyola md": "loyola maryland",
		"maryland eastern shore": "md eastern shore",
		"md east shore": "md eastern shore",
		"mcneese state": "mcneese",
		"miami fl": "miami",
		"mount saint marys": "mount st marys",
		"mt st marys": "mount st marys",
		"nebraska omaha": "omaha",
		"nc asheville": "unc asheville",
		"nc wilmington": "unc wilmington",
		"nicholls": "nicholls state",
		"north carolina central": "nc central",
		"nw state": "northwestern state",
		"penn": "pennsylvania",
		"pitt": "pittsburgh",
		"prairie view": "prairie view a&m",
		"queens nc": "queens university",
		"queens charlotte": "queens university",
		"nc greensboro": "unc greensboro",
		"saint bonaventure": "st bonaventure",
		"st johns": "saint johns",
		"saint josephs": "st josephs",
		"saint francis pa": "st francis pa",
		"stephen austin": "stephen f austin",
		"sfa": "stephen f austin",
		"md baltimore": "umbc",
		"sam houston": "sam houston state",
		"southern": "southern university",
		"s dakota state": "south dakota state",
		"saint thomas mn": "st thomas",
		"st thomas mn": "st thomas",
		"st thomas minnesota": "st thomas",
		"california san diego": "uc san diego",
		"louisiana monroe": "ul monroe",
		"ulm": "ul monroe",
		"massachusetts": "umass",
		"kansas city": "umkc",
		"tenn martin": "ut martin",
		"texas a&m corpus christi": "texas a&m cc",
		"texas a&m corpus": "texas a&m cc",
		"texas arlington": "ut arlington",
		"texas san antonio": "utsa",
		"txso": "texas southern",
		"western ky": "western kentucky",
		"wisc milwaukee": "milwaukee",
		"wisc green bay": "green bay",
		"wv mountaineers": "west virginia",
		"va commonwealth": "vcu"
	}
	if team.endswith(" u"):
		return team[:-2]
	elif team.endswith(" st"):
		team = team[:-3]+" state"
	elif team.startswith("n "):
		team = team.replace("n ", "north ")
	elif team.startswith("w "):
		team = team.replace("w ", "western ")
	elif team.startswith("e "):
		team = team.replace("e ", "eastern ")
	elif team.startswith("c "):
		team = team.replace("c ", "central ")
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
	elif t == "sweden":
		return "swe"
	elif t == "canada":
		return "can"
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
	if "blues" in team:
		return "stl"
	elif "capitals" in team:
		return "wsh"
	elif "kraken" in team:
		return "sea"
	elif "bruins" in team:
		return "bos"
	elif "panthers" in team:
		return "fla"
	elif "blackhawks" in team:
		return "chi"
	elif "utah hockey club" in team:
		return "utah"
	elif "canadiens" in team:
		return "mtl"
	elif "maple leafs" in team:
		return "tor"
	elif "rangers" in team:
		return "nyr"
	elif "penguins" in team:
		return "pit"
	elif "jets" in team:
		return "wpg"
	elif "oilers" in team:
		return "edm"
	elif "flames" in team:
		return "cgy"
	elif "canucks" in team:
		return "van"
	elif "avalanche" in team:
		return "col"
	elif "golden knights" in team:
		return "vgk"
	elif "devils" in team:
		return "nj"
	elif "kings" in team:
		return "la"
	elif "sabres" in team:
		return "buf"
	elif "red wings" in team:
		return "det"
	elif "islanders" in team:
		return "nyi"
	elif "senators" in team:
		return "ott"
	elif "stars" in team:
		return "dal"
	elif "wild" in team:
		return "min"
	elif "sharks" in team:
		return "sj"
	elif "lightning" in team:
		return "tb"
	elif "hurricanes" in team:
		return "car"
	elif "flyers" in team:
		return "phi"
	elif team == "predators":
		return "nsh"
	elif "blue jackets" in team:
		return "cbj"
	elif team == "sweden":
		return "swe"
	elif team == "canada":
		return "can"
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
		if "knicks" in team:
			return "ny"
		return "no"
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

data = {}
props = {}

async def get365Links(sport, keep):
	res = {}
	urls = ["https://www.oh.bet365.com/?_h=CfVWPHD5idsD_8dFdjBYcw%3D%3D&btsffd=1#/AC/B12/C20426855/D47/E120593/F47/N7/", "https://www.oh.bet365.com/?_h=CfVWPHD5idsD_8dFdjBYcw%3D%3D&btsffd=1#/AC/B12/C20426855/D47/E120591/F47/"]
	if sport == "nhl":
		props = ["atgs", "ast-o/u", "ast", "pts-o/u", "pts", "sog-o/u", "sog"]
		ids = ["E170348", "E170487", "E170602", "E170563", "E170601", "E170485", "E170600"]
		for prop, id in zip(props, ids):
			res[prop] = f"https://www.oh.bet365.com/?_h=p2hqPA35Yw8_tTyHi3apXA%3D%3D&btsffd=1#/AC/B17/C20836572/D43/{id}/F43/N6/"
	elif sport == "nba":
		props = ["pts-o/u", "pts-low", "pts-high", "pts", "ast-o/u", "ast", "reb-o/u", "reb", "stl-o/u", "to-o/u", "blk-o/u", "3ptm-o/u", "3ptm", "pts+ast-o/u", "pts+reb-o/u", "reb+ast-o/u", "pts+reb+ast-o/u", "stl+blk-o/u"]
		ids = ["E181378", "E181444", "E181445", "E181446", "E181379", "E181447", "E181380", "E181448", "E181381", "E181382", "E181383", "E181384", "E181449", "E181387", "E181388", "E181389", "E181390", "E181391"]
		for prop, id in zip(props, ids):
			res[prop] = f"https://www.oh.bet365.com/?_h=k5LhKHD5XJf0TyAaSmzA0A%3D%3D&btsffd=1#/AC/B18/C20604387/D43/{id}/F43/N43/"
	elif sport == "soccer":
		#urls = ["https://www.nj.bet365.com/?_h=RZ9RUwb5FXe3IH58lQH52Q%3D%3D&btsffd=1#/AC/B1/C1/D1002/G10236/J99/Q1/F^24/N5/", "https://www.nj.bet365.com/?_h=nElNnPL5dnUh0trxLWRXBw%3D%3D&btsffd=1#/AC/B1/C1/D1002/G177703/J99/Q1/F^24/N8/"]
		urls = ["https://www.nj.bet365.com/?_h=nElNnPL5dnUh0trxLWRXBw%3D%3D&btsffd=1#/AC/B1/C1/D1002/G177703/J99/Q1/F^24/N8/"]
		urls = ["https://www.nj.bet365.com"]
		urls = ["https://www.nj.bet365.com/?_h=lW0GCdv4-5qJllzV4d_gPw%3D%3D&btsffd=1#/AC/B1/C1/D1002/G177703/J99/Q1/F^24/N8/"]
	elif sport == "ncaab":
		urls = ["https://www.oh.bet365.com/?_h=aR_j-P35b_3WdK1mnHaXYQ%3D%3D&btsffd=1#/AC/B18/C21008290/D48/E1453/F10/N1/", "https://www.oh.bet365.com/?_h=aR_j-P35b_3WdK1mnHaXYQ%3D%3D&btsffd=1#/AC/B18/C21008290/D516/E181335/F516/N2/", "https://www.oh.bet365.com/?_h=aR_j-P35b_3WdK1mnHaXYQ%3D%3D&btsffd=1#/AC/B18/C21008290/D48/E928/F40/N4/"]
		#urls = ["https://www.oh.bet365.com/?_h=aR_j-P35b_3WdK1mnHaXYQ%3D%3D&btsffd=1#/AC/B18/C21008290/D516/E181335/F516/N2/", "https://www.oh.bet365.com/?_h=aR_j-P35b_3WdK1mnHaXYQ%3D%3D&btsffd=1#/AC/B18/C21008290/D48/E928/F40/N4/"]

	return res

def run365(sport):
	uc.loop().run_until_complete(write365(sport))

async def write365FromHTML(data, html, sport, prop):
	soup = BS(html, "lxml")
	#with open("out.html", "w") as fh:
	#	fh.write(html)
	for gameDiv in soup.select(".gl-MarketGroupPod"):
		game = gameDiv.find("div", class_="src-FixtureSubGroupButton_Text")
		sep = "v" if sport == "soccer" else "@"
		away, home = map(str, game.text.lower().split(f" {sep} "))
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
		elif sport == "ncaab":
			away = convertCollege(away)
			home = convertCollege(home)
		game = f"{away} {sep} {home}"

		players = gameDiv.find_all("div", class_="srb-ParticipantLabelWithTeam_Name")
		for idx, btn in enumerate(gameDiv.find_all("div", class_="gl-Participant_General")):
			label = btn.get("aria-label").lower().strip()
			odds = label.split(" ")[-1]
			p = label.split(" ")[0]

			if not odds:
				continue

			if not p or p == "@":
				player = parsePlayer(players[idx % len(players)].text)
				line = str(float(btn.parent.find("div").text) - 0.5)
				if line in data[game][prop][player]:
					ou = data[game][prop][player][line]
					under = ""
					over = ou.split("/")[0]
					if int(odds) > int(over):
						over = odds
					if "/" in ou:
						over += "/"+ou.split("/")[-1]
					odds = over

				data[game][prop][player][line] = odds
			else:
				player = parsePlayer(label.split("  ")[0].split(p+" ")[-1])
				if p == "first":
					data[game]["fgs"][player] = odds
				elif p == "anytime":
					data[game]["atgs"][player] = odds
				else:
					line = label.split("  ")[-1].split(" @ ")[0]
					if p == "over":
						data[game][prop][player][line] = odds
					else:
						over = str(data[game][prop][player][line])
						data[game][prop][player][line] = over+"/"+odds

async def write365(sport):
	browser = await uc.start(no_sandbox=True)
	file = f"static/{sport}/bet365.json"
	while True:
		data = nested_dict()
		(game, url) = q.get()
		prop = game
		if url is None:
			q.task_done()
			break

		page = await browser.get(url)
		await page.wait_for(selector=".srb-MarketSelectionButton-selected")

		prefix = ""
		if "1st half" in prop:
			prefix = "1h_"
		elif "2nd half" in prop:
			prefix = "2h_"

		skip = 1
		if prop.split("-")[-1] in ["o/u", "low", "high"]:
			skip = 2
			prop = prop.replace("-o/u", "").replace("-low", "").replace("-high", "")

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
			if prop in ["double_double", "triple_double"]:
				continue
		elif prop == "both teams to score":
			prop = "btts"
		elif prop == "alternative total goals":
			prop = "total"
		elif "spread" in prop:
			if prop == "alternative spread":
				alt = False
			prop = "spread"
		elif prop.endswith("team totals"):
			prop = "team_total"
		elif "totals" in prop or prop == "alternative total":
			prop = "total"
		elif prop == "1st half" or prop == "game lines":
			prop = "lines"
		elif "corners" in prop:
			if prop in ["team corners", "asian corners"]:
				prop = prop.replace(" ", "_")
			else:
				continue
		elif sport == "soccer":
			if prop in ["goalscorers", "player to score or assist", "player passes - under", "player to be booked"]:
				continue
			prop = prop.replace("player ", "").replace(" over/under", "").replace("goalkeeper saves", "saves")
			prop = f"player_{prop}"
			if prop not in []:
				#continue
				pass
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
			for c in ["src-FixtureSubGroupWithShowMore_Closed", "src-FixtureSubGroup_Closed", "src-HScrollFixtureSubGroupWithBottomBorder_Closed", "suf-CompetitionMarketGroupButton_Text[aria-expanded=false]"]:
				divs = await page.query_selector_all("."+c)

				for div in divs:
					await div.scroll_into_view()
					await div.mouse_click()
					#time.sleep(round(random.uniform(0.9, 1.25), 2))
					time.sleep(round(random.uniform(0.4, 0.9), 2))

			links = await page.query_selector_all(".msl-ShowMore_Link")

			for el in links:
				await el.scroll_into_view()
				await el.mouse_click()
				time.sleep(round(random.uniform(0.9, 1.25), 2))

		html = await page.get_content()
		await write365FromHTML(data, html, sport, prop)
		updateData(file, data)
		q.task_done()

	browser.stop()

def getCountry(league):
	if league == "liga-profesional":
		return "argentina"
	elif league == "a-league":
		return "australia"
	elif league == "austrian-bundesliga":
		return "austria"
	elif league == "premyer-liqa":
		return "azerbaijan"
	elif league == "first-division-a":
		return "belgium"
	elif league == "1-hnl":
		return "croatia"
	elif league == "cypriot-1st-division":
		return "cyprus"
	elif league == "first-league":
		return "czech-republic"
	elif league in ["premier-league", "league-championship", "league-one", "league-two"]:
		return "england"
	elif league in ["ligue-1", "ligue-2"]:
		return "france"
	elif "bundesliga" in league:
		return "germany"
	elif league == "greek-super-league":
		return "greece"
	elif league == "liga-nacional":
		return "guatemala"
	elif league == "nb-1":
		return "hungary"
	elif league == "israeli-premier-league":
		return "israel"
	elif league.startswith("serie"):
		return "italy"
	elif league == "maltese-premier-league":
		return "malta"
	elif league == "eredivisie":
		return "netherlands"
	elif league == "nicaragua-primera":
		return "nicaragua"
	elif league == "northern-irish-premiership":
		return "northern-ireland"
	elif league == "ekstraklasa":
		return "poland"
	elif league == "primeira-liga":
		return "portugal"
	elif league == "liga-i":
		return "romania"
	elif league == "premiership":
		return "scotland"
	elif league == "serbian-super-league":
		return "serbia"
	elif league == "slovakian-superliga":
		return "slovakia"
	elif league == "psl":
		return "south-africa"
	elif league in ["la-liga", "la-liga-2"]:
		return "spain"
	elif league == "swiss-super-league":
		return "switzerland"
	elif league == "super-lig":
		return "turkey"
	elif league == "ukrainian-premier-league":
		return "ukraine"
	elif league == "wales-premiership":
		return "wales"
	return league

async def getESPNLinks(sport, tomorrow):
	if not sport:
		sport = "nfl"

	url = "https://espnbet.com/sport/football/organization/united-states/competition/nfl"
	if sport == "ncaaf":
		url = "https://espnbet.com/sport/football/organization/united-states/competition/ncaaf"
	elif sport == "nhl":
		url = "https://espnbet.com/sport/hockey/organization/united-states/competition/nhl"
	elif sport in ["nba", "ncaab"]:
		url = f"https://espnbet.com/sport/basketball/organization/united-states/competition/{sport}"

	browser = await uc.start(no_sandbox=True)
	page = await browser.get(url)

	teams = []
	try:
		await page.wait_for(selector="article")
		teams = await page.query_selector_all("article .text-primary")
	except:
		pass

	games = {}
	for i in range(0, len(teams), 2):
		div = teams[i].parent.parent.parent.parent.parent.parent
		if "live" in div.text_all.lower():
			continue
		if not tomorrow and sport != "nfl" and "Today" not in div.text_all:
			break
			pass
		if tomorrow and datetime.strftime(datetime.now() + timedelta(days=1), "%b %d") not in div.text_all:
			break

		if sport == "nfl":
			away = convert365Team(teams[i].text)
			home = convert365Team(teams[i+1].text)
		elif sport == "nhl":
			away = convert365NHLTeam(teams[i].text)
			home = convert365NHLTeam(teams[i+1].text)
		elif sport == "nba":
			away = convert365NBATeam(teams[i].text)
			home = convert365NBATeam(teams[i+1].text)
		elif sport == "soccer":
			away = convertSoccer(teams[i].text)
			home = convertSoccer(teams[i+1].text)
		else:
			away = teams[i].text.lower()
			if away.startswith("("):
				away = away.split(") ")[-1]
			away = convertCollege(away)
			home = teams[i+1].text.lower()
			if home.startswith("("):
				home = home.split(") ")[-1]
			home = convertCollege(home)
		sep = "v" if sport == "soccer" else "@"
		game = f"{away} {sep} {home}"

		eventId = div.id.split("|")[1]
		#print(game, f"{url}/event/{eventId}")
		games[game] = f"{url}/event/{eventId}"

	browser.stop()
	return games

def runESPN(sport):
	uc.loop().run_until_complete(writeESPN(sport))

async def writeESPNFromHTML(data, html, sport, game, playersMap):
	soup = BS(html, "lxml")

	for detail in soup.find_all("details"):
		prop = detail.find("h2").text.lower()
		skip = 1
		prop = prop.replace("-", " ")
		if "o/u" in prop:
			skip = 3
			if sport == "nba" and " and " not in prop:
				skip = 2
			prop = prop.replace(" o/u", "")

		if prop.startswith("first quarter"):
			continue

		prop = prop.replace("player total ", "").replace("player ", "").replace(" o/u", "").replace("to record a ", "").replace(", ", "+").replace(" and ", "+").replace("points", "pts").replace("rebounds", "reb").replace("assists", "ast").replace("blocks", "blk").replace("steals", "stl").replace("3-pointers made", "3ptm").replace("3-pointers attempted", "3pta").replace("free throws made", "ftm").replace("field goals made", "fgm").replace("field goals attempted", "fga").replace("first goalscorer", "fgs").replace("turnovers", "to").replace("shots on goal", "sog").replace("goals", "atgs").replace(" + ", "+").replace(" ", "_")
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
		elif prop == "3_pointers_made":
			prop = "3ptm"

		if sport == "nhl" and prop in ["atgs", "ast"]:
			skip = 3
		elif sport == "nhl" and prop in ["pts", "sog"]:
			skip = 2

		if prop in ["fgs"]:
			for btn in detail.find_all("button"):
				player = parsePlayer(btn.find("span").text)
				last = player.split(" ")
				p = player.split(" ")[0][0]+" "+last[-1]
				playersMap[p] = player
				data[game][prop][player] = btn.find_all("span")[-1].text.replace("Even", "+100")
		elif skip == 1:
			if not detail.find("tr"):
				continue
			lines = [str(float(x.text.replace("+", "")) - 0.5) for x in detail.find("tr").find_all("th")]
			for row in detail.find("tbody").find_all("tr"):
				player = parsePlayer(row.find("th").text)
				for idx, td in enumerate(row.find_all("td")):
					if td.text == "--":
						continue
					data[game][prop][player][lines[idx]] = td.text.replace("Even", "+100")
		else:
			btns = detail.find_all("button")
			for idx in range(0, len(btns), skip):
				if skip == 2:
					player = btns[idx].find_previous("header").text.lower()
				else:
					player = btns[idx].text.lower().split(" total")[0]

				if sport not in ["ncaab", "nhl"] or len(player.split(" ")[0]) < 3:
					last = player.split(" ")
					player = player.split(" ")[0][0]+" "+last[-1]
				if player in playersMap:
					player = playersMap[player]
				player = parsePlayer(player)
				i = idx
				if skip == 3:
					i += 1

				try:
					o = btns[i].find_all("span")[-1].text.replace("Even", "+100")
					u = btns[i+1].find_all("span")[-1].text.replace("Even", "+100")
				except:
					print(game, prop, player)

				if prop in ["atgs"]:
					data[game][prop][player] = f"{o}/{u}"
				else:
					try:
						line = btns[i].find_all("span")[-2].text.split(" ")[-1]
					except:
						continue
					if line in data[game][prop][player]:
						over = data[game][prop][player][line].split("/")[0]
						if int(over) > int(o):
							o = over
					data[game][prop][player][line] = f"{o}/{u}"

async def writeESPN(sport):
	browser = await uc.start(no_sandbox=True)
	file = f"static/{sport}/espn.json"
	while True:
		data = nested_dict()
		(game, url) = q.get()
		#print(url)
		if url is None:
			q.task_done()
			break
		page = await browser.get(url)
		try:
			await page.wait_for(selector="div[data-testid='away-team-card']")
		except:
			q.task_done()
			continue

		tabs = await page.query_selector_all("button[data-testid=tablist-carousel-tab]")
		for tabIdx in range(len(tabs)):
			arr = ["player props"]
			if sport in ["soccer"]:
				arr.append("lines")
				arr.append("game props")
			if sport in ["ncaaf", "nfl"]:
				arr.append('td scorers')

			if tabs[tabIdx].text_all.lower() not in arr:
				continue

			await tabs[tabIdx].click()
			#print(tabIdx, tabs[tabIdx].text_all)
			await page.wait_for(selector=f"button[data-testid=tablist-carousel-tab]:nth-of-type({tabIdx+1})[aria-selected=true]")
			time.sleep(0.75)
			playersMap = {}
			html = await page.get_content()
			await writeESPNFromHTML(data, html, sport, game, playersMap)
			continue

			details = await page.query_selector_all("details")
			players = {}
			fullProp = ""
			for detailIdx in range(len(details)):
				detail = details[detailIdx]
				#await detail.scroll_into_view()
				prop = detail.children[0].children[0]
				try:
					prop = prop.text.lower()
					fullProp = prop
				except:
					print(game, "skip")
					continue

				#print(prop)

				prefix = ""
				hp = ""
				if "half" in prop:
					hp = "h"
				elif "period" in prop:
					hp = "p"
				elif "quarter" in prop:
					hp = "q"

				if "first" in prop or "1st" in prop:
					prefix = f"1{hp}_"
				elif "second" in prop or "2nd" in prop:
					prefix = f"2{hp}_"
				elif "third" in prop or "3rd" in prop:
					prefix = f"3{hp}_"
				elif "fourth" in prop or "4th" in prop:
					prefix = f"4{hp}_"

				skip = 2
				columns = True
				player = mainLine = ""

				if "moneyline" in prop:
					if "3-way" in prop:
						prop = "3ml"
						skip = 3
					else:
						prop = "ml"
				elif prop in ["match spread", "2-way handicap", "game spread", "1st half spread", "1st period - spread"]:
					prop = "spread"
				elif prop in ["total points", "total goals", "1st half total", "1st period - total goals"]:
					prop = "total"
				elif sport == "nhl" and prop.endswith("total goals (excl ot)"):
					team = convert365NHLTeam(prop.split(" total ")[0])
					if team == game.split(" @ ")[0]:
						prop = "away_total"
					elif team == game.split(" @ ")[-1]:
						prop = "home_total"
					else:
						continue
				elif prop == "to score a touchdown":
					prop = "attd"
					skip = 3
				elif prop == "player total touchdowns":
					prop = "attd"
					skip = 1
				elif "first goalscorer" in prop:
					prop = "fgs"
					skip = 1
				elif prop == "anytime goalscorer" or prop == "anytime goal scorer":
					if sport == "soccer":
						continue
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
				elif sport == "soccer" and tabs[tabIdx].text_all.lower() == "game props" and (prop.endswith("total shots on target") or prop.endswith("total shots") or prop.endswith("total tackles") or prop.endswith("total passes")):
					skip = 1
					suffix = prop.split(" total ")[-1].replace(" ", "_")

					if convertSoccer(prop.split(" total ")[0]) == game.split(" v ")[0]:
						prop = "home"
					elif convertSoccer(prop.split(" total ")[0]) == game.split(" v ")[-1]:
						prop = "away"
					else:
						continue

					prop = f"{prop}_{suffix}"
				elif sport == "soccer" and tabs[tabIdx].text_all.lower() == "player props":
					if (prop.endswith("total shots on target") or prop.endswith("total shots") or prop.endswith("total tackles") or prop.endswith("total passes")):
						player = parsePlayer(prop.split(" total ")[0])
						prop = prop.split(" total ")[-1].replace(" ", "_")
						prop = f"player_{prop}"
						skip = 1
					else:
						continue
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
					skip = 1
				elif prop == "player total rebounds":
					prop = "reb"
					skip = 1
				elif prop == "player total assists":
					prop = "ast"
					skip = 1
					if sport in ["nhl"]:
						skip = 3
				elif sport in ["nba", "ncaab"] and prop.startswith("player"):
					if "first" in prop or "1st" in prop:
						continue
					ou = False
					if "o/u" in prop:
						ou = True
					prop = prop.replace("player total ", "").replace(" o/u", "").replace("player to record a ", "").replace(", ", "+").replace(" and ", "+").replace("points", "pts").replace("rebounds", "reb").replace("assists", "ast").replace("blocks", "blk").replace("steals", "stl").replace("3-pointers made", "3ptm").replace("3-pointers attempted", "3pta").replace("free throws made", "ftm").replace("field goals made", "fgm").replace("field goals attempted", "fga").replace("turnovers", "to").replace(" + ", "+").replace(" ", "_")
					if ou and sport == "ncaab" or (sport == "nba" and ("+" in prop or prop in ["to", "3ptm"])):
						skip = 3
					elif ou:
						skip = 2
					elif sport in ["ncaab", "nba"]:
						skip = 1

					if prop in ["3pta", "fgm", "fga", "ftm"]:
						continue
				elif sport == "ncaab" and " total " in prop:
					if "/" in prop:
						continue
					team = convertCollege(prop.split(" total ")[0])
					if team == game.split(" @ ")[0]:
						prop = "away_total"
					elif team == game.split(" @ ")[1]:
						prop = "home_total"
					else:
						columns = False
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
					if "1st half" in prop or "1st quarter" in prop or "range" in prop or "(excl ot)" in prop:
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

				prop = f"{prefix}{prop}"

				if prop == "1_fgs":
					prop = "fgs"

				if prop in ["1h_attd", "2h_attd"]:
					continue

				if prop == "ast+reb":
					prop = "reb+ast"

				#print(prop, skip, fullProp)

				if "open" not in detail.attributes:
					summary = detail.children[0]
					await summary.click()
					time.sleep(0.5)
					#await detail.wait_for(selector="button")

				data.setdefault(game, {})

				if prop not in data[game]:
					data[game][prop] = {}

				# seeAllLines
				if sport == "ncaab" and prop in ["total", "spread"]:

					btns = await detail.query_selector_all("button")
					if btns[-1].text == "See All Lines":
						await btns[-1].click()
						await page.wait_for(selector="article")
						modal = await page.query_selector("article")
						btns = await modal.query_selector_all("button")
						for i in range(0, len(btns), 2):
							if "pk" in btns[i].text_all:
								continue
							try:
								line = str(float(btns[i].text_all.split(" ")[-2]))
							except:
								continue
							ou = f"{btns[i].text_all.split(' ')[-1]}/{btns[i+1].text_all.split(' ')[-1]}"
							data[game][prop][line] = ou.replace("Even", "+100")

						btn = await page.query_selector(".modal--see-all-lines button")
						await btn.click()
						continue

				sections = [detail]
				if prop == "tackles+ast" or prop == "int":
					sections = await detail.query_selector_all("div[aria-label='']")

				for section in sections:
					btns = await section.query_selector_all("button")
					
					for btnIdx in range(0, len(btns), skip):
						if btns[btnIdx].text == "See All Lines":
							continue
						if "disabled" in btns[btnIdx].attributes and skip != 3:
							continue
						if "carousel-arrow" in btns[btnIdx].attributes:
							continue
						ou = ""
						i = btnIdx
						if sport != "nfl" and skip == 3 and prop not in ["3ml"]:
							i += 1
						if i >= len(btns):
							continue

						try:
							ou = btns[i].text_all.split(" ")[-1]
						except:
							continue
						if skip != 1:
							try:
								ou += "/"+btns[i+1].text_all.split(" ")[-1]
							except:
								pass

						#print(prop, ou)

						ou = ou.replace("Even", "+100")
						if "ml" in prop or prop in ["btts", "dnb"]:
							if prop == "3ml":
								under = await btns[i+2].query_selector_all("span")
								data[game][prop] = ou+"/"+under[1].text
							else:
								data[game][prop] = ou
						elif "ftd" in prop:
							player = await btns[btnIdx].query_selector("span")
							player = parsePlayer(player.text)
							last = player.split(" ")
							try:
								player = player.split(" ")[0][0]+" "+last[-1]
							except:
								continue
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
						elif sport == "nhl" and prop in ["atgs", "fgs"]:
							player = btns[btnIdx].text.split(" Total")[0]
							player = parsePlayer(player)
							if prop == "atgs":
								last = player.split(" ")
								p = player.split(" ")[0][0]+" "+last[-1]
								players[p] = player
							data[game][prop][player] = ou
						elif sport in ["nfl"] and skip == 1 or (sport in ["ncaab", "nba"] and skip == 1 and columns):
							#print(btns[btnIdx])
							player = btns[btnIdx].parent.parent.children[0]

							if not player:
								continue
							player = parsePlayer(player.text)
							if sport not in ["ncaab"]:
								last = player.split(" ")
								player = player.split(" ")[0][0]+" "+last[-1]
							if player not in data[game][prop]:
								data[game][prop][player] = {}
							line = btns[btnIdx].parent.attributes
							if "id" not in line:
								continue
							idIdx = line.index("id")
							line = str(float(line[idIdx+1].split("-")[-1].replace("+","")) - 0.5)
							#print(prop, player, line, ou)
							data[game][prop][player][line] = ou
						elif skip == 2:
							player = btns[btnIdx].parent.parent.parent.parent.children[0].children[0].text
							player = parsePlayer(player)
							if sport not in ["ncaab"]:
								last = player.split(" ")
								player = player.split(" ")[0][0]+" "+last[-1]
							if sport in ["nhl"] and player in players:
								player = players[player]
							line = btns[btnIdx].text_all.split(" ")[1]
							#print(prop, player, line, ou)
							if player not in data[game][prop]:
								data[game][prop][player] = {}
							data[game][prop][player][line] = ou
						elif skip == 3:
							player = btns[btnIdx].text_all.lower().split(" total ")[0]
							player = parsePlayer(player)
							if sport not in ["ncaab", "nhl"]:
								last = player.split(" ")
								player = player.split(" ")[0][0]+" "+last[-1]

							#print(prop, player, btns[btnIdx+1].text_all)
							line = btns[btnIdx+1].text_all.split(" ")[1]
							ou = btns[btnIdx+1].text_all.split(" ")[-1]+"/"+btns[btnIdx+2].text_all.split(" ")[-1]
							#print(prop, player, line, ou)
							if player not in data[game][prop]:
								data[game][prop][player] = {}
							data[game][prop][player][line] = ou.replace("Even", "+100")
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
									if "spread" in prop:
										line = line.split(" ")[-1].replace("+", "")
									elif "+" in line:
										line = str(float(line.replace("+", "")) - 0.5)
									else:
										line = line.split(" ")[1]
								except:
									continue

							if "total" in prop or "spread" in prop:
								data[game][prop][line] = ou
								continue

							if skip == 2 and prop not in ["tackles+ast"]:
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

							if player in players:
								player = players[player]
							if player not in data[game][prop]:
								data[game][prop][player] = {}

							if prop in ["double_double", "triple_double"]:
								data[game][prop][player] = ou
							elif sport == "nfl" and line in data[game][prop][player]:
								try:
									over = int(data[game][prop][player][line])
								except:
									continue
								if "/" in ou and over > int(ou.split("/")[0]):
									data[game][prop][player][line] = str(over)+"/"+ou.split("/")[-1]
								else:
									data[game][prop][player][line] = ou
							else:
								data[game][prop][player][line] = ou

		updateData(file, data)
		q.task_done()

	browser.stop()

async def getMGMLinks(sport=None):
	if not sport:
		sport = "nfl"
	url = "https://sports.mi.betmgm.com/en/sports/football-11/betting/usa-9/nfl-35"
	urls = []
	if sport == "ncaaf":
		url = "https://sports.mi.betmgm.com/en/sports/football-11/betting/usa-9/college-football-211"
	elif sport == "nhl":
		url = "https://sports.mi.betmgm.com/en/sports/hockey-12/betting/usa-9/nhl-34"
	elif sport == "nba":
		url = "https://sports.mi.betmgm.com/en/sports/basketball-7/betting/usa-9/nba-6004"
	elif sport == "ncaab":
		url = "https://sports.mi.betmgm.com/en/sports/basketball-7/betting/usa-9/ncaa-264"
	elif sport == "soccer":
		url = "https://sports.mi.betmgm.com/en/sports/soccer-4/betting/"
		
		l = ["argentina-38", "australia-60", "azerbaijan-77", "belgium-35", "bolivia-44", "colombia-45", "costa-rica-104", "croatia-50", "cyprus-58", "czech-republic-12", "ecuador-110", "europe-7", "england-14", "france-16", "germany-17", "guatemala-127", "honduras-132", "hungary-19", "india-134", "israel-62", "italy-20", "malta-159", "mexico-43", "netherlands-36", "northern-ireland-65", "poland-22", "portugal-37", "romania-24", "scotland-26", "serbia-231", "slovakia-51", "south-africa-197", "spain-28", "switzerland-30", "turkey-31", "ukraine-53"]
		#l = l[l.index("europe-7"):]
		urls = [url+x for x in l]

	if not urls:
		urls = [url]

	browser = await uc.start(no_sandbox=True)
	games = {}
	for url in urls:
		page = await browser.get(url)
		await page.wait_for(selector=".grid-info-wrapper")
		ps = await page.query_selector_all(".participant")

		for pIdx in range(0, len(ps), 2):
			if sport == "ncaab":
				link = ps[pIdx].parent.parent.parent.parent.parent.parent.parent
			else:
				link = ps[pIdx].parent.parent.parent.parent.parent.parent.parent.parent.parent
			t = [x for x in link.parent.parent.children if x.tag != "#comment"][0]
			if "starting" not in t.text_all.lower() and "today" not in t.text_all.lower():
				continue

			away = ps[pIdx].text_all.strip()
			home = ps[pIdx+1].text_all.strip()
			if sport.startswith("ncaa"):
				away = convertCollege(away)
				home = convertCollege(home)
			elif sport == "nhl":
				away = convertMGMNHLTeam(away)
				home = convertMGMNHLTeam(home)
			elif sport == "nba":
				away = convertMGMNBATeam(away)
				home = convertMGMNBATeam(home)
			elif sport == "soccer":
				away = convertSoccer(away)
				home = convertSoccer(home)
			else:
				away = convertMGMTeam(away)
				home = convertMGMTeam(home)

			sep = "v" if sport == "soccer" else "@"
			game = f"{away} {sep} {home}"
			games[game] = link.href+"?market=-1"

	browser.stop()
	return games

def runMGM(sport):
	uc.loop().run_until_complete(writeMGM(sport))

async def writeMGMFromHTML(data, html, sport, game):
	soup = BS(html, "lxml")
	panels = soup.find_all("ms-option-panel")

	for panel in panels:
		prop = panel.find("span", class_="market-name").text.lower()
		if prop == "anytime goalscorer":
			prop = "atgs"
		elif prop == "first goalscorer":
			prop = "fgs"
		elif prop == "player shots":
			prop = "sog"
		elif prop == "player assists":
			prop = "ast"
		elif prop == "player points":
			prop = "pts"

		lines = panel.find_all("div", class_="name")
		odds = panel.find_all("div", class_="value")
		if prop == "game lines":
			data[game]["ml"] = odds[2].text+"/"+odds[-1].text
			line = lines[0].text.strip().replace("+", "")
			data[game]["spread"][line] = odds[0].text+"/"+odds[3].text
			line = lines[1].text.strip().replace("+", "").split(" ")[-1]
			data[game]["total"][line] = odds[1].text+"/"+odds[4].text
		elif prop in ["fgs", "atgs"]:
			for player, o in zip(lines, odds):
				player = parsePlayer(player.text.strip())
				data[game][prop][player] = o.text
		else:
			players = panel.find_all("div", class_="player-props-player-name")
			for idx, player in enumerate(players):
				player = parsePlayer(player.text.strip())
				line = lines[idx*2].text.strip().split(" ")[-1]
				data[game][prop][player][line] = odds[idx*2].text+"/"+odds[idx*2+1].text

async def writeMGM(sport):
	file = f"static/{sport}/mgm.json"
	browser = await uc.start(no_sandbox=True)
	while True:
		data = nested_dict()
		
		(game, url) = q.get()
		if url is None:
			q.task_done()
			break

		page = await browser.get("https://sports.mi.betmgm.com"+url)
		await page.wait_for(selector=".event-details-pills-list")
		#tabs = await page.query_selector_all(".event-details-pills-list button")
		#pages = ["All"]
		#if sport == "soccer":
			#pages = ["", "Players", "Corners"]
		#	pages = ["", "Corners"]

		#await tabs[-1].click()

		groups = await page.query_selector_all(".option-group-column")
		for groupIdx, group in enumerate(groups):
			if not group:
				continue

			panels = [x for x in group.children if x.tag != "#comment"]
			for panelIdx, panel in enumerate(panels):
				prop = [x for x in panel.children if x.tag != "#comment"][0]
				if not prop:
					continue
				prop = prop.text_all.lower()

				multProps = False
				alt = False
				if prop == "first td scorer":
					prop = "ftd"
				elif prop == "anytime td scorer":
					prop = "attd"
				elif prop == "anytime goalscorer" or prop == "goalscorers":
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
				elif prop == "totals":
					prop = "total"
					if sport == "nhl":
						multProps = True
				elif prop.endswith(": total points") or (sport == "nhl" and ": goals" in prop):
					#print(prop, convertMGMNHLTeam(prop.split(":")[0]))
					if sport == "nhl":
						team = convertMGMNHLTeam(prop.split(":")[0])
					else:
						team = convertCollege(prop.split(":")[0].lower())
					if team == game.split(" @ ")[0]:
						prop = "away_total"
					elif team == game.split(" @ ")[-1]:
						prop = "home_total"
					else:
						continue
				elif prop.endswith(": first touchdown scorer"):
					prop = "team_ftd"
				elif prop in ["rushing props", "defensive props", "quarterback props", "receiving props", "kicking props"]:
					multProps = True
				elif sport == "soccer" and prop.endswith("total goals") and ":" not in prop:
					team = convertSoccer(prop.split(" - ")[0])
					if team == game.split(" v ")[0]:
						prop = "home_total"
					elif team == game.split(" v ")[1]:
						prop = "away_total"
					elif prop == "total goals":
						prop = "total"
					else:
						continue
					multProps = True
				elif prop.endswith("total corners"):
					team = convertSoccer(prop.split(" - ")[0])
					if prop == "total corners":
						prop = "corners"
					elif team == game.split(" v ")[0]:
						prop = "home_corners"
					elif team == game.split(" v ")[1]:
						prop = "away_corners"
					else:
						continue
					multProps = True
				elif prop == "draw no bet":
					prop = "dnb"
					multProps = True
					continue
				elif prop.startswith("alternate player"):
					prop = prop.split(" ")[-1].replace("points", "pts").replace("rebounds", "reb").replace("assists", "ast").replace("three-pointers", "3ptm")
					alt = True
				else:
					continue

				if prop == "pass_+_rush_yd":
					prop = "pass+rush"

				#if "total" not in prop:
				#	continue

				up = await panel.query_selector("svg[title=theme-up]")
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
					await show.scroll_into_view()
					time.sleep(0.75)


				html = await page.get_content()
				await writeMGMFromHTML(data, html, sport, game)
				continue

				if alt:
					lis = await panel.query_selector_all("li")
					for liIdx, li in enumerate(lis):
						#a = await li.query_selector("a")
						await li.click()
						try:
							await page.wait_for(selector=f".option-group-column:nth-child({groupIdx+1}) ms-option-panel:nth-child({panelIdx+1}) li:nth-child({liIdx+1}).ds-tab-selected")
						except:
							continue

						line = str(float(li.text.replace("+", "")) - 0.5)
						if prop not in data:
							data[prop] = {}

						players = await panel.query_selector_all(".attribute-key")
						odds = await panel.query_selector_all("ms-option")
						for playerIdx, player in enumerate(players):
							player = parsePlayer(player.text.split(" (")[0].strip())
							if player not in data[prop]:
								data[prop][player] = {}
							over = await odds[playerIdx].query_selector(".value")
							if not over:
								continue
							if line not in data[prop][player]:
								data[prop][player][line] = over.text

				elif multProps:
					mainProp = prop
					lis = await panel.query_selector_all("li")
					for liIdx, li in enumerate(lis):
						await li.click()
						try:
							await page.wait_for(selector=f".option-group-column:nth-child({groupIdx+1}) ms-option-panel:nth-child({panelIdx+1}) li:nth-child({liIdx+1}).ds-tab-selected")
							# from .active
						except:
							continue
						if sport == "soccer" or mainProp in ["total"]:
							prefix = ""
							if "half" in li.text.lower():
								if "1st" in li.text:
									prefix = "1h_"
								elif "2nd" in li.text:
									prefix = "2h_"
							elif "period" in li.text.lower():
								if "1st" in li.text:
									prefix = "1p_"
								elif "2nd" in li.text:
									prefix = "2p_"
								elif "3rd" in li.text:
									prefix = "3p_"
							prop = f"{prefix}{mainProp}"
						else:
							prop = li.text.lower().strip().replace("receiving", "rec").replace("rushing", "rush").replace("passing", "pass").replace("yards", "yd").replace("receptions made", "rec").replace("reception", "rec").replace("extra points made", "xp").replace("points", "pts").replace("field goals made", "fgm").replace("points", "pts").replace("longest pass completion", "longest_pass").replace("completions", "cmp").replace("completion", "cmp").replace("attempts", "att").replace("touchdowns", "td").replace("assists", "ast").replace("defensive interceptions", "def_int").replace("interceptions thrown", "int").replace(" ", "_")
							if prop == "rush+rec_yd":
								prop = "rush+rec"
							elif prop == "pass+rush_yd":
								prop = "pass+rush"

							if "1st" in prop:
								continue

						if prop not in data:
							data[prop] = {}

						players = await panel.query_selector_all(".attribute-key")
						odds = await panel.query_selector_all("ms-option")
						for playerIdx, player in enumerate(players):
							#print(prop, player.text)
							over = await odds[playerIdx*2].query_selector(".value")
							under = await odds[playerIdx*2+1].query_selector(".value")
							if not over:
								continue
							ou = over.text
							if under:
								ou += "/"+under.text
							if sport == "soccer" or mainProp in ["total"]:
								line = str(float(player.text.strip().replace(",", ".")))
								data[prop][line] = ou
							else:
								player = parsePlayer(player.text.split(" (")[0].strip())
								if player not in data[prop]:
									data[prop][player] = {}
								line = await odds[playerIdx*2].query_selector(".name")
								if not line:
									continue
								line = line.text.strip().split(" ")[-1]
							
								data[prop][player][line] = ou

				elif sport == "nba":
					players = await panel.query_selector_all(".attribute-key")
					odds = await panel.query_selector_all(".option-pick")
					for playerIdx, player in enumerate(players):
						player = parsePlayer(player.text.split(" (")[0].strip())
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
								data[prop][player] = ou
							else:
								if player not in data[prop]:
									data[prop][player] = {}
								data[prop][player][line] = ou
				elif prop in ["pts", "ast", "reb", "sog", "bs", "3ptm", "saves"]:
					players = await panel.query_selector_all(".attribute-key")
					odds = await panel.query_selector_all(".option")
					for playerIdx, player in enumerate(players):
						player = parsePlayer(player.text.split(" (")[0].strip())
						over = odds[playerIdx*2]
						under = odds[playerIdx*2+1]
						try:
							line = over.text_all.strip().split(" ")[1]
							ou = over.text_all.split(" ")[-1]+"/"+under.text_all.split(" ")[-1]
						except:
							continue
						data[prop][player] = {
							line: ou
						}
				else:
					odds = await panel.query_selector_all(".option")
					players = await panel.query_selector_all(".attribute-key")
					skip = 1
					for playerIdx in range(0, len(players), skip):
						player = players[playerIdx]
						#print(prop, player)
						if prop in ["atgs", "attd", "2+td", "3+td", "ftd", "fgs", "team_ftd", "team_fgs"]:
							odd = odds[playerIdx]
						else:
							#print(prop, player)
							odd = odds[playerIdx*2]
						try:
							val = await odd.query_selector(".value")
						except:
							continue
						if not val:
							continue

						if "total" in prop:
							line = str(float(player.text.strip()))
							try:
								under = await odds[playerIdx*2+1].query_selector(".value")
								if not under:
									continue
							except:
								continue
							ou = val.text+"/"+under.text
							data[prop][line] = ou
							continue

						player = parsePlayer(player.text.split(" (")[0].strip())
						if "defense" in player and sport == "nfl":
							player = player.split(" ")[0]

						if prop in ["attd", "ftd", "2+td", "3+td", "team_ftd", "atgs", "fgs"]:
							ou = val.text
							if sport == "soccer":
								try:
									val = await odds[playerIdx*3].query_selector(".value")
									if not val:
										continue
									ou = val.text
								except:
									continue
							data[prop][player] = ou

		updateData(file, data)
		q.task_done()

	browser.stop()

async def getFDLinks(sport):
	games = {}
	url = f"https://sportsbook.fanduel.com/navigation/{sport}"
	browser = await uc.start(no_sandbox=True)
	page = await browser.get(url)

	await page.wait_for(selector="span[role=link]")
	links = await page.query_selector_all("span[role=link]")

	for link in links:
		if link.text_all == "More wagers":
			t = link.parent.parent.children[0].children[-1]
			if t.tag != "time" or len(t.text.split(" ")) > 2:
				continue
			url = ""
			if sport in ["ncaab", "nba"]:
				url = link.parent.href
				game = " ".join(link.parent.href.split("/")[-1].split("-")[:-1])
			else:
				url = link.parent.parent.parent.href
				game = " ".join(link.parent.parent.parent.href.split("/")[-1].split("-")[:-1])
			away, home = map(str, game.split(" @ "))
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
			elif sport == "mlb":
				away = convertMLBTeam(away)
				home = convertMLBTeam(home)
			game = f"{away} @ {home}"
			games[game] = url

	browser.stop()
	return games

def runThreads(book, sport, games, totThreads, keep=False):
	threads = []
	file = f"static/{sport}/{book}.json"
	if not keep:
		with open(file, "w") as fh:
			json.dump({}, fh, indent=4)
	for _ in range(totThreads):
		if book == "fanduel" and sport == "ncaab":
			thread = threading.Thread(target=runNCAABFD, args=())
		elif book == "fanduel":
			thread = threading.Thread(target=runFD, args=(sport,))
		elif book == "mgm":
			thread = threading.Thread(target=runMGM, args=(sport,))
		elif book == "draftkings":
			thread = threading.Thread(target=runDK, args=(sport,))
		elif book == "espn":
			thread = threading.Thread(target=runESPN, args=(sport,))
		elif book == "bet365":
			thread = threading.Thread(target=run365, args=(sport,))
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
	#q.task_done()

def runFD(sport):
	uc.loop().run_until_complete(writeFD(sport))

def runNCAABFD():
	uc.loop().run_until_complete(writeNCAABFD())

async def writeNCAABFD():
	browser = await uc.start(no_sandbox=True)
	while True:
		data = {}
		(game,url) = q.get()
		if url is None:
			q.task_done()
			break
		page = await browser.get("https://sportsbook.fanduel.com"+url)
		await page.wait_for(selector="h1")
		game = await page.query_selector("h1")
		game = game.text.lower().replace(" odds", "")
		away, home = map(str, game.split(" @ "))
		awayFull, homeFull = away, home
		game = f"{convertCollege(away)} @ {convertCollege(home)}"

		navs = await page.query_selector_all("nav")
		tabs = await navs[-1].query_selector_all("a")

		for tabIdx in range(len(tabs)):
			try:
				tab = tabs[tabIdx]
			except:
				continue
			await page.wait_for(selector="div[data-test-id=ArrowAction]")

			#if tab.text.lower() not in ["popular", "player points", "player threes", "player rebounds", "player assists", "player combos", "player defense", "half", "team props"]:
			if tab.text.lower() not in ["popular", "player points", "player threes", "player rebounds", "player assists", "player combos", "player defense"]:
				continue

			await tab.scroll_into_view()
			await tab.mouse_click()
			await page.wait_for(selector="div[data-test-id=ArrowAction]")
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
				elif "moneyline" in label:
					if "tie" in label:
						continue
					prop = "ml"
				else:
					if label.startswith("to score") and label.endswith("points"):
						prop = "pts"
						mainLine = str(float(label.split(" ")[-2].replace("+", "")) - 0.5)
						skip = 1
					elif " - alt" in label:
						alt = True
						skip = 1
						player = parsePlayer(label.split(" - ")[0].split(" (")[0])
						prop = label.split("alternate total ")[-1].split("alt ")[-1].replace("assists", "ast").replace("points", "pts").replace("rebounds", "reb").replace("threes", "3ptm").replace(" + ", "+").replace(" ", "_")
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
					elif label.endswith("total points") or (tab.text.lower() in ["team props", "half"] and label[:-2].endswith("alternate total points")):
						if "odd even" in label or "odd/even" in label:
							continue 
						prop = "pts"
						if convertCollege(label.replace("alternate ", "").split(" total")[0]) == game.split(" @ ")[0]:
							prop = "away_total"
						elif convertCollege(label.replace("alternate ", "").split(" total")[0]) == game.split(" @ ")[-1]:
							prop = "home_total"
						elif label.startswith("1st half total points"):
							prop = "total"
					elif "alternate spread" in label or "handicap" in label:
						prop = "spread"
					elif label.endswith("total"):
						if convertCollege(label.replace("1st half ", "").split(" total")[0]) == game.split(" @ ")[0]:
							prop = "away_total"
						elif convertCollege(label.replace("1st half ", "").split(" total")[0]) == game.split(" @ ")[-1]:
							prop = "home_total"
						else:
							print("HERE", label)
							continue
					elif "alternate total points" in label:
						prop = "total"
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
					else:
						continue

				prop = f"{prefix}{prop}"

				if not prop:
					continue

				path = arrow.children[-1].children[0].children[0]
				if prop != "lines" and path.attributes[1].split(" ")[0] != "M.147":
					await arrow.click()

				el = await div.query_selector("div[aria-label='Show more']")
				if el:
					await el.click()

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
				data.setdefault(game, {})

				if prop == "lines":
					btns = btns[1:]
					idx = btns[1].attributes.index("aria-label")
					label = btns[1].attributes[idx+1]
					if "unavailable" not in label:
						data[game]["ml"] = label.split(", ")[2].split(" ")[0]+"/"+btns[4].attributes[idx+1].split(", ")[2].split(" ")[0]

					label = btns[0].attributes[1]
					if "unavailable" not in label:
						line = label.split(", ")[2]
						data[game].setdefault("spread", {})
						data[game]["spread"][float(line.replace("+", ""))] = label.split(", ")[3].split(" ")[0]+"/"+btns[3].attributes[1].split(", ")[3].split(" ")[0]
					line = btns[2].attributes[1].split(", ")[3].split(" ")[1]
					data[game].setdefault("total", {})
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

					data[game].setdefault(prop, {})

					if "ml" in prop:
						data[game][prop] = odds+"/"+btns[i+1].attributes[labelIdx].split(", ")[-1]
					elif skip == 1:
						if mainLine:
							player = parsePlayer(fields[1].split(" (")[0])
							line = mainLine
						elif alt:
							line = fields[1].split(" ")[-1]
						else:
							line = fields[-2]

						player = player.split(" (")[0]
						data[game][prop].setdefault(player, {})
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
						ou = odds
						if i+1 < len(btns) and "unavailable" not in btns[i+1].attributes[labelIdx]:
							try:
								ou += "/"+btns[i+1].attributes[labelIdx].split(", ")[-1]
							except:
								pass

						if "total" in prop or "spread" in prop:
							line = line.split(" ")[-1]
							ou = ou.split(" ")[0]
							data[game].setdefault(prop, {})
							data[game][prop][line] = ou
							continue

						player = parsePlayer(fields[0].lower().split(" (")[0])
						data[game][prop].setdefault(player, {})
						data[game][prop][player][line] = ou
	
		with lock:
			with open(file) as fh:
				d = json.load(fh)

			d[game] = data[game].copy()
			with open(file, "w") as fh:
				json.dump(d, fh, indent=4)
		q.task_done()
	browser.stop()

async def writeSoccerFD(keep, league, tomorrow):
	base = f"https://sportsbook.fanduel.com/soccer"
	url = ""
	if league:
		url += league.replace(" ", "-")
	else:
		url += "?tab=live-upcoming"

	leagues = [base+url]
	leagues = ["argentinian-primera-division","australian-a-league-men's","austrian-bundesliga","azerbaijan-premier-league","belgian-first-division-a","bosnia-and-herzegovina---premier-league","bulgarian-a-pfg","colombian-primera-a","costa-rican-primera-division","croatian-1-hnl","cyprus---1st-division","czech-1-liga", "ecuador-serie-a","english-premier-league", "english-championship", "english-fa-cup", "english-football-league-cup","english-league-1", "english-league-2", "french-ligue-1", "french-ligue-2", "german-bundesliga", "german-bundesliga-2", "greek-super-league", "guatemalan-liga-nacional", "hungarian-nb-i", "fifa-world-cup", "uefa-nations-league", "international-friendlies", "uefa-champions-league", "uefa-europa-league", "fifa-club-world-cup", "uefa-europa-conference-league", "irish-premier-division", "italian-serie-a", "italian-serie-b", "italian-cup", "maltese-premier-league", "mexican-liga-mx", "dutch-eredivisie", "dutch-cup", "northern-irish-premiership", "polish-ekstraklasa", "portuguese-cup", "portuguese-primeira-liga", "romanian-liga-i", "scottish-premiership", "serbian-first-league", "serbian-super-league", "slovakian-superliga", "south-africa---premier-division", "spanish-la-liga", "spanish-segunda-division", "swiss-super-league", "turkish-super-league", "wales---premiership"]
	#leagues = leagues[leagues.index("uefa-champions-league"):]
	if league:
		leagues = [league]
	browser = await uc.start(no_sandbox=True)

	data = {}
	if keep:
		with open(f"static/soccer/fanduelLines.json") as fh:
			data = json.load(fh)

	for league in leagues:
		print(league)
		url = base+"/"+league
		page = await browser.get(url)
		time.sleep(2)

		await page.wait_for(selector="#main ul")

		links = await page.query_selector_all("#main ul")
		j = 1
		if len(leagues) > 1:
			j = 0

		if "More wagers" in links[0].text_all:
			links = await links[0].query_selector_all("li")
		elif "More wagers" in links[j].text_all:
			links = await links[j].query_selector_all("li")
		else:
			links = await links[j+1].query_selector_all("li")
		linkIdx = -1

		#while True:
		for linkIdx in range(0, len(links)):
			linkIdx += 1
			#print(links[linkIdx].text_all)
			if linkIdx >= len(links) or links[linkIdx].text_all.strip() == "":
				break
			if "half" in links[linkIdx].text_all.lower() or "overtime" in links[linkIdx].text_all.lower():
				continue

			t = await links[linkIdx].query_selector("time")
			if not t:
				continue

			if tomorrow:
				day = datetime.strftime(datetime.now() + timedelta(days=1), "%a")
				#print(day, t.text)
				if day not in t.text:
					continue
					pass

			if t and ("Mon" in t.text or "Tue" in t.text or "Wed" in t.text or "Thu" in t.text or "Fri" in t.text or "Sat" in t.text or "Sun" in t.text or "2025" in t.text):
				if not tomorrow:
					break
				pass

			teams = await links[linkIdx].query_selector_all("span[role=text]")
			if not teams:
				continue
			away = teams[0].text.lower()
			home = teams[1].text.lower()
			away = convertSoccer(away)
			home = convertSoccer(home)
			game = f"{away} v {home}"

			if "(w)" in game or "women" in game:
				#continue
				pass

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

				#if tab.text.lower() not in ["goal scorer", "goals", "team props", "half", "shots on target", "shots", "assists", "corners", "saves"]:
				if tab.text.lower() not in ["goals", "team props", "half", "shots on target", "shots", "corners", "saves"]:
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
					elif label.startswith("goalkeeper to make"):
						mainLine = str(float(label.split(" ")[-4]) - 0.5)
						prop = "player_saves"
						continue
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
			j = 1
			if len(leagues) > 1:
				j = 0
				
			if "More wagers" in links[0].text_all:
				links = await links[0].query_selector_all("li")
			elif "More wagers" in links[j].text_all:
				links = await links[j].query_selector_all("li")
			else:
				links = await links[j+1].query_selector_all("li")
			linkIdx = -1

		with open(f"static/soccer/fanduelLines.json", "w") as fh:
			json.dump(data, fh, indent=4)
	browser.stop()

async def writeFD(sport):
	file = f"static/{sport}/fanduel.json"
	browser = await uc.start(no_sandbox=True)
	while True:
		data = nested_dict()
		(game, url) = q.get()
		if url is None:
			q.task_done()
			break

		page = await browser.get("https://sportsbook.fanduel.com"+url)
		await page.wait_for(selector="nav")

		navs = await page.query_selector_all("nav")
		tabs = await navs[-1].query_selector_all("a")

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
				#if tab.text.lower() not in ["player combos"]:
					continue
			elif sport == "mlb":
				if tab.text.lower() not in ["batter props"]:
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
				label = arrow.children[0].children[0].text.lower()
				div = arrow.parent.parent.parent

				prop = prefix = fullPlayer = player = mainLine = ""
				skip = 2
				player = False
				alt = False

				prefix = ""
				hp = ""
				if "half" in label:
					hp = "h"
				elif "period" in label:
					hp = "p"
				elif "quarter" in label:
					hp = "q"

				if "first half" in label or "first period" in label or "first quarter" in label or "1st half" in label or "1st period" in label or "1st quarter" in label:
					prefix = f"1{hp}_"
				elif "second" in label or "2nd" in label:
					prefix = f"2{hp}_"
				elif "third" in label or "3rd" in label:
					prefix = f"3{hp}_"
				elif "fourth" in label or "4th" in label:
					prefix = f"4{hp}_"

				if label == "game lines":
					prop = "lines"
				elif "moneyline (3 way)" in label:
					prop = "3ml"
					skip = 3
				elif label == "alternate puck line":
					skip = 1
					prop = "spread"
				elif label == "any time goal scorer":
					prop = "atgs"
					skip = 1
				elif label.endswith("total goals"):
					team = convertNHLTeam(label.split(" total")[0])
					if tab.text.lower() == "goals":
						prop = "atgs"
					elif team == game.split(" @ ")[0]:
						prop = "away_total"
					elif team == game.split(" @ ")[-1]:
						prop = "home_total"
					else:
						prop = "total"
				elif label == "first goal scorer":
					prop = "fgs"
					skip = 1
				elif label == "first home team goal scorer" or label == "first away team goal scorer":
					prop = "team_fgs"
					skip = 1
				elif label == "touchdown scorers":
					prop = "attd"
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
					if "to record" in label or "specials" in label or "performance" in label or "featured" in label or "x+" in label or "first 3 minutes" in label:
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
				elif sport == "mlb":
					skip = 1
					if label == "to hit a home run":
						prop = "hr"
					elif label == "to record a hit":
						prop = "h"
					#elif label == "to record 2+ hit":
					#	prop = "2+h"
					else:
						continue
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

				path = arrow.children[-1].children[0].children[0]
				if prop != "lines" and path.attributes[1].split(" ")[0] != "M.147":
					await arrow.click()
					#await div.wait_for(selector="div[role=button]")
					#await div.wait_for(selector="div[aria-label='Show more']")

				if "Show more" in div.children[-1].text_all:
					el = await div.children[-1].query_selector("div[aria-label='Show more']")
					if el:
						await el.click()
					#await div.wait_for("div[aria-label='Show less']")

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
						#print(label.split(","), btns[3].attributes[1].split(", "))
						data[game]["spread"][float(line.replace("+", ""))] = label.split(", ")[3].split(" ")[0]+"/"+btns[3].attributes[1].split(", ")[3].split(" ")[0]
					try:
						line = btns[2].attributes[1].split(", ")[3].split(" ")[1]
					except:
						continue
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

					if prop == "3ml":
						data[game][prop] = odds+"/"+btns[i+1].attributes[labelIdx].split(", ")[-1]+"/"+btns[i+2].attributes[labelIdx].split(", ")[-1]
					elif "spread" in prop:
						line = fields[-2].split(" ")[-1]
						team = convertNHLTeam(fields[-2].replace(f" {line}", ""))
						line = line.replace("+", "")
						isAway = True
						if team == game.split(" @ ")[-1]:
							line = str(float(line) * -1)
							isAway = False

						if line not in data[game][prop]:
							if not isAway:
								continue
							data[game][prop][line] = odds
						else:
							data[game][prop][line] += "/"+odds
					elif "total" in prop:
						if prop in ["away_total", "home_total"]:
							line = fields[-2].split(" ")[-1]
						else:
							line = fields[-2].split(" ")[0]
						data[game][prop][line] = odds+"/"+btns[i+1].attributes[labelIdx].split(", ")[-1].split(" ")[0]
					elif prop == "kicking_pts":
						player = parsePlayer(arrow.text.lower().split(" total ")[0])
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
							try:
								data[game]["ftd"][player] = btns[i+1].attributes[labelIdx].split(", ")[2]
							except:
								continue
					elif sport == "nhl" and prop in ["atgs", "fgs", "pts", "ast", "sog", "team_fgs"]:
						player = parsePlayer(fields[1].split(" (")[0].split(" - ")[0])
						if mainLine:
							data[game][prop][player][mainLine] = odds
						else:
							if prop in ["pts", "sog", "ast"]:
								line = fields[-2]

							if skip == 1:
								data[game][prop][player] = odds
							elif prop == "atgs":
								if player in data[game][prop] and int(data[game][prop][player]) > int(odds):
									data[game][prop][player] += "/"+btns[i+1].attributes[labelIdx].split(", ")[-1].split(" ")[0]
								else:
									try:
										data[game][prop][player] = odds+"/"+btns[i+1].attributes[labelIdx].split(", ")[-1].split(" ")[0]
									except:
										pass
							else:
								if player in data[game][prop] and line in data[game][prop][player] and int(data[game][prop][player][line].split("/")[0]) > int(odds.split("/")[0]):
									data[game][prop][player][line] += "/"+btns[i+1].attributes[labelIdx].split(", ")[-1].split(" ")[0]
								else:
									data[game][prop][player][line] = odds+"/"+btns[i+1].attributes[labelIdx].split(", ")[-1].split(" ")[0]
					elif prop in ["double_double", "triple_double"]:
						player = parsePlayer(fields[1].split(" (")[0])
						data[game][prop][player] = odds
					elif skip == 1 and prop == "reb+ast":
						player = parsePlayer(fields[0].split(" - alt")[0])
						if "reb + ast" in player:
							player = player.replace("   alt reb + ast", "")
						line = fields[1].split(" ")[-1]
						
						if line in data[game][prop][player]:
							if "under" in fields[1].lower() and "/" not in data[game][prop][player][line]:
								data[game][prop][player][line] += f"/{odds}"
						elif "under" in fields[1].lower():
							data[game][prop][player][line] = f"-/{odds}"
						else:
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
						elif prop == "sacks" or prop == "def_int" or prop == "h":
							player = parsePlayer(fields[1].split(" to Record")[0].split(" (")[0])
							line = "0.5"
						elif prop == "hr":
							player = parsePlayer(fields[1].split(" to Record")[0].split(" (")[0])
						else:
							line = fields[x].lower().replace(fullPlayer+" ", "").split(" ")[0].replace("+", "")
							line = str(float(line) - 0.5)

						player = player.split(" (")[0]
						if line in data[game][prop][player]:
							continue

						if prop == "hr":
							data[game][prop][player] = odds
						else:
							data[game][prop][player][line] = odds
					elif prop == "pass+rush":
						player = parsePlayer(fields[0].split(" (")[0].split(" -")[0])
						line  = fields[2]
						data[game][prop][player][line] = odds+"/"+btns[i+1].attributes[labelIdx].split(", ")[3].split(" ")[0]
					else:
						if sport == "nba" and alt:
							line = fields[1].split(" ")[0]
						elif sport == "ncaab":
							line = fields[-2]
						player = parsePlayer(fields[0].lower().split(" (")[0].split(" - alt")[0])
						data[game][prop][player][line] = odds
						if i+1 < len(btns) and "unavailable" not in btns[i+1].attributes[labelIdx]:
							try:
								if sport == "ncaab":
									data[game][prop][player][line] += "/"+btns[i+1].attributes[labelIdx].split(", ")[-1]
								else:
									data[game][prop][player][line] += "/"+btns[i+1].attributes[labelIdx].split(", ")[2].split(" ")[0]
							except:
								continue
			
		updateData(file, data)
		q.task_done()
	browser.stop()

async def writeSoccerDK(keep, league, tomorrow):
	base = "https://sportsbook.draftkings.com/leagues/soccer/"
	#if league:
	#	url += league.replace(" ", "-")
	#else:
	#	url += "champions-league"
	data = {}
	if keep:
		with open(f"static/soccer/draftkings.json") as fh:
			data = json.load(fh)

	"""
		arr=[]; for (let x of document.querySelectorAll(".league-link__link")) { arr.push(x.href.split("/").pop()) }; console.log(arr);
	"""

	urls = ["australia---league-a", "austria---bundesliga", "azerbaijan---premier", "belgium---first-division-a", "bolivia---premiera", "bulgaria---first-league", "caf-champions-league", "champions-league", "champions-league-women", "colombia---primera", "costa-rica---primera-div", "croatia---1.hnl", "cyprus---1st-div", "czech-republic---first-league", "ecuador---primera-a", "england---championship", "english-football-league-cup", "english-fa-cup", "england---league-one", "england---league-two", "england---premier-league", "europa-conference-league", "europa-league", "france---ligue-1", "france---ligue-2", "germany---2.bundesliga", "germany---1.bundesliga", "greece---super-league", "guatemala---liga-nacional", "honduras---liga-nacional", "hungary---nb-i", "india---i-league", "israel---premier-league", "italy-cup", "italy---serie-a", "italy---serie-b", "mexico---liga-mx", "netherlands-cup", "netherlands---eredivisie", "northern-ireland---premier", "poland---ekstraklasa", "portugal-cup", "portugal---primeira-liga", "romania---liga-1", "scotland---premiership", "serbia---superliga", "south-africa---premier", "spain---la-liga", "spain---segunda", "swiss---super-league", "turkey---super-ligi", "uefa-nations-league", "wales---premier", "world-cup-2026"]
	#urls = urls[urls.index("mexico---liga-mx"):]
	if league:
		urls = [league]

	browser = await uc.start(no_sandbox=True)
	for url in urls:
		print(url)
		page = await browser.get(base+url)
		time.sleep(1)

		try:
			await page.wait_for(selector="div[role=tablist]")
			tablist = await page.query_selector("div[role=tablist]")
			mainTabs = await tablist.query_selector_all("a")
		except:
			continue

		for mainIdx, mainTab in enumerate(mainTabs):
			#if mainTab.text.lower() not in ["game lines", "goalscorer props", "player shots", "player assists", "defense props", "corners"]:
			if mainTab.text.lower() not in ["defense props"]:
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
				elif prop == "goalkeeper saves":
					prop = "player_saves"
				else:
					continue

				prop = f"{prefix}{prop}"

				if prop != "player_saves":
					#continue
					pass

				gameDivs = await page.query_selector_all(".sportsbook-event-accordion__wrapper")
				for gameDiv in gameDivs:
					game = await gameDiv.query_selector(".sportsbook-event-accordion__title")

					if prop in ["spread", "total"]:
						more = await gameDiv.query_selector(".view-more__button span")
						await more.mouse_click()
					
					t = await gameDiv.query_selector(".sportsbook-event-accordion__date")

					x = "tomorrow" if tomorrow else "today"
					if x not in t.text_all.lower():
						continue

					away, home = map(str, game.text_all.lower().split(" vs "))
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
						try:
							data[game][prop] = odds[0].text.replace("\u2212", "-")+"/"+odds[1].text.replace("\u2212", "-")
						except:
							pass
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
							line = btns[i].text_all.split(" ")[-2].replace("+", "")
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
						odds = await gameDiv.query_selector_all("button[data-testid='sb-selection-picker__selection-0']")
						mostBtns = 0
						for odd in odds:
							mostBtns = max(mostBtns, len(odd.parent.children))
							#await odd.click()
						for i in range(mostBtns):
							odds = await gameDiv.query_selector_all(f"button[data-testid='sb-selection-picker__selection-{i}']")
							#if i != 0:
							for odd in odds:
								await odd.click()

							odds = await gameDiv.query_selector_all(f"button[data-testid='sb-selection-picker__selection-{i}']")

							for oIdx, odd in enumerate(odds):
								player = parsePlayer(odd.parent.parent.parent.parent.parent.children[0].text)
								if player not in data[game][prop]:
									data[game][prop][player] = {}

								line = str(float(odd.text_all.split(" ")[0].replace("+", "")) - 0.5)
								if " " in odd.text_all:
									data[game][prop][player][line] = odd.text_all.split(" ")[-1]

						el = await page.query_selector("div[data-testid='betslip-header-clear-all-button']")
						if el:
							await el.click()
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


async def getDKLinks(sport):
	if sport in ["nba", "ncaab"]:
		league = "basketball"
	elif sport == "nhl":
		league = "hockey"
	elif sport == "soccer":
		await writeSoccerDK(keep, league, tomorrow)
		exit()
	elif sport == "mlb":
		league = "baseball"
	else:
		league = "football"

	url = f"https://sportsbook.draftkings.com/leagues/{league}/{sport}"
	browser = await uc.start(no_sandbox=True)
	page = await browser.get(url)
	await page.wait_for(selector=".sportsbook-table__body")

	teams = await page.query_selector_all(".sportsbook-table__body .event-cell")
	games = []
	for i in range(0, len(teams), 2):
		t = teams[i].parent.children[0].text_all
		away = teams[i].children[0].text_all
		home = teams[i+1].children[0].text_all

		if sport == "ncaab":
			away = convertCollege(away)
			home = convertCollege(home)
			away = away.split(" logo ")[0]
			home = home.split(" logo ")[0]
			away = convertCollege(away)
			home = convertCollege(home)
		elif sport == "nba":
			away = convert365NBATeam(away)
			home = convert365NBATeam(home)
		elif sport == "nhl":
			away = convert365NHLTeam(away)
			home = convert365NHLTeam(home)
		else:
			away = convert365Team(away)
			home = convert365Team(home)
		game = f"{away} @ {home}"
		games.append(game)

	browser.stop()

	#res = {"game lines": f"https://sportsbook.draftkings.com/leagues/hockey/nhl?category=game-lines"}
	#return res
	res = {}
	tabs = []

	if sport in ["nba", "ncaab"]:
		tabs = ["game lines", "player points", "player combos", "player rebounds", "player assists", "player threes", "player defense"]
	elif sport == "nhl":
		tabs = ["game lines", "goalscorer", "shots on goal", "points", "assists", "blocks", "goalie props", "team totals"]
		#tabs = ["game lines"]

	for tab in tabs:
		category = tab.replace(" ", "-")
		url = f"https://sportsbook.draftkings.com/leagues/{league}/{sport}?category={category}"
		if tab == "player defense":
			for key in ["blocks", "steals"]:
				res[key] = f"{url}&subcategory={key}"
			for key in ["blocks", "steals", "steals+blocks", "turnovers"]:
				res[key] = f"{url}&subcategory={key.replace('+','-+-')}-o/u"
			continue
		elif tab == "player combos":
			for key in ["pts+reb+ast", "pts+reb", "pts+ast"]:
				for game in games:
					res[f"{game}-{key}"] = f"{url}&subcategory={key.replace('+','-+-')}"
			for key in ["pts+reb+ast", "pts+reb", "pts+ast", "ast+reb"]:
				res[key] = f"{url}&subcategory={key.replace('+','-+-')}-o/u"
			continue
		# OU just needs 1 thread
		if tab in ["shots on goal", "points", "assists", "player points", "player rebounds", "player assists", "player threes"]:
			res[tab+"-o/u"] = f"{url}&subcategory={category.replace('player-', '')}-o/u"
		# thread for each game beacuse how DK has their alts
		if tab in ["shots on goal", "points", "assists"]:
			for game in games:
				res[f"{game}-{category}"] = url
		res[tab] = url
	return res

def runDK(sport):
	return uc.loop().run_until_complete(writeDK(sport))

async def writeDKFromHTML(data, html, sport, prop):
	soup = BS(html, "lxml")
	skip = 1
	if prop == "game_lines":
		skip = 2
		divs = soup.find("tbody", class_="sportsbook-table__body").find_all("tr")
	else:
		divs = soup.select(".sportsbook-event-accordion__wrapper")

	#print(len(divs))
	for idx in range(0, len(divs), skip):
		gameDiv = divs[idx]
		if gameDiv.find("svg", class_="sportsbook__icon--live"):
			#continue
			pass

		if prop == "game_lines":
			away = gameDiv.select(".event-cell__name-text")[0].text
			home = divs[idx+1].select(".event-cell__name-text")[0].text
		else:
			game = eval(gameDiv.find("div").get("data-tracking"))["value"]
			away, home = map(str, game.split(" @ "))

		if sport == "ncaab":
			away = convertCollege(away)
			home = convertCollege(home)
		elif sport == "nba":
			away = convert365NBATeam(away)
			home = convert365NBATeam(home)
		elif sport == "nhl":
			away = convert365NHLTeam(away)
			home = convert365NHLTeam(home)
		else:
			away = convert365Team(away)
			home = convert365Team(home)
		game = f"{away} @ {home}"

		#print(game)
		if prop == "game_lines":
			tds = gameDiv.select("td")
			tds2 = divs[idx+1].select("td")
			if len(tds)+len(tds2) != 6:
				continue
			data[game]["ml"] = f"{tds[-1].text}/{tds2[-1].text}".replace("\u2212", "-")
			line = str(float(tds[0].find("span", class_="sportsbook-outcome-cell__line").text))
			data[game]["spread"][line] = f"{tds[0].find_all('span')[-1].text}/{tds2[0].find_all('span')[-1].text}".replace("\u2212", "-")
			line = str(float(tds[1].find("span", class_="sportsbook-outcome-cell__line").text))
			data[game]["total"][line] = f"{tds[1].find_all('span')[-1].text}/{tds2[1].find_all('span')[-1].text}".replace("\u2212", "-")
		else:
			for row in gameDiv.select(".sportsbook-table__body tr"):
				player = parsePlayer(row.select(".sportsbook-row-name")[0].text)
				line = row.select(".sportsbook-outcome-cell__line")[0].text
				odds = [x.text.replace("\u2212", "-") for x in row.select(".sportsbook-odds")]
				data[game][prop][player][line] = "/".join(odds)

async def writeDK(sport):
	file = f"static/{sport}/draftkings.json"
	browser = await uc.start(no_sandbox=True)
	while True:
		data = nested_dict()
		(game, url) = q.get()
		#print(game, url)
		mainTab = game
		if url is None:
			browser.stop()
			q.task_done()
			return

		page = await browser.get(url)
		c = ".sportsbook-event-accordion__wrapper"
		if game == "game lines":
			c = ".sportsbook-table__body tr"
		try:
			await page.wait_for(selector=c)
		except:
			q.task_done()
			continue

		singleGame = game.split("-")[0]
		if " @ " in singleGame:
			prop = game.replace(f"{singleGame}-", "")
		else:
			prop = game

		skip = 1
		prop = prop.replace("-", " ")
		if "o/u" in prop:
			skip = 2
			prop = prop.replace(" o/u", "")

		alt = False
		if prop.startswith("alt"):
			alt = True

		prefix = ""
		if "1st half" in prop:
			prefix = "1h_"
		elif "2nd half" in prop:
			prefix = "2h_"

		#print(prop, url)
		if "halves" in url:
			if "team totals" in prop:
				if "odd/even" in prop:
					q.task_done()
					continue
				prop = f"team_total"
			else:
				q.task_done()
				continue
		elif "team-props" in url:
			if prop in ["team totals", "alt team totals"]:
				prop = "team_total"
			else:
				q.task_done()
				continue
		else:
			prop = prop.split(" (")[0].replace("player ", "").replace("alternate ", "").replace("alt ", "").replace("puck line", "spread").replace("interceptions", "int").replace("passing", "pass").replace("receiving", "rec").replace("rushing", "rush").replace("attempts", "att").replace("receptions", "rec").replace("reception", "rec").replace("completions", "pass_cmp").replace("completion", "cmp").replace("tds", "td").replace("yards", "yd").replace("points", "pts").replace("rebounds", "reb").replace("assists", "ast").replace("threes", "3ptm").replace("blocks", "blk").replace("turnovers", "to").replace("steals", "stl").replace("shots on goal", "sog").replace("goalscorer", "atgs").replace("goalie props", "saves").replace(" + ", "+").replace(" ", "_")
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

		#print(prop)

		if mainTab.endswith("o/u") or mainTab in ["goalie props", "game lines"]:
			time.sleep(0.5)
			html = await page.get_content()
			await writeDKFromHTML(data, html, sport, prop)
			browser.stop()
			updateData(file, data)
			q.task_done()
			continue

		#if prop == "attd" or prop == "td_scorer":
		#	continue

		sel = ".sportsbook-event-accordion__wrapper"
		rowSkip = 1
		if prop == "game" or prop == "1st_half":
			sel = ".sportsbook-table__body tr"
			rowSkip = 2
		gameDivs = await page.query_selector_all(sel)
		#print(prop, len(gameDivs))
		for gameIdx in range(0, len(gameDivs), rowSkip):
			gameDiv = gameDivs[gameIdx]

			#if sport != "nfl" and prop != "game" and prop != "1st_half" and not tomorrow and "Today" not in gameDiv.text_all:
			#if "Today" not in gameDiv.text_all:
			#	continue

			if prop == "game" or prop == "1st_half":
				away = await gameDiv.query_selector(".event-cell__name-text")
				home = await gameDivs[gameIdx+1].query_selector(".event-cell__name-text")
				away, home = away.text.lower(), home.text.lower()
			else:
				game = await gameDiv.query_selector(".sportsbook-event-accordion__title")
				if not game:
					continue

				if prop in ["spread", "total"]:
					more = await gameDiv.query_selector(".view-more__button span")
					await more.mouse_click()

				#print(gameIdx, len(gameDivs))
				if " vs " in game.text_all.lower():
					away, home = map(str, game.text_all.lower().replace(" vs ", " @ ").split(" @ "))
				else:
					away, home = map(str, game.text_all.lower().replace(" at ", " @ ").split(" @ "))
			if sport == "ncaab":
				away = convertCollege(away)
				home = convertCollege(home)
				away = away.split(" logo ")[0]
				home = home.split(" logo ")[0]
				away = convertCollege(away)
				home = convertCollege(home)
			elif sport == "nba":
				away = convert365NBATeam(away)
				home = convert365NBATeam(home)
			elif sport == "nhl":
				away = convert365NHLTeam(away)
				home = convert365NHLTeam(home)
			else:
				away = convert365Team(away)
				home = convert365Team(home)

			game = f"{away} @ {home}"

			if " @ " in singleGame and game != singleGame:
				continue

			if prop == "game" or prop == "1st_half":
				btns = await gameDiv.query_selector_all("div[role=button]")
				if len(btns) < 3:
					continue
				homeBtns = await gameDivs[gameIdx+1].query_selector_all("div[role=button]")
				p = "1h_ml" if prop == "1st_half" else "ml"
				data[game][p] = (btns[-1].text+"/"+homeBtns[-1].text).replace("\u2212", "-")
				#spread
				spans = await btns[0].query_selector_all("span")
				under = await homeBtns[0].query_selector_all("span")
				line = str(float(spans[0].text_all.replace("+", "")))
				p = "1h_spread" if prop == "1st_half" else "spread"
				data[game][p] = {
					line: (spans[-1].text+"/"+under[-1].text).replace("\u2212", "-")
				}
				#total
				under = await homeBtns[1].query_selector_all("span")
				line = str(float(btns[1].text_all.split(" ")[-2]))
				p = "1h_total" if prop == "1st_half" else "total"
				data[game][p] = {
					line: (btns[1].text_all.split(" ")[-1]+"/"+homeBtns[1].text_all.split(" ")[-1]).replace("\u2212", "-")
				}
			elif prop == "atgs":
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
			elif "team_total" in prop:
				for div in gameDiv.children[-1].children:
					t = div.text_all.lower()
					if sport == "ncaab":
						team = convertCollege(t.replace("alternate ", "").split(":")[0].split(" total points")[0])
					else:
						team = convert365NHLTeam(t.split(":")[0])

					pre = ""
					if "1st half" in t:
						pre = "1h_"
					if "2nd half" in t:
						pre = "2h_"

					p = "home_total"
					if team == game.split(" @ ")[0]:
						p = "away_total"

					p = f"{pre}{p}"
					btns = div.children[-1].children
					for i in range(0, len(btns), 2):
						ou = btns[i].text_all.split(" ")[-1]+"/"+btns[i+1].text_all.split(" ")[-1]
						line = btns[i].text_all.split(" ")[-2]
						data[game][p][line] = ou.replace("\u2212", "-")
			elif "attd" in prop:
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
					player = parsePlayer(btn.attributes[attrIdx+1].strip().split(" (")[0])
					#print(player, odds.text)
					data[game]["attd"][player] = odds.text.replace("\u2212", "-")
			elif mainTab == "player not to score":
				btns = await gameDiv.query_selector_all("ul div[role=button]")
				for btn in btns:
					odds = await btn.query_selector(".sportsbook-odds")
					if not odds:
						continue
					attrIdx = btn.attributes.index("aria-label")
					player = parsePlayer(btn.attributes[attrIdx+1].strip())
					if player in data[game]["attd"] and "/" not in data[game]["attd"][player]:
						data[game]["attd"][player] += "/"+odds.text.replace("\u2212", "-")
			elif prop in ["spread", "total"]:
				btns = await gameDiv.query_selector_all(f".view-more div[role=button]")
				for i in range(0, len(btns), 2):
					line = str(float(btns[i].text_all.split(" ")[-2].replace("+", "")))
					over = btns[i].text_all.split(" ")[-1].replace("\u2212", "-")
					under = btns[i+1].text_all.split(" ")[-1].replace("\u2212", "-")
					data[game][prop][line] = f"{over}/{under}"
			elif sport == "ncaab" or (sport in ["nba", "nhl"] and skip == 1):
				"""
				odds = await gameDiv.query_selector_all(".sb-selection-picker__selection--focused")
				players = await gameDiv.query_selector_all(".side-rail-name")
				for oIdx, odd in enumerate(odds):
					player = parsePlayer(players[oIdx].text)
					line = str(float(odd.text_all.split(" ")[0].replace("+", "")) - 0.5)
					o = odd.text_all.split(" ")[-1]
					if player not in data[game][prop]:
						data[game][prop][player] = {}
					data[game][prop][player][line] = o
				"""
				odds = await gameDiv.query_selector_all("button[data-testid='sb-selection-picker__selection-0']")
				mostBtns = 0
				for odd in odds:
					mostBtns = max(mostBtns, len(odd.parent.children))
					#await odd.click()

				for i in range(mostBtns):
					odds = await gameDiv.query_selector_all(f"button[data-testid='sb-selection-picker__selection-{i}']")
					#if i != 0:
					for odd in odds:
						await odd.click()

					odds = await gameDiv.query_selector_all(f"button[data-testid='sb-selection-picker__selection-{i}']")

					for oIdx, odd in enumerate(odds):
						player = parsePlayer(odd.parent.parent.parent.parent.parent.children[0].text)
						line = str(float(odd.text_all.split(" ")[0].replace("+", "")) - 0.5)
						if " " in odd.text_all:
							data[game][prop][player][line] = odd.text_all.split(" ")[-1]

				#el = await page.query_selector("div[data-testid='betslip-header-clear-all-button']")
				#if el:
				#	await el.click()

			elif skip == 1 or alt:
				divs = await gameDiv.query_selector_all(".component-29")
				for div in divs:
					player = await div.query_selector("p")
					if not player:
						continue
					player = parsePlayer(player.text_all.lower().split(" alt ")[0].split(" points")[0].split(" rebounds")[0].split(" assists")[0].split(" three")[0].split(" blocks")[0].split(" steals")[0].split(" alternate")[0])

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

					try:
						line = await tds[0].query_selector(".sportsbook-outcome-cell__line")
					except:
						continue
					if not line:
						continue
					line = line.text
					odds = await tds[0].query_selector(".sportsbook-odds")
					under = await tds[1].query_selector(".sportsbook-odds")
					if not odds:
						continue

					#print(game, prop, player, line)
					if line in data[game][prop][player]:
						over = data[game][prop][player][line]
						if "/" in over:
							continue
						if int(over) < int(odds.text.replace("\u2212", "-")):
							over = odds.text.replace("\u2212", "-")
						data[game][prop][player][line] = over
						if under:
							data[game][prop][player][line] += "/"+under.text.replace("\u2212", "-")
					else:
						data[game][prop][player][line] = odds.text.replace("\u2212", "-")
						if under:
							data[game][prop][player][line] += "/"+under.text.replace("\u2212", "-")

		updateData(file, data)
		q.task_done()

	browser.stop()

def updateData(file, data):
	if data:
		with lock:
			with open(file) as fh:
				d = json.load(fh)
			merge_dicts(d, data)
			with open(file, "w") as fh:
				json.dump(d, fh, indent=4)

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("--bet365", action="store_true")
	parser.add_argument("--fd", action="store_true")
	parser.add_argument("--espn", action="store_true")
	parser.add_argument("--mgm", action="store_true")
	parser.add_argument("--dk", action="store_true")
	parser.add_argument("--keep", action="store_true")
	parser.add_argument("--tomorrow", action="store_true")
	parser.add_argument("--tmrw", action="store_true")
	parser.add_argument("--threads", type=int, default=7)
	parser.add_argument("--team", "-t")
	parser.add_argument("--prop", "-p")
	parser.add_argument("--sport")
	parser.add_argument("--league")

	args = parser.parse_args()

	if args.bet365:
		games = uc.loop().run_until_complete(get365Links(args.sport, args.keep))
		runThreads("bet365", args.sport, games, args.threads, args.keep)
	if args.fd:
		games = uc.loop().run_until_complete(getFDLinks(args.sport))
		#games = {}
		#games["vgk @ det"] = "/ice-hockey/nhl/vegas-golden-knights-@-detroit-red-wings-34126907"
		runThreads("fanduel", args.sport, games, args.threads)

	if args.espn:
		games = uc.loop().run_until_complete(getESPNLinks(args.sport, args.tomorrow or args.tmrw))
		#games = {}
		#games["vgk @ det"] = "https://espnbet.com/sport/hockey/organization/united-states/competition/nhl/event/381a07af-75f9-4bef-ae27-d9305981f79d"
		runThreads("espn", args.sport, games, args.threads)

	if args.mgm:
		games = uc.loop().run_until_complete(getMGMLinks(args.sport))
		#games = {}
		#games["vgk @ det"] = "/en/sports/events/vegas-golden-knights-at-detroit-red-wings-17082663"
		runThreads("mgm", args.sport, games, args.threads)

	if args.dk:
		games = uc.loop().run_until_complete(getDKLinks(args.sport))
		runThreads("draftkings", args.sport, games, args.threads, args.keep)

