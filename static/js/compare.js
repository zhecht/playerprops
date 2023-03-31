

function find_best() {
	var table_ids = ["airyards_table", "nextgen_table", "redzone_table"];
	for (var i = 0; i < table_ids.length; ++i) {
		var stats1 = document.getElementById(table_ids[i]).getElementsByTagName("tr")[1].getElementsByTagName("td");
		var stats2 = document.getElementById(table_ids[i]).getElementsByTagName("tr")[2].getElementsByTagName("td");
		for (var s = 0; s < stats1.length; ++s) {
			var val1 = parseFloat(stats1[s].innerText.split(" ")[0]);
			var val2 = parseFloat(stats2[s].innerText.split(" ")[0]);
			if (val1 >= val2) {
				stats1[s].className = "best";
			}
			if (val2 >= val1) {
				stats2[s].className = "best";
			}
		}
	}
}

function fix_fp() {
	var rows = document.getElementById("fp_table").getElementsByTagName("tr");
	for (var r = 1; r < rows.length; ++r) {
		if (rows[r].className != "title") {
			var tds = rows[r].getElementsByTagName("td");
			tds[tds.length - 1].remove();
		}
	}
}

fix_fp();
find_best();