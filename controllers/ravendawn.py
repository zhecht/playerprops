from flask import *

ravendawn_blueprint = Blueprint('ravendawn', __name__, template_folder='views')

@ravendawn_blueprint.route('/ravendawn')
def ravendawn_route():
	with open("ravendawn.json") as fh:
		data = json.load(fh)
	return render_template("ravendawn.html", data=data)

# each pack is 12000
# 12000 * demand + (distance * 9)

if __name__ == "__main__":
	pass