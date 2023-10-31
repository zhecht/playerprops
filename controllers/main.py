from flask import *
from lxml import etree
#from sql_helper import *
#try:
#  import controllers.read_rosters as read_rosters
#  from controllers.oauth import *
#except:
  #import read_rosters
  #from oauth import *

main_blueprint = Blueprint('main', __name__, template_folder='views')


@main_blueprint.route('/')
def main_route():
  #oauth = MyOAuth()

  #all_teams = read_standings()
  return render_template("main.html", players=[])