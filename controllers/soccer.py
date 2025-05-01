from flask import *
from datetime import datetime,timedelta
from subprocess import call
from bs4 import BeautifulSoup as BS
try:
	from shared import convertSoccer, convertImpOdds, convertAmericanFromImplied
except:
	from controllers.shared import convertSoccer, convertImpOdds, convertAmericanFromImplied
import math
import json
import os
import re
import argparse
import unicodedata
import time
from twilio.rest import Client

soccerprops_blueprint = Blueprint('soccerprops', __name__, template_folder='views')

prefix = ""
if os.path.exists("/home/zhecht/playerprops"):
	# if on linux aka prod
	prefix = "/home/zhecht/playerprops/"
elif os.path.exists("/home/playerprops/playerprops"):
	# if on linux aka prod
	prefix = "/home/playerprops/playerprops/"

def parsePlayer(player):
	player = strip_accents(player).lower().replace(".", "").replace("'", "").replace("-", " ").replace(" jr", "").replace(" iii", "").replace(" ii", "")
	if player == "mohammed diomande":
		player = "mohamed diomande"
	elif player == "ivanan":
		return "ivan ivan"
	elif player == "toral bayramov":
		player = "tural bayramov"
	elif player == "matt godden":
		player = "matthew godden"
	elif player == "danilo orsi":
		player = "danilo orsi dadomo"
	elif player == "will wright":
		return "william wright"
	elif player == "paddy madden":
		return "patrick madden"
	elif player == "macauley southam hales":
		return "macauley southam"
	elif player == "emmanuel osadebe":
		return "emma osaoabe"
	elif player == "chris maguire":
		return "christopher maguire"
	elif player == "tam oware":
		return "thomas oware"
	elif player == "cameron odonnel":
		return "cameron odonnell"
	elif player == "morgyn neill":
		return "morgyn neil"
	elif player == "jon robertson":
		return "john robertson"
	elif player == "joshua debayo":
		return "josh debayo"
	elif player == "cammy ballantyne":
		return "cameron ballantyne"
	elif player == "emerson urso":
		return "emerson lima"
	elif player == "marc casado torras":
		return "marc casado"
	elif player == "xavi quintilla":
		return "xavier quintilla"
	elif player == "emerson marcelina":
		return "marcelina emerson"
	elif player == "savio":
		return "savinho"
	return player

@soccerprops_blueprint.route('/soccerprops')
def props_route():
	with open("static/soccer/ev.json") as fh:
		dataIn = json.load(fh)
	data = []
	for key in dataIn:
		if dataIn[key]["player"]:
			data.append(dataIn[key])
	#print(data[0])
	return render_template("soccerprops.html", data=data)

def parseTeam(player):
	return strip_accents(player).lower().replace(".", "").replace("'", "").replace(" ", "-")

def strip_accents(text):
	try:
		text = unicode(text, 'utf-8')
	except NameError: # unicode is a default on python 3 
		pass

	text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode("utf-8")

	return str(text)

def convertDecOdds(odds):
	if odds == 0:
		return 0
	if odds > 0:
		decOdds = 1 + (odds / 100)
	else:
		decOdds = 1 - (100 / odds)
	return decOdds

def convertAmericanOdds(avg):
	if avg >= 2:
		avg = (avg - 1) * 100
	else:
		avg = -100 / (avg - 1)
	return round(avg)

def writeCorners():
	outfile = f"soccerout"

	time.sleep(0.3)
	os.system(f"curl 'https://www.windrawwin.com/statistics/corners/usa-major-league-soccer/' --compressed -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0' -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8' -H 'Accept-Language: en-US,en;q=0.5' -H 'Referer: https://www.windrawwin.com/results/houston/' -H 'Alt-Used: www.windrawwin.com' -H 'Connection: keep-alive' -H 'Cookie: ASPSESSIONIDCUCSSQDA=HHEJKDNAFOCPOKLJBGFHEMPC; ASPSESSIONIDSGASSQDC=BPCMDAKAMJEFEDHEJCKPCFGO; ASPSESSIONIDQGAQTSBD=LEJCKKBBBABAADPNEPCLABOK; ASPSESSIONIDSGCRRTDD=NCHDOFOAPEEKDHKLNBOGBFAJ; ASPSESSIONIDAWCRQRBA=AMCJLPHAGNKDNMLIOCOMPNIP; ASPSESSIONIDSECRRQBC=NFHDHIKAAEAEOMKOGHFGMLFM; ASPSESSIONIDCWBTSRCA=IKKMLILABMLJPHJFKCBOEKDN; ASPSESSIONIDCWDRQQAB=JBPBCDDBENAMAKALOGMDGIHM; ASPSESSIONIDCUBRSRBA=DHLOOPIAGACHNJLMCHHJDFKH; ASPSESSIONIDCUASQQAB=ECDMPFNACBJAMOMGBGKMONOE; ASPSESSIONIDCUBSRRAA=MFKEMAMAKIEALAJCOBIODOFK; ASPSESSIONIDCWATSQBD=CGEDIALACLIBEALNDCHMEFPK; ASPSESSIONIDSGDSQTCC=AKHHIHHAMJMPGKJMHLIHLHFN; ASPSESSIONIDAWCTTQAD=EIFOMCCBKOAIKPAGLDCEEGHJ; ASPSESSIONIDSGATRSDC=NDOAGCBBDDJOFCDIJDOMNLOA; ASPSESSIONIDCWBSRQAA=BPMABIJANMELHBNLLBFDAHEK; ASPSESSIONIDQGBQRSDC=FPDIBMGBJPIFODLKHJNINGOI; ASPSESSIONIDAUAQTQAB=HNBMIJOAHFJPALBNFPNBPNHO; ASPSESSIONIDQGCQTRAD=LJEJFDEBPBEHIDCGDBBEBHOG; ASPSESSIONIDAUDTSSAA=HJJIDBNAJNAHGEOGGJHPFCEO; ASPSESSIONIDSEBSQRDD=JEPIMLFBBLIAHDHPCGCEMNDM; ASPSESSIONIDAUARQSCA=KPFHEMGBGECIIFMCLEJBMICL; ASPSESSIONIDCWBSQRBB=DDLJILEBGHOMMHOOKAMOEBKL; ASPSESSIONIDSECSQRAC=AKPDOKCBPIIMIOHENMMPHMKP; ASPSESSIONIDAUCTTRAC=MDCGEKABKMGEIEFLHJLIHPJK; ASPSESSIONIDAWAQRQBD=OAFHGMHBNEJGNOGLDIBFCLBC; ASPSESSIONIDCWDSSQAA=LMALIPJBLDEOIEGLABGNPMGA; ASPSESSIONIDAUCSTRAC=CGKIBNJBMFOPLEDNFFLNEMAJ; ASPSESSIONIDAUCRRTCA=AODPGFLBLHPNCPJGHAGMNMHD; ASPSESSIONIDAUAQRQCA=EBNKINABAILCPGBHILFMEEBJ; ASPSESSIONIDCUBRRRDB=PKBPBCABKELBKGDIHCPBBPGI; ASPSESSIONIDQEDSRQBD=JKEJKMIBBEPDOKHJKCJEKKHG' -o {outfile}")

	soup = BS(open(outfile, 'rb').read(), "lxml")
	totals = {}

	leagues = {}
	for league in soup.find("select", id="leaguenav").find_all("option"):
		if league.get("value"):
			leagues[league.text.lower()] = league.get("value").split("/")[-2]

	for league in leagues:
		time.sleep(0.3)
		os.system(f"curl 'https://www.windrawwin.com/statistics/corners/{leagues[league]}/' --compressed -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0' -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8' -H 'Accept-Language: en-US,en;q=0.5' -H 'Referer: https://www.windrawwin.com/results/houston/' -H 'Alt-Used: www.windrawwin.com' -H 'Connection: keep-alive' -H 'Cookie: ASPSESSIONIDCUCSSQDA=HHEJKDNAFOCPOKLJBGFHEMPC; ASPSESSIONIDSGASSQDC=BPCMDAKAMJEFEDHEJCKPCFGO; ASPSESSIONIDQGAQTSBD=LEJCKKBBBABAADPNEPCLABOK; ASPSESSIONIDSGCRRTDD=NCHDOFOAPEEKDHKLNBOGBFAJ; ASPSESSIONIDAWCRQRBA=AMCJLPHAGNKDNMLIOCOMPNIP; ASPSESSIONIDSECRRQBC=NFHDHIKAAEAEOMKOGHFGMLFM; ASPSESSIONIDCWBTSRCA=IKKMLILABMLJPHJFKCBOEKDN; ASPSESSIONIDCWDRQQAB=JBPBCDDBENAMAKALOGMDGIHM; ASPSESSIONIDCUBRSRBA=DHLOOPIAGACHNJLMCHHJDFKH; ASPSESSIONIDCUASQQAB=ECDMPFNACBJAMOMGBGKMONOE; ASPSESSIONIDCUBSRRAA=MFKEMAMAKIEALAJCOBIODOFK; ASPSESSIONIDCWATSQBD=CGEDIALACLIBEALNDCHMEFPK; ASPSESSIONIDSGDSQTCC=AKHHIHHAMJMPGKJMHLIHLHFN; ASPSESSIONIDAWCTTQAD=EIFOMCCBKOAIKPAGLDCEEGHJ; ASPSESSIONIDSGATRSDC=NDOAGCBBDDJOFCDIJDOMNLOA; ASPSESSIONIDCWBSRQAA=BPMABIJANMELHBNLLBFDAHEK; ASPSESSIONIDQGBQRSDC=FPDIBMGBJPIFODLKHJNINGOI; ASPSESSIONIDAUAQTQAB=HNBMIJOAHFJPALBNFPNBPNHO; ASPSESSIONIDQGCQTRAD=LJEJFDEBPBEHIDCGDBBEBHOG; ASPSESSIONIDAUDTSSAA=HJJIDBNAJNAHGEOGGJHPFCEO; ASPSESSIONIDSEBSQRDD=JEPIMLFBBLIAHDHPCGCEMNDM; ASPSESSIONIDAUARQSCA=KPFHEMGBGECIIFMCLEJBMICL; ASPSESSIONIDCWBSQRBB=DDLJILEBGHOMMHOOKAMOEBKL; ASPSESSIONIDSECSQRAC=AKPDOKCBPIIMIOHENMMPHMKP; ASPSESSIONIDAUCTTRAC=MDCGEKABKMGEIEFLHJLIHPJK; ASPSESSIONIDAWAQRQBD=OAFHGMHBNEJGNOGLDIBFCLBC; ASPSESSIONIDCWDSSQAA=LMALIPJBLDEOIEGLABGNPMGA; ASPSESSIONIDAUCSTRAC=CGKIBNJBMFOPLEDNFFLNEMAJ; ASPSESSIONIDAUCRRTCA=AODPGFLBLHPNCPJGHAGMNMHD; ASPSESSIONIDAUAQRQCA=EBNKINABAILCPGBHILFMEEBJ; ASPSESSIONIDCUBRRRDB=PKBPBCABKELBKGDIHCPBBPGI; ASPSESSIONIDQEDSRQBD=JKEJKMIBBEPDOKHJKCJEKKHG' -o {outfile}")

		soup = BS(open(outfile, 'rb').read(), "lxml")
		for row in soup.find_all("div", class_="wttr2"):
			if not row.find("a") or not row.find("div", class_="statteam"):
				continue
			team = convertSoccer(row.find("a").text.lower()).replace("sj", "sj earthquakes")
			corners = float(row.find("div", class_="statpld").text)
			cornersAgainst = float(row.find("div", class_="statnum").text)

			totals[team] = {
				"corners": corners,
				"cornersAgainst": cornersAgainst,
				"cornersTotal": round(corners+cornersAgainst, 1),
				"link": row.find("a").get("href").split("/")[-2],
				"league": league
			}

	with open("static/soccer/corners.json", "w") as fh:
		json.dump(totals, fh, indent=4)

def writeLeagues(bookArg):
	with open("static/soccer/leagues.json") as fh:
		leagues = json.load(fh)

	for book in ["pn", "bv", "dk", "kambi"]:
		if bookArg and book != bookArg:
			continue
		outfile = "outsoccer"

		if book == "pn":
			url = 'curl "https://guest.api.arcadia.pinnacle.com/0.1/sports/29/leagues?all=false&brandId=0" --compressed -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0" -H "Accept: application/json" -H "Accept-Language: en-US,en;q=0.5" -H "Referer: https://www.pinnacle.com/" -H "Content-Type: application/json" -H "X-API-Key: CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R" -H "X-Device-UUID: 66ac2815-a68dc902-a5052c0c-c60f3d05" -H "Origin: https://www.pinnacle.com" -H "Connection: keep-alive" -H "Sec-Fetch-Dest: empty" -H "Sec-Fetch-Mode: cors" -H "Sec-Fetch-Site: same-site" -H "Pragma: no-cache" -H "Cache-Control: no-cache" -o '+outfile
			os.system(url)
			with open(outfile) as fh:
				data = json.load(fh)

			leagues["pn"] = {}
			for row in data:
				name = row["name"].lower()
				leagues["pn"][name] = row["id"]
		elif book == "bv":
			url = "https://services.bovada.lv/services/sports/event/v2/nav/A/description/soccer?lang=en"
			os.system(f"curl -k \"{url}\" -o {outfile}")
			with open(outfile) as fh:
				data = json.load(fh)

			links = []
			print()
			for row in data["children"]:
				links.append(row["link"])

			leagues["bv"] = {}
			childLinks = []
			for link in links:
				url = f"https://services.bovada.lv/services/sports/event/v2/nav/A/description{link}?lang=en"
				time.sleep(0.2)
				os.system(f"curl -k \"{url}\" -o {outfile}")
				with open(outfile) as fh:
					data = json.load(fh)
				for row in data["children"]:
					childLinks.append(row["link"])

			for link in childLinks:
				url = f"https://services.bovada.lv/services/sports/event/v2/nav/A/description{link}?lang=en"
				time.sleep(0.2)
				os.system(f"curl -k \"{url}\" -o {outfile}")
				with open(outfile) as fh:
					data = json.load(fh)
				current = data["current"]["description"]
				for row in data["children"]:
					leagues["bv"][current+" "+row["description"]] = row["link"]
		elif book == "dk":
			url = "https://sportsbook.draftkings.com/sports/soccer"
			time.sleep(0.2)
			#os.system(f"curl -k \"{url}\" -o {outfile}")

			soup = BS(open(outfile, 'rb').read(), "lxml")

			data = "{}"
			for script in soup.find_all("script"):
				if not script.string:
					continue
				if "__INITIAL_STATE" in script.string:
					m = re.search(r"__INITIAL_STATE__ = {(.*?)};", script.string)
					if m:
						data = m.group(1).replace("false", "False").replace("true", "True").replace("null", "None")
						data = f"{{{data}}}"
						break

			data = eval(data)
			leagues["dk"] = {}
			for row in data["sports"]["data"]:
				if row["displayName"] != "Soccer":
					continue
				for event in row["eventGroupInfos"]:
					leagues["dk"][event["eventGroupId"]] = event["eventGroupName"]
		elif book == "kambi":
			url = "https://eu-offering-api.kambicdn.com/offering/v2018/pivuslarl-lbr/group.json?lang=en_US&market=US&client_id=2&ncid=1695395534961"

			time.sleep(0.2)
			os.system(f"curl -k \"{url}\" -o {outfile}")
			with open(outfile) as fh:
				data = json.load(fh)

			leagues["kambi"] = {}
			for group in data["group"]["groups"]:
				if group["name"] != "Soccer":
					continue
				for league in group["groups"]:
					leagues["kambi"][league["termKey"]] = league["id"]
	

	with open("static/soccer/leagues.json", "w") as fh:
		json.dump(leagues, fh, indent=4)


