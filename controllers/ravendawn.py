from flask import *

ravendawn_blueprint = Blueprint('ravendawn', __name__, template_folder='views')

@ravendawn_blueprint.route('/ravendawn')
def ravendawn_route():
	with open("ravendawn.json") as fh:
		data = json.load(fh)
	return render_template("ravendawn.html", data=data)

@ravendawn_blueprint.route('/updateJSON', methods=["POST"])
def json_route():
	data = json.loads(request.data)
	with open("ravendawn.json", "w") as fh:
		json.dump(data, fh, indent=4)
	return jsonify(success=1)

if __name__ == "__main__":
	pass

	with open("ravendawn.json") as fh:
		data = json.load(fh)

	lands = ["darzuac", "defiance", "margrove", "orca bay", "rivercrest", "riverend", "seabreeze"]