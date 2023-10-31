import argparse
import glob
import json
import math
import os
import operator
import re
import time

from bs4 import BeautifulSoup as BS
from bs4 import Comment
from sys import platform
from subprocess import call
from glob import glob

try:
	from controllers.functions import *
except:
	from functions import *

try:
  import urllib2 as urllib
except:
  import urllib.request as urllib

from datetime import datetime

prefix = ""
if os.path.exists("/home/zhecht/playerprops"):
	prefix = "/home/zhecht/playerprops/"
elif os.path.exists("/home/playerprops/playerprops"):
	# if on linux aka prod
	prefix = "/home/playerprops/playerprops/"

def merge_two_dicts(x, y):
	z = x.copy()
	z.update(y)
	return z

def get_abbr(team):
	if team == "ari":
		return "crd"
	elif team == "bal":
		return "rav"
	elif team == "hou":
		return "htx"
	elif team == "ind":
		return "clt"
	elif team == "lac":
		return "sdg"
	elif team == "lar":
		return "ram"
	elif team == "lvr":
		return "rai"
	elif team == "ten":
		return "oti"
	elif team == "tb":
		return "tam"
	elif team == "no":
		return "nor"
	elif team == "gb":
		return "gnb"
	elif team == "sf":
		return "sfo"
	elif team == "ne":
		return "nwe"
	return team

def get_default(key):
	# return default
	if key in ["rush_yds", "rec_yds"]:
		return 0.1
	elif key in ["pass_yds"]:
		return 0.04
	elif key == "ppr":
		return 0.5
	elif key in ["rush_td", "rec_td"]:
		return 6
	elif key in ["pass_td"]:
		return 4
	elif key in ["fumbles_lost", "pass_int"]:
		return -2
	elif key in ["xpm"]:
		return 1
	return 0

def get_points(key, val, settings):
	if key == "rec":
		key = "ppr"
	multiply = settings[key] if key in settings else get_default(key)
	if key in settings and key in ["rush_yds", "rec_yds", "pass_yds"]:
		multiply = 1.0 / multiply

	if key == "fg_made":
		pts = 0
		for fg in val:
			if int(fg) >= 50:
				pts += settings["field_goal_50+"] if "field_goal_50+" in settings else 5
			elif int(fg) >= 40:
				pts += settings["field_goal_40-49"] if "field_goal_40-49" in settings else 4
			elif int(fg) >= 30:
				pts += settings["field_goal_30-39"] if "field_goal_30-39" in settings else 3
			elif int(fg) >= 20:
				pts += settings["field_goal_20-29"] if "field_goal_20-29" in settings else 3
			else:
				pts += settings["field_goal_0-19"] if "field_goal_0-19" in settings else 3
		return pts
	return val * multiply
	return 0

def get_points_from_PA(pts_allowed, settings):
	points = settings.get("0_points_allowed", 10)
	if pts_allowed >= 1 and pts_allowed <= 6:
		points = settings.get("1-6_points_allowed", 7)
	elif pts_allowed >= 7 and pts_allowed <= 13:
		points = settings.get("7-13_points_allowed", 4)
	elif pts_allowed >= 14 and pts_allowed <= 20:
		points = settings.get("14-20_points_allowed", 1)
	elif pts_allowed >= 21 and pts_allowed <= 27:
		points = settings.get("21-27_points_allowed", 0)
	elif pts_allowed >= 28 and pts_allowed <= 34:
		points = settings.get("28-34_points_allowed", -1)
	elif pts_allowed >= 35:
		points = settings.get("35+_points_allowed", -4)
	return points

def calculate_defense_points(stats, settings):
	pts_allowed = stats.get("rush_td", 0)*6 + stats.get("pass_td", 0)*6 + stats.get("xpm", 0) + stats.get("fgm", 0)*3 + stats.get("2pt_conversions", 0)*2
	points = get_points_from_PA(pts_allowed, settings)
	points += (stats.get("kick_ret_td",0) * 6)
	points += (stats.get("punt_ret_td",0) * 6)
	
	multiply = settings.get("interception", 2)
	points += (stats.get("pass_int",0) * multiply)
	
	multiply = settings.get("fumble_recovery",2)
	points += (stats.get("fumbles_lost",0) * multiply)

	multiply = settings.get("safety",2)
	points += (stats.get("safety",0) * multiply)

	multiply = settings.get("touchdown",6)
	points += (stats.get("def_tds",0) * multiply)

	multiply = settings.get("sack", 1)
	points += (stats.get("pass_sacked",0) * multiply)
	return points

