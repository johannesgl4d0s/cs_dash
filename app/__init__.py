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

def home():
      data = [
            ("01-01-2020", 1567),
            ("02-01-2020", 1456),
            ("03-01-2020", 1908),
            ("04-01-2020", 896),
            ("05-01-2020", 755),
            ("06-01-2020", 453),
      ]

      labels = [row[0] for row in data]
      values = [row[1] for row in data]

      return labels,values

app = Flask(__name__)
app.config.from_object("config")
db = SQLA(app)
appbuilder = AppBuilder(app, db.session,  base_template='base.html', indexview=MyIndexView)
# Upload folder
UPLOAD_FOLDER = r'C:\Users\johan\nilm-dashboard\nilm-dashboard\app\static\files'
app.config['UPLOAD_FOLDER'] =  UPLOAD_FOLDER


# @app.route("/appliance/<name>")
# def plot_graph(name):
#       labels,values = home()
#       return redirect(url_for('Home.appliance', appliance_name = name, labels = labels, values=values))



@app.route("/appliance/<name>", methods=['POST'])
def uploadFiles(name):
      # get the uploaded file
      uploaded_file = request.files['file']
      filename = secure_filename(uploaded_file.filename)
      new_filename = f'{filename.split(".")[0]}_{str(datetime.today())}.csv'
      uploaded_file.filename = new_filename.replace(" ", "").replace(":", "_")
      if uploaded_file.filename != '':
           logging.info(uploaded_file.filename)
           file_path = os.path.join(app.config['UPLOAD_FOLDER'], uploaded_file.filename)
           logging.info(file_path)
          # set the file path
           uploaded_file.save(file_path)
           labels,values = home()
          # save the file
      return redirect(url_for('Home.appliance', appliance_name = name , labels = labels, values=values))



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
