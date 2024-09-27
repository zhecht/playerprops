
import time
import json
import random
import unicodedata
import nodriver as uc

def convertTeam(team):
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
	return t

def strip_accents(text):
	try:
		text = unicode(text, 'utf-8')
	except NameError: # unicode is a default on python 3
		pass

	text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode("utf-8")

	return str(text)

def parsePlayer(player):
	player = strip_accents(player).lower().replace(".", "").replace("'", "").replace("-", " ").replace(" jr", "").replace(" sr", "").replace(" iii", "").replace(" ii", "")
	return player

data = {}
props = {}
async def write365():
	# start with multi
	url = "https://www.oh.bet365.com/?_h=CfVWPHD5idsD_8dFdjBYcw%3D%3D&btsffd=1#/AC/B12/C20426855/D47/E120593/F47/N7/"

	browser = await uc.start(no_sandbox=True)
	page = await browser.get(url)

	await page.wait_for(selector=".srb-MarketSelectionButton-selected")
	btns = await page.query_selector_all(".srb-MarketSelectionButton")
	for btnIdx in range(0, len(btns)):
		btn = btns[btnIdx]
		await page.wait_for(selector=".srb-MarketSelectionButton-selected")
		if btnIdx != 0:
			await btn.scroll_into_view()
			await btn.mouse_click()
		await page.wait_for(selector=".srb-MarketSelectionButton-selected")
		btns = await page.query_selector_all(".srb-MarketSelectionButton")
		prop = await page.query_selector(".srb-MarketSelectionButton-selected")
		prop = prop.text.lower()
		
		if prop in props:
			continue
		props[prop] = True

		alt = False
		if "sack" in prop:
			continue
		if "touchdown scorers" in prop:
			if "multi" in prop:
				prop = "2+td"
			else:
				prop = "attd"
		else:
			if "milestones" in prop:
				alt = True
			prop = prop.replace("player ", "").replace(" and ", "+").replace(" milestones", "").replace("passing", "pass").replace("rushing", "rush").replace("receiving", "rec").replace("receptions", "rec").replace("reception", "rec").replace("points", "pts").replace("assists", "ast").replace("interceptions", "int").replace("completions", "cmp").replace("attempts", "att").replace("yards", "yd").replace("touchdowns", "td").replace(" + ", "+").replace(" ", "_")
			if prop == "longest_pass_completion":
				prop = "longest_pass"
			elif prop == "longest_rush_attempt":
				prop = "longest_rush"
			elif prop == "rush+rec_yd":
				prop = "rush+rec"

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
			away = convertTeam(away)
			home = convertTeam(home)

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
				o1 = await odds1[idx].query_selector_all("span")
				o1 = o1[-1].text
				o2 = ""
				if odds2:
					o2 = await odds2[idx].query_selector_all("span")
					o2 = o2[-1].text
				o3 = await odds3[idx].query_selector_all("span")
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

				if prop == "2+td":
					data[game][prop][p] = o1
					if o3:
						data[game]["3+td"][p] = o3
				elif prop == "attd":
					if o3:
						data[game][prop][p] = o3
					data[game]["ftd"][p] = o2
					data[game]["ltd"][p] = o1
				else:
					if p not in data[game][prop]:
						data[game][prop][p] = {}
					line = await odds1[idx].query_selector_all("span")
					line = line[-2].text
					data[game][prop][p][line] = f"{o1}/{o2}"

	with open("static/nfl/bet365.json", "w") as fh:
		json.dump(data, fh, indent=4)

	#time.sleep(50)
	browser.quit()

if __name__ == '__main__':
	uc.loop().run_until_complete(write365())
