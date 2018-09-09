import os
import re
from flask import Flask, jsonify, render_template, request
import json

from cs50 import SQL
from helpers import lookup

# Configure application
app = Flask(__name__)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///mashup.db")

os.system("export API_KEY=AIzaSyArL_E9_1GeRdHh5E4d2bIuC_xAppp6s04")
print (os.environ.get("API_KEY"))

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
def index():
    """Render map"""
    if not os.environ.get("API_KEY"):
        raise RuntimeError("API_KEY not set")
    return render_template("index.html", key=os.environ.get("API_KEY"))


@app.route("/articles")
def articles():
    """Look up articles for geo"""
    if request.method == "GET":
        return jsonify(lookup(request.args.to_dict()["geo"]))


@app.route("/search")
def search():
    """Search for places that match query"""

    # TODO
    if request.method == "GET":
        print (request.args.get('q'))
        qs = request.args.get('q')
        qs = qs.split(',')
        new_qs = []
        rows = []
        for q in qs:
            new_qs.append(q.strip()) # = requires q exactly equal to a postal code which isnt all that compelling for autocomplete

        #用参数列表的第一个参数尝试模糊查询数据库的其中五列，得到字典组成的列表
        rows = db.execute("SELECT * FROM places WHERE postal_code LIKE :q OR coutry_code LIKE :q OR place_name LIKE :q OR admin_name1 LIKE :q OR \
        admin_code1 LIKE :q", q = new_qs[0]+"%")

        #删除第一个参数，用剩余参数对上一步加载的列表中的字典进行筛查，字典中存在以某参数开头的值时保留该字典，否则从列表中删除
        new_qs.pop(0)
        count = len(rows)
        if count != 0:
            for j in range(len(new_qs)):
                i = 0
                while (i<count):
                    if rows[i]["postal_code"].startswith(new_qs[j]) or rows[i]["coutry_code"].startswith( new_qs[j]) or rows[i]["place_name"].startswith(new_qs[j]) \
                    or rows[i]["admin_name1"].startswith(new_qs[j]) or rows[i]["admin_code1"].startswith(new_qs[j]):
                        i += 1
                    else:
                        rows.pop(i)
                        count -= 1


        return jsonify(rows)


@app.route("/update")
def update():
    """Find up to 10 places within view"""

    # Ensure parameters are present
    if not request.args.get("sw"):
        raise RuntimeError("missing sw")
    if not request.args.get("ne"):
        raise RuntimeError("missing ne")

    # Ensure parameters are in lat,lng format
    if not re.search("^-?\d+(?:\.\d+)?,-?\d+(?:\.\d+)?$", request.args.get("sw")):
        raise RuntimeError("invalid sw")
    if not re.search("^-?\d+(?:\.\d+)?,-?\d+(?:\.\d+)?$", request.args.get("ne")):
        raise RuntimeError("invalid ne")

    # Explode southwest corner into two variables
    sw_lat, sw_lng = map(float, request.args.get("sw").split(","))

    # Explode northeast corner into two variables
    ne_lat, ne_lng = map(float, request.args.get("ne").split(","))

    # Find 10 cities within view, pseudorandomly chosen if more within view
    if sw_lng <= ne_lng:

        # Doesn't cross the antimeridian
        rows = db.execute("""SELECT * FROM places
                          WHERE :sw_lat <= latitude AND latitude <= :ne_lat AND (:sw_lng <= longitude AND longitude <= :ne_lng)
                          GROUP BY coutry_code, place_name, admin_code1
                          ORDER BY RANDOM()
                          LIMIT 10""",
                          sw_lat=sw_lat, ne_lat=ne_lat, sw_lng=sw_lng, ne_lng=ne_lng)

    else:

        # Crosses the antimeridian
        rows = db.execute("""SELECT * FROM places
                          WHERE :sw_lat <= latitude AND latitude <= :ne_lat AND (:sw_lng <= longitude OR longitude <= :ne_lng)
                          GROUP BY coutry_code, place_name, admin_code1
                          ORDER BY RANDOM()
                          LIMIT 10""",
                          sw_lat=sw_lat, ne_lat=ne_lat, sw_lng=sw_lng, ne_lng=ne_lng)

    # Output places as JSON
    print ("update called")
    print (len(rows))
    return jsonify(rows)
