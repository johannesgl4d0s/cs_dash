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
import numpy as np
from app.deepmodels import *


from app import appbuilder, db, app

logging.getLogger()




def load_models():
    fridge_weights = os.path.join(app.config['UPLOAD_FOLDER_WEIGHTS'], 'seq2seq-temp-weights-fridge-epoch0.h5')

    kettle_weights = os.path.join(app.config['UPLOAD_FOLDER_WEIGHTS'], 'seq2seq-temp-weights-kettle-epoch0.h5')
    microwave_weights = os.path.join(app.config['UPLOAD_FOLDER_WEIGHTS'], 'seq2seq-temp-weights-microwave-epoch0.h5')
    wm_weights = os.path.join(app.config['UPLOAD_FOLDER_WEIGHTS'], 'seq2seq-temp-weights-washing_machine-epoch0.h5')

    fridge = return_seq2seq()
    kettle = return_seq2seq()
    microwave = return_seq2seq()
    wm = return_seq2seq()

    fridge.load_weights(fridge_weights)
    kettle.load_weights(kettle_weights)
    microwave.load_weights(microwave_weights)
    wm.load_weights(wm_weights)
    return fridge, kettle, microwave, wm




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
            fig = px.line(df, x="timestamp", y="power", title="Power Consumption History")
            fig_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        return self.render_template('history.html', fig_json=fig_json)
        
    
    @expose('/leaderboard')
    def leaderboard(self):
        user_id = self.appbuilder.sm.current_user.id

        # compute average power consumption for the user (last month)
        sql = """
            SELECT 
                ROUND(AVG(power), 2) as avg_power 
            FROM history
            WHERE user_id = :user_id
            GROUP BY
                strftime('%Y-%m', timestamp)
            ORDER BY 
                strftime('%Y-%m', timestamp) DESC
        """
        try:
            user_power = db.engine.execute(sql, user_id = user_id).fetchone()[0]
        except:
            user_power = 0


        # compute average power consumption for remaining users (last month)
        sql = """
            SELECT ROUND(AVG(power), 2) as avg_power
            FROM history
            WHERE user_id != :user_id
            GROUP BY
                strftime('%Y-%m', timestamp)
            ORDER BY 
                strftime('%Y-%m', timestamp) DESC
        """
        try:
            other_power = db.engine.execute(sql, user_id = user_id).fetchone()[0]
            savings = round((user_power - other_power) / other_power * 100, 2)
        except:
            other_power = 0
            savings = 0

        # plotly
        fig = px.bar(x=["You", "Others"], y=[user_power, other_power], 
                     labels={"x": "User", "y": "Average Power Consumption"})
        fig_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

        # render template
        return self.render_template('leaderboard.html', user_power=user_power, 
                                    other_power=other_power, savings=savings, fig_json=fig_json)
    
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
            # Load Data from DB
            sql = "SELECT timestamp, power FROM history WHERE user_id = :user_id order by timestamp"
            df = pd.DataFrame(db.engine.execute(sql, user_id = user_id), columns=["timestamp", "power"])

            # Normalise data
            mean_frz, std_frz, df_new = normalise(df['power'])
            WINDOW_SIZE =99

            df_new = np.pad(df_new.reshape(-1), (WINDOW_SIZE//2, WINDOW_SIZE//2 +1))
            df_new = np.array([df_new[i:i+WINDOW_SIZE] for i in range(len(df_new)-WINDOW_SIZE)])
            fridge, kettle, microwave, wm = load_models()

            # Make Predictions
            if appliance_name == "washingmachine":
                y_predict = fridge.predict(df_new)
            elif appliance_name == "kettle":
                y_predict = kettle.predict(df_new)
            elif appliance_name == "dishwasher":
                y_predict = wm.predict(df_new)
            else:
                y_predict = microwave.predict(df_new)
        
            y_predict = aggregate_seq(y_predict)
            y_predict = y_predict[:len(df['power'])]
            y_predict = pd.DataFrame(y_predict, columns = ['power'])
            y_predict.set_index(df['timestamp'], inplace=True)

            fig = px.line(y_predict)
            fig_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

        return self.render_template('appliance.html', appliance_name=appliance_name, fig_json=fig_json)
    

    @expose('/appliance/<string:appliance_name>', methods=['POST'])
    def upload_files(self, appliance_name):  
        # Request Validation
        if "file" not in request.files:
            raise Exception("No file uploaded")
        
        if ".csv" not in request.files['file'].filename:
            raise Exception("No csv file uploaded")

        user_id = self.appbuilder.sm.current_user.id
        df = pd.read_csv(request.files.get("file"), sep=";").dropna().reset_index(drop=True)
        df.columns = ["timestamp", "power"]

        # Upload Data to DB
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
    

appbuilder.add_view_no_menu(Home())


@appbuilder.app.errorhandler(404)
def page_not_found(e):
    return (
        render_template(
            "404.html", base_template=appbuilder.base_template, appbuilder=appbuilder
        ),
        404,
    )
