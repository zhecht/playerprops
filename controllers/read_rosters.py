import argparse
import datetime
import glob
import json
import os
import operator
import time

from bs4 import BeautifulSoup as BS
from sys import platform
from lxml import etree

try:
	from controllers.functions import *
except:
	from functions import *

try:
  import urllib2 as urllib
except:
  import urllib.request as urllib

prefix = ""
if os.path.exists("/home/zhecht/fantasy"):
  prefix = "/home/zhecht/fantasy/"
elif os.path.exists("/home/playerprops/fantasy"):
	# if on linux aka prod
	prefix = "/home/playerprops/fantasy/"
elif os.path.exists("/mnt/c/Users/Zack/Documents/fantasy"):
  prefix = "/mnt/c/Users/Zack/Documents/fantasy/"

players_prefix = "players"
is_merrick = False

ns = {
	'base': "http://fantasysports.yahooapis.com/fantasy/v2/base.rng"
}

position_priority = {
	"QB": 0,
	"RB": 1,
	"WR": 2,
	"TE": 3,
	"W/R/T": 4,
	"K": 5,
	"DEF": 6,
	"BN": 7,
	"IR": 8
}

def merge_two_dicts(x, y):
	z = x.copy()
	z.update(y)
	return z

def write_cron_FA():
	#4murcjs
	import oauth
	oauth = oauth.MyOAuth(is_merrick)

	if not os.path.exists(f"{prefix}static/{players_prefix}/FA"):
		os.mkdir(f"{prefix}static/{players_prefix}/FA")

	for status in ["W", "FA"]:
		for i in range(0,1000,25):
			html = oauth.getData(f"https://fantasysports.yahooapis.com/fantasy/v2/league/{oauth.league_key}/players;start={i};status={status}").text
			with open(f"{prefix}static/{players_prefix}/FA/{status}_{i}_{i+25}.xml", "w") as fh:
				fh.write(html)
			time.sleep(2)

def write_cron_FA_json():	
	for i in range(0,1000,25):
		j = {}
		for status in ["FA", "W"]:
			tree = etree.parse(f"{prefix}static/{players_prefix}/FA/{status}_{i}_{i+25}.xml")
			players_xpath = tree.xpath('.//base:player', namespaces=ns)
			for player in players_xpath:
				
				pid = player.find('.//base:player_id', namespaces=ns).text
				first = player.find('.//base:first', namespaces=ns).text
				last = player.find('.//base:last', namespaces=ns).text
				full = player.find('.//base:full', namespaces=ns).text
				pos = player.find('.//base:display_position', namespaces=ns).text
				selected_pos = player.findall('.//base:position', namespaces=ns)[-1].text
				nfl_team = player.find('.//base:editorial_team_abbr', namespaces=ns).text

				if pos == "WR,RB":
					pos = "WR"

				j[full.lower().replace(".", "").replace("'", "")] = [nfl_team, pos, pid]
			with open(f"{prefix}static/{players_prefix}/FA/{status}_{i}_{i+25}.json", "w") as fh:
				json.dump(j, fh, indent=4)

		os.remove(f"{prefix}static/{players_prefix}/FA/{status}_{i}_{i+25}.xml")

def write_cron_rosters():
	import oauth
	oauth = oauth.MyOAuth(is_merrick)

	if not os.path.exists(f"{prefix}static/{players_prefix}"):
		os.mkdir(f"{prefix}static/{players_prefix}")

	for i in range(1,13):
		html = oauth.getData(f"https://fantasysports.yahooapis.com/fantasy/v2/team/{oauth.league_key}.t.{i}/roster").text
		if not os.path.exists(f"{prefix}static/{players_prefix}/{i}"):
			os.mkdir(f"{prefix}static/{players_prefix}/{i}")
		with open(f"{prefix}static/{players_prefix}/{i}/roster.xml", "w") as fh:
			fh.write(html)

# return total amt of players at RB/WR in league settings
def get_total_at_pos(settings):
	roster_positions = settings["fantasy_content"]["league"][1]["settings"][0]["roster_positions"]
	total_at_pos = {}
	for j in roster_positions:
		pos = j["roster_position"]["position"]
		total_at_pos[pos] = j["roster_position"]["count"]
	return total_at_pos

def write_settings():
	import oauth
	oauth = oauth.MyOAuth(is_merrick)

	xml = oauth.getData("https://fantasysports.yahooapis.com/fantasy/v2/league/{}/settings?format=json".format(oauth.league_key)).text
	extra = "" if players_prefix == "players" else "_merrick"
	with open("{}static/settings{}.json".format(prefix, extra), "w") as fh:
		fh.write(xml)

def read_settings():
	j = {}
	extra = "" if players_prefix == "players" else "_merrick"
	with open("{}static/settings{}.json".format(prefix, extra)) as fh:
		j = json.loads(fh.read())
	return j

def write_cron_standings():
	import oauth
	oauth = oauth.MyOAuth(is_merrick)

	xml = oauth.getData("https://fantasysports.yahooapis.com/fantasy/v2/league/{}/standings".format(oauth.league_key)).text
	with open("{}static/standings.xml".format(prefix), "w") as fh:
		fh.write(xml)