def writePinnacle(date, debug=None):
	if not date:
		date = str(datetime.now())[:10]

	outfile = f"socceroutPN"

	res = {}
	
	with open("static/soccer/leagues.json") as fh:
		leagues = json.load(fh)

	if False:
		leagues = {
			"pn": {
				"uefa - champions league": 2627
			}
		}

	for league in leagues["pn"]:
		url = 'curl "https://guest.api.arcadia.pinnacle.com/0.1/leagues/'+str(leagues["pn"][league])+'/matchups?brandId=0" --compressed -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0" -H "Accept: application/json" -H "Accept-Language: en-US,en;q=0.5" -H "Referer: https://www.pinnacle.com/" -H "Content-Type: application/json" -H "X-API-Key: CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R" -H "X-Device-UUID: 66ac2815-a68dc902-a5052c0c-c60f3d05" -H "Origin: https://www.pinnacle.com" -H "Connection: keep-alive" -H "Sec-Fetch-Dest: empty" -H "Sec-Fetch-Mode: cors" -H "Sec-Fetch-Site: same-site" -H "Pragma: no-cache" -H "Cache-Control: no-cache" -o '+outfile

		time.sleep(0.2)
		os.system(url)
		with open(outfile) as fh:
			data = json.load(fh)

		ids = []
		for row in data:
			if str(datetime.strptime(row["startTime"], "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=4))[:10] != date:
				continue
			if row["parent"] and row["parent"]["id"] not in ids:
				ids.append(row["parent"]["id"])

		#ids = ["1601362569"]
		for bid in ids:
			url = 'curl "https://guest.api.arcadia.pinnacle.com/0.1/matchups/'+str(bid)+'/related" --compressed -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0" -H "Accept: application/json" -H "Accept-Language: en-US,en;q=0.5" -H "Referer: https://www.pinnacle.com/" -H "Content-Type: application/json" -H "X-API-Key: CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R" -H "X-Device-UUID: 66ac2815-a68dc902-a5052c0c-c60f3d05" -H "Origin: https://www.pinnacle.com" -H "Connection: keep-alive" -H "Sec-Fetch-Dest: empty" -H "Sec-Fetch-Mode: cors" -H "Sec-Fetch-Site: same-site" -H "Pragma: no-cache" -H "Cache-Control: no-cache" -H "TE: trailers" -o '+outfile

			time.sleep(0.3)
			os.system(url)
			with open(outfile) as fh:
				related = json.load(fh)

			relatedData = {}
			for row in related:
				if True or "special" in row:
					try:
						prop = row["units"].lower()
					except:
						continue

					over = under = 0
					if "id" in row["participants"][0]:
						over = row["participants"][0]["id"]
						under = row["participants"][1]["id"]
						if row["participants"][0]["name"] == "Under":
							over, under = under, over
					player = ""
					if "special" in row:
						player = parsePlayer(row["special"]["description"].split(" (")[0])
					relatedData[row["id"]] = {
						"player": player,
						"prop": prop,
						"over": over,
						"under": under
					}

			if debug:
				with open("t2", "w") as fh:
					json.dump(related, fh, indent=4)

			url = 'curl "https://guest.api.arcadia.pinnacle.com/0.1/matchups/'+str(bid)+'/markets/related/straight" --compressed -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0" -H "Accept: application/json" -H "Accept-Language: en-US,en;q=0.5" -H "Referer: https://www.pinnacle.com/" -H "Content-Type: application/json" -H "X-API-Key: CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R" -H "X-Device-UUID: 66ac2815-a68dc902-a5052c0c-c60f3d05" -H "Origin: https://www.pinnacle.com" -H "Connection: keep-alive" -H "Sec-Fetch-Dest: empty" -H "Sec-Fetch-Mode: cors" -H "Sec-Fetch-Site: same-site" -H "Pragma: no-cache" -H "Cache-Control: no-cache" -H "TE: trailers" -o '+outfile

			time.sleep(0.3)
			os.system(url)
			with open(outfile) as fh:
				data = json.load(fh)

			if debug:
				with open("t3", "w") as fh:
					json.dump(data, fh, indent=4)

			try:
				gamesMatchup = related[0]["id"] if related[0]["units"] == "Games" else related[1]["id"]
			except:
				gamesMatchup = ""
			try:
				player1 = related[0]["participants"][0]["name"].lower()
				player2 = related[0]["participants"][1]["name"].lower()
			except:
				continue

			game = f"{convertSoccer(player1)} v {convertSoccer(player2)}"
			if game in res:
				continue
			res[game] = {}

			for row in data:
				try:
					prop = row["type"]
				except:
					continue
				keys = row["key"].split(";")

				prefix = ""
				if keys[1] == "1":
					prefix = "1h_"
				elif keys[1] == "3":
					prefix = "2h_"

				overId = underId = 0
				player = ""

				#if row["matchupId"] == 1578461072:
				#	print(relatedData[1578461072])

				if row["matchupId"] != int(bid):
					if row["matchupId"] not in relatedData:
						continue
					player = relatedData[row["matchupId"]]["player"]
					prop = relatedData[row["matchupId"]]["prop"]
					overId = relatedData[row["matchupId"]]["over"]
					underId = relatedData[row["matchupId"]]["under"]

					if "regular" in prop:
						if "draw no bet" in player:
							prop = "dnb"
						elif player == "both teams to score?" or player == "both teams to score? 1st half":
							prop = "btts"
						else:
							continue

					elif prop == "corners" and row["type"] == "spread":
						prop = "corners_spread"
				else:
					pass

				if prop == "moneyline":
					continue

				if prop == "goals":
					prop = "atgs"
					if prop not in res[game]:
						res[game][prop] = {}

				prop = f"{prefix}{prop}"
				switched = 0
				prices = row["prices"]
				if overId:
					try:
						ou = f"{prices[0]['price']}/{prices[1]['price']}"
					except:
						continue
					if prices[0]["participantId"] == underId:
						ou = f"{prices[1]['price']}/{prices[0]['price']}"
						switched = 1

					if prop == "atgs":
						player = parsePlayer(player[5:-6])
						res[game][prop][player] = ou
					elif "dnb" in prop or "btts" in prop:
						res[game][prop] = ou
						continue

					if prop not in res[game]:
						res[game][prop] = {}

					if "points" in prices[0] and prop not in []:
						handicap = str(prices[switched]["points"])
						res[game][prop][player] = handicap+" "+ou
					else:
						res[game][prop][player] = ou
				else:
					ou = f"{prices[0]['price']}/{prices[1]['price']}"
					if "points" in prices[0]:
						handicap = str(prices[0]["points"])
						if prop not in res[game]:
							res[game][prop] = {}
						try:
							res[game][prop][handicap] = ou
						except:
							continue
					else:
						res[game][prop] = ou

	with open("static/soccer/pinnacle.json", "w") as fh:
		json.dump(res, fh, indent=4)


def writeMGM(date=None):

	if not date:
		date = str(datetime.now())[:10]

	res = {}
	#leagues = {102849: "mls", 102855: "champions", 102856: "uefa europa league", 102919: "efa europa conference league", 102841: "epl", 102829: "la liga", 	102842: "bundesliga", 102846: "serie a", 102843: "ligue 1", 102373: "liga mx", 101551: "league one", 101550: "league two", 102782: "efl", 102717: "china"}
	for tourney in [None]:
		url = f"https://sports.mi.betmgm.com/cds-api/bettingoffer/fixtures?x-bwin-accessid=NmFjNmUwZjAtMGI3Yi00YzA3LTg3OTktNDgxMGIwM2YxZGVh&lang=en-us&country=US&userCountry=US&subdivision=US-Michigan&fixtureTypes=Standard&state=Latest&offerMapping=Filtered&offerCategories=Gridable&fixtureCategories=Gridable,NonGridable,Other&sportIds=4&regionIds=&competitionIds=&conferenceIds=&isPriceBoost=false&statisticsModes=SeasonStandings&skip=0&take=150&sortBy=StartDate"
		outfile = f"socceroutMGM"

		time.sleep(0.3)
		os.system(f"curl -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0' -k \"{url}\" -o {outfile}")

		with open(outfile) as fh:
			data = json.load(fh)

		ids = []
		for row in data.get("fixtures", []):
			if str(datetime.strptime(row["startDate"], "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=4))[:10] != date:
				continue
			ids.append(row["id"])

		#ids = ["2:7515348"]
		for mgmid in ids:
			url = f"https://sports.mi.betmgm.com/cds-api/bettingoffer/fixture-view?x-bwin-accessid=NmFjNmUwZjAtMGI3Yi00YzA3LTg3OTktNDgxMGIwM2YxZGVh&lang=en-us&country=US&userCountry=US&subdivision=US-Michigan&offerMapping=All&scoreboardMode=Full&fixtureIds={mgmid}&state=Latest&includePrecreatedBetBuilder=true&supportVirtual=false&useRegionalisedConfiguration=true&includeRelatedFixtures=false&statisticsModes=All"
			time.sleep(0.3)
			os.system(f"curl -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0' -k \"{url}\" -o {outfile}")

			with open(outfile) as fh:
				data = json.load(fh)

			try:
				data = data["fixture"]
			except:
				continue
			game = strip_accents(data["name"]["value"].lower())

			try:
				p1, p2 = map(str, game.split(" - "))
				game = f"{convertSoccer(p1)} v {convertSoccer(p2)}"
			except:
				continue

			res[game] = {}
			for row in data["optionMarkets"]:
				prop = row["name"]["value"].lower()

				prefix = ""
				if "1st half" in prop:
					prefix = "1h_"
				if "2nd half" in prop:
					prefix = "2h_"

				if ";" in prop:
					continue
				if "draw no bet" in prop:
					if "and" in prop:
						continue
					prop = "dnb"
				elif "both teams to score" in prop:
					if "and" in prop or "both halves" in prop:
						continue
					prop = "btts"
				elif "anytime goalscorer" in prop:
					prop = "atgs"
				elif "2way handicap" in prop:
					prop = "spread"
				elif "total corners" in prop:
					if ":" in prop or "odd" in prop:
						continue
					if p1 in prop:
						prop = "home_corners"
					elif p2 in prop:
						prop = "away_corners"
					else:
						prop = "corners"
				elif "total goals" in prop:
					if "exact" in prop or "odd/even" in prop or "bands" in prop or "and" in prop or ":" in prop:
						continue
					if "match result" in prop or "double chance" in prop:
						continue
					if p1 in prop:
						prop = "home_total"
					elif p2 in prop:
						prop = "away_total"
					else:
						prop = "total"
				else:
					continue

				prop = f"{prefix}{prop}"

				results = row['options']
				try:
					ou = f"{results[0]['price']['americanOdds']}"
				except:
					continue
				if len(results) > 1 and "americanOdds" in results[1]["price"]:
					ou += f"/{results[1]['price']['americanOdds']}"
				if "dnb" in prop or "btts" in prop:
					res[game][prop] = ou
				elif len(results) >= 2:
					if prop not in res[game]:
						res[game][prop] = {}

					skip = 1 if prop == "atgs" else 2
					for idx in range(0, len(results), skip):
						val = results[idx]["name"]["value"].lower()
						if "spread" in prop:
							val = val.split(" ")[-1][1:-1]
						elif "corners" in prop:
							val = val.split(" ")[-1]
						ou = str(results[idx]['price']["americanOdds"])
						if prop in ["atgs"]:
							val = parsePlayer(val)
							res[game][prop][val] = ou
						else:
							try:
								ou = f"{results[idx]['price']['americanOdds']}/{results[idx+1]['price']['americanOdds']}"
							except:
								continue
							res[game][prop][str(float(val.replace(',', '.').split(" ")[-1]))] = ou

	with open("static/soccer/mgm.json", "w") as fh:
		json.dump(res, fh, indent=4)

def writeBovada(date=None):
	url = "https://www.bovada.lv/sports/soccer/"

	if not date:
		date = str(datetime.now())[:10]

	leagues = []

	leagues.extend([
		"europe/belgium/first-division-a",
		"europe/england/championship",
		"europe/england/premier-league", 
		"europe/england/league-one",
		"europe/france/ligue-1",
		"europe/germany/1-bundesliga",
		"europe/italy/serie-a",
		"europe/spain/la-liga",

		"international-club/uefa-champions-league",
		"international-club/uefa-europa-conference-league",
		"international-club/uefa-europa-league",

		"north-america/united-states/mls",
		"north-america/mexico/liga-mx-apertura"

		"south-america/argentina/copa-de-la-liga-profesional",
		"south-america/argentina/primera-nacional",
		"south-america/brazil/brasileirao-serie-a",
		"south-america/brazil/brasileiro-serie-b",
		"south-america/chile/primera-b",
		"south-america/chile/primera-division",
		"south-america/colombia/primera-a-clausura",
		"south-america/colombia/primera-b",
		"south-america/peru/primera-division",
	])

	outfile = f"socceroutBV"

	with open("static/soccer/leagues.json") as fh:
		leagues = json.load(fh)["bv"]

	ids = []
	for which in leagues:
		#continue
		if which != "UEFA Champions League":
			pass
			#continue
		url = f"https://www.bovada.lv/services/sports/event/coupon/events/A/description{leagues[which]}?marketFilterId=def&preMatchOnly=true&eventsLimit=5000&lang=en"

		time.sleep(0.3)
		os.system(f"curl -k \"{url}\" -o {outfile}")

		with open(outfile) as fh:
			data = json.load(fh)

		try:
			for link in data[0]["events"]:
				if str(datetime.fromtimestamp(link["startTime"] / 1000) - timedelta(hours=2))[:10] != date:
					continue
				ids.append(link["link"])
		except:
			continue

	res = {}
	
	#ids = ['/soccer/europe/england/premier-league-2-u21/west-bromwich-albion-u21-reading-u21-202412161400']
	for link in ids:
		url = f"https://www.bovada.lv/services/sports/event/coupon/events/A/description{link}?lang=en"
		time.sleep(0.3)
		os.system(f"curl -k \"{url}\" -o {outfile}")

		with open(outfile) as fh:
			data = json.load(fh)

		try:
			comp = data[0]['events'][0]['competitors']
		except:
			continue
		player1 = strip_accents(comp[0]['name'].lower())
		player2 = strip_accents(comp[1]['name'].lower())
		game = f"{convertSoccer(player1)} v {convertSoccer(player2)}"

		res[game] = {}

		for row in data[0]["events"][0]["displayGroups"]:
			desc = row["description"].lower()

			if desc in ["game lines", "alternate lines", "both teams to score", "player props", "corner props", "game stats"]:
				for market in row["markets"]:

					prefix = ""
					if market["period"]["abbreviation"] == "1H":
						prefix = "1h_"

					prop = market["description"].lower()
					if prop == "spread" or prop == "goal spread":
						prop = "spread"
					elif "draw no bet" in prop:
						prop = "dnb"
					elif prop == "total" or "total goals" in prop:
						if "exact" in prop or "&" in prop or "and" in prop or "asian" in prop:
							continue
						if player1 in strip_accents(prop):
							prop = "home_total"
						elif player2 in strip_accents(prop):
							prop = "away_total"
						else:
							prop = "total"
					elif prop == "both teams to score":
						prop = "btts"
					elif prop == "anytime goal scorer":
						prop = "atgs"
					elif prop == "to assist a goal":
						prop = "assist"
					elif prop == "to score or assist a goal":
						prop = "goal_assist"
					elif "total corners" in prop:
						if player1 in strip_accents(prop):
							prop = "home_corners"
						elif player2 in strip_accents(prop):
							prop = "away_corners"
						elif prop == "total corners handicap":
							prop = "corners_spread"
						else:
							prop = "corners"
					elif "total attempts" in prop:
						suffix = ""
						if "on-target" in prop:
							suffix = "_on_target"

						if player1 in strip_accents(prop):
							prop = "home_shots"
						elif player2 in strip_accents(prop):
							prop = "away_shots"
						elif prop == "total attempts" or prop == "total attempts on target":
							prop = "game_shots"
						else:
							prop = "player_shots"

						prop += suffix
					elif "total tackles" in prop:
						if player1 in strip_accents(prop):
							prop = "home_tackles"
						elif player2 in strip_accents(prop):
							prop = "away_tackles"
						elif prop == "total tackles":
							prop = "game_tackles"
						else:
							prop = "player_tackles"
					elif "total offsides" in prop:
						if player1 in strip_accents(prop):
							prop = "home_offsides"
						elif player2 in strip_accents(prop):
							prop = "away_offsides"
						else:
							prop = "offsides"
					else:
						continue

					prop = f"{prefix}{prop}"

					#if market["period"]["main"] == False:
					#	continue

					if not len(market["outcomes"]):
						continue

					if "dnb" in prop or prop in ["btts"]:
						try:
							res[game][prop] = f"{market['outcomes'][0]['price']['american']}/{market['outcomes'][1]['price']['american']}".replace("EVEN", "100")
						except:
							continue
					else:
						if prop not in res[game]:
							res[game][prop] = {}

						outcomes = market["outcomes"]
						skip = 1 if prop in ["atgs", "assist", "goal_assist"] else 2
						for idx in range(0, len(outcomes), skip):
							if "handicap" not in outcomes[idx]["price"]:
								if "tackles" in prop or "offsides" in prop or "shots" in prop:
									handicap = outcomes[idx]["description"].split(" ")[-1]
								else:
									handicap = parsePlayer(outcomes[idx]["description"].split(" - ")[-1])
							else:
								handicap = str(float(outcomes[idx]["price"]["handicap"]))
								if "handicap2" in outcomes[idx]["price"]:
									handicap = str((float(handicap) + float(outcomes[idx]["price"]["handicap2"])) / 2)

							ou = f"{market['outcomes'][idx]['price']['american']}"
							if skip == 2:
								try:
									under = f"{market['outcomes'][idx+1]['price']['american']}"
									if market["outcomes"][idx+1]["description"] == "Over":
										ou = under+"/"+ou
									else:
										ou += "/"+under
								except:
									continue

							if "player" in prop:
								handicap = parsePlayer(market["description"].split(" - ")[-1])
								if handicap not in res[game][prop]:
									res[game][prop][handicap] = {}
								line = outcomes[idx]["description"].split(" ")[-1]
								res[game][prop][handicap][line] = ou.replace("EVEN", "100")
							elif prop == "assist":
								if handicap not in res[game][prop]:
									res[game][prop][handicap] = {}
								res[game][prop][handicap]["0.5"] = ou.replace("EVEN", "100")
							else:
								res[game][prop][handicap] = ou.replace("EVEN", "100")

		with open("static/soccer/bovada.json", "w") as fh:
			json.dump(res, fh, indent=4)

	with open("static/soccer/bovada.json", "w") as fh:
		json.dump(res, fh, indent=4)

def writeKambi(date=None):
	data = {}
	outfile = f"soccerout.json"

	if not date:
		date = str(datetime.now())[:10]

	leagues = [
		"brazil/brasileirao_serie_a",
		"brazil/brasileirao_serie_b",
		"champions_league/all",
		"china/super_league",
		"england/premier_league",
		"england/efl_cup",
		"england/league_one",
		"england/league_two",
		"england/the_championship",
		"europa_conference_league/all",
		"europa_league/all",
		"france/ligue_1",
		"france/ligue_2",
		"germany/bundesliga",
		"italy/serie_a",
		"italy/serie_b",
		"mexico/liga_mx",
		"spain/la_liga",
		"spain/la_liga_2",
		"uefa_nations_league__w_",
		"usa/mls",
	]

	if False:
		leagues = [
			"champions_league/all",
		]

	with open("static/soccer/leagues.json") as fh:
		leagues = json.load(fh)["kambi"]

	for gender in leagues:
		url = f"https://eu-offering-api.kambicdn.com/offering/v2018/pivuslarl-lbr/listView/football/{gender}/all/all/matches.json?lang=en_US&market=US"
		time.sleep(0.2)
		os.system(f"curl -k \"{url}\" -o {outfile}")
		
		with open(outfile) as fh:
			j = json.load(fh)

		eventIds = {}

		if "events" not in j:
			continue

		fullTeams = {}
		for event in j["events"]:
			game = event["event"]["name"].lower()
			player1, player2 = map(str, game.split(f" {event['event']['nameDelimiter']} "))
			game = f"{convertSoccer(player1)} v {convertSoccer(player2)}"
			fullTeams[game] = [strip_accents(player1).replace("munich", "munchen"), strip_accents(player2).replace("munich", "munchen")]
			if game in eventIds:
				continue

			if event["event"]["state"] == "STARTED":
				continue
			eventIds[game] = event["event"]["id"]
			data[game] = {}


		#eventIds = {"leipzig v aston villa": 1021554748}
		for game in eventIds:
			eventId = eventIds[game]
			teamIds = {}

			player1, player2 = fullTeams[game]
			
			time.sleep(0.3)
			url = f"https://eu-offering-api.kambicdn.com/offering/v2018/pivuslarl-lbr/betoffer/event/{eventId}.json"
			os.system(f"curl -k \"{url}\" -o {outfile}")

			with open(outfile) as fh:
				j = json.load(fh)

			if "closed" not in j["betOffers"][0]:
				continue

			if str(datetime.strptime(j["betOffers"][0]["closed"], "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=4))[:10] != date:
				continue

			player1 = strip_accents(j["events"][0]["awayName"].lower())
			player2 = strip_accents(j["events"][0]["homeName"].lower())

			i = 0
			for betOffer in j["betOffers"]:
				label = strip_accents(betOffer["criterion"]["label"].lower())

				prefix = ""
				if "1st half" in label:
					prefix = "1h_"
				if "2nd half" in label:
					prefix = "2h_"

				if "total goals" in label:
					if player1 in label:
						label = "away_total"
					elif player2 in label:
						label = "home_total"
					else:
						label = "total"
				elif "asian total" in label:
					if player1 in label:
						label = "away_asian_total"
					elif player2 in label:
						label = "home_asian_total"
					else:
						label = "asian_total"
				elif "both teams to score" in label:
					if "and" in label or "halves" in label:
						continue
					label = "btts"
				elif "asian handicap" in label:
					label = "spread"
				elif "draw no bet" in label:
					label = "dnb"
				elif label == "to score":
					label = "atgs"
				elif label == "to give an assist":
					label = "assist"
				elif "total shots" in label:
					suffix = ""
					if "on target" in label:
						suffix = "_on_target"
					if player1 in label:
						label = "away_shots"
					elif player2 in label:
						label = "home_shots"
					else:
						label = "game_shots"

					label += suffix
				elif "player's shots" in label:
					suffix = ""
					if "on target" in label:
						suffix = "_on_target"

					label = "player_shots"
					label += suffix
				elif "total corners" in label:
					#print(label, (player1, player2), player1 in label, player2 in label)
					if player1 in label:
						label = "away_corners"
					elif player2 in label:
						label = "home_corners"
					else:
						label = "corners"
				else:
					continue

				label = f"{prefix}{label}"
				if "oddsAmerican" not in betOffer["outcomes"][0]:
					continue
				if len(betOffer["outcomes"]) == 1 or "oddsAmerican" not in betOffer["outcomes"][1]:
					ou = betOffer["outcomes"][0]["oddsAmerican"]
				else:
					ou = betOffer["outcomes"][0]["oddsAmerican"]+"/"+betOffer["outcomes"][1]["oddsAmerican"]
					if betOffer["outcomes"][0]["label"] == "Under" or betOffer["outcomes"][0]["label"] == "No":
						ou = betOffer["outcomes"][1]["oddsAmerican"]+"/"+betOffer["outcomes"][0]["oddsAmerican"]
				if "btts" in label or "dnb" in label:
					data[game][label] = ou
				else:
					if label not in data[game]:
						data[game][label] = {}

					line = ""
					try:
						line = betOffer["outcomes"][0]["line"] / 1000
					except:
						pass

					if "player" in label or label in ["atgs", "assist"]:
						player = betOffer["outcomes"][0]["participant"]
						try:
							last, first = map(str, player.split(", "))
							player = parsePlayer(f"{first} {last}")
						except:
							player = parsePlayer(player)
						if player not in data[game][label]:
							data[game][label][player] = {}

						if label in ["atgs"]:
							data[game][label][player] = ou
						elif label == "assist":
							data[game][label][player]["0.5"] = ou
						else:
							data[game][label][player][line] = ou
					else:
						data[game][label][line] = ou

		with open(f"static/soccer/kambi.json", "w") as fh:
			json.dump(data, fh, indent=4)

def writeFanduel():
	url = "https://mi.sportsbook.fanduel.com/soccer"

	apiKey = "FhMFpcPWXMeyZxOx"

	js = """
	{
		const as = document.querySelectorAll("a");
		const urls = {};
		for (a of as) {
			if (a.innerText.indexOf("More wagers") >= 0 && a.href.indexOf("/soccer/") >= 0) {
				const time = a.parentElement.querySelector("time");
				if (time && (time.innerText.split(" ")[0] === "MON" || time.innerText.split(" ").length < 3)) {
					urls[a.href] = 1;	
				}
			}
		}
		console.log(Object.keys(urls));
	}
	"""

	games = [
    "https://sportsbook.fanduel.com/soccer/euro-2024/denmark-v-england-33318180",
    "https://sportsbook.fanduel.com/soccer/euro-2024/spain-v-italy-33318182"
]

	lines = {}
	#games = ["https://mi.sportsbook.fanduel.com/soccer/uefa-champions-league/ac-milan-v-newcastle-32607038"]
	for game in games:
		gameId = game.split("-")[-1]
		game = game.split("/")[-1][:-9].replace("-v-", "-@-").replace("-", " ")
		away, home = map(str, game.split(" v "))
		game = f"{convertSoccer(away)} v {convertSoccer(home)}"

		lines[game] = {}

		outfile = "soccerout"

		for tab in ["popular", "goals", "shots", "corners", "passes"]:
			time.sleep(0.42)
			url = f"https://sbapi.mi.sportsbook.fanduel.com/api/event-page?_ak={apiKey}&eventId={gameId}"
			if tab:
				url += f"&tab={tab}"
			call(["curl", "-H", "User-fasAgent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/113.0", "-H", 'x-px-context: _px3=02c9ab1c8d0655c3f57f55884b4aaa616a9a3995e8935408345199e8e71aef9e:Fa57xPlp9jkOygctuLr5buwfVIYS/s9bO7ouGbCabNNgpUmFDpOmHSEedRAOBuNRxPAv/bz5ZXCcbuf8AzLaYg==:1000:vo2IkE270qC7lKtbOjenvuAG6ddT1JVIo+uu+qpt6skvw99qELnBjQKNUJoJrlg3IZ6UwbIRlDbUMwcBi88eewvV3nAE9NYPdsHmAUqexdpyhIiakXRXRePc2VtDTnTF2mePGiJx30FP9Mi0V8pxH1qYSTM/Z9SJX9VlWy6f3gs1EFMZHHAD1WwUR1gA/Jq24xaKyiwvt48GHU85aLLH75mTWhCByf5k4nR7R8Kc+H0=;_pxvid=00692951-e181-11ed-a499-ebf9b9755f04;pxcts=006939ed-e181-11ed-a499-537250516c45;', "-k", url, "-o", outfile])

			with open(outfile) as fh:
				data = json.load(fh)

			if "markets" not in data["attachments"]:
				continue

			if data["attachments"]["events"][str(gameId)]["inPlay"]:
				continue

			for market in data["attachments"]["markets"]:
				marketName = data["attachments"]["markets"][market]["marketName"].lower()
				runners = data["attachments"]["markets"][market]["runners"]

				if marketName in ["both teams to score", "to score or assist", "anytime goalscorer", "anytime assist", "tie no bet", "match shots on target"] or "over/under" in marketName or marketName.startswith("player to have") or marketName.startswith("team to have") or "total corners" in marketName:

					prefix = ""
					if "1st half" in marketName or "first half" in marketName:
						prefix = "1h_"
					elif "each half" in marketName:
						prefix = "bh_"

					prop = ""
					if marketName == "both teams to score":
						prop = "btts"
					elif marketName == "anytime goalscorer":
						prop = "atgs"
					elif marketName == "tie no bet":
						prop = "dnb"
					elif marketName == "to score or assist":
						prop = "score_assist"
					elif marketName == "anytime assist":
						prop = "assist"
					elif "over/under" in marketName:
						if marketName.startswith("home team"):
							prop = "away_total"
						elif marketName.startswith("away team"):
							prop = "home_total"
						else:
							prop = "total"
					elif marketName.startswith("player to have"):
						prop = "player_shots"
						if "on target" in marketName:
							prop += "_on_target"
					elif marketName.startswith("team to have"):
						prop = "team_shots"
						if "on target" in marketName:
							prop += "_on_target"
					elif marketName == "match shots on target":
						prop = "game_shots_on_target"
					elif "total corners" in marketName:
						if marketName.startswith("home"):
							prop = "away_corners"
						elif marketName.startswith("away"):
							prop = "home_corners"
						else:
							prop = "corners"
					else:
						continue

					prop = f"{prefix}{prop}"

					if prop not in ["btts", "dnb"] and prop not in lines[game]:
						lines[game][prop] = {}

					if prop in ["score_assist", "assist", "atgs"] or "shots" in prop:
						skip = 1
						for i in range(0, len(runners), skip):
							runner = runners[i]
							player = parsePlayer(runner["runnerName"])

							if runner["runnerStatus"] == "SUSPENDED":
								continue
							if "team_shots" in prop:
								player = "away" if player == away else "home"

							try:
								ou = str(runner['winRunnerOdds']['americanDisplayOdds']['americanOdds'])
							except:
								continue
							if skip == 2:
								ou += "/"+str(runners[i+1]['winRunnerOdds']['americanDisplayOdds']['americanOdds'])

							if "team_shots" in prop:
								if prop in lines[game]:
									del lines[game][prop]
								p = (player+"_"+prop).replace("_team", "")
								if p not in lines[game]:
									lines[game][p] = {}
								handicap = str(float(marketName.split(" ")[3]) - 0.5)
								lines[game][p][handicap] = ou
							elif "player_shots" in prop:
								handicap = str(float(marketName.split(" ")[3]) - 0.5)
								if player not in lines[game][prop]:
									lines[game][prop][player] = {}
								lines[game][prop][player][handicap] = ou
							elif prop == "game_shots_on_target":
								handicap = str(float(runner["runnerName"].split(" ")[0]) - 0.5)
								lines[game][prop][handicap] = ou
							elif prop == "assist":
								if player not in lines[game][prop]:
									lines[game][prop][player] = {}
								lines[game][prop][player]["0.5"] = ou
							else:
								lines[game][prop][player] = ou
					else:
						for i in range(0, len(runners), 2):
							handicap = ""
							try:
								if "corners" in prop:
									handicap = marketName.split(" ")[-1]
								else:
									handicap = marketName.split(" ")[-2]
							except:
								pass

							try:
								ou = f"{runners[i]['winRunnerOdds']['americanDisplayOdds']['americanOdds']}/{runners[i+1]['winRunnerOdds']['americanDisplayOdds']['americanOdds']}"
							except:
								continue
							if runners[i]["runnerName"].startswith("Under"):
								ou = f"{runners[i+1]['winRunnerOdds']['americanDisplayOdds']['americanOdds']}/{runners[i]['winRunnerOdds']['americanDisplayOdds']['americanOdds']}"

							if prop in ["btts", "dnb"]:
								lines[game][prop] = ou
							else:
								lines[game][prop][handicap] = ou
	
	with open(f"static/soccer/fanduelLines.json", "w") as fh:
		json.dump(lines, fh, indent=4)

def devig(evData, player="", ou="575/-900", finalOdds=630, prop="hr", sharp=False):

	prefix = ""
	if sharp:
		prefix = "pn_"

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
		if u > 1:
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

	if player not in evData:
		evData[player] = {}
	evData[player][f"{prefix}fairVal"] = fairVal
	evData[player][f"{prefix}implied"] = implied
	
	evData[player][f"{prefix}ev"] = ev

def writeDK(date, leagueArg=""):
	url = "https://sportsbook.draftkings.com/leagues/soccer/champions-league"

	if not date:
		date = str(datetime.now())[:10]

	mainCats = {
		"game lines": 490,
		"goalscorer": 537,
		"shots/assists": 1113,
		"game props": 540,
		"team props": 541,
		"corners": 543
	}

	subCats = {
		490: [6497, 13171, 13170],
		537: [4690, 11783],
		1113: [11004, 11005, 11006, 12377],
		540: [5645],
		543: [4846, 4849, 4845, 5462]
	}

	subCatProps = {
		6497: "dnb", 13171: "total", 13170: "spread", 4690: "atgs", 11783: "score_assist", 11004: "player_shots_on_target", 11005: "player_shots", 11006: "assist", 12377: "bh_player_shots_on_target", 5645: "btts", 4846: "corners", 4845: "1h_corners", 5462: "2h_corners"
	}

	if False:
		mainCats = {"corners": 543}
		subCats = {543: [4846, 4849, 4845, 5462]}

	cookie = ""
	lines = {}
	fullGame = {}
	with open("static/soccer/leagues.json") as fh:
		leagues = json.load(fh)["dk"]

	for league in leagues:
		if leagueArg and leagues[league].lower() != leagueArg.lower():
			continue
		for mainCat in mainCats:
			for subCat in subCats.get(mainCats[mainCat], [0]):
				time.sleep(0.3)
				url = f"https://sportsbook-nash-usmi.draftkings.com/sites/US-MI-SB/api/v5/eventgroups/{league}/categories/{mainCats[mainCat]}"
				if subCat:
					url += f"/subcategories/{subCat}"
				url += "?format=json"
				outfile = "socceroutDK"
				os.system(f"curl {url} --compressed -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0' -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8' -H 'Accept-Language: en-US,en;q=0.5' -H 'Accept-Encoding: gzip, deflate, br' -H 'Connection: keep-alive' {cookie} -o {outfile}")

				with open(outfile) as fh:
					data = json.load(fh)

				events = {}
				if "eventGroup" not in data:
					continue

				for event in data["eventGroup"]["events"]:
					start = f"{event['startDate'].split('T')[0]}T{':'.join(event['startDate'].split('T')[1].split(':')[:2])}Z"
					startDt = datetime.strptime(start, "%Y-%m-%dT%H:%MZ") - timedelta(hours=4)
					if startDt.day != int(date[-2:]):
						continue
						pass
					game = event["name"].lower().replace(" vs ", " v ")
					away, home = map(str, game.split(" v "))
					game = f"{convertSoccer(away)} v {convertSoccer(home)}"
					fullGame[game] = event["name"].lower().replace(" vs ", " v ")
					if "eventStatus" in event and "state" in event["eventStatus"] and event["eventStatus"]["state"] == "STARTED":
						continue

					if game not in lines:
						lines[game] = {}

					events[event["eventId"]] = game

				for catRow in data["eventGroup"]["offerCategories"]:
					if catRow["offerCategoryId"] != mainCats[mainCat]:
						continue
					if "offerSubcategoryDescriptors" not in catRow:
						continue
					for cRow in catRow["offerSubcategoryDescriptors"]:
						if "offerSubcategory" not in cRow:
							continue
						for offerRow in cRow["offerSubcategory"]["offers"]:
							for row in offerRow:
								try:
									game = events[row["eventId"]]
								except:
									continue

								away, home = map(str, fullGame[game].split(" v "))

								if "label" not in row:
									continue

								label = row["label"].lower().split(" [")[0]

								if subCatProps.get(subCat, ""):
									label = subCatProps[subCat]
								else:
									if "team total goals" in label:
										if label.startswith(away):
											label = "away_total"
										else:
											label = "home_total"
									elif "team total corners" in label:
										if label.startswith(away):
											label = "away_corners"
										else:
											label = "home_corners"

								if label in ["dnb", "btts"]:
									if len(row['outcomes']) == 0:
										continue
									if row["label"].lower() == "both teams to score no draw":
										continue

									if len(row['outcomes']) == 1:
										continue
									lines[game][label] = f"{row['outcomes'][0]['oddsAmerican']}"
									lines[game][label] += f"/{row['outcomes'][1]['oddsAmerican']}"
								else:
									if label not in lines[game]:
										lines[game][label] = {}

									outcomes = row["outcomes"]
									skip = 1 if label in ["atgs", "score_assist", "assist"] or "shots" in label else 2
									for i in range(0, len(outcomes), skip):
										if skip == 1:
											try:
												line = parsePlayer(outcomes[i]["participant"])
											except:
												continue
											if not line:
												line = parsePlayer(outcomes[i]["label"])
											if "criterionName" in outcomes[i] and outcomes[i]["criterionName"] != "Anytime Scorer":
												continue
										else:
											try:
												line = str(outcomes[i]["line"])
											except:
												continue
										try:
											ou = str(outcomes[i]['oddsAmerican'])
											if skip == 2:
												ou += f"/{outcomes[i+1]['oddsAmerican']}"
												if outcomes[i]['label'] == 'Under':
													ou = f"{outcomes[i+1]['oddsAmerican']}/{outcomes[i]['oddsAmerican']}"

											if "shots" in label or label in ["assist"]:
												if line not in lines[game][label]:
													lines[game][label][line] = {}
												handicap = str(float(row["label"].split(" ")[3]) - 0.5)
												lines[game][label][line][handicap] = ou
											else:
												lines[game][label][line] = ou
										except:
											continue
								

	with open("static/soccer/draftkings.json", "w") as fh:
		json.dump(lines, fh, indent=4)

def writeCZ(date=None, token=None, keep=None):
	if not date:
		date = str(datetime.now())[:10]

	res = {}
	if keep:
		with open("static/soccer/caesars.json") as fh:
			res = json.load(fh)

	url = "https://api.americanwagering.com/regions/us/locations/mi/brands/czr/sb/v4/sports/football/events/schedule"
	outfile = "socceroutCZ"
	cookie = "ca95f0df-2820-461e-9433-779074af4a6c:EgoAZaaIrYnhAAAA:2QUHraQzVgfuSvKDcwuoRbHiZCxXs1hMN8Zlj0AGOZYELSga3iSBkAweRvEa//bM+xqmboAdxLHMjiJB/85pBZS4zO2T/XWvi3BZp5umnnghVonRLfvgPcSA/QwtAolO/PNHNoDEzmw0Zsm+mfG6kUCSLklcHClOZhR5aZbvIMBQ7iBXOfhHcNKAF/6FWk0Ji1LIB+C3AeoM9J+Htpu8IU8ri9fLasWcvjUbbTNbOeEUGl2yAEUa/G+p+kI5ycCdWLtriA+yxFzzEg=="

	if token:
		cookie = token
	
	os.system(f"curl '{url}' --compressed -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:131.0) Gecko/20100101 Firefox/131.0' -H 'Accept: */*' -H 'Accept-Language: en-US,en;q=0.5' -H 'Accept-Encoding: gzip, deflate, br, zstd' -H 'Referer: https://sportsbook.caesars.com/' -H 'content-type: application/json' -H 'X-Unique-Device-Id: b51ee484-42d9-40de-81ed-5c6df2f3122a' -H 'X-Platform: cordova-desktop' -H 'X-App-Version: 7.15.1' -H 'x-aws-waf-token: {cookie}' -H 'Origin: https://sportsbook.caesars.com' -H 'Connection: keep-alive' -H 'Sec-Fetch-Dest: empty' -H 'Sec-Fetch-Mode: cors' -H 'Sec-Fetch-Site: cross-site' -H 'Priority: u=4' -o {outfile}")

	with open(outfile) as fh:
		data = json.load(fh)

	games = []
	for league in data.get("competitions", []):
		for event in league["events"]:
			if str(datetime.strptime(event["startTime"], "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=4))[:10] == date:
				if "(W)" in event["name"]:
					continue
				game = event["name"].lower().replace("|", "").replace(" vs ", " v ")
				away, home = map(str, game.split(" v "))
				game = f"{convertSoccer(away)} v {convertSoccer(home)}"
				if game in res:
					continue
				games.append(event["id"])

	#games = ["34c2c0fb-7af4-467d-a2c9-f79017105ec5"]
	for gameId in games:
		for tab in ["", "Player%20Props", "Team%20Props", "Match%20Props", "Corners"]:
			url = f"https://api.americanwagering.com/regions/us/locations/mi/brands/czr/sb/v4/events/{gameId}"
			if tab:
				url += f"/tabs/{tab}"
			time.sleep(0.2)
			os.system(f"curl '{url}' --compressed -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:131.0) Gecko/20100101 Firefox/131.0' -H 'Accept: */*' -H 'Accept-Language: en-US,en;q=0.5' -H 'Accept-Encoding: gzip, deflate, br, zstd' -H 'Referer: https://sportsbook.caesars.com/' -H 'content-type: application/json' -H 'X-Unique-Device-Id: b51ee484-42d9-40de-81ed-5c6df2f3122a' -H 'X-Platform: cordova-desktop' -H 'X-App-Version: 7.15.1' -H 'x-aws-waf-token: {cookie}' -H 'Origin: https://sportsbook.caesars.com' -H 'Connection: keep-alive' -H 'Sec-Fetch-Dest: empty' -H 'Sec-Fetch-Mode: cors' -H 'Sec-Fetch-Site: cross-site' -H 'Priority: u=4' -o {outfile}")

			try:
				with open(outfile) as fh:
					data = json.load(fh)
			except:
				continue

			#with open("out", "w") as fh:
			#	json.dump(data, fh, indent=4)

			game = data["name"].lower().replace("|", "").replace(" vs ", " v ")
			away, home = map(str, game.split(" v "))
			game = f"{convertSoccer(away)} v {convertSoccer(home)}"

			if game not in res:
				res[game] = {}

			for market in data["markets"]:
				if "name" not in market:
					continue

				if market["active"] == False:
					continue
				prop = market["name"].lower().replace("|", "").split(" (")[0]
				template = market["templateName"].lower().replace("|", "")
				display = market["displayName"].lower()

				prefix = player = ""
				playerProp = False
				if "1st half" in prop:
					prefix = "1h_"
				elif "2nd half" in prop:
					prefix = "2h_"

				skip = 2
				if prop == "draw no bet":
					prop = "dnb"
				elif prop == "both teams to score":
					prop = "btts"
				elif prop == "handicap betting":
					prop = "spread"
				elif prop == "total goals":
					prop = "total"
				elif prop.startswith("total match goals"):
					if "over/under" not in prop:
						continue
					prop = "total"
				elif prop == "anytime goalscorer":
					prop = "atgs"
					skip = 1
				elif prop.endswith("half betting"):
					prop = "ml"
					skip = 3
				elif template in ["first away goalscorer", "first home goalscorer"]:
					prop = "team_fgs"
					skip = 1
				elif prop == "player to score a header":
					prop = "header"
					skip = 1
				elif prop == "total match shots":
					prop = "game_shots"
					skip = 1
				elif prop == "total match shots on target":
					prop = "game_shots_on_target"
					skip = 1
				elif prop == "total match tackles":
					prop = "game_tackles"
					skip = 1
				elif display == "total corners" or display == "1st half corners" or display == "2nd half corners":
					prop = "corners"
				elif display.endswith("total corners"):
					prop = f"{display.split(' ')[0]}_corners"
				elif template.startswith("total player"):
					prop = template.split(" ")[-1]
					if prop == "target":
						prop = "shots_on_target"
					prop = "player_"+prop
					skip = 1
				elif template.startswith("total home") or template.startswith("total away"):
					prop = "_".join(template[6:].split(" "))
					skip = 1
				else:
					continue

				prop = f"{prefix}{prop}"

				if prop not in res[game]:
					res[game][prop] = {}

				selections = market["selections"]
				mainLine = ""
				for i in range(0, len(selections), skip):
					try:
						ou = str(selections[i]["price"]["a"])
					except:
						continue
					if skip == 3:
						ou += f"/{selections[i+1]['price']['a']}/{selections[i+2]['price']['a']}"
					elif skip == 2:
						ou += f"/{selections[i+1]['price']['a']}"
						if selections[i]["name"].lower().replace("|", "").split(" ")[0] in ["under", "home"]:
							ou = f"{selections[i+1]['price']['a']}/{selections[i]['price']['a']}"

					if "ml" in prop or "btts" in prop or prop in ["dnb"]:
						res[game][prop] = ou
					elif prop in ["atgs", "fgs", "team_fgs", "header"]:
						player = parsePlayer(selections[i]["name"].replace("|", ""))
						res[game][prop][player] = ou
					elif "spread" in prop:
						line = str(market["line"])
						mainLine = line
						res[game][prop][line] = ou
					elif prop.startswith("away") or prop.startswith("home") or prop in ["game_shots", "game_shots_on_target", "game_tackles"] or "corners" in prop:
						if "corners" in prop:
							line = selections[i]["name"].split(" ")[-2]
						else:
							line = selections[i]["name"].replace("|", "").split(" ")[-1]
						res[game][prop][line] = ou
					elif "total" in prop:
						line = str(market.get("line", ""))
						if not line:
							line = selections[i]["name"].split(" ")[-1]
						if line not in res[game][prop]:
							res[game][prop][line] = ou
						else:
							over = int(res[game][prop][line].split("/")[0])
							if int(ou.split("/")[0]) > over:
								over = int(ou.split("/")[0])
							under = int(res[game][prop][line].split("/")[-1])
							if int(ou.split("/")[-1]) > under:
								under = int(ou.split("/")[-1])
							res[game][prop][line] = f"{over}/{under}"
					else:
						player = parsePlayer(market["name"].lower().replace("|", "").split(" total ")[0])
						line = str(float(selections[i]["name"][1:-2]) - 0.5)
						if player not in res[game][prop]:
							res[game][prop][player] = {}
						res[game][prop][player][line] = ou

				#print(market["name"], prop, mainLine)
				if prop in ["spread", "total"]:
					try:
						linePrices = market["movingLines"]["linePrices"]
					except:
						continue
					for prices in linePrices:
						selections = prices["selections"]
						if prop == "spread":
							line = float(prices["line"])
							ou = f"{selections[0]['price']['a']}/{selections[1]['price']['a']}"
							if selections[0]["selectionType"] == "home":
								line *= -1
								ou = f"{selections[1]['price']['a']}/{selections[0]['price']['a']}"
							line = str(line)
						else:
							line = str(float(prices["line"]))
							ou = f"{selections[0]['price']['a']}/{selections[1]['price']['a']}"
							if selections[0]["selectionType"] == "under":
								ou = f"{selections[1]['price']['a']}/{selections[0]['price']['a']}"
						if line == mainLine:
							continue
						res[game][prop][line] = ou

		with open("static/soccer/caesars.json", "w") as fh:
			json.dump(res, fh, indent=4)

	with open("static/soccer/caesars.json", "w") as fh:
		json.dump(res, fh, indent=4)


def writePointsbet(date=None):
	url = "https://api.mi.pointsbet.com/api/v2/sports/soccer/events/nextup"
	outfile = f"socceroutPB"
	os.system(f"curl -k \"{url}\" -o {outfile}")

	with open(outfile) as fh:
		data = json.load(fh)

	if not date:
		date = str(datetime.now())[:10]

	games = []
	for row in data["events"]:
		games.append(row["key"])

	res = {}
	#games = ["331623"]
	for gameId in games:
		url = f"https://api.mi.pointsbet.com/api/mes/v3/events/{gameId}"
		time.sleep(0.3)
		outfile = f"socceroutPB"
		os.system(f"curl -k \"{url}\" -o {outfile}")

		try:
			with open(outfile) as fh:
				data = json.load(fh)
		except:
			continue

		startDt = datetime.strptime(data["startsAt"], "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=4)
		if startDt.day != int(date[-2:]):
			continue

		playerIds = {}
		try:
			filters = data["presentationData"]["presentationFilters"]
			for row in filters:
				playerIds[row["id"].split("-")[-1]] = parsePlayer(row["name"].lower())
			for row in data["presentationData"]["presentations"]:
				if row["columnTitles"] and "Anytime TD" in row["columnTitles"]:
					for r in row["rows"]:
						playerIds[r["rowId"].split("-")[-1]] = parsePlayer(r["title"].lower())

					break
		except:
			pass

		game = away = home= ""
		try:
			for market in data["fixedOddsMarkets"]:
				if market["eventName"].lower() == "draw no bet":
					away = market["outcomes"][0]["name"].lower()
					home = market["outcomes"][1]["name"].lower()
					game = f"{convertSoccer(away)} v {convertSoccer(home)}"
					break
		except:
			continue

		res[game] = {}

		for market in data["fixedOddsMarkets"]:
			prop = market["name"].lower().split(" (")[0]
			playerProp = False

			prefix = ""
			if "1st half" in prop:
				prefix = "1h_"
			elif "2nd half" in prop:
				prefix = "2h_"

			if "&" in prop or "odd/even" in prop or "both halves" in prop or "number" in prop:
				continue
			if "draw no bet" in prop:
				prop = f"dnb"
			elif "both teams to score" in prop:
				if "and" in prop or "yes/no" in prop:
					continue
				prop = f"btts"
			elif "anytime goalscorer" in prop:
				prop = f"atgs"
			elif "anytime goalscorer" in prop:
				prop = f"atgs"
			elif prop == "alternate spread" or "spread" in prop:
				if "-" in prop or "3 way" in prop:
					continue
				prop = "spread"
			elif prop.endswith("goals") or prop.endswith("total") or prop.endswith("total 1st half") or prop.endswith("total 2nd half"):
				if "exact" in prop or "+" in prop:
					continue
				if prop in [f"1st half {away} total goals", f"1st half {home} total goals", f"2nd half {away} total goals", f"2nd half {home} total goals"]:
					continue
				if away in prop:
					prop = "away_total"
				elif home in prop:
					prop = "home_total"
				else:
					prop = "total"
			elif "total corners" in prop:
				if "exact" in prop:
					continue
				if away in prop:
					prop = "away_corners"
				elif home in prop:
					prop = "home_corners"
				else:
					prop = "corners"
			elif "total assists" in prop:
				playerProp = True
				prop = "assist"
			elif "total passes" in prop:
				playerProp = True
				prop = "player_passes"
			elif "total shots" in prop:
				playerProp = True
				suffix = ""
				if "outside" in prop:
					suffix += "_outside_box"
				if "on target" in prop:
					suffix += "_on_target"

				if "player" in prop:
					prop = "player_shots"
				else:
					prop = "total_shots"
				prop += suffix
			else:
				continue

			prop = f"{prefix}{prop}"

			if "ml" not in prop and prop not in res[game]:
				res[game][prop] = {}

			outcomes = market["outcomes"]
			skip = 1 if prop in ["atgs", "assist", "player_passes"] or "shots" in prop else 2
			for i in range(0, len(outcomes), skip):
				if outcomes[i]["price"] == 1:
					continue
				over = convertAmericanOdds(outcomes[i]["price"])
				under = ""
				try:
					if skip == 2:
						under = convertAmericanOdds(outcomes[i+1]["price"])
				except:
					pass
				ou = f"{over}"

				if under:
					ou += f"/{under}"
					if outcomes[i]["name"].startswith("Under") or outcomes[i]["name"] == "No":
						ou = f"{under}/{over}"
					elif prop == "spread" and outcomes[i]["side"] == "Away":
						ou = f"{under}/{over}"

				ou = ou.replace("Even", "100")

				if "btts" in prop or "dnb" in prop:
					res[game][prop] = ou
				else:
					if prop not in res[game]:
						res[game][prop] = {}

					if playerProp:
						try:
							player = playerIds[outcomes[i]["playerId"]]
						except:
							continue
						if player not in res[game][prop]:
							res[game][prop][player] = {}
						points = str(float(outcomes[i]["points"]) - 0.5)
						#if player == "emile smith rowe":
						#	print(prop, points, ou, market["name"])
						res[game][prop][player][points] = ou
					elif prop in ["atgs"]:
						try:
							player = playerIds[outcomes[i]["playerId"]]
						except:
							continue
						res[game][prop][player] = ou
					else:
						points = str(float(outcomes[i]["points"]))
						if points == "0.0":
							continue
						res[game][prop][points] = ou

	with open("static/soccer/pointsbet.json", "w") as fh:
		json.dump(res, fh, indent=4)

def writeSGP():

	url = "https://sportsbook.draftkings.com/event/cadiz-vs-atletico-madrid/30189293?sgpmode=true"
	outfile = "outsoccer"
	os.system(f"curl {url} -o {outfile}")

	soup = BS(open(outfile, 'rb').read(), "lxml")

	data = "{}"
	for script in soup.find_all("script"):
		if not script.string:
			continue
		if "__INITIAL_STATE" in script.string:
			m = re.search(r"__INITIAL_STATE__ = {(.*?)};", script.string)
			if m:
				data = m.group(1).replace("false", "False").replace("true", "True").replace("null", "None")
				data = f"{{{data}}}"
				break

	data = eval(data)

	for offer in data["offers"]:
		for offerId in data["offers"][offer]:
			offerRow = data["offers"][offer][offerId]
			prop = offerRow["label"].lower()

			if prop == "team total number of goals":
				prop = "team_total"

			else:
				continue

def convertStat(stat):
	stat = stat.lower()
	if stat in ["shot attempts", "totalshots"]:
		stat = "shots"
	elif stat in ["shots on goal", "shotsontarget"]:
		stat = "sot"
	elif stat == "totalgoals":
		stat = "g"
	elif stat == "corner kicks":
		stat = "corners"
	elif stat in ["yellow cards", "yellowcards"]:
		stat = "yellows"
	return stat

def printMatchup(matchup):
	with open("static/soccer/teamLeagues.json") as fh:
		teamLeagues = json.load(fh)

	home, away = map(str, matchup.split(" v "))
	home = home.replace(" ", "-")
	away = away.replace(" ", "-")
	homeLeague, awayLeague = teamLeagues[home], teamLeagues[away]
	with open(f"static/soccerreference/{homeLeague}/{home}.json") as fh:
		homeData = json.load(fh)
	with open(f"static/soccerreference/{awayLeague}/{away}.json") as fh:
		awayData = json.load(fh)
	data = {}

	# total goals
	output = ""

	homeAH = homeData["teamStats"]["tot"]["awayHome"].split(",")
	awayAH = awayData["teamStats"]["tot"]["awayHome"].split(",")

	output += f"\nTotal Goals\n"
	totGoals = homeData["teamStats"]["tot"]["total_goals"].split(",")
	awayTotGoals = awayData["teamStats"]["tot"]["total_goals"].split(",")
	output += f"{', '.join(totGoals[-20:])}\n"
	output += f"{', '.join(awayTotGoals[-20:])}\n\n"
	output += f"{home}\t\t{away}\n\n"
	for ou in [0.5, 1.5, 2.5, 3.5]:
		overArr = [x for x in totGoals if int(x) > ou]
		over = int(len(overArr) * 100 / len(totGoals))

		overArr = [x for x, ah in zip(totGoals, homeAH) if int(x) > ou and ah == "h"]
		l = [x for x in homeAH if x == "h"]
		overAH = int(len(overArr) * 100 / len(l))

		overArrL10 = [x for x in totGoals[-10:] if int(x) > ou]
		overL10 = int(len(overArrL10) * 100 / len(totGoals[-10:]))

		awayOverArr = [x for x in awayTotGoals if int(x) > ou]
		awayOver = int(len(awayOverArr) * 100 / len(awayTotGoals))

		awayOverArrL10 = [x for x in awayTotGoals[-10:] if int(x) > ou]
		awayOverL10 = int(len(awayOverArrL10) * 100 / len(awayTotGoals[-10:]))

		overArr = [x for x, ah in zip(totGoals, awayAH) if int(x) > ou and ah == "a"]
		l = [x for x in awayAH if x == "a"]
		awayOverAH = int(len(overArr) * 100 / len(l))

		output += f"{over}%/{overL10}%/{overAH}%\t\t{awayOver}%/{awayOverL10}%/{awayOverAH}%\t\to{ou}\n"

	output += f"\n{home} Goals\n"
	tot = homeData["teamStats"]["tot"]["goals"].split(",")
	totAgainst = awayData["teamStats"]["tot"]["goals_against"].split(",")
	output += f"{', '.join(tot[-20:])}\n"
	output += f"{', '.join(totAgainst[-20:])}\n"
	for ou in [0.5, 1.5, 2.5, 3.5]:
		overArr = [x for x in tot if int(x) > ou]
		over = int(len(overArr) * 100 / len(tot))
		overArrL10 = [x for x in tot[-10:] if int(x) > ou]
		overL10 = int(len(overArrL10) * 100 / len(tot[-10:]))
		overArr = [x for x, ah in zip(tot, homeAH) if int(x) > ou and ah == "h"]
		l = [x for x in homeAH if x == "h"]
		overAH = int(len(overArr) * 100 / len(l))

		underArr = [x for x in totAgainst if int(x) > ou]
		under = int(len(underArr) * 100 / len(totAgainst))
		underArrL10 = [x for x in totAgainst[-10:] if int(x) > ou]
		underL10 = int(len(underArrL10) * 100 / len(totAgainst[-10:]))
		overArr = [x for x, ah in zip(totAgainst, awayAH) if int(x) > ou and ah == "a"]
		l = [x for x in awayAH if x == "a"]
		awayOverAH = int(len(overArr) * 100 / len(l))

		output += f"{over}%/{overL10}%/{overAH}%\t\t{under}%/{underL10}%/{awayOverAH}%\t\to{ou}\n"

	output += f"\n{away} Goals\n"
	tot = awayData["teamStats"]["tot"]["goals"].split(",")
	totAgainst = homeData["teamStats"]["tot"]["goals_against"].split(",")
	output += f"{', '.join(tot[-20:])}\n"
	output += f"{', '.join(totAgainst[-20:])}\n"
	for ou in [0.5, 1.5, 2.5, 3.5]:
		overArr = [x for x in tot if int(x) > ou]
		over = int(len(overArr) * 100 / len(tot))
		overArrL10 = [x for x in tot[-10:] if int(x) > ou]
		overL10 = int(len(overArrL10) * 100 / len(tot[-10:]))
		overArr = [x for x, ah in zip(tot, homeAH) if int(x) > ou and ah == "h"]
		l = [x for x in homeAH if x == "h"]
		overAH = int(len(overArr) * 100 / len(l))

		underArr = [x for x in totAgainst if int(x) > ou]
		under = int(len(underArr) * 100 / len(totAgainst))
		underArrL10 = [x for x in totAgainst[-10:] if int(x) > ou]
		underL10 = int(len(underArrL10) * 100 / len(totAgainst[-10:]))
		overArr = [x for x, ah in zip(totAgainst, awayAH) if int(x) > ou and ah == "a"]
		l = [x for x in awayAH if x == "a"]
		awayOverAH = int(len(overArr) * 100 / len(l))

		output += f"{over}%/{overL10}%/{overAH}%\t\t{under}%/{underL10}%/{awayOverAH}%\t\to{ou}\n"

	output += f"\n{home} SOT\n"
	tot = homeData["teamStats"]["tot"]["sot"].split(",")
	totAgainst = awayData["teamStats"]["tot"]["sot_against"].split(",")
	output += f"{', '.join(tot[-20:])}\n"
	output += f"{', '.join(totAgainst[-20:])}\n"
	for ou in [1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5]:
		overArr = [x for x in tot if int(x) > ou]
		over = int(len(overArr) * 100 / len(tot))
		overArrL10 = [x for x in tot[-10:] if int(x) > ou]
		overL10 = int(len(overArrL10) * 100 / len(tot[-10:]))
		overArr = [x for x, ah in zip(tot, homeAH) if int(x) > ou and ah == "h"]
		l = [x for x in homeAH if x == "h"]
		overAH = int(len(overArr) * 100 / len(l))

		underArr = [x for x in totAgainst if int(x) > ou]
		under = int(len(underArr) * 100 / len(totAgainst))
		underArrL10 = [x for x in totAgainst[-10:] if int(x) > ou]
		underL10 = int(len(underArrL10) * 100 / len(totAgainst[-10:]))
		overArr = [x for x, ah in zip(totAgainst, awayAH) if int(x) > ou and ah == "a"]
		l = [x for x in awayAH if x == "a"]
		awayOverAH = int(len(overArr) * 100 / len(l))

		output += f"{over}%/{overL10}%/{overAH}%\t\t{under}%/{underL10}%/{awayOverAH}%\t\to{ou}\n"

	output += f"\n{home} Shots\n"
	tot = homeData["teamStats"]["tot"]["shots"].split(",")
	totAgainst = awayData["teamStats"]["tot"]["shots_against"].split(",")
	output += f"{', '.join(tot[-20:])}\n"
	output += f"{', '.join(totAgainst[-20:])}\n"
	for ou in [6.5, 7.5, 8.5, 9.5, 10.5, 11.5, 12.5, 13.5, 14.5, 15.5, 16.5]:
		overArr = [x for x in tot if int(x) > ou]
		over = int(len(overArr) * 100 / len(tot))
		overArrL10 = [x for x in tot[-10:] if int(x) > ou]
		overL10 = int(len(overArrL10) * 100 / len(tot[-10:]))
		overArr = [x for x, ah in zip(tot, homeAH) if int(x) > ou and ah == "h"]
		l = [x for x in homeAH if x == "h"]
		overAH = int(len(overArr) * 100 / len(l))

		underArr = [x for x in totAgainst if int(x) > ou]
		under = int(len(underArr) * 100 / len(totAgainst))
		underArrL10 = [x for x in totAgainst[-10:] if int(x) > ou]
		underL10 = int(len(underArrL10) * 100 / len(totAgainst[-10:]))
		overArr = [x for x, ah in zip(totAgainst, awayAH) if int(x) > ou and ah == "a"]
		l = [x for x in awayAH if x == "a"]
		awayOverAH = int(len(overArr) * 100 / len(l))

		output += f"{over}%/{overL10}%/{overAH}%\t\t{under}%/{underL10}%/{awayOverAH}%\t\to{ou}\n"


	output += f"\n{away} SOT\n"
	tot = awayData["teamStats"]["tot"]["sot"].split(",")
	totAgainst = homeData["teamStats"]["tot"]["sot_against"].split(",")
	output += f"{', '.join(tot[-20:])}\n"
	output += f"{', '.join(totAgainst[-20:])}\n"
	for ou in [1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5]:
		overArr = [x for x in tot if int(x) > ou]
		over = int(len(overArr) * 100 / len(tot))
		overArrL10 = [x for x in tot[-10:] if int(x) > ou]
		overL10 = int(len(overArrL10) * 100 / len(tot[-10:]))
		overArr = [x for x, ah in zip(tot, homeAH) if int(x) > ou and ah == "h"]
		l = [x for x in homeAH if x == "h"]
		overAH = int(len(overArr) * 100 / len(l))

		underArr = [x for x in totAgainst if int(x) > ou]
		under = int(len(underArr) * 100 / len(totAgainst))
		underArrL10 = [x for x in totAgainst[-10:] if int(x) > ou]
		underL10 = int(len(underArrL10) * 100 / len(totAgainst[-10:]))
		overArr = [x for x, ah in zip(totAgainst, awayAH) if int(x) > ou and ah == "a"]
		l = [x for x in awayAH if x == "a"]
		awayOverAH = int(len(overArr) * 100 / len(l))

		output += f"{over}%/{overL10}%/{overAH}%\t\t{under}%/{underL10}%/{awayOverAH}%\t\to{ou}\n"

	output += f"\n{away} Shots\n"
	tot = awayData["teamStats"]["tot"]["shots"].split(",")
	totAgainst = homeData["teamStats"]["tot"]["shots_against"].split(",")
	output += f"{', '.join(tot[-20:])}\n"
	output += f"{', '.join(totAgainst[-20:])}\n"
	for ou in [6.5, 7.5, 8.5, 9.5, 10.5, 11.5, 12.5, 13.5, 14.5, 15.5, 16.5]:
		overArr = [x for x in tot if int(x) > ou]
		over = int(len(overArr) * 100 / len(tot))
		overArrL10 = [x for x in tot[-10:] if int(x) > ou]
		overL10 = int(len(overArrL10) * 100 / len(tot[-10:]))
		overArr = [x for x, ah in zip(tot, homeAH) if int(x) > ou and ah == "h"]
		l = [x for x in homeAH if x == "h"]
		overAH = int(len(overArr) * 100 / len(l))

		underArr = [x for x in totAgainst if int(x) > ou]
		under = int(len(underArr) * 100 / len(totAgainst))
		underArrL10 = [x for x in totAgainst[-10:] if int(x) > ou]
		underL10 = int(len(underArrL10) * 100 / len(totAgainst[-10:]))
		overArr = [x for x, ah in zip(totAgainst, awayAH) if int(x) > ou and ah == "a"]
		l = [x for x in awayAH if x == "a"]
		awayOverAH = int(len(overArr) * 100 / len(l))

		output += f"{over}%/{overL10}%/{overAH}%\t\t{under}%/{underL10}%/{awayOverAH}%\t\to{ou}\n"

	output += f"\nTotal Shots\n"
	totGoals = homeData["teamStats"]["tot"]["shots"].split(",")
	totGoalsAgainst = homeData["teamStats"]["tot"]["shots_against"].split(",")
	awayTotGoals = awayData["teamStats"]["tot"]["shots"].split(",")
	awayTotGoalsAgainst = awayData["teamStats"]["tot"]["shots_against"].split(",")
	output += f"{', '.join([str(int(x)+int(y)) for x,y in zip(totGoals[-20:], totGoalsAgainst[-20:])])}\n"
	output += f"{', '.join([str(int(x)+int(y)) for x,y in zip(awayTotGoals[-20:], awayTotGoalsAgainst[-20:])])}\n\n"
	output += f"{home}\t\t{away}\n\n"
	for ou in [20.5, 21.5, 22.5, 23.5, 24.5, 25.5, 26.5, 27.5, 28.5, 29.5, 30.5]:
		overArr = [x for x, y in zip(totGoals, totGoalsAgainst) if int(x) + int(y) > ou]
		over = int(len(overArr) * 100 / len(totGoals))
		overArrL10 = [x for x, y in zip(totGoals[-10:], totGoalsAgainst[-10:]) if int(x) + int(y) > ou]
		overL10 = int(len(overArrL10) * 100 / len(totGoals[-10:]))
		overArr = [x for x, y, ah in zip(totGoals, totGoalsAgainst, homeAH) if int(x) + int(y) > ou and ah == "h"]
		l = [x for x in homeAH if x == "h"]
		overAH = int(len(overArr) * 100 / len(l))

		awayOverArr = [x for x, y in zip(awayTotGoals, awayTotGoalsAgainst) if int(x) + int(y) > ou]
		awayOver = int(len(awayOverArr) * 100 / len(awayTotGoals))
		awayOverArrL10 = [x for x, y in zip(awayTotGoals[-10:], awayTotGoalsAgainst[-10:]) if int(x) + int(y) > ou]
		awayOverL10 = int(len(awayOverArrL10) * 100 / len(awayTotGoals[-10:]))
		overArr = [x for x, y, ah in zip(awayTotGoals, awayTotGoalsAgainst, awayAH) if int(x) + int(y) > ou and ah == "a"]
		l = [x for x in awayAH if x == "a"]
		awayOverAH = int(len(overArr) * 100 / len(l))

		output += f"{over}%/{overL10}%/{overAH}%\t\t{awayOver}%/{awayOverL10}%/{awayOverAH}%\t\to{ou}\n"

	output += f"\nTotal SOT\n"
	totGoals = homeData["teamStats"]["tot"]["sot"].split(",")
	totGoalsAgainst = homeData["teamStats"]["tot"]["sot_against"].split(",")
	awayTotGoals = awayData["teamStats"]["tot"]["sot"].split(",")
	awayTotGoalsAgainst = awayData["teamStats"]["tot"]["sot_against"].split(",")
	output += f"{', '.join([str(int(x)+int(y)) for x,y in zip(totGoals[-20:], totGoalsAgainst[-20:])])}\n"
	output += f"{', '.join([str(int(x)+int(y)) for x,y in zip(awayTotGoals[-20:], awayTotGoalsAgainst[-20:])])}\n\n"
	output += f"{home}\t\t{away}\n\n"
	for ou in [6.5, 7.5, 8.5, 9.5, 10.5, 11.5, 12.5, 13.5, 14.5]:
		overArr = [x for x, y in zip(totGoals, totGoalsAgainst) if int(x) + int(y) > ou]
		over = int(len(overArr) * 100 / len(totGoals))
		overArrL10 = [x for x, y in zip(totGoals[-10:], totGoalsAgainst[-10:]) if int(x) + int(y) > ou]
		overL10 = int(len(overArrL10) * 100 / len(totGoals[-10:]))
		overArr = [x for x, y, ah in zip(totGoals, totGoalsAgainst, homeAH) if int(x) + int(y) > ou and ah == "h"]
		l = [x for x in homeAH if x == "h"]
		overAH = int(len(overArr) * 100 / len(l))

		awayOverArr = [x for x, y in zip(awayTotGoals, awayTotGoalsAgainst) if int(x) + int(y) > ou]
		awayOver = int(len(awayOverArr) * 100 / len(awayTotGoals))
		awayOverArrL10 = [x for x, y in zip(awayTotGoals[-10:], awayTotGoalsAgainst[-10:]) if int(x) + int(y) > ou]
		awayOverL10 = int(len(awayOverArrL10) * 100 / len(awayTotGoals[-10:]))
		overArr = [x for x, y, ah in zip(awayTotGoals, awayTotGoalsAgainst, awayAH) if int(x) + int(y) > ou and ah == "a"]
		l = [x for x in awayAH if x == "a"]
		awayOverAH = int(len(overArr) * 100 / len(l))

		output += f"{over}%/{overL10}%/{overAH}%\t\t{awayOver}%/{awayOverL10}%/{awayOverAH}%\t\to{ou}\n"

	output += f"\n1H Goals\n"
	totGoals = homeData["teamStats"]["tot"]["1h_goals"].split(",")
	totGoalsAgainst = homeData["teamStats"]["tot"]["1h_goals_against"].split(",")
	awayTotGoals = awayData["teamStats"]["tot"]["1h_goals"].split(",")
	awayTotGoalsAgainst = awayData["teamStats"]["tot"]["1h_goals_against"].split(",")
	output += f"{', '.join([str(int(x)+int(y)) for x,y in zip(totGoals[-20:], totGoalsAgainst[-20:])])}\n"
	output += f"{', '.join([str(int(x)+int(y)) for x,y in zip(awayTotGoals[-20:], awayTotGoalsAgainst[-20:])])}\n\n"
	output += f"{home}\t\t{away}\n\n"
	for ou in [0.5,1.5,2.5,3.5]:
		overArr = [x for x, y in zip(totGoals, totGoalsAgainst) if int(x) + int(y) > ou]
		over = int(len(overArr) * 100 / len(totGoals))
		overArrL10 = [x for x, y in zip(totGoals[-10:], totGoalsAgainst[-10:]) if int(x) + int(y) > ou]
		overL10 = int(len(overArrL10) * 100 / len(totGoals[-10:]))
		overArr = [x for x, y, ah in zip(totGoals, totGoalsAgainst, homeAH) if int(x) + int(y) > ou and ah == "h"]
		l = [x for x in homeAH if x == "h"]
		overAH = int(len(overArr) * 100 / len(l))

		awayOverArr = [x for x, y in zip(awayTotGoals, awayTotGoalsAgainst) if int(x) + int(y) > ou]
		awayOver = int(len(awayOverArr) * 100 / len(awayTotGoals))

		awayOverArrL10 = [x for x, y in zip(awayTotGoals[-10:], awayTotGoalsAgainst[-10:]) if int(x) + int(y) > ou]
		awayOverL10 = int(len(awayOverArrL10) * 100 / len(awayTotGoals[-10:]))
		overArr = [x for x, y, ah in zip(awayTotGoals, awayTotGoalsAgainst, awayAH) if int(x) + int(y) > ou and ah == "a"]
		l = [x for x in awayAH if x == "a"]
		awayOverAH = int(len(overArr) * 100 / len(l))

		output += f"{over}%/{overL10}%/{overAH}%\t\t{awayOver}%/{awayOverL10}%/{awayOverAH}%\t\to{ou}\n"

	output += f"\n2H Goals\n"
	totGoals = homeData["teamStats"]["tot"]["2h_goals"].split(",")
	totGoalsAgainst = homeData["teamStats"]["tot"]["2h_goals_against"].split(",")
	awayTotGoals = awayData["teamStats"]["tot"]["2h_goals"].split(",")
	awayTotGoalsAgainst = awayData["teamStats"]["tot"]["2h_goals_against"].split(",")
	output += f"{', '.join([str(int(x)+int(y)) for x,y in zip(totGoals[-20:], totGoalsAgainst[-20:])])}\n"
	output += f"{', '.join([str(int(x)+int(y)) for x,y in zip(awayTotGoals[-20:], awayTotGoalsAgainst[-20:])])}\n\n"
	output += f"{home}\t\t{away}\n\n"
	for ou in [0.5,1.5,2.5,3.5]:
		overArr = [x for x, y in zip(totGoals, totGoalsAgainst) if int(x) + int(y) > ou]
		over = int(len(overArr) * 100 / len(totGoals))

		overArrL10 = [x for x, y in zip(totGoals[-10:], totGoalsAgainst[-10:]) if int(x) + int(y) > ou]
		overL10 = int(len(overArrL10) * 100 / len(totGoals[-10:]))
		overArr = [x for x, y, ah in zip(totGoals, totGoalsAgainst, homeAH) if int(x) + int(y) > ou and ah == "h"]
		l = [x for x in homeAH if x == "h"]
		overAH = int(len(overArr) * 100 / len(l))

		awayOverArr = [x for x, y in zip(awayTotGoals, awayTotGoalsAgainst) if int(x) + int(y) > ou]
		awayOver = int(len(awayOverArr) * 100 / len(awayTotGoals))

		awayOverArrL10 = [x for x, y in zip(awayTotGoals[-10:], awayTotGoalsAgainst[-10:]) if int(x) + int(y) > ou]
		awayOverL10 = int(len(awayOverArrL10) * 100 / len(awayTotGoals[-10:]))
		overArr = [x for x, y, ah in zip(awayTotGoals, awayTotGoalsAgainst, awayAH) if int(x) + int(y) > ou and ah == "a"]
		l = [x for x in awayAH if x == "a"]
		awayOverAH = int(len(overArr) * 100 / len(l))

		output += f"{over}%/{overL10}%/{overAH}%\t\t{awayOver}%/{awayOverL10}%/{awayOverAH}%\t\to{ou}\n"

	output += f"\nTotal Corners\n"
	totGoals = homeData["teamStats"]["tot"]["corners"].split(",")
	totGoalsAgainst = homeData["teamStats"]["tot"]["corners_against"].split(",")
	awayTotGoals = awayData["teamStats"]["tot"]["corners"].split(",")
	awayTotGoalsAgainst = awayData["teamStats"]["tot"]["corners_against"].split(",")
	output += f"{', '.join([str(int(x)+int(y)) for x,y in zip(totGoals[-20:], totGoalsAgainst[-20:])])}\n"
	output += f"{', '.join([str(int(x)+int(y)) for x,y in zip(awayTotGoals[-20:], awayTotGoalsAgainst[-20:])])}\n\n"
	output += f"{home}\t\t{away}\n\n"
	for ou in [6.5, 7.5, 8.5, 9.5, 10.5, 11.5, 12.5]:
		overArr = [x for x, y in zip(totGoals, totGoalsAgainst) if int(x) + int(y) > ou]
		over = int(len(overArr) * 100 / len(totGoals))

		overArrL10 = [x for x, y in zip(totGoals[-10:], totGoalsAgainst[-10:]) if int(x) + int(y) > ou]
		overL10 = int(len(overArrL10) * 100 / len(totGoals[-10:]))
		overArr = [x for x, y, ah in zip(totGoals, totGoalsAgainst, homeAH) if int(x) + int(y) > ou and ah == "h"]
		l = [x for x in homeAH if x == "h"]
		overAH = int(len(overArr) * 100 / len(l))

		awayOverArr = [x for x, y in zip(awayTotGoals, awayTotGoalsAgainst) if int(x) + int(y) > ou]
		awayOver = int(len(awayOverArr) * 100 / len(awayTotGoals))

		awayOverArrL10 = [x for x, y in zip(awayTotGoals[-10:], awayTotGoalsAgainst[-10:]) if int(x) + int(y) > ou]
		awayOverL10 = int(len(awayOverArrL10) * 100 / len(awayTotGoals[-10:]))
		overArr = [x for x, y, ah in zip(awayTotGoals, awayTotGoalsAgainst, awayAH) if int(x) + int(y) > ou and ah == "a"]
		l = [x for x in awayAH if x == "a"]
		awayOverAH = int(len(overArr) * 100 / len(l))

		output += f"{over}%/{overL10}%/{overAH}%\t\t{awayOver}%/{awayOverL10}%/{awayOverAH}%\t\to{ou}\n"

	output += f"\n{home} Corners\n"
	tot = homeData["teamStats"]["tot"]["corners"].split(",")
	totAgainst = awayData["teamStats"]["tot"]["corners_against"].split(",")
	output += f"{', '.join(tot[-20:])}\n"
	output += f"{', '.join(totAgainst[-20:])}\n"
	for ou in [1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5]:
		overArr = [x for x in tot if int(x) > ou]
		over = int(len(overArr) * 100 / len(tot))
		overArrL10 = [x for x in tot[-10:] if int(x) > ou]
		overL10 = int(len(overArrL10) * 100 / len(tot[-10:]))
		overArr = [x for x, ah in zip(tot, homeAH) if int(x) > ou and ah == "h"]
		l = [x for x in homeAH if x == "h"]
		overAH = int(len(overArr) * 100 / len(l))

		underArr = [x for x in totAgainst if int(x) > ou]
		under = int(len(underArr) * 100 / len(totAgainst))
		underArrL10 = [x for x in totAgainst[-10:] if int(x) > ou]
		underL10 = int(len(underArrL10) * 100 / len(totAgainst[-10:]))
		overArr = [x for x, ah in zip(totAgainst, awayAH) if int(x) > ou and ah == "a"]
		l = [x for x in awayAH if x == "a"]
		awayOverAH = int(len(overArr) * 100 / len(l))

		output += f"{over}%/{overL10}%/{overAH}%\t\t{under}%/{underL10}%/{awayOverAH}%\t\to{ou}\n"

	output += f"\n{away} Corners\n"
	tot = awayData["teamStats"]["tot"]["corners"].split(",")
	totAgainst = homeData["teamStats"]["tot"]["corners_against"].split(",")
	output += f"{', '.join(tot[-20:])}\n"
	output += f"{', '.join(totAgainst[-20:])}\n"
	for ou in [1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5]:
		overArr = [x for x in tot if int(x) > ou]
		over = int(len(overArr) * 100 / len(tot))
		overArrL10 = [x for x in tot[-10:] if int(x) > ou]
		overL10 = int(len(overArrL10) * 100 / len(tot[-10:]))
		overArr = [x for x, ah in zip(tot, homeAH) if int(x) > ou and ah == "h"]
		l = [x for x in homeAH if x == "h"]
		overAH = int(len(overArr) * 100 / len(l))

		underArr = [x for x in totAgainst if int(x) > ou]
		under = int(len(underArr) * 100 / len(totAgainst))
		underArrL10 = [x for x in totAgainst[-10:] if int(x) > ou]
		underL10 = int(len(underArrL10) * 100 / len(totAgainst[-10:]))
		overArr = [x for x, ah in zip(totAgainst, awayAH) if int(x) > ou and ah == "a"]
		l = [x for x in awayAH if x == "a"]
		awayOverAH = int(len(overArr) * 100 / len(l))

		output += f"{over}%/{overL10}%/{overAH}%\t\t{under}%/{underL10}%/{awayOverAH}%\t\to{ou}\n"

	output += f"\nBTTS\n"
	homeTot = homeData["teamStats"]["tot"]["btts"].split(",")
	awayTot = awayData["teamStats"]["tot"]["btts"].split(",")

	output += f"{', '.join(homeTot[-20:])}\n"
	output += f"{', '.join(awayTot[-20:])}\n\n"

	overArr = [x for x in homeTot if x == "y"]
	over = int(len(overArr) * 100 / len(homeTot))
	overArrL10 = [x for x in homeTot[-10:] if x == "y"]
	overL10 = int(len(overArrL10) * 100 / len(homeTot[-10:]))

	awayOverArr = [x for x in awayTot if x == "y"]
	awayOver = int(len(awayOverArr) * 100 / len(awayTot))
	awayOverArrL10 = [x for x in awayTot[-10:] if x == "y"]
	awayOverL10 = int(len(awayOverArrL10) * 100 / len(awayTot[-10:]))

	output += f"{over}%/{overL10}%\t\t{awayOver}%/{awayOverL10}%\n\n"

	for idx, teamData in enumerate([homeData, awayData]):
		for player in teamData["playerStats"]:
			if not teamData["playerStats"][player]["tot"]:
				continue
			team = home if idx == 0 else away
			output += f"\n{player.title()} ({team})\n"
			for stat in ["sot", "shots"]:
				tot = teamData["playerStats"][player]["tot"][stat].split(",")
				output += f"{stat} {', '.join(tot[-20:])}\n"
				for ou in [0.5, 1.5, 2.5]:
					overArr = [x for x in tot if int(x) > ou]
					over = int(len(overArr) * 100 / len(tot))
					overArrL10 = [x for x in tot[-10:] if int(x) > ou]
					overL10 = int(len(overArrL10) * 100 / len(tot[-10:]))
					ahData = homeAH if idx == 0 else awayAH
					if idx == 0:
						overArr = [x for x, ah in zip(tot, ahData) if int(x) > ou and ah == "h"]
						l = [x for x in ahData if x == "h"]
					else:
						overArr = [x for x, ah in zip(tot, ahData) if int(x) > ou and ah == "a"]
						l = [x for x in ahData if x == "a"]
					overAH = int(len(overArr) * 100 / len(l))

					output += f"\t{ou} {over}%/{overL10}%\n"


	with open("static/soccer/matchup.txt", "w") as fh:
		fh.write(output)
	#print(output)


def writeESPN(teamArg):
	if not teamArg:
		return

	with open("static/soccer/espnIds.json") as fh:
		espnIds = json.load(fh)

	with open("static/soccer/playerIds.json") as fh:
		playerIds = json.load(fh)

	with open("static/soccer/teamLeagues.json") as fh:
		teamLeagues = json.load(fh)

	with open("static/soccer/boxscores.json") as fh:
		boxscores = json.load(fh)

	team = teamArg.replace(" ", "-")
	if team not in espnIds:
		print(f"{team} not found in espn ids")
		return

	league = teamLeagues[team]

	if team not in boxscores:
		boxscores[team] = []

	path = f"static/soccerreference/{league}/{team}.json"
	if True or not os.path.exists(path):
		with open(path, "w") as fh:
			json.dump({}, fh, indent=4)

	with open(path) as fh:
		teamData = json.load(fh)

	if not teamData:
		j = {
			"playerStats": {},
			"teamStats": {}
		}
		teamData = j.copy()

	years = [""]
	#if league == "mls" or team in ["jeonbuk-motors"]:
	#	years.append("2023")

	for year in years:
		url = f"https://www.espn.com/soccer/team/results/_/id/{espnIds[team]}"
		if year:
			url += "/season/"+year
		outfile = "outsoccer"
		time.sleep(0.2)
		os.system(f"curl {url} -o {outfile}")

		soup = BS(open(outfile, 'rb').read(), "lxml")

		for table in soup.find_all("table"):
			year = table.findPrevious("div", class_="Table__Title").text[-4:]
			for row in table.find("tbody").find_all("tr"):
				date = row.find("td").text.strip().split(", ")[-1]
				dt = datetime.strptime(date+" "+year, "%b %d %Y")
				date = str(dt)[:10]
				try:
					gameId = row.find("span", class_="score").find_all("a")[1].get("href").split("/")[-2]
				except:
					continue

				#print(gameId)
				if gameId in boxscores[team]:
					pass
					#continue
				if gameId != "717732":
					pass
					#continue
				boxscores[team].append(gameId)

				time.sleep(0.2)
				url = f"https://www.espn.com/soccer/match/_/gameId/{gameId}"
				os.system(f"curl {url} -o {outfile}")
				soup = BS(open(outfile, 'rb').read(), "lxml")

				data = "{}"
				for script in soup.find_all("script"):
					if not script.string:
						continue
					if "__espnfitt__" in script.string:
						m = re.search(r"__espnfitt__'\]={(.*?)};", script.string)
						if m:
							data = m.group(1).replace("false", "False").replace("true", "True").replace("null", "None")
							data = f"{{{data}}}"
							break

				data = eval(data)

				if "page" not in data or "lineUps" not in data["page"]["content"]["gamepackage"] or "tmlne" not in data["page"]["content"]["gamepackage"]:
					continue

				teamGraphs = "tmStatsGrph" in data["page"]["content"]["gamepackage"]
				#teamGraphs = False

				with open("out", "w") as fh:
					json.dump(data, fh, indent=4)

				# Write Player Stats
				oppTeamStats = {}
				for lineupRow in data["page"]["content"]["gamepackage"]["lineUps"]:
					currTeam = parseTeam(lineupRow["team"]["displayName"])
					if currTeam not in playerIds:
						playerIds[currTeam] = {}

					for playerId in lineupRow["playersMap"]:
						playerRow = lineupRow["playersMap"][playerId]
						player = parsePlayer(playerRow["name"])
						playerIds[currTeam][player] = playerId

						#print(currTeam, team, player)

						if currTeam == team:
							if player not in teamData["playerStats"]:
								teamData["playerStats"][player] = {
									"tot": {}
								}

							# When no tmGraph, players that don't play have stats = {}. players that play have no stats key
							if "stats" not in playerRow:
								if not teamGraphs:
									#print(player)
									teamData["playerStats"][player][date] = {}
								continue

							if "appearances" in playerRow["stats"]:
								teamData["playerStats"][player][date] = {}

							for stat in playerRow["stats"]:
								teamData["playerStats"][player][date][convertStat(stat)] = playerRow["stats"][stat]


				teamData["teamStats"][date] = {}
				isTeam = data["page"]["content"]["gamepackage"]["gmStrp"]["tms"][0]["links"].split("/")[-1] == team
				idx = 0
				if isTeam and not data["page"]["content"]["gamepackage"]["gmStrp"]["tms"][0]["isHome"]:
					idx = 1
				elif not isTeam and data["page"]["content"]["gamepackage"]["gmStrp"]["tms"][0]["isHome"]:
					idx = 1
				
				fullTeam = data["page"]["content"]["gamepackage"]["gmStrp"]["tms"][0]["displayName"].lower()
				fullTeamOpp = data["page"]["content"]["gamepackage"]["gmStrp"]["tms"][1]["displayName"].lower()
				if not isTeam:
					fullTeam = data["page"]["content"]["gamepackage"]["gmStrp"]["tms"][1]["displayName"].lower()
					fullTeamOpp = data["page"]["content"]["gamepackage"]["gmStrp"]["tms"][0]["displayName"].lower()
				fullTeam = strip_accents(fullTeam)
				fullTeamOpp = strip_accents(fullTeamOpp)
				j = {
					"egnatia": "egnatia rrogozhine",
					"fk qarabag": "qarabag",
					"if elfsborg": "elfsborg",
					"iran": "ir iran",
					"malmo ff": "malmo",
					"milton keynes dons": "mk dons",
					"nk celje": "celje",
					"rigas futbola skola": "rigas fs",
					"st johnstone": "st. johnstone",
				}
				fullTeamOpp = j.get(fullTeamOpp, fullTeamOpp)

				isHome = False
				if idx == 0:
					isHome = True
				teamData["teamStats"][date]["awayHome"] = "h" if isHome else "a"

				if teamGraphs:
					# Write Team Stats
					for teamStatsRow in data["page"]["content"]["gamepackage"]["tmStatsGrph"]["stats"][0]["data"]:
						stat = convertStat(teamStatsRow["name"].lower())
						teamData["teamStats"][date][stat] = teamStatsRow["values"][idx]
						otherIdx = 1 if idx == 0 else 0
						if stat in ["sot", "shots", "corners"]:
							teamData["teamStats"][date][stat+"_against"] = teamStatsRow["values"][otherIdx]

				# Write Timeline Info
				firstHalfScore = [0,0]
				secondHalfScore = [0,0]
				halftime = False
				for eventRow in data["page"]["content"]["gamepackage"]["tmlne"]["keyEvents"]:
					eventType = eventRow["type"]
					if eventType == "halftime":
						halftime = True
						continue

					if "goal" in eventType or "scored" in eventType:
						if "homeAway" not in eventRow:
							continue
						eventTeamIdx = 0 if eventRow["homeAway"] == "home" else 1
						if not halftime:
							firstHalfScore[eventTeamIdx] += 1
						else:
							secondHalfScore[eventTeamIdx] += 1

				# If no graph and no player stats, read from commentary
				if not teamGraphs:
					commentary = data["page"]["content"]["gamepackage"]["meta"]["mtchCmmntry"]["lnk"]
					time.sleep(0.2)
					url = "https://www.espn.com"+commentary
					os.system(f"curl {url} -o {outfile}")
					soup = BS(open(outfile, 'rb').read(), "lxml")

					data = "{}"
					for script in soup.find_all("script"):
						if not script.string:
							continue
						if "__espnfitt__" in script.string:
							m = re.search(r"__espnfitt__'\]={(.*?)};", script.string)
							if m:
								data = m.group(1).replace("false", "False").replace("true", "True").replace("null", "None")
								data = f"{{{data}}}"
								break

					data = eval(data)

					#with open("out", "w") as fh:
					#	json.dump(data, fh, indent=4)

					try:
						allCommentary = data["page"]["content"]["gamepackage"]["mtchCmmntry"]["allCommentary"][::-1]
					except:
						del teamData["teamStats"][date]
						continue
					if len(allCommentary) < 30:
						continue

					# halftime wasn't found in timeline
					if not halftime:
						firstHalfScore[0] = 0
						firstHalfScore[1] = 0
						secondHalfScore[0] = 0
						secondHalfScore[1] = 0

					for player in teamData["playerStats"]:
						if date in teamData["playerStats"][player]:
							teamData["playerStats"][player][date] = {"shots": 0, "sot": 0}

					for row in allCommentary:
						detail = row["dtls"].lower()

						if not halftime:
							if detail.startswith("first half ends"):
								homeScore = detail.split(", ")[1][-1]
								awayScore = detail[-2]
								firstHalfScore[0] = int(homeScore)
								firstHalfScore[1] = int(awayScore)
							elif detail.startswith("second half ends"):
								homeScore = int(detail.split(", ")[1][-1])
								awayScore = int(detail[-2])
								secondHalfScore[0] = homeScore - firstHalfScore[0]
								secondHalfScore[1] = awayScore - firstHalfScore[1]


						suffix = ""
						if strip_accents(detail).split(".")[0].endswith(fullTeamOpp):
							suffix = "_against"
						
						stat = player = ""
						if detail.startswith("corner,"):
							stat = "corners"
						elif detail.split(".")[0] in ["attempt blocked", "attempt missed", "attempt saved", "penalty saved", "penalty missed", "penalty blocked"] or " post " in detail or "goal!" in detail:
							player = parsePlayer(detail.split(" (")[0].split(". ")[-1])
							stat = "shots"
							if " saved." in detail or "goal!" in detail:
								stat = "sot"

							#print(detail, player, fullTeamOpp)
							if strip_accents(detail).split("(")[-1].split(")")[0] == fullTeamOpp:
								suffix = "_against"

						if not stat:
							continue

						if stat+suffix not in teamData["teamStats"][date]:
							teamData["teamStats"][date][stat+suffix] = 0
						if stat == "sot" and "shots"+suffix not in teamData["teamStats"][date]:
							teamData["teamStats"][date]["shots"+suffix] = 0
						teamData["teamStats"][date][stat+suffix] += 1
						if stat == "sot":
							teamData["teamStats"][date]["shots"+suffix] += 1

						if player and not suffix:
							teamData["playerStats"][player][date][stat] += 1
							if stat == "sot":
								teamData["playerStats"][player][date]["shots"] += 1


				finalScore = [firstHalfScore[0]+secondHalfScore[0], firstHalfScore[1]+secondHalfScore[1]]
				teamData["teamStats"][date]["btts"] = "y" if 0 not in finalScore else "n"
				teamData["teamStats"][date]["total_goals"] = finalScore[0] + finalScore[1]
				teamData["teamStats"][date]["goals"] = finalScore[idx]
				teamData["teamStats"][date]["1h_goals"] = firstHalfScore[idx]
				teamData["teamStats"][date]["2h_goals"] = secondHalfScore[idx]

				otherIdx = 1 if idx == 0 else 0
				teamData["teamStats"][date]["goals_against"] = finalScore[otherIdx]
				teamData["teamStats"][date]["1h_goals_against"] = firstHalfScore[otherIdx]
				teamData["teamStats"][date]["2h_goals_against"] = secondHalfScore[otherIdx]

	#exit()

	writeTotals(teamData)
	with open(path, "w") as fh:
		json.dump(teamData, fh, indent=4)

	with open("static/soccer/boxscores.json", "w") as fh:
		json.dump(boxscores, fh, indent=4)

def writeTotals(teamData):
	dates = [x for x in teamData["teamStats"] if x != "tot"]
	tot = {}
	for date in sorted(dates):
		for stat in teamData["teamStats"][date]:
			val = teamData["teamStats"][date][stat]
			if stat not in tot:
				tot[stat] = []
			tot[stat].append(val)

	stats = tot.keys()
	for stat in stats:
		tot[stat] = ",".join([str(x) for x in tot[stat]])

	teamData["teamStats"]["tot"] = tot.copy()

	for player in teamData["playerStats"]:
		dates = [x for x in teamData["playerStats"][player] if x != "tot"]
		tot = {}
		for date in sorted(dates):
			for stat in teamData["playerStats"][player][date]:
				val = teamData["playerStats"][player][date][stat]
				if stat not in tot:
					tot[stat] = []
				tot[stat].append(val)

		stats = tot.keys()
		for stat in stats:
			tot[stat] = ",".join([str(x) for x in tot[stat]])

		teamData["playerStats"][player]["tot"] = tot.copy()


def writeESPNIds(date=""):

	if not date:
		date = str(datetime.now())[:10]

	url = f"https://www.espn.com/soccer/schedule/_/date/{date.replace('-', '')}"
	outfile = "outsoccer"
	os.system(f"curl {url} -o {outfile}")

	soup = BS(open(outfile, 'rb').read(), "lxml")

	with open("static/soccer/espnIds.json") as fh:
		espnIds = json.load(fh)

	with open("static/soccer/teamLeagues.json") as fh:
		teamLeagues = json.load(fh)

	teams = []
	for table in soup.find_all("div", class_="ScheduleTables"):
		league = table.find("div", class_="Table__Title").text.lower()
		league = parseTeam(league).replace(" ", "-")
		if "women" in league or league.endswith(" f"):
			continue
		if league not in ["us-open-cup", "english-league-two", "english-national-league", "scottish-league-one"]:
			pass
			#continue
		if not os.path.isdir(f"static/soccerreference/{league}"):
			os.mkdir(f"static/soccerreference/{league}")

		for row in table.find("tbody").find_all("tr"):
			try:
				awayId = row.find("td").find("span").find("a").get("href")
				homeId = row.find_all("td")[1].find("span").find("a").get("href")
				awayTeam = awayId.split("/")[-1]
				homeTeam = homeId.split("/")[-1]
			except:
				continue

			teams.append(awayTeam)
			teams.append(homeTeam)

			espnIds[awayTeam] = awayId.split("/")[-2]
			espnIds[homeTeam] = homeId.split("/")[-2]
			teamLeagues[awayTeam] = league
			teamLeagues[homeTeam] = league


	with open("static/soccer/espnIds.json", "w") as fh:
		json.dump(espnIds, fh, indent=4)

	with open("static/soccer/teamLeagues.json", "w") as fh:
		json.dump(teamLeagues, fh, indent=4)

	#teams = teams[teams.index("hamrun-spartans"):]
	for team in teams:
		pass
		print("\n\n",team,"\n\n")
		writeESPN(team)

def write365():

	lines = ""
	props = "https://www.oh.bet365.com/?_h=MHxK6gn5idsD_JJ0gjhGEQ%3D%3D#/AC/B13/C20904590/D7/E83/F4/"

	js = """
	
	const data = {};

	{
		for (const main of document.querySelectorAll(".gl-MarketGroupContainer")) {
			let title = document.getElementsByClassName("rcl-MarketGroupButton_MarketTitle")[0].innerText.toLowerCase();
			let prop = title.replace("moneyline", "ml");

			if (prop == "team corners") {
				prop = "corners";
			}

			if (["set", "total_sets", "set1_total", "away_total"].indexOf(prop) >= 0) {
				for (div of document.getElementsByClassName("src-FixtureSubGroup")) {
					let game = div.querySelector(".src-FixtureSubGroupButton_Text").innerText.toLowerCase().replace(" vs ", " v ").replaceAll(".", "").replaceAll("/", " / ");
					let away = game.split(" v ")[0];
					let home = game.split(" v ")[1];
					if (away.indexOf(" / ") >= 0) {
						let away1 = away.split(" / ")[0];
						let away2 = away.split(" / ")[1];
						let home1 = home.split(" / ")[0];
						let home2 = home.split(" / ")[1];
						game = away1.split(" ")[away1.split(" ").length - 1]+" / "+away2.split(" ")[away2.split(" ").length - 1]+" v "+home1.split(" ")[home1.split(" ").length - 1]+" / "+home2.split(" ")[home2.split(" ").length - 1];
					} else {
						away = away.split(" ")[away.split(" ").length - 1];
						home = home.split(" ")[home.split(" ").length - 1];
						game = away+" v "+home;
					}

					if (data[game] === undefined) {
						data[game] = {};
					}

					if (div.classList.contains("src-FixtureSubGroup_Closed")) {
						div.click();
					}

					if (prop == "away_total") {
						let ou = div.querySelectorAll(".srb-ParticipantCenteredStackedWithMarketBorders_Handicap")[0].innerText.replace("Over ", "");
						
						data[game]["away_total"] = {};
						data[game]["away_total"][ou] = div.querySelectorAll(".srb-ParticipantCenteredStackedWithMarketBorders_Odds")[0].innerText+"/"+div.querySelectorAll(".srb-ParticipantCenteredStackedWithMarketBorders_Odds")[1].innerText;

						ou = div.querySelectorAll(".srb-ParticipantCenteredStackedWithMarketBorders_Handicap")[2].innerText.replace("Over ", "");
						data[game]["home_total"] = {};
						data[game]["home_total"][ou] = div.querySelectorAll(".srb-ParticipantCenteredStackedWithMarketBorders_Odds")[2].innerText+"/"+div.querySelectorAll(".srb-ParticipantCenteredStackedWithMarketBorders_Odds")[3].innerText;
					} else if (prop == "total_sets") {
						data[game][prop] = {};

						let ou = div.querySelectorAll(".gl-Participant_General")[1].querySelector(".gl-ParticipantBorderless_Odds").innerText+"/"+div.querySelectorAll(".gl-Participant_General")[0].querySelector(".gl-ParticipantBorderless_Odds").innerText;
						data[game][prop]["2.5"] = ou;
					} else {
						data[game][prop] = {};
						let arr = [];
						for (const set of div.querySelector(".gl-Market").querySelectorAll(".gl-Market_General-cn1")) {
							arr.push(set.innerText);
						}

						let idx = 0;
						for (const playerDiv of div.querySelectorAll(".gl-Participant_General")) {
							let set = arr[idx % arr.length];
							const odds = playerDiv.querySelector(".gl-ParticipantOddsOnly_Odds").innerText;

							if (prop == "set") {
								if (idx >= arr.length) {
									let s1 = set.split("-")[0];
									let s2 = set.split("-")[1];
									set = s2+"-"+s1;
								}
								
								data[game][prop][set] = odds;
							} else {
								if (idx < arr.length) {
									data[game][prop][set] = odds;
								} else {
									data[game][prop][set] += "/"+odds;
								}
							}
							idx += 1;
						}
					}
				}
			} else {
				let games = [];
				let idx = 0;
				for (div of main.querySelector(".gl-Market_General").children) {
					if (idx === 0 || div.classList.contains("Hidden")) {
						idx += 1;
						continue;
					}
					if (div.classList.contains("rcl-MarketHeaderLabel-isdate")) {
						//break;
						continue;
					}
					let away = div.querySelectorAll(".rcl-ParticipantFixtureDetailsTeam_TeamName")[0].innerText.toLowerCase().replaceAll(".", "");
					let home = div.querySelectorAll(".rcl-ParticipantFixtureDetailsTeam_TeamName")[1].innerText.toLowerCase().replaceAll(".", "");
					let game = (away+" v "+home).replaceAll("/", " / ");
					if (away.indexOf("/") >= 0) {
						let away1 = away.split("/")[0];
						let away2 = away.split("/")[1];
						let home1 = home.split("/")[0];
						let home2 = home.split("/")[1];
						game = away1.split(" ")[away1.split(" ").length - 1]+" / "+away2.split(" ")[away2.split(" ").length - 1]+" v "+home1.split(" ")[home1.split(" ").length - 1]+" / "+home2.split(" ")[home2.split(" ").length - 1];
					} else {
						away = away.split(" ")[away.split(" ").length - 1];
						home = home.split(" ")[home.split(" ").length - 1];
						game = away+" v "+home;
					}
					games.push(game);

					if (!data[game]) {
						data[game] = {};
					}
				}

				idx = 0;
				let divs = main.querySelectorAll(".gl-Market_General")[1].querySelectorAll(".gl-Participant_General");
				for (let i = 0; i < divs.length; i += 1) {
					let game = games[idx];

					if (!game) {
						break;
					}

					if (prop.indexOf("ml") >= 0) {
						let odds = divs[i].querySelector(".sgl-ParticipantOddsOnly80_Odds").innerText;
						data[game][prop] = odds;
					} else {
						let line = divs[i].querySelector(".src-ParticipantCenteredStacked80_Handicap").innerText;
						let odds = divs[i].querySelector(".src-ParticipantCenteredStacked80_Odds").innerText;
						if (!data[game][prop]) {
							data[game][prop] = {};
						}
						line = parseFloat(line).toString();
						data[game][prop][line] = odds;
					}
					idx += 1;
				}

				idx = 0;
				divs = main.querySelectorAll(".gl-Market_General")[2].querySelectorAll(".gl-Participant_General");
				for (let i = 0; i < divs.length; i += 1) {
					let game = games[idx];

					if (!game) {
						break;
					}

					if (prop.indexOf("ml") >= 0) {
						let odds = divs[i].querySelector(".sgl-ParticipantOddsOnly80_Odds").innerText;
						data[game][prop] += "/"+odds;
					} else {
						let line = divs[i].querySelector(".src-ParticipantCenteredStacked80_Handicap").innerText;
						let odds = divs[i].querySelector(".src-ParticipantCenteredStacked80_Odds").innerText;
						if (prop.indexOf("spread") >= 0) {
							line = (parseFloat(line) * -1).toString();
						} else {
							line = parseFloat(line).toString();
						}

						data[game][prop][line] += "/"+odds;
					}
					idx += 1;
				}
			}
		}
		console.log(data);
	}

	"""
	pass

def writeLineups(league=None):
	lineups = {}
	if False:
		with open(f"{prefix}static/soccer/lineups.json") as fh:
			lineups = json.load(fh)

	leagues = ["", "fran", "seri", "liga", "bund", "lmx"]
	for league in leagues:
		url = "https://www.rotowire.com/soccer/lineups.php"
		if league:
			url += f"?league={league.upper()}"
		outfile = "outsoccerl"
		time.sleep(0.5)
		os.system(f"curl '{url}' --compressed -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:133.0) Gecko/20100101 Firefox/133.0' -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8' -H 'Accept-Language: en-US,en;q=0.5' -H 'Referer: https://www.rotowire.com/soccer/lineups.php' -H 'Connection: keep-alive' -H 'Cookie: PHPSESSID=fa8217e19e4a32a38d5bd2e3e46e4487; g_uuid=8ccd1e2c-792c-4822-a45e-9b68d791c622; cohort_id=3; usprivacy=1NNN; g_sid=1729631249817.jm63rbi; g_device=macos%7Cdesktop; ktag_version=20241128; cookieyes-consent=consentid:dHRLVWZXcDZsYkVZazdGUFZwa2E4YU5acFNQQk5WMFI,consent:yes,action:no,necessary:yes,functional:yes,analytics:yes,performance:yes,advertisement:yes,other:yes' -H 'Upgrade-Insecure-Requests: 1' -H 'Sec-Fetch-Dest: document' -H 'Sec-Fetch-Mode: navigate' -H 'Sec-Fetch-Site: same-origin' -H 'Priority: u=0, i' -o {outfile}")
		soup = BS(open(outfile, 'rb').read(), "lxml")

		rotoTeams = []
		for game in soup.find_all("div", class_="lineup"):
			if "is-tools" in game.get("class"):
				continue
			teams = game.find_all("div", class_="lineup__mteam")
			lineupList = game.find_all("ul", class_="lineup__list")
			statusList = game.find_all("li", class_="lineup__status")
			for idx, teamLink in enumerate(teams):
				team = teamLink.text.lower().strip()
				rotoTeams.append(team)
				team = convertSoccer(team)
				try:
					lineups[team] = {
						"confirmed": False if "is-expected" in statusList[idx].get("class") else True,
						"starters": []
					}
				except:
					continue
				for playerIdx, li in enumerate(lineupList[idx].find_all("li", class_="lineup__player")):
					player = " ".join(li.find("a").get("href").split("/")[-1].split("-")[:-1])
					player = parsePlayer(player)
					pos = li.find("div").text

					if playerIdx < 11:
						lineups[team]["starters"].append(player)
					elif "hide" in li.get("class"):
						continue

	with open(f"{prefix}static/soccer/lineups.json", "w") as fh:
		json.dump(lineups, fh, indent=4)

def writeDaily(date=None):
	if not date:
		date = str(datetime.now())[:10]

	with open(f"{prefix}static/soccer/kambi.json") as fh:
		kambiLines = json.load(fh)

	with open(f"{prefix}static/soccer/pinnacle.json") as fh:
		pnLines = json.load(fh)

	with open(f"{prefix}static/soccer/mgm.json") as fh:
		mgmLines = json.load(fh)

	with open(f"{prefix}static/soccer/fanduelLines.json") as fh:
		fdLines = json.load(fh)

	with open(f"{prefix}static/soccer/draftkings.json") as fh:
		dkLines = json.load(fh)

	with open(f"{prefix}static/soccer/espn.json") as fh:
		espnLines = json.load(fh)

	with open(f"{prefix}static/soccer/caesars.json") as fh:
		czLines = json.load(fh)

	with open(f"{prefix}static/soccer/bet365.json") as fh:
		bet365Lines = json.load(fh)

	lines = {
		"pn": pnLines,
		"kambi": kambiLines,
		"mgm": mgmLines,
		"fd": fdLines,
		"espn": espnLines,
		"365": bet365Lines,
		"dk": dkLines,
		"cz": czLines
	}

	with open(f"static/soccer/lines/{date}.json", "w") as fh:
		json.dump(lines, fh)

def writeEV(propArg="", bookArg="fd", teamArg="", boost=None, singles=None, doubles=None, dateArg=None):
	writeDaily(dateArg)
	if not boost:
		boost = 1

	with open(f"{prefix}static/soccer/draftkings.json") as fh:
		dkLines = json.load(fh)

	with open(f"{prefix}static/soccer/bet365.json") as fh:
		bet365Lines = json.load(fh)

	with open(f"{prefix}static/soccer/fanduelLines.json") as fh:
		fdLines = json.load(fh)

	with open(f"{prefix}static/soccer/mgm.json") as fh:
		mgmLines = json.load(fh)

	with open(f"{prefix}static/soccer/pinnacle.json") as fh:
		pnLines = json.load(fh)

	with open(f"{prefix}static/soccer/caesars.json") as fh:
		czLines = json.load(fh)

	with open(f"{prefix}static/soccer/bovada.json") as fh:
		bvLines = json.load(fh)

	with open(f"{prefix}static/soccer/kambi.json") as fh:
		kambiLines = json.load(fh)

	with open(f"{prefix}static/soccer/espn.json") as fh:
		espnLines = json.load(fh)

	with open(f"{prefix}static/soccer/ev.json") as fh:
		evData = json.load(fh)

	with open(f"{prefix}static/soccer/lineups.json") as fh:
		lineups = json.load(fh)

	with open(f"{prefix}static/soccer/teamLeagues.json") as fh:
		teamLeagues = json.load(fh)

	with open(f"{prefix}static/soccer/schedule.json") as fh:
		schedule = json.load(fh)

	with open(f"{prefix}static/soccer/roster.json") as fh:
		roster = json.load(fh)

	lines = {
		"pn": pnLines,
		"kambi": kambiLines,
		"mgm": mgmLines,
		"fd": fdLines,
		"dk": dkLines,
		"365": bet365Lines,
		"cz": czLines,
		"espn": espnLines,
		#"bv": bvLines
	}

	date = dateArg
	if not date:
		date = str(datetime.now())[:10]

	leagues = {}
	for league in schedule[date]:
		for game in schedule[date][league]:
			leagues[game] = league

	evData = {}
	games = []
	for book in lines:
		for game in lines[book]:
			if game not in games:
				games.append(game)

	for game in games:
		if teamArg and teamArg not in game:
			continue

		try:
			team1, team2 = map(str, game.split(" v "))
		except:
			continue

		props = {}
		for book in lines:
			if game not in lines[book]:
				continue
			for prop in lines[book][game]:
				props[prop] = 1

		for prop in props:

			if propArg and prop != propArg:
				continue

			if prop in ["assist"]:
				continue

			handicaps = {}
			for book in lines:
				lineData = lines[book]

				if game in lineData and prop in lineData[game]:
					if type(lineData[game][prop]) is not dict:
						handicaps[(" ", " ")] = ""
						break
					for handicap in lineData[game][prop]:
						player = playerHandicap = ""
						try:
							player = float(handicap)
							player = ""
							handicaps[(handicap, playerHandicap)] = player
						except:
							player = handicap
							playerHandicap = ""
							if " " in lineData[game][prop][player]:
								playerHandicap = lineData[game][prop][player].split(" ")[0]
								handicaps[(handicap, playerHandicap)] = player
							elif type(lineData[game][prop][player]) is dict:
								for h in lineData[game][prop][player]:
									handicaps[(handicap, h)] = player
							else:
								handicaps[(handicap, "0.5")] = player

			for handicap, playerHandicap in handicaps:
				player = handicaps[(handicap, playerHandicap)]

				for i in range(2):
					highestOdds = []
					books = []
					odds = []

					for book in lines:
						lineData = lines[book]
						if game in lineData and prop in lineData[game]:
							#print(book, game, prop, handicap)
							if book == "cz" and prop == "player_tackles":
								#continue
								pass

							if type(lineData[game][prop]) is str:
								val = lineData[game][prop]
							else:
								if handicap not in lineData[game][prop]:
									continue
								val = lineData[game][prop][handicap]

							if player.strip():
								if type(val) is dict:
									if playerHandicap not in val:
										continue
									val = lineData[game][prop][handicap][playerHandicap]
								else:
									if " " in val and playerHandicap != val.split(" ")[0]:
										continue
									val = lineData[game][prop][handicap].split(" ")[-1]

							try:
								o = val.split(" ")[-1].split("/")[i]
								ou = val.split(" ")[-1]
							except:
								if i == 1:
									continue
								o = val
								ou = val

							if not o or o == "-" or "odds" in o.lower():
								continue

							try:
								highestOdds.append(int(o.replace("+", "")))
								odds.append(ou)
								books.append(book)
							except:
								continue

					if len(books) < 2:
						continue

					pn = ""
					try:
						bookIdx = books.index("pn")
						pn = odds[bookIdx]
						odds.remove(pn)
						books.remove("pn")
					except:
						pass

					evBook = ""
					l = odds
					if bookArg:
						if bookArg not in books:
							continue
						evBook = bookArg
						idx = books.index(bookArg)
						maxOU = odds[idx]
						try:
							line = maxOU.split("/")[i]
						except:
							continue
					else:
						maxOdds = []
						for odds in l:
							try:
								maxOdds.append(int(odds.split("/")[i]))
							except:
								maxOdds.append(-10000)

						if not maxOdds:
							continue

						maxOdds = max(maxOdds)
						maxOU = ""
						for odds, book in zip(l, books):
							try:
								if str(int(odds.split("/")[i])) == str(maxOdds):
									evBook = book
									maxOU = odds
									break
							except:
								pass

						line = maxOdds

					line = convertAmericanOdds(1 + (convertDecOdds(int(line)) - 1) * boost)

					l.remove(maxOU)
					books.remove(evBook)
					if pn:
						books.append("pn")
						l.append(pn)

					avgOver = []
					avgUnder = []

					for book in l:
						if book and book != "-":
							avgOver.append(convertImpOdds(int(book.split("/")[0])))
							if "/" in book:
								avgUnder.append(convertImpOdds(int(book.split("/")[1])))
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

					if i == 1:
						ou = f"{avgUnder}/{avgOver}"
					else:
						ou = f"{avgOver}/{avgUnder}"

					if ou == "-/-" or ou.startswith("-/") or ou.startswith("0/"):
						continue

					if ou.endswith("/-") or ou.endswith("/0"):
						ou = ou.split("/")[0]

					if not line:
						continue

					key = f"{game} {prop} {handicap} {'over' if i == 0 else 'under'} {playerHandicap}"
					if key in evData:
						continue
					if True:
						pass
						devig(evData, key, ou, line, prop=prop)
						if pn:
							if i == 1:
								pn = f"{pn.split('/')[1]}/{pn.split('/')[0]}"
							devig(evData, key, pn, line, prop=prop, sharp=True)
						#devigger(evData, player, ou, line, dinger, avg=True, prop=prop)
						if key not in evData:
							#print(key)
							continue
						if float(evData[key]["ev"]) > 0:
							#print(evData[key]["ev"], game, prop, handicap, int(line), ou, evBook, "\n\t", l)
							pass

						teamsArr = []
						team = hit = hitL10 = minLog = log = p = ""
						if player and player in roster and game in leagues:
							potentialTeams = roster[player]
							away, home = map(str, game.split(" v "))
							
							if away in potentialTeams:
								team = away
							elif home in potentialTeams:
								team = home
							
							leagueArg = league.replace(" ", "_")
							
							statsProp = prop.replace("player_", "")
							if statsProp == "saves":
								statsProp = "gk_saves"
							p = player
							teamsArr = [team]
						elif game in leagues and prop not in ["dnb", "btts", "total", "spread"] and "1h_" not in prop and "2h_" not in prop:
							p = "teamStats"
							if "away_" in prop:
								teamsArr = [game.split(" v ")[1]]
							elif "home_" in prop:
								teamsArr = [game.split(" v ")[0]]
							else:
								teamsArr = game.split(" v ")
							team = teamsArr[0]
							statsProp = prop.replace("away_", "").replace("home_", "").replace("game_", "")
							if "corners" in prop:
								statsProp = "corner_kicks"

						tArg = team.replace(" ", "_")
						leagueArg = leagues.get(game, "").replace(" ", "_")
						path = f"static/soccer/stats/{leagueArg}/{tArg}.json"
						if team and os.path.exists(path):
							with open(path) as fh:
								stats = json.load(fh)

							if p in stats and statsProp in stats[p]:
								arr = stats[p][statsProp].split(",")
								arr = [int(x) for x in arr if x != ""]
								arrAgainst = []
								if p == "teamStats":
									#arrAgainst = stats[p+"Against"][statsProp].split(",")
									#arrAgainst = [int(x) for x in arrAgainst if x != ""]
									pass
								if len(teamsArr) > 1:
									tArg = teamsArr[1].replace(" ", "_")
									path = f"static/soccer/stats/{leagueArg}/{tArg}.json"
									with open(path) as fh:
										stats2 = json.load(fh)
									arr2 = stats2[p][statsProp].split(",")
									arr2 = [int(x) for x in arr2 if x != ""]
									arr = [x + y for x,y in zip(arr, arr2)]

								if len(arr):
									log = ",".join([str(x) for x in arr[-10:]])
									if player:
										minLog = ",".join(stats[p]["minutes"].split(",")[-5:])
									logAgainst = ",".join([str(x) for x in arrAgainst[-10:]])
									if i == 1:
										hit = len([x for x in arr if int(x) < float(playerHandicap or handicap)]) * 100 / len(arr)
										hitL10 = len([x for x in arr[-10:] if int(x) < float(playerHandicap or handicap)]) * 100 / len(arr[-10:])
									else:
										hit = len([x for x in arr if int(x) > float(playerHandicap or handicap)]) * 100 / len(arr)
										hitL10 = len([x for x in arr[-10:] if int(x) > float(playerHandicap or handicap)]) * 100 / len(arr[-10:])

						lineupStatus = "-"
						if player and team in lineups:
							if player in lineups[team]["starters"]:
								if lineups[team]["confirmed"]:
									lineupStatus = "🟢"
								else:
									lineupStatus = "🟡"
							else:
								if lineups[team]["confirmed"]:
									lineupStatus = "🔴"
								else:
									lineupStatus = ""

						implied = 0
						if line > 0:
							implied = 100 / (line + 100)
						else:
							implied = -line / (-line + 100)
						implied = round(implied * 100)

						evData[key]["lineupStatus"] = lineupStatus
						evData[key]["game"] = game
						evData[key]["team"] = team
						evData[key]["hit"] = hit
						evData[key]["hitL10"] = hitL10
						evData[key]["log"] = log
						evData[key]["minLog"] = minLog
						evData[key]["player"] = player
						evData[key]["book"] = evBook
						evData[key]["books"] = books
						evData[key]["ou"] = ou
						evData[key]["under"] = i == 1
						evData[key]["odds"] = l
						evData[key]["line"] = line
						evData[key]["fullLine"] = maxOU
						evData[key]["handicap"] = handicap
						evData[key]["playerHandicap"] = playerHandicap
						evData[key]["prop"] = prop
						j = {b: o for o, b in zip(l, books)}
						j[evBook] = maxOU
						evData[key]["bookOdds"] = j
						evData[key]["implied"] = implied

	with open(f"static/soccer/ev.json", "w") as fh:
		json.dump(evData, fh, indent=4)

def printEV(propArg):

	with open(f"static/soccer/ev.json") as fh:
		evData = json.load(fh)

	with open("static/soccer/corners.json") as fh:
		corners = json.load(fh)

	with open("static/soccer/totals.json") as fh:
		totals = json.load(fh)

	with open("static/soccer/winLoss.json") as fh:
		winLoss = json.load(fh)

	data = []
	for game in evData:
		d = evData[game]
		j = [f"{k}:{d['bookOdds'][k]}" for k in d["bookOdds"] if k != d["book"]]
		data.append((d["ev"], game, d["line"], d["book"], j, d))

	for row in sorted(data):
		if not propArg and (row[-1]["prop"] in ["atgs", "assist"] or "player_shots" in row[-1]["prop"]):
			continue
		print(row[:-1])

	output = "\t".join(["EV", "PN EV", "EV Book", "Imp", "Game", "Player", "Prop", "O/U", "FD", "DK", "MGM", "Bet365", "CZ", "PN", "Kambi", "ESPN", "% Over", "Splits"]) + "\n"
	for row in sorted(data, reverse=True):
		if row[-1]["prop"] not in ["atgs", "score_or_assist", "team_fgs", "header"]:
			continue
		ou = ("u" if row[-1]["under"] else "o")+" "
		if row[-1]["player"]:
			ou += row[-1]["playerHandicap"]
		else:
			ou += row[-1]["handicap"]
		teamGame = row[-1]["team"]
		if not teamGame:
			teamGame = row[-1]["game"]
		arr = [row[0], row[-1].get("pn_ev", "-"), str(row[-1]["line"])+" "+row[-1]["book"].replace("kambi", "br").upper(), f"{row[-1]['implied']}%", teamGame, row[-1]["player"], row[-1]["prop"], ou]
		for book in ["fd", "dk", "mgm", "365", "cz", "pn", "kambi", "espn"]:
			o = str(row[-1]["bookOdds"].get(book, "-"))
			if o.startswith("+"):
				o = "'"+o
			arr.append(str(o))
		try:
			hit = round(float(row[-1]['hit']))
		except:
			hit = "-"
		arr.extend([f"{hit}%", row[-1]['log']])
		output += "\t".join([str(x) for x in arr])+"\n"

	#with open("static/soccer/atgs.csv", "w") as fh:
	#	fh.write(output)

	output = "\t".join(["EV", "EV Book", "Imp", "Game", "Player", "Prop", "O/U", "FD", "DK", "Bet365", "CZ", "Kambi", "ESPN", "L10% Over", "% Over", "Splits", "", "Minutes"]) + "\n"
	for row in sorted(data, reverse=True):
		if "player_" not in row[-1]["prop"] and row[-1]["prop"] not in ["assist"]:
			continue
		ou = ("u" if row[-1]["under"] else "o")+" "
		if row[-1]["player"]:
			ou += row[-1]["playerHandicap"]
		else:
			ou += row[-1]["handicap"]
		teamGame = row[-1]["team"]
		if not teamGame:
			teamGame = row[-1]["game"]
		arr = [row[0], str(row[-1]["line"])+" "+row[-1]["book"].replace("kambi", "br").upper(), f"{row[-1]['implied']}%", teamGame, row[-1]["handicap"].title(), row[-1]["prop"].replace("player_", ""), ou]
		for book in ["fd", "dk", "365", "cz", "kambi", "espn"]:
			o = str(row[-1]["bookOdds"].get(book, "-"))
			if o.startswith("+"):
				o = "'"+o
			arr.append(str(o))
		try:
			hit = round(float(row[-1]['hit']))
		except:
			#continue
			hit = "-"
		try:
			hitL10 = round(float(row[-1]['hitL10']))
		except:
			hitL10 = "-"
		arr.extend([f"{hitL10}%", f"{hit}%", row[-1]['log'], row[-1]["lineupStatus"], row[-1]['minLog']])
		output += "\t".join([str(x) for x in arr])+"\n"

	with open("static/soccer/playerProps.csv", "w") as fh:
		fh.write(output)

	output = "\t".join(["EV", "EV Book", "Imp", "Game", "Prop", "O/U", "FD", "DK", "MGM", "Bet365", "CZ", "PN", "Kambi", "ESPN", "L10% Over", "% Over", "Splits"]) + "\n"
	for row in sorted(data, reverse=True):
		if "player_" in row[-1]["prop"] or row[-1]["prop"] in ["atgs", "team_fgs", "assist", "score_or_assist", "header"]:
			continue
		ou = ("u" if row[-1]["under"] else "o")+" "
		if row[-1]["player"]:
			ou += row[-1]["playerHandicap"]
		else:
			ou += row[-1]["handicap"]
		arr = [row[0], str(row[-1]["line"])+" "+row[-1]["book"].replace("kambi", "br").upper(), f"{row[-1]['implied']}%", row[-1]["game"], row[-1]["prop"], ou]
		for book in ["fd", "dk", "mgm", "365", "cz", "pn", "kambi", "espn"]:
			o = str(row[-1]["bookOdds"].get(book, "-"))
			if o.startswith("+"):
				o = "'"+o
			arr.append(str(o))
		try:
			hit = round(float(row[-1]['hit']))
		except:
			#continue
			hit = "-"
		try:
			hitL10 = round(float(row[-1]['hitL10']))
		except:
			hitL10 = "-"
		arr.extend([f"{hitL10}%", f"{hit}%", row[-1]['log']])
		output += "\t".join([str(x) for x in arr])+"\n"

	with open("static/soccer/props.csv", "w") as fh:
		fh.write(output)


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("-d", "--date", help="date")
	parser.add_argument("--action", action="store_true", help="Action Network")
	parser.add_argument("--avg", action="store_true", help="AVG")
	parser.add_argument("--all", action="store_true", help="ALL AVGs")
	parser.add_argument("--fd", action="store_true", help="Fanduel")
	parser.add_argument("--dk", action="store_true", help="Fanduel")
	parser.add_argument("--cz", action="store_true")
	parser.add_argument("--pb", action="store_true", help="Pointsbet")
	parser.add_argument("--writeBV", action="store_true", help="Bovada")
	parser.add_argument("--bv", action="store_true", help="Bovada")
	parser.add_argument("--ev", action="store_true", help="EV")
	parser.add_argument("--bpp", action="store_true", help="BPP")
	parser.add_argument("--kambi", action="store_true", help="Kambi")
	parser.add_argument("--mgm", action="store_true", help="MGM")
	parser.add_argument("--pn", action="store_true", help="Pinnacle")
	parser.add_argument("-p", "--print", action="store_true", help="Print")
	parser.add_argument("-g", "--game", help="Game")
	parser.add_argument("-t", "--team", help="Team")
	parser.add_argument("-l", "--league", help="League")
	parser.add_argument("-k", "--k", action="store_true", help="Ks")
	parser.add_argument("--ml", action="store_true", help="Moneyline and Totals")
	parser.add_argument("--prop", help="Prop")
	parser.add_argument("-u", "--update", action="store_true", help="Update")
	parser.add_argument("--under", action="store_true", help="Under")
	parser.add_argument("--nocz", action="store_true", help="No CZ Lines")
	parser.add_argument("--no365", action="store_true", help="No 365 Devig")
	parser.add_argument("--nobr", action="store_true", help="No BR/Kambi lines")
	parser.add_argument("--dinger", action="store_true", help="Dinger Tues")
	parser.add_argument("--plays", action="store_true", help="Plays")
	parser.add_argument("--summary", action="store_true", help="Summary")
	parser.add_argument("--text", action="store_true", help="Text")
	parser.add_argument("--lineups", action="store_true", help="Lineups")
	parser.add_argument("--singles", action="store_true", help="Singles")
	parser.add_argument("--doubles", action="store_true", help="Doubles")
	parser.add_argument("--lineupsLoop", action="store_true", help="Lineups")
	parser.add_argument("--totals", action="store_true", help="Totals")
	parser.add_argument("--corners", action="store_true", help="Corners")
	parser.add_argument("--leagues", action="store_true", help="Leagues")
	parser.add_argument("--sgp", action="store_true", help="SGP")
	parser.add_argument("--boost", help="Boost", type=float)
	parser.add_argument("--book", help="Book")
	parser.add_argument("--token")
	parser.add_argument("--espnIds", action="store_true", help="ESPN Ids")
	parser.add_argument("--espn", action="store_true", help="ESPN")
	parser.add_argument("--keep", action="store_true")
	parser.add_argument("--debug", action="store_true")
	parser.add_argument("-m", "--matchup", help="Matchup")
	parser.add_argument("--player", help="Player")

	args = parser.parse_args()

	if args.espnIds:
		writeESPNIds(date=args.date)

	if args.espn:
		for team in args.team.split(","):
			writeESPN(team)

	if args.matchup:
		#writeESPN(args.matchup.split(" v ")[0])
		#writeESPN(args.matchup.split(" v ")[1])
		printMatchup(args.matchup)

	if args.leagues:
		writeLeagues(args.book)

	if args.lineups:
		writeLineups(args.league)

	if args.totals:
		writeTotals(args.team)

	if args.corners:
		writeCorners()

	if args.fd:
		writeFanduel()

	if args.sgp:
		writeSGP()

	if args.dk:
		writeDK(args.date, args.league)

	if args.kambi:
		writeKambi(args.date)

	if args.bv:
		writeBovada(args.date)

	if args.mgm:
		writeMGM(args.date)

	if args.cz:
		writeCZ(args.date, args.token, args.keep)

	if args.pn:
		writePinnacle(args.date, args.debug)

	if args.pb:
		writePointsbet(args.date)

	if args.update:
		#writeFanduel()
		#writeDK(args.date)
		#writeBovada(args.date)
		print("BR")
		writeKambi(args.date)
		#print("MGM")
		#writeMGM(args.date)
		#writePointsbet(args.date)
		print("PN")
		writePinnacle(args.date)
		print("CZ")
		writeCZ(args.date, args.token, args.keep)

	if args.ev:
		writeEV(propArg=args.prop, bookArg=args.book, boost=args.boost, doubles=args.doubles, singles=args.singles, teamArg=args.team, dateArg=args.date)

	if args.print:
		printEV(args.prop)


	if args.player:
		with open(f"{prefix}static/soccer/draftkings.json") as fh:
			dkLines = json.load(fh)

		with open(f"{prefix}static/soccer/bet365.json") as fh:
			bet365Lines = json.load(fh)

		with open(f"{prefix}static/soccer/fanduelLines.json") as fh:
			fdLines = json.load(fh)

		with open(f"{prefix}static/soccer/kambi.json") as fh:
			kambiLines = json.load(fh)

		with open(f"{prefix}static/soccer/mgm.json") as fh:
			mgmLines = json.load(fh)

		with open(f"{prefix}static/soccer/pinnacle.json") as fh:
			pnLines = json.load(fh)

		with open(f"{prefix}static/soccer/caesars.json") as fh:
			czLines = json.load(fh)

		with open(f"{prefix}static/soccer/espn.json") as fh:
			espnLines = json.load(fh)
	
		player = args.player

		for game in bet365Lines:
			for prop in bet365Lines[game]:
				if args.prop and args.prop != prop:
					continue

				dk = fd = bet365 = kambi = espn = cz = mgm = pn = ""
				try:
					mgm = mgmLines[game][prop][player]
				except:
					pass
				try:
					dk = dkLines[game][prop][player]
				except:
					pass
				try:
					fd = fdLines[game][prop][player]
				except:
					pass
				try:
					bet365 = bet365Lines[game][prop][player]
				except:
					pass
				try:
					kambi = kambiLines[game][prop][player]
				except:
					pass
				try:
					pn = pnLines[game][prop][player]
				except:
					pass
				try:
					espn = espnLines[game][prop][player]
				except:
					pass
				try:
					cz = czLines[game][prop][player]
				except:
					pass

				if not mgm and not fd and not bet365 and not kambi and not pn and not espn and not cz:
					continue

				print(f"{prop} fd='{fd}'\ndk='{dk}'\n365='{bet365}'\nkambi='{kambi}'\ncz='{cz}'\nespn='{espn}'\npn={pn}\nmgm={mgm}")

