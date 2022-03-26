# https://g6a35f299a6bdd5-db202203181048.adb.eu-milan-1.oraclecloudapps.com/ords/admin/monthly_incidents_real_time_2104/?limit=1000&offset=7500
# python 3.9

from dash import Dash, html, dcc
from os.path import exists
from flask import Flask, redirect, render_template, session;
import flask
import flask_login
import requests
# import dash_auth
import pandas as pd
import numpy as np
from kpis import KPIS
    
# @note Safely suppress copy warnings they are ok    
pd.set_option('mode.chained_assignment', None)
    
server = Flask(__name__);

# https://gist.github.com/danielfennelly/9a7e9b71c0c38cd124d0862fd93ce217
server.secret_key = 'super secret string'  # Change this in production!

login_manager = flask_login.LoginManager()
login_manager.init_app(server)

# @note Only for demo purposes
users = {'riccardo@demo.com': {'pw': 'demo'}}

class User(flask_login.UserMixin):
    pass

@login_manager.user_loader
def user_loader(email):
    if email not in users:
        return

    user = User()
    user.id = email
    return user

@login_manager.request_loader
def request_loader(request):
    email = request.form.get('email')
    if email not in users:
        return

    user = User()
    user.id = email

    user.is_authenticated = request.form['pw'] == users[email]['pw']
    return user

@login_manager.unauthorized_handler
def unauthorized_handler():
    return 'Unauthorized'

app = Dash(
    server=server,
    url_base_pathname = '/dashboard/'
)

@server.route('/', methods=['GET', 'POST'])
def login():
    # https://stackoverflow.com/questions/52286507/how-to-merge-flask-login-with-a-dash-application
    for view_func in server.view_functions:
        if view_func == app.config['url_base_pathname']:
            server.view_functions[view_func] = flask_login.login_required(server.view_functions[view_func])
    
    if flask.request.method == 'GET':
        if flask_login.current_user.is_authenticated:
            return flask.redirect(flask.url_for('/dashboard/'))
        
        return render_template('login.html')

    email = flask.request.form['email']
    if (email in users) and flask.request.form['pw'] == users[email]['pw']:
        user = User()
        user.id = email
        flask_login.login_user(user)
        # session["me"] = email;
        return flask.redirect(flask.url_for('/dashboard/'))

    return 'Bad login'

@server.route('/logout')
def logout():
    flask_login.logout_user()
    return 'Logged out'

stats = KPIS();
localCopyForSpeed = [
    ["local_db.csv", "https://g6a35f299a6bdd5-db202203181048.adb.eu-milan-1.oraclecloudapps.com/ords/admin/monthly_incidents_real_time_2104/"], 
    ["local_db_backlog.csv", "https://g6a35f299a6bdd5-db202203181048.adb.eu-milan-1.oraclecloudapps.com/ords/admin/monthly_incidents_real_time_2104_backlog/"]
];
loopCopies = 1;

for localCopy in localCopyForSpeed:
    file_exists = exists(localCopy[0]);
    if not file_exists:
        collectMore = True;
        pPage = 10000;
        offset = 0;
        
        if loopCopies == 1:
            db = pd.DataFrame(columns = ['incident code', 'customer company group', 'customer company', 'create date-time', 'resolution date-time', 'incident status', 'incident description', 'support group', 'tower group', 'domain group', 'priority', 'urgency', 'resolution description', 'assigned organization', 'inc.category', 'last modified date', 'inc type', 'inc element', 'aging', 'localizacion cliente', 'departamento cliente']);
        else:
            db_backlog = pd.DataFrame(columns = ['incident code', 'customer company group', 'customer company', 'create date-time', 'resolution date-time', 'incident status', 'incident description', 'support group', 'tower group', 'domain group', 'priority', 'resolution description', 'assigned organization', 'inc.category', 'last modified date', 'inc type', 'inc element', 'aging', 'localizacion cliente', 'departamento cliente']);

        while (collectMore):
            data = requests.get(localCopy[1] + "?limit=" + str(pPage) + "&offset=" + str(offset));

            for item in data.json()["items"]:
                del item["links"]
                vals = list(item.values());
                # item = pd.DataFrame.from_dict(data = vals, orient = "index", columns = item.keys());
                # db = db.concat([db, vals], ignore_index = True);
                if loopCopies == 1:
                    db.loc[db.shape[0]] = vals;
                else:
                    db_backlog.loc[db_backlog.shape[0]] = vals;

            collectMore = data.json()["hasMore"];
            offset = offset + pPage;
        if loopCopies == 1:
            db.to_csv("local_db.csv", index = False);
        else:
            db_backlog.to_csv("local_db_backlog.csv", index = False);
    else:
        if loopCopies == 1:
            db = pd.read_csv("local_db.csv");
        else:
            db_backlog = pd.read_csv("local_db_backlog.csv");
        
    loopCopies += 1;

criticalSLAData = stats.criticalMeetsSLA(db);
app.layout = html.Div(children=[
    html.H1(children='Dashboard'),

    html.Div(children=[
       html.H3(children='Welcome!') 
    ]),
    
    html.A('Logout', href="/logout"),
    
    html.Div(children=[
       html.H4(children='Critical Incidents for April 2021: ' + str(stats.criticalIncidents(db))) 
    ]),
    
    html.Div(children=[
       html.H4(children='Total Incidents for April 2021: ' + str(stats.totalIncidents(db))) 
    ]),

    html.H4(children='Incident type breakdown'),
    dcc.Graph(
        id = 'pie-chart-breakdown',
        figure = stats.fractionIncidents(db)
    ),
    
    html.H4(children='Backlog type breakdown'),
    dcc.Graph(
        id = 'pie-chart-backlog',
        figure = stats.backlogPriority(db_backlog)
    ),
    
    html.H4(children='Incident type breakdown'),
    dcc.Graph(
        id = 'pie-chart-type-brkd',
        figure = stats.incidentTypeBreakdown(db)
    ),
    
    html.H4(children='P1 SLA Resolution time'),
    dcc.Graph(
        id = 'pie-chart-sla-meets',
        figure = criticalSLAData["chart"]
    ),
    
    html.Div(children=[
       html.H4(children='P1 Average time of resolution when SLA-compliant for April 2021: ' + str(criticalSLAData["timings"]["meets"])) 
    ]),
    
    html.Div(children=[
       html.H4(children='P1 Average time of resolution when NOT SLA-compliant for April 2021: ' + str(criticalSLAData["timings"]["doesnot"])) 
    ]),
    
    html.H4(children='Custom KPI: Breakdown of incident status type (null values are shown to highlight the number of missing column values'),
    dcc.Graph(
        id = 'pie-chart-custom',
        figure = stats.custom(db)
    )
])

if __name__ == '__main__':
    app.run_server(debug=True, port = 8050)



