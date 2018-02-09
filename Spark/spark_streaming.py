from __future__ import print_function
import os
os.environ['PYSPARK_SUBMIT_ARGS'] = '--packages org.apache.spark:spark-streaming-kafka-0-8_2.11:2.0.2 pyspark-shell'
import sys
import json
import time
import threading
from pyspark import SparkContext
from pyspark.streaming import StreamingContext
from pyspark.streaming.kafka import KafkaUtils
import re, itertools
from cassandra.cluster import Cluster
from functools import partial
from itertools import combinations
from kafka import KafkaProducer, KafkaClient

def group(tags_list):
    tags_list=set(tags_list)
    groups=itertools.combinations(tags_list,2)
    tag_groups=[i for i in groups]
    return tag_groups

def send_to_kafka(val,topic):
    for ele in val:
        producer.send(topic, bytes(ele))


def save_results(time, rdd):
    num_of_record = rdd.count()
    if num_of_record == 0:
        return
    for hash_frequency in rdd.take(10):
        count=hash_frequency[1]
        hash1=hash_frequency[0][0]
        hash2=hash_frequency[0][1]
        session.execute(to_cassandra,(time, hash1,hash2,count))
    
def re_order(x,y):
    x=x.lower()
    y=y.lower()
    if x>y:
        return (y,x)
    else:
        return (x,y)
    

# List all the Kafka Brokers
brokers = "Your Kafka Brokers Public DNS"

# List the Topics
topics = "twitter_stream"

# Specify the Cassandra Master
cassandra_master = "Your Cassandra Public DNS"

#Create Cassandra Cluster
cluster = Cluster([cassandra_master])

#Create Session
session=cluster.connect()

#Create Keyspace if not exist
create_keyspace = "CREATE KEYSPACE IF NOT EXISTS TWORK WITH REPLICATION = {'class' : 'SimpleStrategy','replication_factor' : 3}"
session.execute(create_keyspace)


create_table = session.prepare("CREATE TABLE IF NOT EXISTS TWORK.tweet(time timestamp, hash1 text, hash2 text, count int, PRIMARY KEY  ((hash1,hash2),time)) WITH CLUSTERING ORDER BY (time DESC);") 

#Create Table
session.execute(create_table)

#Preapare Creating Insert Statement
to_cassandra = session.prepare("INSERT INTO TWORK.tweet(time,hash1,hash2,count) VALUES (?,?,?,?)USING TTL 7776000")

#Initialize SparkContext
sc = SparkContext(appName="TrendingHashTags")
ssc = StreamingContext(sc, 1)
sc.setLogLevel('ERROR')

# get stream data from kafka
kafkaStream = KafkaUtils.createDirectStream(ssc, [topics], {"metadata.broker.list": brokers})
tweet_parsed = kafkaStream.map(lambda v: json.loads(v[1].decode('utf-8'))) \
.map(lambda v: v['hashtags'])

#Count the number of messages in the current Batch
count=tweet_parsed.count()

#batch_count topic for total number of tweets in a batch
count.foreachRDD(lambda x: send_to_kafka(x.collect(),"batch_count"))

# Group the hashtags
tweet_tag_groups=tweet_parsed.map(lambda x: group(x))
tweet_only_tags=tweet_tag_groups.filter(lambda x: x<> [] and x<> None)

#Reorder and Flatten the RDD
hash_tags_as_flat_map=tweet_only_tags.flatMap(lambda x:x) \
.map(lambda (x,y):re_order(x,y)) \
.map(lambda (x,y): ((x,y),1))

#Aggregate and Count the hash_tags
aggregated_hashtags=hash_tags_as_flat_map.reduceByKey(lambda x,y:int(x)+int(y))

#Sort the Aggregrated groups according to Count
sorted_groups=aggregated_hashtags.transform \
(lambda rdd:rdd.sortBy(lambda x: x[1],ascending= False))

#Send the results back to Central Kafka Broker
producer = KafkaProducer(bootstrap_servers='Your Kafka Node Public DNS')
sorted_groups.foreachRDD(lambda x: send_to_kafka(x.collect(),"groups_count"))
# Topic trending_tags_pair  for sending trending tags only
sorted_groups.foreachRDD(lambda x: send_to_kafka(x.take(5),"trending_tags_pair"))

# Push data to Cassandra
sorted_groups.foreachRDD(save_results)

ssc.start()
ssc.awaitTermination()
