
const teamFormatter = function(cell, params, rendered) {
	const div = document.createElement("div");
	div.className = cell.getValue().toLowerCase();
	div.innerText = cell.getValue().toUpperCase();
	return div;
}