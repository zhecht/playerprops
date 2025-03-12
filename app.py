from flask import Flask, render_template
import os
import controllers

app = Flask(__name__, template_folder='views')

app.register_blueprint(controllers.main_blueprint)
app.register_blueprint(controllers.props_blueprint)
app.register_blueprint(controllers.altprops_blueprint)
app.register_blueprint(controllers.nbaprops_blueprint)
app.register_blueprint(controllers.soccerprops_blueprint)
app.register_blueprint(controllers.draft_blueprint)
app.register_blueprint(controllers.mlbprops_blueprint)
app.register_blueprint(controllers.mlbdraft_blueprint)
app.register_blueprint(controllers.ncaab_blueprint)
app.register_blueprint(controllers.ncaabprops_blueprint)
app.register_blueprint(controllers.nfl_blueprint)
app.register_blueprint(controllers.nhl_blueprint)
app.register_blueprint(controllers.nhlprops_blueprint)
app.register_blueprint(controllers.betting_blueprint)
app.register_blueprint(controllers.bets_blueprint)
app.register_blueprint(controllers.ravendawn_blueprint)
app.register_blueprint(controllers.march_blueprint)
#app.register_blueprint(controllers.trades_print)

app.secret_key = os.urandom(24)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
    #app.run(host='localhost', port=3000, debug=True)