def calculate_aggregate_stats(settings=None):
	if not settings:
		settings = {"ppr": 0.5}
	test_settings = settings.copy()
	teamlinks = {}
	with open("{}static/profootballreference/teams.json".format(prefix)) as fh:
		teamlinks = json.loads(fh.read())

	totPlays = {}
	for team in teamlinks:
		team = team.split("/")[-2]

		if team not in totPlays:
			totPlays[team] = [0]*CURR_WEEK
		with open(f"{prefix}static/profootballreference/{team}/roster.json") as fh:
			roster = json.load(fh)

		stats = {}
		path = f"{prefix}static/profootballreference/{team}"
		files = glob(f"{path}/wk*.json")
		for f in files:
			m = re.search(r'wk(\d+).json', f)
			week = m.group(1)
			team_stats = {}
			with open(f) as fh:
				team_stats = json.loads(fh.read())

			for player in team_stats:
				player = fixName(player)
				if player not in stats:
					stats[player] = {"tot": {"standard_points": 0, "half_points": 0, "full_points": 0}}
				if f"wk{week}" not in stats[player]:
					stats[player][f"wk{week}"] = {}

				isOffense = roster.get(player, "") in ["QB", "RB", "WR", "WR/RB", "TE"]
				if isOffense and int(week) <= CURR_WEEK and not totPlays[team][int(week)-1] and "snap_perc" in team_stats[player] and team_stats[player]["snap_perc"]:
					plays = int(math.ceil(team_stats[player]["snap_counts"] / (team_stats[player]["snap_perc"] / 100)))
					totPlays[team][int(week)-1] = plays

				points = 0
				points_arr = {"standard": 0, "half": 0, "full": 0}
				for player_stats_str in team_stats[player]:
					if player_stats_str not in stats[player]["tot"]:
						if player_stats_str == "fg_made":
							stats[player]["tot"][player_stats_str] = []
						else:
							stats[player]["tot"][player_stats_str] = 0
					stats[player]["wk{}".format(week)][player_stats_str] = team_stats[player][player_stats_str]
					if player_stats_str == "fg_made":
						stats[player]["tot"][player_stats_str].extend(team_stats[player][player_stats_str])
					else:
						stats[player]["tot"][player_stats_str] += team_stats[player][player_stats_str]

					if player_stats_str == "rec":
						test_settings["ppr"] = 0
						points_arr["standard"] += get_points(player_stats_str, team_stats[player][player_stats_str], test_settings)
						test_settings["ppr"] = 0.5
						points_arr["half"] += get_points(player_stats_str, team_stats[player][player_stats_str], test_settings)
						test_settings["ppr"] = 1
						points_arr["full"] += get_points(player_stats_str, team_stats[player][player_stats_str], test_settings)
					else:
						points += get_points(player_stats_str, team_stats[player][player_stats_str], settings)
				# calculate def points
				for s in ["standard", "half", "full"]:
					pts = round(points + points_arr[s], 2)
					if player == "OFF":
						pts = calculate_defense_points(team_stats[player], settings)
					stats[player]["wk{}".format(week)]["{}_points".format(s)] = pts
					stats[player]["tot"]["{}_points".format(s)] += pts
			
		fixStats(team, stats)
		with open(f"{path}/stats.json", "w") as fh:
			json.dump(stats, fh, indent=4)

	for team in totPlays:
		totPlays[team] = ",".join(str(x) for x in totPlays[team])
	with open(f"{prefix}static/tot_plays.json", "w") as fh:
		json.dump(totPlays, fh, indent=4)

	writeRunPassTotals()

def writeRunPassTotals():
	with open(f"{prefix}static/profootballreference/teams.json") as fh:
		teamlinks = json.load(fh)

	runPassTotals = {}
	for team in teamlinks:
		team = team.split("/")[-2]
		runPassTotals[team] = {}
		path = f"{prefix}static/profootballreference/{team}"
		with open(f"{path}/stats.json") as fh:
			stats = json.load(fh)

		for name in stats:
			for wk in stats[name]:
				if wk == "tot":
					continue
				week = int(wk[2:])
				if wk not in runPassTotals[team]:
					runPassTotals[team][wk] = {"pass": 0, "run": 0}
				passAtt = stats[name][wk].get("pass_att", 0)
				runAtt = stats[name][wk].get("rush_att", 0)
				if passAtt:
					runPassTotals[team][wk]["pass"] += passAtt
				if runAtt:
					runPassTotals[team][wk]["run"] += runAtt

	res = {}
	for team in runPassTotals:
		res[team] = {"run": "", "pass": ""}
		runs = []
		passes = []
		for wk in sorted(runPassTotals[team].keys()):
			runs.append(runPassTotals[team][wk]["run"])
			passes.append(runPassTotals[team][wk]["pass"])

		res[team]["passPerc"] = round(sum(passes) / (sum(passes) + sum(runs))*100, 1)
		res[team]["run"] = ",".join([str(x) for x in runs])
		res[team]["pass"] = ",".join([str(x) for x in passes])


	with open(f"{prefix}static/runPassTotals.json", "w") as fh:
		json.dump(res, fh, indent=4)

def fixStats(team, stats):
	pass

# return (in order) list of opponents
def get_opponents(team):
	schedule = {}
	with open("{}static/profootballreference/schedule.json".format(prefix)) as fh:
		schedule = json.loads(fh.read())
	opps = []
	for i in range(1, 20):
		opp_team = "BYE"
		if f"wk{i}" not in schedule:
			continue
		for games in schedule[f"wk{i}"]:
			away, home = games.split(" @ ")
			if away == team or TEAM_TRANS.get(away, away) == TEAM_TRANS.get(team, team):
				opp_team = home
			elif home == team or TEAM_TRANS.get(home, home) == TEAM_TRANS.get(team, team):
				opp_team = away
		opps.append(opp_team)
	return opps


# read rosters and return ARRAY of players on team playing POS 
def get_players_by_pos_team(team, pos):
	nfl_trades = read_nfl_trades()
	roster = {}
	if team == "BYE":
		return []
	with open("{}static/profootballreference/{}/roster.json".format(prefix, team)) as fh:
		roster = json.loads(fh.read())
	arr = []
	for player in roster:
		if roster[player].lower() == pos.lower():
			arr.append(player)
	for player in nfl_trades:
		if nfl_trades[player]["from"] == team:
			opp_roster = {}
			with open("{}static/profootballreference/{}/roster.json".format(prefix, nfl_trades[player]["team"])) as fh:
				opp_roster = json.loads(fh.read())
			if player in opp_roster and opp_roster[player].lower() == pos.lower():
				arr.append(player)
	# IR is not listed on roster
	ir_data = [
		#("cle", "QB", "baker mayfield"),
	]
	for data in ir_data:
		if team == data[0] and pos == data[1] and data[2] not in arr:
			arr.append(data[2])
	return arr

def get_tot_team_games(curr_week, schedule):
	j = {}
	for i in range(1, curr_week + 1):
		games = schedule[str(i)]
		for game in games:
			t1,t2 = game.split(" @ ")
			if t1 not in j:
				j[t1] = 0
			if t2 not in j:
				j[t2] = 0
			j[t1] += 1
			j[t2] += 1
	return j

