from flask import render_template, request, redirect, url_for, jsonify
import os
from os.path import join, dirname, realpath
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder import ModelView, ModelRestApi

from werkzeug.utils import secure_filename
from datetime import datetime
import logging
logging.getLogger()
import pandas as pd
import json
import plotly
import plotly.express as px

from . import appbuilder, db, app

"""
    Create your Model based REST API::

    class MyModelApi(ModelRestApi):
        datamodel = SQLAInterface(MyModel)

    appbuilder.add_api(MyModelApi)


    Create your Views::


    class MyModelView(ModelView):
        datamodel = SQLAInterface(MyModel)


    Next, register your Views::


    appbuilder.add_view(
        MyModelView,
        "My View",
        icon="fa-folder-open-o",
        category="My Category",
        category_icon='fa-envelope'
    )
"""

"""
    Application wide 404 error handler
"""

from flask_appbuilder import AppBuilder, BaseView, expose, has_access
from app import appbuilder


class Home(BaseView):
    route_base = '/'
    @expose('/dashboard')
    def dashboard(self):
        print(app.config)
        self.update_redirect()
        return self.render_template('dashboard.html')

    @expose('/history/<string:period>')
    def history(self, period):
        self.update_redirect()
        return self.render_template('history.html')
    
    @expose('/leaderboard')
    def leaderboard(self):
        self.update_redirect()
        return self.render_template('leaderboard.html')
    
    @expose('/forecasting')
    def forecasting(self):
        self.update_redirect()
        return self.render_template('forecast.html')
    
    @expose('/tips')
    def tips(self):
        self.update_redirect()
        return self.render_template('tips.html')

    @expose('/appliance/<string:appliance_name>')
    def appliance(self, appliance_name, model_name=None):
        """
        This function allows provides an appliance name that need to be disaggregated and the 
        """

        # Compute Path and File Name
        current_user = str(self.appbuilder.sm.current_user)
        file_name = f'{current_user}_power_data.csv'
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_name)

        # Check if file exists
        fig_json = None
        if os.path.exists(file_path):
            # Process file
            df = pd.read_csv(file_path).dropna().reset_index(drop=True)
            df.columns = ["Timestamp", "Power"]
            fig = px.line(df, x="Timestamp", y="Power")
            fig_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
  
        return self.render_template('appliance.html', appliance_name=appliance_name, fig_json=fig_json)
    
    @expose('/appliance/<string:appliance_name>', methods=['POST'])
    def upload_files(self, appliance_name):  
        # Request Validation
        if "file" not in request.files:
            raise Exception("No file uploaded")
        
        if ".csv" not in request.files['file'].filename:
            raise Exception("No csv file uploaded")

        # Compute Path and File Name
        current_user = str(self.appbuilder.sm.current_user)
        file_name = f'{current_user}_power_data.csv'
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_name)
        
        # Save file
        uploaded_file = request.files['file']
        uploaded_file.save(file_path)

        # Process file
        df = pd.read_csv(file_path).dropna().reset_index(drop=True)
        df.columns = ["Timestamp", "Power"]
        fig = px.line(df, x="Timestamp", y="Power")
        fig_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

        #return jsonify({"file": file_name, "upload": file_path, "fig": fig_json})
        return self.render_template('appliance.html', appliance_name=appliance_name, fig_json=fig_json)

    

appbuilder.add_view_no_menu(Home())


@appbuilder.app.errorhandler(404)
def page_not_found(e):
    return (
        render_template(
            "404.html", base_template=appbuilder.base_template, appbuilder=appbuilder
        ),
        404,
    )


db.create_all()