from app import app
from flask import Flask, jsonify, render_template, request, redirect
import time, math
from kafka import KafkaConsumer, KafkaClient
from ast import literal_eval as make_tuple
from cassandra.cluster import Cluster
# Specify the Cassandra Master
cassandra_masters = "Your Cassandra Node Public DNS"
#Create Cassandra Cluster
cluster = Cluster([cassandra_masters])

#Create Session
session=cluster.connect()

#Time Series Analysis
@app.route('/_timeseries')
def timeseries():
    """Retrieve time series for currKey"""
    cumulative = []
    hashtags = []
    count = 0
    consumer = KafkaConsumer(group_id='my-group',bootstrap_servers ='Your Kafka Public DNS',auto_offset_reset='latest')
    consumer.subscribe(['batch_count'])
    for msg in consumer:
        cumulative.append(int(msg[6].decode('utf-8')))
        break
    consumer.subscribe(['trending_tags_pair'])
    for msg in consumer:
        pair=[]
        count += 1
	a=msg[6].decode('utf-8')
	a=make_tuple(a)	
        pair=[((a[0][0],a[0][1]),a[1])]
        hashtags.append(pair)
        if count == 3:
            break
    hashtags=hashtags[::-1]
    consumer.close()
    return jsonify(cumulative = cumulative,hashtags = hashtags)

# returns slide deck as redirect for easy access
@app.route('/deck')
def deck():
 return redirect("https://docs.google.com/presentation/d/1suRGQ3mCASmHuDNGnU6hPWPI64X99RdQH8F4CL4J15Q/edit#slide=id.p3")


@app.route('/searchresults', methods=['POST'])
def email_post():
    start_date = request.form['start_date']
    end_date = request.form['end_date']
    hash_tag=request.form['hash_tag']
    stmt = "SELECT hash2, sum(count)  FROM TWORK.tweet  WHERE time >= %s and time <= %s and  hash1 =%s GROUP BY hash2 ALLOW FILTERING;"
    response = session.execute(stmt, parameters=[start_date,end_date, hash_tag])
    dict={}
    taglist=[]
    for ele in response:
        val={'hash2':ele[0],'count':ele[1]}
        taglist.append(val)
    sortedList=sorted(taglist,key=lambda x:x['count'],reverse=True)
    print(sortedList)
    return render_template("search.html", output=sortedList)



@app.route('/searchresults')
@app.route('/')
@app.route('/index.html')
def index():
    return render_template('index.html')