def get_point_totals(curr_week, settings, over_expected):
	teams = os.listdir("{}static/profootballreference".format(prefix))
	scoring_key = "half"
	all_team_stats = {}
	projections = {}
	with open(f"{prefix}static/projections/projections.json") as fh:
		projections = json.load(fh).copy()
	# read all team stats into { team -> player -> [tot, wk1, wk2]}
	for team in teams:
		if team.find("json") >= 0:
			continue
		stats = {}
		with open(f"{prefix}static/profootballreference/{team}/stats.json") as fh:
			all_team_stats[team] = json.load(fh).copy()
		#if over_expected:
			#with open(f"{prefix}static/projections/projections.json") as fh:
			#	projections[team] = json.load(fh).copy()
	ranks = []
	for team in all_team_stats:
		pos_tot = {}
		for pos in ["QB", "RB", "WR", "TE", "K", "DEF"]:
			pos_tot[pos] = {}
			players = get_players_by_pos_team(team, pos)
			
			if pos == "DEF":
				players = ["OFF"]
			for player in players:
				if pos != "DEF" and player not in all_team_stats[team]:
					continue
				for wk in all_team_stats[team][player]: # tot, wk1, wk2
					try:
						if int(wk.replace("wk","")) > curr_week:
							continue
					except:
						pass

					if wk not in pos_tot[pos]:
						pos_tot[pos][wk] = 0
						pos_tot[pos][wk+"_proj"] = 0
						pos_tot[pos][wk+"_act"] = 0

					# don't add if this player had 0 snaps
					if pos not in ["K", "DEF"] and ("snap_counts" not in all_team_stats[team][player][wk] or not all_team_stats[team][player][wk]["snap_counts"]):
						continue

					real_pts = 0
					if player == "OFF":
						real_pts = calculate_defense_points(all_team_stats[team][player][wk], settings)
						if over_expected:
							if wk == "tot":
								pass
							elif projections[team][wk]:
								real_pts = (real_pts / projections[team][wk]) - 1
								real_pts *= 100
								pos_tot[pos][wk+"_proj"] += projections[team][wk]
								pos_tot[pos][wk+"_act"] += all_team_stats[team][player][wk]["half_points"]
					elif over_expected:
						if wk == "tot" or player not in projections or wk not in projections[player] or not projections[player][wk]:
							pass
							#real_pts = all_team_stats[team][player][wk]
						else:
							real_pts = (all_team_stats[team][player][wk]["half_points"] / projections[player][wk]) - 1
							real_pts *= 100
							pos_tot[pos][wk+"_proj"] += projections[player][wk]
							pos_tot[pos][wk+"_act"] += all_team_stats[team][player][wk]["half_points"]
					else:
						real_pts = get_points_from_settings(all_team_stats[team][player][wk], settings)
					pos_tot[pos][wk] += real_pts
					#pos_tot[pos][wk] += all_team_stats[team][player][wk]["half_points"]
		j = { "team": team }
		for pos in pos_tot:
			for wk in range(1, curr_week + 1):
				if "wk{}".format(wk) not in pos_tot[pos]: # game hasn't played
					j["{}_wk{}".format(pos, wk)] = 0
				elif f"wk{wk}_proj" in pos_tot[pos] and pos_tot[pos][f"wk{wk}_proj"]:
					j[f"{pos}_wk{wk}_proj"] = pos_tot[pos][f"wk{wk}_proj"]
					j[f"{pos}_wk{wk}_act"] = pos_tot[pos][f"wk{wk}_act"]
					j[f"{pos}_wk{wk}"] = round(((pos_tot[pos][f"wk{wk}_act"] / pos_tot[pos][f"wk{wk}_proj"]) - 1) * 100, 2)
				else:
					j["{}_wk{}".format(pos, wk)] = round(pos_tot[pos]["wk{}".format(wk)], 2)
					#j["{}_tot".format(pos)] += pos_tot[pos]["wk{}".format(wk)]
			#j["{}_tot".format(pos)] = round(j["{}_tot".format(pos)], 2)
		ranks.append(j)
	return ranks


def read_schedule():
	with open("{}static/profootballreference/schedule.json".format(prefix)) as fh:
		j = json.loads(fh.read())
	return j

def read_nfl_trades():
	with open("{}static/nfl_trades.json".format(prefix)) as fh:
		returned_json = json.loads(fh.read())
	return returned_json

def get_defense_tot(curr_week, point_totals_dict, over_expected):
	defense_tot = []
	schedule = read_schedule()
	tot_team_games = get_tot_team_games(curr_week, schedule)
	teams = os.listdir("{}static/profootballreference".format(prefix))
	for team in teams:
		if team.find("json") >= 0:
			continue
		# get opp schedule
		j = {"team": team}
		opponents = get_opponents(team)[:curr_week]
		for week, opp_team in enumerate(opponents):
			for pos in ["QB", "RB", "WR", "TE", "K", "DEF"]:
				key = f"{pos}_wk{week+1}"
				tot_key = f"{pos}_tot"
				act_key = f"{pos}_act"
				proj_key = f"{pos}_proj"
				for k in [key, tot_key, act_key, proj_key]:
					if k not in j:
						j[k] = 0
				if opp_team != "BYE":
					which_team = opp_team
					if pos == "DEF":
						which_team = team
					if over_expected:
						#print(which_team, point_totals_dict[which_team])
						if pos == "K" and f"{pos}_wk{week+1}_act" not in point_totals_dict[which_team]:
							continue
							
						j[act_key] += point_totals_dict[which_team][f"{pos}_wk{week+1}_act"]
						j[proj_key] += point_totals_dict[opp_team][f"{pos}_wk{week+1}_proj"]
						j[key] += point_totals_dict[which_team][key]
						j[tot_key] += point_totals_dict[which_team][key]
					else:
						j[key] += point_totals_dict[which_team][key]
						j[tot_key] += point_totals_dict[which_team][key]
						
		for pos in ["QB", "RB", "WR", "TE", "K", "DEF"]:
			games = tot_team_games[team]
			if over_expected and j[f"{pos}_proj"]:
				j[f"{pos}_ppg"] = round(((j[f"{pos}_act"] / j[f"{pos}_proj"]) - 1) * 100, 2)
			else:
				j[f"{pos}_ppg"] = round(j[f"{pos}_tot"] / games, 2)
		defense_tot.append(j)
	return defense_tot

