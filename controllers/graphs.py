from flask import *
import operator
import sys
from controllers.espn_stats import *
from controllers.stats import *
from controllers.fantasypros_stats import *
from controllers.read_rosters import *
from controllers.borischen import *


graphs_blueprint = Blueprint('graphs', __name__, template_folder='views')

def merge_two_dicts(x, y):
	z = x.copy()
	z.update(y)
	return z

@graphs_blueprint.route('/graphs')
def graphs_route():
	real_week = 5

	try:
		arg_week = int(request.args.get("week"))
		cutoff = arg_week + 1
		is_all_weeks = False
	except:
		arg_week = 1
		cutoff = real_week
		is_all_weeks = True

	if arg_week >= real_week:
		arg_week = 1
		cutoff = 2

	players_on_teams, name_translations = read_rosters()
	players_on_FA = read_FA()
	players_on_teams = merge_two_dicts(players_on_teams, players_on_FA)
	error_graphs = []
	total_pos_players = [0,0,0,0]
	total_players = 0
	for curr_week in range(arg_week, cutoff):
		yahoo_json = read_yahoo_stats(curr_week, curr_week + 1)
		espn_json = read_espn_stats(curr_week, curr_week + 1)
		fantasypros_json = read_fantasypros_stats(curr_week, curr_week + 1)
		actual_json = read_actual_stats(curr_week, curr_week + 1)
		

		player_info = {"qb": [], "rb": [], "wr": [], "te": []}
		for player in actual_json:
			if player not in players_on_teams:
				continue
			try:
				espn_proj = espn_json[player]
				yahoo_proj = yahoo_json[player]
				fantasypros_proj = fantasypros_json[player]
				actual = 0 if actual_json[player] == "-" else float(actual_json[player])
			except:
				#print(player)
				continue

			if actual == 0 or yahoo_proj == 0 or espn_proj == 0 or player not in players_on_teams:# or yahoo_proj < 5:
				continue

			try:
				yahoo_err = round(((yahoo_proj - actual) / yahoo_proj), 2)
				espn_err = round(((espn_proj - actual) / espn_proj), 2)
				fantasypros_err = round(((fantasypros_proj - actual) / fantasypros_proj), 2)
			except:
				continue

			if abs(yahoo_err) > 2 or abs(espn_err) > 2 or abs(fantasypros_err) > 2:
				continue
			
			player_info[players_on_teams[player]["position"].lower()].append({"name": player, "espn": espn_err, "yahoo": yahoo_err, "fantasypros": fantasypros_err, "actual": actual})

		#graphs = {"site_names": ["yahoo", "espn", "fantasypros"], "overall_perc_err": [0,0,0], "overall_length": 0, "pos_length": [0,0,0,0], "pos_perc_err": ["qb": [0,0,0], "rb": [0,0,0], "wr": [0,0,0], "te": [0,0,0]]}
		for site_idx, site in enumerate(["yahoo", "espn", "fantasypros"]):
			if len(error_graphs) < 3:
				error_graphs.append({"name": site, "overall_perc_err": 0, "pos_perc_err": [0,0,0,0] })

			for pos_idx, position in enumerate(["qb", "rb", "wr", "te"]):
				for player_arr in player_info[position]:
					error_graphs[site_idx]["overall_perc_err"] += abs(player_arr[site])
					error_graphs[site_idx]["pos_perc_err"][pos_idx] += abs(player_arr[site])
					if site == "yahoo":
						#print(player_arr)
						total_players += 1
						total_pos_players[pos_idx] += 1


		pass
	#endof week for	loop
	#print(total_pos_players, total_players, error_graphs)
	for graph in error_graphs:
		graph["overall_perc_err"] = 100 - round((graph["overall_perc_err"] / total_players) * 100, 2)
		for i in range(4):
			graph["pos_perc_err"][i] = 100 - round((graph["pos_perc_err"][i] / total_pos_players[i]) * 100, 2)

	return render_template("graphs.html", real_week=real_week, graphs=error_graphs, curr_week=arg_week, sites=["yahoo", "espn", "fantasypros"], all_weeks=[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17], is_all_weeks=is_all_weeks)

	"""
		yahoo_rankings_sorted = sorted(player_rankings, key=operator.itemgetter("yahoo"))
		espn_rankings_sorted = sorted(player_rankings, key=operator.itemgetter("espn"))
		fantasypros_rankings_sorted = sorted(player_rankings, key=operator.itemgetter("fantasypros"))
		actual_rankings_sorted = sorted(player_rankings, key=operator.itemgetter("actual"), reverse=True)
		
		for position in ["qb", "rb", "te", "wr"]:
			
			for site in ["yahoo", "espn", "fantasypros"]:
				total_perc_err = 0
				total_abs_perc_err = 0
				graph = {"week": curr_week, "title": "Wk{} {} % Err Vs. Projected Rank [{}]".format(curr_week, site, position), "position": position, "site": site, "actual": [], "projected": [], "perc_err": [], "abs_err": [], "abs_perc_err": [], "full_name": [], "name": []}

				arr = yahoo_rankings_sorted
				if site == "espn":
					arr = espn_rankings_sorted
				elif site == "fantasypros":
					arr = fantasypros_rankings_sorted
				
				arr = actual_rankings_sorted
				for player in arr:
					try:
						if player["position"] == position:
							graph["name"].append(" ".join(player["name"].split(" ")[1:]))
							graph["full_name"].append(player["name"])
							
							#actual = actual_json[player["name"]]
							graph["actual"].append(str(player["actual"]))
							#graph["projected"].append(str(proj))
							graph["perc_err"].append(str(player[site]))
							total_abs_perc_err += abs(player[site])

					except:
						continue
				
				cutoff = 30 if (position == "qb" or position == "te") else 40
				for key in ["actual", "projected", "perc_err", "abs_perc_err", "name", "full_name"]:
					graph[key] = graph[key][:cutoff]

				total_players = len(graph["name"])

				#avg_perc_err = total_perc_err / float(total_players)
				

				for key in ["actual", "projected", "perc_err", "abs_perc_err", "name", "full_name"]:
					graph[key] = ','.join(graph[key])

				#graph["avg_perc_err"] = avg_perc_err
				graph["avg_abs_perc_err"] = round(total_abs_perc_err / float(total_players), 2)
				
				error_graphs.append(graph)


	return render_template("graphs.html", real_week=real_week, error_graphs=error_graphs, curr_week=arg_week, sites=["yahoo", "espn", "fantasypros"], all_weeks=[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17], is_all_weeks=is_all_weeks, pos=arg_pos)

	"""
