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

def counts(rdd):
    num_records=rdd.count()
    print(num_records)

def group(tags_list):
    tags_list=set(tags_list)
    groups=itertools.combinations(tags_list,2)
    tag_groups=[i for i in groups]
    #print(tag_groups)
    return tag_groups

def send_to_kafka(val,topic):
    for ele in val:
        producer.send(topic, bytes(ele))


def save_results(time, rdd):
    num_of_record = rdd.count()
    if num_of_record == 0:
        return
    time=time
    

    trending= rdd.take(10)
    for elements in trending:
        print(elements)

    for hash_frequency in rdd.take(10):
        #hash_grp=str(hash_frequency[0][0])+ ", "+str(hash_frequency[0][1])
        count=hash_frequency[1]
        hash1=hash_frequency[0][0]
        hash2=hash_frequency[0][1]
        session.execute(to_cassandra,(time, hash1,hash2,count))
    max_time=session.execute("SELECT MAX(time) FROM TWORK.tweet")
    maxitm=max_time[0][0]
    print('max=',maxitm)
    
def re_order(x,y):
    x=x.lower()
    y=y.lower()
    if x>y:
        return (y,x)
    else:
        return (x,y)
    

# List all the Kafka Brokers
brokers = "ec2-34-224-210-199.compute-1.amazonaws.com:9092,ec2-52-5-190-49.compute-1.amazonaws.com:9092,ec2-34-235-173-226.compute-1.amazonaws.com:9092"

# List the Topics
topics = "twitter_stream"

# Specify the Cassandra Master
cassandra_master = "ec2-34-195-160-149.compute-1.amazonaws.com"

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

# InitialcountoDEtex
sc = SparkContext(appName="TrendingHashTags")
ssc = StreamingContext(sc, 1)
sc.setLogLevel('ERROR')

# get stream data from kafka
kafkaStream = KafkaUtils.createDirectStream(ssc, [topics], {"metadata.broker.list": brokers})
tweet_parsed = kafkaStream.map(lambda v: json.loads(v[1].decode('utf-8'))) \
.map(lambda v: v['hashtags'])#.cache()
#tweet_parsed.pprint()
count=tweet_parsed.count()
count.pprint()
#tweet_parsed.foreachRDD(counts)
#batch_count topic for total number of tweets in a batch
count.foreachRDD(lambda x: send_to_kafka(x.collect(),"batch_count"))
tweet_tag_groups=tweet_parsed.map(lambda x: group(x))#.cache()
tweet_only_tags=tweet_tag_groups.filter(lambda x: x<> [] and x<> None)#.cache()
hash_tags_as_flat_map=tweet_only_tags.flatMap(lambda x:x) \
.map(lambda (x,y):re_order(x,y)) \
.map(lambda (x,y): ((x,y),1))#.cache()
#hash_tags_as_flat_map.pprint()

aggregated_hashtags=hash_tags_as_flat_map.reduceByKey(lambda x,y:int(x)+int(y))#.cache()#.map(lambda (x,y):(y,x)).cache()

#Sort the Aggregrated groups
sorted_groups=aggregated_hashtags.transform \
(lambda rdd:rdd.sortBy(lambda x: x[1],ascending= False))
#sorted_groups.pprint()
#To kafka
producer = KafkaProducer(bootstrap_servers='ec2-34-235-173-226.compute-1.amazonaws.com')
sorted_groups.foreachRDD(lambda x: send_to_kafka(x.collect(),"groups_count"))
#trending_tags_pair topic for sending trending tags only
sorted_groups.foreachRDD(lambda x: send_to_kafka(x.take(5),"trending_tags_pair"))
sorted_groups.foreachRDD(save_results)
ssc.start()
ssc.awaitTermination()