# get rankns of teeams sorted by highest fantasy points scored
def get_ranks(curr_week, settings, over_expected):
	ranks = {}
	point_totals = get_point_totals(curr_week, settings, over_expected)
	for pos in ["QB", "RB", "WR", "TE", "K", "DEF"]:
		for week in range(1, curr_week + 1):
			key = "{}_wk{}".format(pos, week)
			# storred like RB_wk3, etc
			sorted_ranks = sorted(point_totals, key=operator.itemgetter(key), reverse=True)
			for idx, arr in enumerate(sorted_ranks):
				if arr["team"] not in ranks:
					ranks[arr["team"]] = {"RB": {}, "WR": {}, "TE": {}, "QB": {}, "K": {}, "DEF": {}}
				ranks[arr["team"]][pos]["wk{}".format(week)] = idx + 1

	# total opponent's numbers for DEFENSE outlooks
	point_totals_dict = {}
	for arr in point_totals:
		point_totals_dict[arr["team"]] = arr.copy()
	defense_tot = get_defense_tot(curr_week, point_totals_dict, over_expected)

	for pos in ["QB", "RB", "WR", "TE", "K", "DEF"]:
		sorted_ranks = sorted(defense_tot, key=operator.itemgetter("{}_tot".format(pos)), reverse=True)
		for idx, arr in enumerate(sorted_ranks):
			ranks[arr["team"]][pos]["tot"] = idx + 1

	return ranks, defense_tot


def get_pretty_stats(stats, pos, settings):
	#s = "{} PTS - {}".format(stats["points"], player.title())
	s = ""
	if not stats:
		return s
	pos = pos.upper()
	if pos != "K" and "snap_counts" in stats and not stats["snap_counts"]:
		s += "-"
	elif pos == "QB":
		s = "-"
		if "pass_att" in stats:
			s = "{}/{} {} Pass Yds".format(stats["pass_cmp"], stats["pass_att"], stats["pass_yds"])
			if stats["pass_td"]:
				s += ", {} Pass TD".format(stats["pass_td"])
			if stats["pass_int"]:
				s += ", {} Int".format(stats["pass_int"])
	elif pos in ["WR", "TE"]:
		if "targets" in stats and stats["targets"]:
			s = "{}/{} {} Rec Yds".format(stats["rec"], stats["targets"], stats["rec_yds"])
			if stats["rec_td"]:
				s += " {} Rec TD".format(stats["rec_td"])
		else:
			s = "0 Targets"
	elif pos == "K":
		if "xpm" in stats and "fgm" in stats:
			if "fg_made" not in stats:
				s = "{} XP / {} FG made".format(stats["xpm"], stats["fgm"])
			elif "xpm" in stats:
				s = "{} XP / {} FG made {}".format(stats["xpm"], stats["fgm"], stats["fg_made"])
	elif pos == "DEF":
		pts_allowed = stats["rush_td"]*6 + stats["pass_td"]*6 + stats["xpm"] + stats["fgm"]*3 + stats["2pt_conversions"]*2
		s += "{} pts allowed".format(pts_allowed)
		if stats["pass_int"]:
			s += " / {} Int".format(stats["pass_int"])
		if stats["pass_sacked"]:
			plural = "s" if stats["pass_sacked"] > 1 else ""
			s += " / {} Sack{}".format(stats["pass_sacked"], plural)
		if stats["fumbles_lost"]:
			plural = "s" if stats["fumbles_lost"] > 1 else ""
			s += " / {} Fumble{}".format(stats["fumbles_lost"], plural)
		if stats["safety"]:
			s += " / {} Safety".format(stats["safety"])
		if stats["def_tds"]:
			s += " / {} Def TDs".format(stats["def_tds"])
	else: # RB
		s = "0 Rush Yds"
		if "rush_yds" in stats and "rec_yds" in stats:
			s = "{} Rush Yds".format(stats["rush_yds"])
			if stats["rush_td"]:
				s += ", {} Rush TD".format(stats["rush_td"])
			if stats["rec"]:
				s += ", {} Rec, {} Rec Yds".format(stats["rec"], stats["rec_yds"])
			if stats["rec_td"]:
				s += ", {} Rec TD".format(stats["rec_td"])
	return s

def get_suffix(num):
	if num >= 11 and num <= 13:
		return "th"
	elif num % 10 == 1:
		return "st"
	elif num % 10 == 2:
		return "nd"
	elif num % 10 == 3:
		return "rd"
	return "th"

def get_points_from_settings(stats, settings):
	points = 0
	for s in stats:
		if s.find("points") >= 0:
			continue
		points += get_points(s, stats[s], settings)
	return points

