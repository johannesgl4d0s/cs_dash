from flask import render_template, request, redirect, url_for, jsonify
import os
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder import expose, BaseView

from werkzeug.utils import secure_filename
from datetime import datetime
import logging
import pandas as pd
import json
import plotly
import plotly.express as px
import sqlite3

from app import appbuilder, db, app

logging.getLogger()

class Home(BaseView):
    route_base = '/'
    @expose('/dashboard')
    def dashboard(self):
        print(app.config)
        self.update_redirect()
        return self.render_template('dashboard.html')

    @expose('/history/<string:period>')
    def history(self, period):
        if period == "last3months":
            period_filter = "-3 months"
        elif period == "lastyear":
            period_filter = "-1 year"
        else:
            period_filter = "-100 years"  
        sql = """
            SELECT user_id, timestamp, power
            FROM history
            WHERE user_id = :user_id AND timestamp > (
                    SELECT DATETIME(MAX(timestamp), :period_filter)
                    FROM history
                    WHERE user_id = :user_id
            ) 
            ORDER BY timestamp
        """

        user_id = self.appbuilder.sm.current_user.id
        count_data = db.engine.execute("SELECT COUNT(*) FROM history WHERE user_id = :user_id", user_id = user_id).fetchone()[0]
        
        fig_json = None
        if count_data > 0:
            data = db.engine.execute(sql, user_id = user_id, period_filter = period_filter).fetchall()
            df = pd.DataFrame(data=data, columns=["user_id", "timestamp", "power"])
            fig = px.line(df, x="timestamp", y="power")
            fig_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        return self.render_template('history.html', fig_json=fig_json)
        

    
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
        user_id = self.appbuilder.sm.current_user.id        
        count_data = db.engine.execute("SELECT COUNT(*) FROM history WHERE user_id = :user_id", user_id = user_id).fetchone()[0]

        fig_json = None
        if count_data > 0:
            sql = "SELECT timestamp, power FROM history WHERE user_id = :user_id order by timestamp"
            df = pd.DataFrame(db.engine.execute(sql, user_id = user_id), columns=["timestamp", "power"])
            fig = px.line(df, x="timestamp", y="power")
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
        user_id = self.appbuilder.sm.current_user.id
        now = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        file_name = f'{current_user}_power_data_{now}.csv'
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_name)
        
        # Save file
        uploaded_file = request.files['file']
        uploaded_file.save(file_path)

        # Process file
        df = pd.read_csv(file_path, sep=";").dropna().reset_index(drop=True)
        df.columns = ["timestamp", "power"]

        # Upload Data to DB
        #db.engine.execute("DELETE FROM history WHERE user_id = :user_id", user_id = user_id)
        con = sqlite3.connect("app.db")
        sql = """
            INSERT INTO history (user_id, timestamp, power)
            VALUES (:user_id, :timestamp, :power)
            ON CONFLICT (user_id, timestamp) DO UPDATE SET power = :power
        """
        df["user_id"] = user_id
        df_dict = df.to_dict(orient="records")
        con.executemany(sql, df_dict)
        con.commit()
        con.close()

        return redirect(url_for('Home.appliance', appliance_name=appliance_name))

        #return jsonify({"file": file_name, "upload": file_path, "fig": fig_json, "user_id": user_id})
        #return self.render_template('appliance.html', appliance_name=appliance_name, fig_json=fig_json)

    

appbuilder.add_view_no_menu(Home())


@appbuilder.app.errorhandler(404)
def page_not_found(e):
    return (
        render_template(
            "404.html", base_template=appbuilder.base_template, appbuilder=appbuilder
        ),
        404,
    )
