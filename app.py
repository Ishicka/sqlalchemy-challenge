import numpy as np 
import sqlalchemy
import datetime as dt
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify 
from typing import Union, Dict

#################################################
# Database Setup
#################################################
# create engine to hawaii.sqlite
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables

Base.prepare(engine, reflect=True)


# Save references to each table
Station = Base.classes.station
Measurement = Base.classes.measurement
# Create our session (link) from Python to the DB
session = Session(engine)


#################################################
# Flask Setup
#################################################
app = Flask(__name__)


#################################################
# Flask Routes
#################################################
@app.route('/')
def home():
    return (
        "Welcome to the Climate App! Available routes:\n"
        "/api/v1.0/precipitation\n"
        "/api/v1.0/stations\n"
        "/api/v1.0/tobs\n"
        "/api/v1.0/<start>\n"
        "/api/v1.0/<start>/<end>"
    )
@app.route("/api/v1.0/precipitation")
def precipitation():

    prep_scores = session.query(Measurement.date, Measurement.prcp).all()

    precipitation = []
    for date, prcp in prep_scores:
        precipitationDict = {}
        precipitationDict["date"] = date
        precipitationDict["precipitation"] = prcp 
        precipitation.append(precipitationDict)

    return jsonify(precipitation)


@app.route("/api/v1.0/stations")
def stations():

    total_stat = session.query(Station.station, Station.name).all()

    stations = []
    for station, name in total_stat:
        stationDict = {}
        stationDict["station"] = station 
        stationDict["name"] = name 
        stations.append(stationDict)

    return jsonify(stations)


@app.route("/api/v1.0/tobs")
def tobs():
    most_act_stat = session.query(Measurement.date, Measurement.station, Measurement.tobs) \
        .group_by(Measurement.station) \
        .order_by(func.count(Measurement.tobs).desc()).first()[0]

    twelve_month_data = session.query(Measurement.date, Measurement.station, Measurement.tobs) \
        .filter(Measurement.station == most_act_stat) \
        .filter(Measurement.date >= func.date_sub(func.now(), dt.timedelta(days=365))).all()

    tobs_ = []
    for date, station, tobs in twelve_month_data:
        tobsDict = {}
        tobsDict["date"] = date
        tobsDict["station"] = station
        tobsDict["tobs"] = tobs
        tobs_.append(tobsDict)

    return jsonify(tobs_)

# Calculate latest_date globally
latest_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()[0]

# Flask Routes
@app.route("/api/v1.0/<start>")
def start_route(start: str):
    """Return temperature data from the `start` date to the end of the data set.

    :param start: string start date in YYYY-MM-DD form
    :return: json data
    """
    # no date is after MOST_RECENT_DATE, so it can be the end date
    data = temperature_date_range_data(start, latest_date)
    return jsonify(data)

@app.route("/api/v1.0/<start>/<end>")
def start_end_range_route(start: str, end: Union[str, dt.date]):
    """Return temperature data in the date range `start` to `end`.

    :param start: string start date in YYYY-MM-DD form
    :param end: string end date in YYYY-MM-DD form
    :return: json data
    """
    data = temperature_date_range_data(start, end)
    return jsonify(data)

def temperature_date_range_data(start: str, end: Union[str, dt.date]) -> Dict[str, float]:
    """Calculates the Min, Max, Average of temperatures in the date range `start` to `end`.

    :param start: string start date in YYYY-MM-DD form
    :param end: string end date in YYYY-MM-DD form
    :return: dictionary containing temperature statistics
    """
    temp_data = session.query(func.min(Measurement.tobs).label("TMIN"),
                              func.max(Measurement.tobs).label("TMAX"),
                              func.avg(Measurement.tobs).label("TAVG"))\
                        .filter(Measurement.date >= start, Measurement.date <= end)\
                        .one()
    
    data = {"TMIN": temp_data.TMIN, "TMAX": temp_data.TMAX, "TAVG": temp_data.TAVG}
    return data



if __name__ == "__main__":
    app.run(debug=True)