# Given a team, show stats from other players at the same pos 
def position_vs_opponent_stats(team, pos, ranks, settings=None):

	opp_stats = []
	tot_stats = {"points": 0, "stats": {}, "title": f"TOTAL vs. {pos.upper()}"}
	team = get_abbr(team)
	team_schedule = get_opponents(team)
	scoring_key = "half"
	if settings:
		if settings["ppr"] == 0:
			scoring_key = "standard"
		elif settings["ppr"] == 1:
			scoring_key = "full"
	for idx, opp_team in enumerate(team_schedule):        
		week = idx + 1
		if opp_team == "BYE":
			opp_stats.append({"week": week, "players": "", "team": team})
			continue
		if pos == "DEF":
			path = "{}static/profootballreference/{}".format(prefix, team)
		else:
			path = "{}static/profootballreference/{}".format(prefix, opp_team)
		team_stats = {}
		with open("{}/stats.json".format(path)) as fh:
			team_stats = json.loads(fh.read())

		if pos == "DEF":
			players_arr = ["OFF"]
		else:
			players_arr = get_players_by_pos_team(opp_team, pos)
		display_team = TEAM_TRANS[team] if team in TEAM_TRANS else team
		display_opp_team = TEAM_TRANS[opp_team] if opp_team in TEAM_TRANS else opp_team
		
		j = {
			"title": "<i style='text-decoration:underline;'>{} vs. {} {}</i>".format(
				display_team.upper(),
				display_opp_team.upper(),
				pos.upper()
			),
			"week": week,
			"opp": display_opp_team.upper(),
			"text": "",
			"rank": "",
			"points": 0.0,
			"players": "",
			"stats": None
		}
		total_stats = {}
		player_txt = []
		for player in players_arr:
			if player not in team_stats or "wk{}".format(week) not in team_stats[player]:
				continue
			elif pos not in ["K", "DEF"] and ("snap_counts" not in team_stats[player]["wk{}".format(week)] or not team_stats[player]["wk{}".format(week)]["snap_counts"]):
				# don't add if player got 0 snaps / messes up percs
				continue

			week_stats = team_stats[player]["wk{}".format(week)]
			
			for s in week_stats:
				#print(player, s, week)
				if s not in total_stats:
					total_stats[s] = [] if s == "fg_made" else 0

				if s == "fg_made":
					total_stats[s].extend(week_stats[s])
				else:
					total_stats[s] += week_stats[s]
			if player == "OFF":
				real_pts = calculate_defense_points(week_stats, settings)
			else:
				real_pts = get_points_from_settings(week_stats, settings)
			player_txt.append("wk{} {}: {} {} pts ({})".format(idx, opp_team, player, real_pts, get_pretty_stats(week_stats, pos, settings)))
			if "points" not in total_stats:
				total_stats["points"] = 0
			total_stats["points"] += real_pts
		try:
			j["team"] = team
			j["opp_team"] = opp_team
			j["stats"] = total_stats 
			j["text"] = get_pretty_stats(total_stats, pos, settings)
			if player == "OFF":
				real_pts = calculate_defense_points(total_stats, settings)
			else:
				real_pts = get_points_from_settings(total_stats, settings)
			j["points"] = round(real_pts, 2)
			j["players"] = player_txt

			# TOT
			tot_stats["points"] += j["points"]
			for key in total_stats:
				if key not in tot_stats["stats"]:
					tot_stats["stats"][key] = 0
				tot_stats["stats"][key] += total_stats[key]
		except:
			pass

		opp_stats.append(j)
	tot_stats["text"] = get_pretty_stats(tot_stats["stats"], pos, settings)
	tot_stats["rank"] = "{} points allowed <span>{}{} highest</span>".format(
		round(tot_stats["points"], 2),
		0,0)
	#   ranks[opp_team][pos.upper()]["tot"],
	#   get_suffix(ranks[opp_team][pos.upper()]["tot"])
	#)
	return opp_stats, tot_stats

def get_total_ranks(curr_week, settings):
	ranks, defense_tot = get_ranks(curr_week, settings)

	print("RANK|QB|RB|WR|TE|K|DEF")
	print(":--|:--|:--|:--|:--|:--|:--")
	for idx in range(1, 33):
		s = "**{}**".format(idx)
		for pos in ["QB", "RB", "WR", "TE", "K", "DEF"]:
			sorted_ranks = sorted(defense_tot, key=operator.itemgetter("{}_ppg".format(pos)), reverse=True)
			display_team = sorted_ranks[idx - 1]["team"]
			if display_team in TEAM_TRANS:
				display_team = TEAM_TRANS[display_team]
			tot = round(sorted_ranks[idx - 1]["{}_tot".format(pos)], 2)
			s += "|{} {}".format(display_team, sorted_ranks[idx - 1]["{}_ppg".format(pos)])
		print(s)

def write_team_links():
	url = "https://www.pro-football-reference.com/teams/"
	soup = BS(urllib.urlopen(url).read(), "lxml")
	time.sleep(2)
	rows = soup.find("table", id="teams_active").find_all("tr")[2:]
	j = {}
	for tr in rows:
		try:
			link = tr.find("th").find("a").get("href")
			j[link] = 1
		except:
			pass
	with open("{}static/profootballreference/teams.json".format(prefix), "w") as fh:
		json.dump(j, fh, indent=4)

def fix_roster(roster, team):
	if team == "atl":
		roster["cordarrelle patterson"] = "RB"
		roster["avery williams"] = "RB"
	elif team == "chi":
		roster["michael badgley"] = "K"
	elif team == "clt":
		roster["rodrigo blankenship"] = "K"
	elif team == "jax":
		roster["riley patterson"] = "K"
	elif team == "nor":
		roster["taysom hill"] = "TE"
	elif team == "kan":
		roster["matt ammendola"] = "K"
	return

def writeSchedule(week):
	url = f"https://www.espn.com/nfl/schedule/_/week/{week}"
	if week > 18:
		url = f"https://www.espn.com/nfl/schedule/_/week/{week-18}/year/2022/seasontype/3"
	week = f"wk{week}"
	outfile = "out"
	call(["curl", "-k", url, "-o", outfile])
	soup = BS(open(outfile, 'rb').read(), "lxml")

	with open(f"{prefix}static/profootballreference/boxscores.json") as fh:
		boxscores = json.load(fh)

	with open(f"{prefix}static/profootballreference/schedule.json") as fh:
		schedule = json.load(fh)

	with open(f"{prefix}static/profootballreference/scores.json") as fh:
		scores = json.load(fh)

	schedule[week] = []

	for table in soup.findAll("div", class_="ResponsiveTable"):
		try:
			date = table.find("div", class_="Table__Title").text.strip()
			date = str(datetime.strptime(date, "%A, %B %d, %Y"))[:10]
		except:
			continue

		if week not in boxscores:
			boxscores[week] = {}
		if week not in scores:
			scores[week] = {}
		for row in table.findAll("tr")[1:]:
			tds = row.findAll("td")
			awayTeam = tds[0].findAll("a")[-1].get("href").split("/")[-2]
			homeTeam = tds[1].findAll("a")[-1].get("href").split("/")[-2]
			score = tds[2].find("a").text.strip()
			if ", " in score:
				scoreSp = score.replace(" (2OT)", "").replace(" (OT)", "").split(", ")
				if awayTeam.upper() in scoreSp[0]:
					scores[week][awayTeam] = int(scoreSp[0].replace(awayTeam.upper()+" ", ""))
					scores[week][homeTeam] = int(scoreSp[1].replace(homeTeam.upper()+" ", ""))
				else:
					scores[week][awayTeam] = int(scoreSp[1].replace(awayTeam.upper()+" ", ""))
					scores[week][homeTeam] = int(scoreSp[0].replace(homeTeam.upper()+" ", ""))
			boxscore = tds[2].find("a").get("href")
			boxscores[week][f"{awayTeam} @ {homeTeam}"] = boxscore
			schedule[week].append(f"{awayTeam} @ {homeTeam}")

	with open(f"{prefix}static/profootballreference/boxscores.json", "w") as fh:
		json.dump(boxscores, fh, indent=4)

	with open(f"{prefix}static/profootballreference/scores.json", "w") as fh:
		json.dump(scores, fh, indent=4)

	with open(f"{prefix}static/profootballreference/schedule.json", "w") as fh:
		json.dump(schedule, fh, indent=4)


