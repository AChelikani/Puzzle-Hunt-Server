from flask import Flask
from flask import Flask, flash, redirect, render_template, request, session, abort
import os
from sqlalchemy.orm import sessionmaker
from tabledef import *
import solutions
import info
import config
import slackweb

engine = create_engine('sqlite:///tutorial.db', echo=True)
slack = slackweb.Slack(url=config.SLACK_HOOK)
app = Flask(__name__)

@app.route('/live')
def home():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        return profile()

@app.route('/')
def base():
    return render_template('home.html')

@app.route('/profile')
def profile():
    return render_template('profile.html', teamname=session['team'])

@app.route('/puzzles')
def puzzles():
    return render_template('puzzles.html')

@app.route('/puzzles/<puzzlenum>')
def pick_puzzle(puzzlenum):
    # Add error checking for puzzlenum
    return render_template('puzzle' + str(puzzlenum) + '.html')

@app.route('/scoreboard')
def scoreboard():
    return render_template('scoreboard.html')

@app.route('/login', methods=['POST'])
def do_admin_login():

    POST_USERNAME = str(request.form['username'])
    POST_PASSWORD = str(request.form['password'])

    Session = sessionmaker(bind=engine)
    s = Session()
    query = s.query(User).filter(User.username.in_([POST_USERNAME]), User.password.in_([POST_PASSWORD]) )
    result = query.first()
    if result:
        session['logged_in'] = True
        session['team'] = POST_USERNAME
    else:
        flash('wrong password!')
    return home()

@app.route('/solve', methods=['POST'])
def solve():
    puzzle = dict(request.form).keys()[0]
    guess = request.form[puzzle]
    slack.notify(text=guess + " for " + puzzle + " by " + session['team'], channel="#guesses")
    if (puzzle in solutions.SOLUTIONS and solutions.SOLUTIONS[puzzle] == guess):
        Session = sessionmaker(bind=engine)
        s = Session()
        s.query(User).filter(User.username == session['team']).update(User.puzzles: User.puzzles * info.IDENTIFIERS[puzzle])
        s.query(User).filter(User.username == session['team']).update(User.score: User.score + 1)
        print "correct"
        return puzzles()
    else:
        print "wrong"
        return pick_puzzle(1)

@app.route("/logout")
def logout():
    session['logged_in'] = False
    return home()

if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=True,host='0.0.0.0', port=4000)
