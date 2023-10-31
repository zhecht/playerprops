

$(document).ready(function(){
	var my_team = localStorage.getItem("my_team");
	var path_arr = window.location.pathname.split('/');
	var team_loc = $.inArray("team", path_arr);
	var graphs_loc = $.inArray("graphs", path_arr);
	var is_rankings_loc = $.inArray("rankings", path_arr);
	var is_team_page = (team_loc !== -1);
	var is_graphs_page = (graphs_loc !== -1);
	if (!is_team_page && !is_graphs_page && !is_rankings_loc) {
		if (my_team !== null) {
			window.location.href = "/team/"+my_team;
			return;
		}
		$("#lineup_col").hide();
		$("#teams_col,#darkened_back").show();
	}
});

var links = document.getElementById("nav").getElementsByTagName("a");
for (var i in links) {
	links[i].addEventListener("click", function(event){
		show_data(event);
	});
}

function show_data(el) {
	var link;
	var txt = el.target.innerText;
	console.log(txt);
	if (txt == "Defensive Ranks") {
		link = "defense?over_expected=true";
	} else if (txt == "RBBC Trends") {
		link = "rbbc";
	} else if (txt == "Redzone Look Trends") {
		link = "redzone";
	}
	window.location.href = "/"+link;
	el.preventDefault();
	return false;
}

function changeTeam(selected) {
	window.location.href = "/team/"+(selected+1);
}

$(".teamButton").click(function(){
	var id = $(this).attr('id');
	localStorage.setItem("my_team", id);
	window.location.href = "/team/"+id;
});


$(".playerRow").hover(
	function() {
		if ($(this).hasClass("headerRow") == false) {
			$(this).toggleClass("highlight");
		}
		
	}, function() {
		if ($(this).hasClass("headerRow") == false) {
			$(this).toggleClass("highlight");
		}
	}
);


var projected_trace = {
	x: [],
	y: [],
	name: "Yahoo",
	type: "bar",
	marker: {
		color: "#7405ba"
	}
};
var actual_trace = {
	x: [],
	y: [],
	name: "Actual",
	type: "bar",
	marker: {
		color: "green"
	}
};
var espn_trace = {
	x: [],
	y: [],
	name: "ESPN",
	type: "bar",
	marker: {
		color: "#d00"
	}
};
var snaps_trace = {
	x: [],
	y: [],
	type: "scatter",
	mode: 'lines+markers',
	line: {shape: 'linear'}
};

function makeWeekArray(week_len) {
	var arr = [];
	for(var i = 1; i < week_len + 1; ++i) {
		arr.push(i)
	}
	return arr;
}

$(".playerRow").click(function(){
	var invalidRow = $(this).hasClass('benchRow') || $(this).hasClass('headerRow');
	if (invalidRow)
		return
	var player_id = parseInt($(this).attr('id'));
	var weekly_proj = $("#weekly_proj_"+player_id).val().split(",");

	var name = $(this).find("td.name").text();
	$("#player_name").text(name);
	projected_trace['x'] = makeWeekArray(weekly_proj.length);
	projected_trace['y'] = weekly_proj;

	actual_trace['x'] = makeWeekArray(weekly_proj.length);
	actual_trace['y'] = $("#weekly_act_"+player_id).val().split(",");

	espn_trace['x'] = makeWeekArray(weekly_proj.length);
	espn_trace['y'] = $("#weekly_proj_espn_"+player_id).val().split(",");

	var width = $('#plot_col').width();
	var layout = {
		title: "Projections",
		barmode: "group",
		autosize: false,
		width: width * .8,
		xaxis: {
			autotick: false,
			title: "Week"
		},
		yaxis: {
			title: "Points"
		}
	};
	Plotly.newPlot("plot_div", [actual_trace,projected_trace, espn_trace], layout);

	snaps_trace['x'] = makeWeekArray(weekly_proj.length);
	snaps_trace['y'] = $("#snap_counts_"+player_id).val().split(",");
	var layout2 = {
		title: "Snap Counts",
		autosize: false,
		width: width * .8,
		xaxis: {
			autotick: false,
			title: "Week"
		},
		yaxis: {
			title: "Snap %"
		}

	};
	Plotly.newPlot("snaps_plot", [snaps_trace], layout2);

});