def writeRosters():
	with open(f"{prefix}static/profootballreference/playerIds.json") as fh:
		playerIds = json.load(fh)

	roster = {}
	for team in os.listdir(f"{prefix}static/profootballreference/"):
		if team.endswith(".json"):
			continue

		roster[team] = {}
		url = f"https://www.espn.com/nfl/team/roster/_/name/{team}/"
		outfile = "out"
		time.sleep(0.2)
		call(["curl", "-k", url, "-o", outfile])
		soup = BS(open(outfile, 'rb').read(), "lxml")

		for table in soup.findAll("table"):
			for row in table.findAll("tr")[1:]:
				nameLink = row.findAll("td")[1].find("a").get("href").split("/")
				fullName = nameLink[-1].replace("-", " ")
				playerId = int(nameLink[-2])
				playerIds[team][fullName] = playerId
				roster[team][fullName] = row.findAll("td")[2].text.strip()

	with open(f"{prefix}static/profootballreference/playerIds.json", "w") as fh:
		json.dump(playerIds, fh, indent=4)

	with open(f"{prefix}static/profootballreference/roster.json", "w") as fh:
		json.dump(roster, fh, indent=4)

def write_stats(week):
	with open(f"{prefix}static/profootballreference/boxscores.json") as fh:
		boxscores = json.load(fh)

	with open(f"{prefix}static/profootballreference/playerIds.json") as fh:
		playerIds = json.load(fh)

	week = f"wk{week}"
	if week not in boxscores:
		print("No games found for this week")
		exit()

	allStats = {}
	for game in boxscores[week]:
		away, home = map(str, game.split(" @ "))

		if away not in allStats:
			allStats[away] = {}
		if home not in allStats:
			allStats[home] = {}


		gameId = boxscores[week][game].split("/")[-1].split("=")[-1]
		url = f"https://site.web.api.espn.com/apis/site/v2/sports/football/nfl/summary?region=us&lang=en&contentorigin=espn&event={gameId}"
		outfile = "out"
		time.sleep(0.3)
		call(["curl", "-k", url, "-o", outfile])

		with open("out") as fh:
			data = json.load(fh)

		if "code" in data and data["code"] == 400:
			continue

		if "players" not in data["boxscore"]:
			continue
		for teamRow in data["boxscore"]["players"]:
			team = teamRow["team"]["abbreviation"].lower()
			if team not in playerIds:
				playerIds[team] = {}

			for statRow in teamRow["statistics"]:
				title = statRow["name"]
				shortHeader = ""
				if title == "receiving":
					shortHeader = "rec"
				elif title == "defensive":
					shortHeader = "def"
				elif title == "interceptions":
					shortHeader = "def_int"
				elif title in ["puntReturns", "kickReturns", "punting", "fumbles"]:
					shortHeader = title
				else:
					shortHeader = title[:4]

				headers = [h.lower() for h in statRow["labels"]]

				for playerRow in statRow["athletes"]:
					player = playerRow["athlete"]["displayName"].lower().replace("'", "").replace(".", "")
					playerId = int(playerRow["athlete"]["id"])

					playerIds[team][player] = playerId
					if player not in allStats[team]:
						allStats[team][player] = {}

					for header, stat in zip(headers, playerRow["stats"]):
						if header == "car":
							header = "rush_att"
						elif header == "rec":
							if shortHeader == "fumbles":
								header = "fumbles_recovered"
							else:
								header = "rec"
						elif header == "fum":
							header = "fumbles"
						elif header == "lost":
							header = "fumbles_lost"
						elif header == "tot":
							header = "tackles_combined"
						elif header == "solo":
							header = "tackles_solo"
						elif shortHeader == "def" and header == "td":
							header = "def_td"
						elif shortHeader == "def_int" and header == "int":
							header = "def_int"
						elif shortHeader in ["pass", "rush", "rec", "def_int", "returns"]:
							header = f"{shortHeader}_{header}"

						if header == "pass_c/att":
							made, att = map(int, stat.split("/"))
							allStats[team][player]["pass_cmp"] = made
							allStats[team][player]["pass_att"] = att
						elif header in ["xp", "fg"]:
							made, att = map(int, stat.split("/"))
							allStats[team][player][header+"m"] = made
							allStats[team][player][header+"a"] = att
						elif header == "pass_sacks":
							made, att = map(int, stat.split("-"))
							allStats[team][player]["pass_sacks"] = made
						else:
							val = stat
							try:
								val = float(val)
							except:
								val = 0.0
							allStats[team][player][header] = val

	for team in allStats:
		if not os.path.isdir(f"{prefix}static/profootballreference/{team}"):
			os.mkdir(f"{prefix}static/profootballreference/{team}")
		with open(f"{prefix}static/profootballreference/{team}/{week}.json", "w") as fh:
			json.dump(allStats[team], fh, indent=4)

	write_totals()

	with open(f"{prefix}static/profootballreference/playerIds.json", "w") as fh:
		json.dump(playerIds, fh, indent=4)

