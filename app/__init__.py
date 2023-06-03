import logging

from flask import Flask, render_template, request, redirect, url_for
import os
from os.path import join, dirname, realpath
from flask_appbuilder import AppBuilder, SQLA
from werkzeug.utils import secure_filename
from datetime import datetime


from app.newindex import MyIndexView

"""
 Logging configuration
"""

logging.basicConfig(format="%(asctime)s:%(levelname)s:%(name)s:%(message)s")
logging.getLogger().setLevel(logging.DEBUG)

app = Flask(__name__)
app.config.from_object("config")
db = SQLA(app)
appbuilder = AppBuilder(app, db.session,  base_template='base.html', indexview=MyIndexView)


# @app.route("/appliance/<name>")
# def plot_graph(name):
#       labels,values = home()
#       return redirect(url_for('Home.appliance', appliance_name = name, labels = labels, values=values))



"""
from sqlalchemy.engine import Engine
from sqlalchemy import event

#Only include this for SQLLite constraints
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    # Will force sqllite contraint foreign keys
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
"""

from . import views