def write_scoreboard():
	import oauth
	oauth = oauth.MyOAuth(is_merrick)

	xml = oauth.getData("https://fantasysports.yahooapis.com/fantasy/v2/league/{}/scoreboard?format=json".format(oauth.league_key)).text
	extra = "" if players_prefix == "players" else "_merrick"
	with open("{}static/scoreboard{}.json".format(prefix, extra), "w") as fh:
		fh.write(xml)

def read_scoreboard(merrick):
	j = {}
	with open("{}static/scoreboard{}.json".format(prefix, extra)) as fh:
		j = json.loads(fh.read())
	scoreboard = j["fantasy_content"]["league"][1]["scoreboard"]

def read_FA():
	files = glob.glob("{}static/{}/FA/*.json".format(prefix, players_prefix))
	players_on_FA = {}

	for fn in files:
		fa_json = {}
		with open(fn) as fh:
			fa_json = json.loads(fh.read())
		for player in fa_json:
			
			team, position, pid = fa_json[player]
			if position == "WR,RB":
				position = "WR"
			if player in players_on_FA:
				continue

			players_on_FA[fixName(player)] = {"team_id": 0, "position": position, "pid": 0, "nfl_team": team}

	return players_on_FA

def read_FA_translations():
	files = glob.glob("{}static/{}/FA/*".format(prefix, players_prefix))
	players_on_FA = {}
	translations = {}

	for fn in files:
		fa_json = {}
		if fn.endswith("xml"):
			continue
		with open(fn) as fh:
			fa_json = json.loads(fh.read())
		for player in fa_json:
			
			team, position, pid = fa_json[player]
			if position == "WR,RB":
				position = "WR"
			players_on_FA[player] = {"team_id": 0, "position": position, "pid": 0, "nfl_team": team}
			if position == "DEF":
				translations[player] = player
			else:
				player = player.title()
				first = player.split(" ")[0][0]
				last = " ".join(player.split(" ")[1:])
				translations[f"{first}. {last} {team.upper()}"] = player.lower().replace("'", "")
	return players_on_FA, translations

def update_players_on_teams(players_on_teams):
	if "cordarrelle patterson" in players_on_teams:
		players_on_teams["cordarrelle patterson"]["position"] = "RB"
	return

def read_rosters(skip_remove_puncuation=False, players_prefix=players_prefix):
	players_on_teams = {}
	name_translations = {}
	for i in range(1,13):
		tree = etree.parse("{}static/{}/{}/roster.xml".format(prefix, players_prefix, i))
		players_xpath = tree.xpath('.//base:player', namespaces=ns)

		for player in players_xpath:
			
			pid = player.find('.//base:player_id', namespaces=ns).text
			first = player.find('.//base:first', namespaces=ns).text
			last = player.find('.//base:last', namespaces=ns).text
			full = player.find('.//base:full', namespaces=ns).text
			pos = player.find('.//base:display_position', namespaces=ns).text
			selected_pos = player.findall('.//base:position', namespaces=ns)[-1].text
			nfl_team = player.find('.//base:editorial_team_abbr', namespaces=ns).text

			if pos == "WR,RB":
				pos = "WR"

			players_on_teams[fixName(full)] = {"team_id": i, "position": pos, "pid": pid, "nfl_team": nfl_team, "fantasy_position": position_priority[selected_pos]}
			if pos == "DEF":
				name_translations[full] = fixName(full)
			else:
				name_translations["{}. {} {}".format(first[0], last, nfl_team)] = fixName(full)
				name_translations["{}. {} {}".format(first[0], last, nfl_team.upper())] = fixName(full)

	fixTranslations(name_translations)
	if skip_remove_puncuation:
		return players_on_teams, name_translations

	update_players_on_teams(players_on_teams)
	return players_on_teams, name_translations

def fixTranslations(name_translations):
	name_translations["I. Smith Jr. MIN"] = "irv smith jr"

def read_standings():
	
	tree = etree.parse("{}static/standings.xml".format(prefix))
	teams_xpath = tree.xpath('.//base:team', namespaces=ns)

	all_teams = []
	for team in teams_xpath:
		team_id = int(team.find('.//base:team_id', namespaces=ns).text)
		name = team.find('.//base:name', namespaces=ns).text
		all_teams.append({'id': team_id, 'name': name})

	all_teams = sorted(all_teams,key=operator.itemgetter('id'))
	return all_teams

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-c", "--cron", action="store_true", help="Start Cron Job")
	parser.add_argument("-merrick", "--merrick", action="store_true")

	args = parser.parse_args()

	if args.merrick:
		players_prefix = "merrick_players"
		is_merrick = True

	if args.cron:
		print("WRITING ROSTERS")
		write_settings()
		write_scoreboard()
		write_cron_standings()
		write_cron_rosters()
		write_cron_FA()
		write_cron_FA_json()
	else:
		#write_scoreboard()
		write_cron_rosters()
		write_cron_FA()
		write_cron_FA_json()
		#write_settings()
		pass