def writeQBLongest(week):
	with open(f"{prefix}static/profootballreference/roster.json") as fh:
		roster = json.load(fh)
	with open(f"{prefix}static/nfl_trades.json") as fh:
		nfl_trades = json.load(fh)

	longestRanks = {}
	for team in os.listdir(f"{prefix}static/profootballreference/"):
		if team.endswith("json"):
			continue

		longestRanks[team] = {}
		for file in glob(f"{prefix}static/profootballreference/{team}/*.json"):
			with open(file) as fh:
				stats = json.load(fh)

			wk = file.split("/")[-1].replace(".json", "")
			longestRanks[team][wk] = {}

			longestRec = passAtt = 0
			qb = ""
			for player in stats:
				if player in nfl_trades:
					try:
						pos = roster[nfl_trades[player]["team"]][player]
					except:
						continue
				else:
					try:
						currStats = stats
						pos = roster[team][player]
					except:
						continue
				if pos not in ["QB","WR","TE","RB"]:
					continue
				if pos not in longestRanks[team][wk]:
					longestRanks[team][wk][pos] = {
						"pass_long": [],
						"rec_long": [],
						"rush_long": []
					}
				for prop in ["pass_long", "rush_long", "rec_long"]:
					val = stats[player].get(prop, 0)
					if val:
						longestRanks[team][wk][pos][prop].append(val)
				if stats[player].get("pass_att", 0) > passAtt:
					passAtt = stats[player]["pass_att"]
					qb = player
				longestRec = max(longestRec, stats[player].get("rec_long", 0))
			if qb:
				stats[qb]["pass_long"] = longestRec
				if not longestRanks[team][wk]["QB"][
				"pass_long"] or longestRec > max(longestRanks[team][wk]["QB"][
				"pass_long"]):
					longestRanks[team][wk]["QB"][
				"pass_long"].append(longestRec)

			with open(file, "w") as fh:
				json.dump(stats, fh, indent=4)

	with open(f"{prefix}static/props/longestRanks.json", "w") as fh:
		json.dump(longestRanks, fh, indent=4)

def write_totals():
	totals = {}
	for team in os.listdir(f"{prefix}static/profootballreference/"):
		if team.endswith("json"):
			continue
		if team not in totals:
			totals[team] = {}

		for file in glob(f"{prefix}static/profootballreference/{team}/*.json"):
			with open(file) as fh:
				stats = json.load(fh)
			for player in stats:
				if player not in totals[team]:
					totals[team][player] = stats[player]
				else:
					for header in stats[player]:
						if header not in totals[team][player]:
							totals[team][player][header] = 0
						totals[team][player][header] += stats[player][header]

				if "gamesPlayed" not in totals[team][player]:
					totals[team][player]["gamesPlayed"] = 0
				if len(set(stats[player].values())) > 1:
					totals[team][player]["gamesPlayed"] += 1

	with open(f"{prefix}static/profootballreference/totals.json", "w") as fh:
		json.dump(totals, fh, indent=4)

def convertESPNHeader(header):
	if header == "completions":
		return "pass_cmp"
	elif header == "longest pass":
		return "pass_long"
	elif header == "long rushing":
		return "rush_long"
	elif header == "long reception":
		return "rec_long"
	elif header == "long interception":
		return "int_long"
	elif header == "interceptions":
		return "pass_int"
	elif header == "yards per pass attempt":
		return "pass_avg"
	elif header == "yards per rush attempt":
		return "rush_avg"
	elif header == "yards per reception":
		return "rec_avg"
	elif header == "completion percentage":
		return "pass_cmp_pct"
	elif header == "total sacks":
		return "pass_sacks"
	elif header == "passer rating":
		return "passer_rtg"
	elif header == "receptions":
		return "rec"
	elif header == "total tackles":
		return "tackles_combined"
	elif header == "solo tackles":
		return "tackles_solo"
	elif header == "assist tackles":
		return "tackles_assists"

	header = header.replace("attempts", "att").replace("passing", "pass").replace("rushing", "rush").replace("receiving", "rec").replace("yards", "yds").replace("touchdowns", "td").replace("adjusted ", "").replace("targets", "tgts")
	return "_".join(header.split(" "))

def writeAverages():
	with open(f"{prefix}static/profootballreference/playerIds.json") as fh:
		ids = json.load(fh)

	with open(f"{prefix}static/profootballreference/averages.json") as fh:
		averages = json.load(fh)

	with open(f"{prefix}static/profootballreference/lastYearStats.json") as fh:
		lastYearStats = json.load(fh)

	if 0:
		ids = {}

	for team in ids:
		if team not in averages:
			averages[team] = {}
		if team not in lastYearStats:
			lastYearStats[team] = {}

		for player in ids[team]:
			pId = ids[team][player]
			if player in averages[team]:
				pass
				continue

			year = "2021"
			if player in []:
				year = "2020"
			
			gamesPlayed = 0
			averages[team][player] = {}
			lastYearStats[team][player] = {}

			time.sleep(0.3)
			url = f"https://www.espn.com/nfl/player/gamelog/_/id/{pId}/type/nfl/year/{year}"
			outfile = "out"
			call(["curl", "-k", url, "-o", outfile])
			soup = BS(open(outfile, 'rb').read(), "lxml")

			for table in soup.findAll("table")[:-1]:
				if "postseason" in table.text.strip().lower() or "preseason" in table.text.strip().lower():
					continue
				headers = []
				for th in soup.findAll("tr")[1].findAll("th")[3:]:
					headers.append(convertESPNHeader(th.get("title").lower()))
				for row in table.findAll("tr")[2:]:
					if row.text.lower().startswith("regular season stats"):
						for idx, td in enumerate(row.findAll("td")[1:]):
							header = headers[idx]
							val = td.text.strip().replace(",", "")
							if "-" in val:
								val = "0"
							if "." not in val:
								val = round(float(val) / gamesPlayed, 2)
							else:
								val = float(val)
							averages[team][player][header] = val

						averages[team][player]["gamesPlayed"] = gamesPlayed
					else:
						tds = row.findAll("td")
						if len(tds) > 1 and ("@" in tds[1].text or "vs" in tds[1].text):
							#opp = tds[1].findAll("a")[-1].get("href").split("/")[-2]
							dateStr = tds[0].text.strip()
							if 1 <= int(dateStr.split(" ")[-1].split("/")[0]) <= 4:
								dateStr += f"/{int(year)+1}"
							else:
								dateStr += f"/{year}"
							date = str(datetime.strptime(dateStr, "%a %m/%d/%Y")).split(" ")[0]
							lastYearStats[team][player][date] = {}
							gamesPlayed += 1
							for idx, td in enumerate(tds[3:]):
								header = headers[idx]
								try:
									val = float(td.text.strip())
								except:
									val = 0.0
								lastYearStats[team][player][date][header] = val

	with open(f"{prefix}static/profootballreference/averages.json", "w") as fh:
		json.dump(averages, fh, indent=4)

	with open(f"{prefix}static/profootballreference/lastYearStats.json", "w") as fh:
		json.dump(lastYearStats, fh, indent=4)

def convertTeamRankingsTeam(team):
	if team == "green bay":
		return "gb"
	elif team == "jacksonville":
		return "jax"
	elif team == "new orleans":
		return "no"
	elif team == "new england":
		return "ne"
	elif team == "las vegas":
		return "lv"
	elif team == "tampa bay":
		return "tb"
	elif team == "san francisco":
		return "sf"
	elif team == "washington":
		return "wsh"
	elif team == "kansas city":
		return "kc"
	return team.replace(" ", "")[:3]

def write_rankings():
	baseUrl = "https://www.teamrankings.com/nfl/stat/"
	pages = ["plays-per-game", "opponent-plays-per-game", "tackles-per-game", "opponent-tackles-per-game", "points-per-game", "opponent-points-per-game", "1st-half-points-per-game", "opponent-1st-half-points-per-game", "qb-sacked-per-game", "sacks-per-game", "opponent-yards-per-rush-attempt", "opponent-yards-per-completion", "opponent-rushing-attempts-per-game", "opponent-rushing-yards-per-game", "opponent-pass-attempts-per-game", "opponent-passing-yards-per-game", "opponent-completions-per-game", "opponent-passing-touchdowns-per-game", "interceptions-per-game"]
	ids = ["playspg", "oplayspg", "tpg", "otpg", "ppg", "oppg", "1hppg", "o1hppg", "qbspg", "spg", "oydpra", "oydpc", "oruattpg", "oruydpg", "opaattpg", "opaydpg", "ocmppg", "opatdpg", "ointpg"]

	rankings = {}
	for idx, page in enumerate(pages):
		url = baseUrl+page
		outfile = "out"
		time.sleep(0.2)
		call(["curl", "-k", url, "-o", outfile])
		soup = BS(open(outfile, 'rb').read(), "lxml")

		for row in soup.find("table").findAll("tr")[1:]:
			tds = row.findAll("td")
			team = convertTeamRankingsTeam(row.find("a").text.lower())
			if team not in rankings:
				rankings[team] = {}
			if ids[idx] not in rankings[team]:
				rankings[team][ids[idx]] = {}

			rankings[team][ids[idx]] = {
				"rank": int(tds[0].text),
				"season": float(tds[2].text.replace("%", "")),
				"last3": float(tds[3].text.replace("%", ""))
			}

	with open(f"{prefix}static/profootballreference/rankings.json", "w") as fh:
		json.dump(rankings, fh, indent=4)

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-c", "--cron", action="store_true", help="Start Cron Job")
	parser.add_argument("-r", "--ranks", action="store_true", help="Get Ranks")
	parser.add_argument("--averages", help="averages", action="store_true")
	parser.add_argument("-schedule", "--schedule", help="Print Schedule", action="store_true")
	parser.add_argument("--rankings", help="Rankings", action="store_true")
	parser.add_argument("--roster", help="Roster", action="store_true")
	parser.add_argument("--stats", help="Stats", action="store_true")
	parser.add_argument("-s", "--start", help="Start Week", type=int)
	parser.add_argument("-e", "--end", help="End Week", type=int)
	parser.add_argument("-t", "--team", help="Get Team")
	parser.add_argument("-p", "--pos", help="Get Pos")
	parser.add_argument("-w", "--week", help="Week", type=int)

	args = parser.parse_args()
	curr_week = ""
	if args.start:
		curr_week = args.start
	settings = {'0_points_allowed': 10, '7-13_points_allowed': 4, 'sack': 1, 'ppr': 0.5, 'touchdown': 6, 'pass_tds': 4, 'fumble_recovery': 2, '1-6_points_allowed': 7, 'xpm': 1, 'fumbles_lost': -2, 'rec_tds': 6, 'interception': 2, 'field_goal_0-19': 3, 'safety': 2, 'field_goal_50+': 5, 'pass_yds': 25, 'field_goal_20-29': 3, 'pass_int': -2, 'rush_yds': 10, 'rush_tds': 6, '21-27_points_allowed': 0, '28-34_points_allowed': -1, '14-20_points_allowed': 1, 'field_goal_30-39': 3, 'field_goal_40-49': 4, '35+_points_allowed': -4, 'rec_yds': 10}

	if args.week:
		curr_week = int(args.week)
	else:
		curr_week = CURR_WEEK

	if args.averages:
		writeAverages()
	elif args.schedule:
		writeSchedule(curr_week)
	elif args.stats:
		write_stats(curr_week)
		writeQBLongest(curr_week)
	elif args.ranks:
		get_total_ranks(curr_week, settings)
	elif args.team and args.pos:
		ranks = get_ranks(curr_week, settings)
		opp, tot = position_vs_opponent_stats(args.team, args.pos, ranks, settings)
		teamname = TEAM_TRANS[args.team] if args.team in TEAM_TRANS else args.team
		print("**{} vs. {}**".format(teamname.upper(), args.pos))
		for idx, data in enumerate(opp):
			if idx + 1 > curr_week:
				continue
			print("\n#Wk{} vs. {} {} - {} pts".format(data["week"], data["opp"], args.pos, data["points"]))
			arr = [ d.split(": ")[1] for d in data["players"] ]
			print("\n".join(arr))
	elif args.roster:
		writeRosters()
	elif args.rankings:
		write_rankings()
	elif args.cron:
		pass
		# only needs to be run once in a while
		write_rankings()
		writeSchedule(curr_week)
		writeSchedule(curr_week+1)
		write_stats(curr_week)
		writeQBLongest(curr_week)

	#write_stats(curr_week)
	#writeSchedule(curr_week+1)
	#writeQBLongest(curr_week)