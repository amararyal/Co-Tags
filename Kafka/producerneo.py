/* This Code is responsible for reading and playing the static archived file to simulate streaming.
Multiple processes are used to read the input file in Chunk */

# Import Statements
from twitter import *
from kafka.producer import KafkaProducer
import multiprocessing as mp,os,json
import json
import re
from random import randint


def process_wrapper(chunkStart, chunkSize):
     producer = KafkaProducer(bootstrap_servers='ec2-34-235-173-226.compute-1.amazonaws.com')
     with open('twitter.txt') as f:
        f.seek(chunkStart)
        lines = f.read(chunkSize).splitlines()
        empty_tweet=0
        for line in lines:
            loaded_json = json.loads(line)
            tags_list=[]
            hash_tags=loaded_json['entities']['hashtags']
	   # print(hash_tags)
            try:
                for ele in hash_tags:
		    if re.match("^[A-Za-z0-9_-]*$", ele['text']):
                    	tags_list.append(ele['text'].lower())
		if len(tags_list)==0:
                    pass
                else:
                    tweet_tags={'hashtags':tags_list}
                    producer.send('twitter_stream', json.dumps(tweet_tags).encode('utf-8'))
            except:
                empty_tweet+=1

def chunkify(fname,size=1024*1024):
    fileEnd = os.path.getsize(fname)
    with open(fname,'r') as f:
        chunkEnd = f.tell()
        while True:
            chunkStart = chunkEnd
            f.seek(size,1)
            f.readline()
            chunkEnd = f.tell()
            yield chunkStart, chunkEnd - chunkStart
            if chunkEnd > fileEnd:
                break

#init objects
pool = mp.Pool(12)
jobs = []

#create jobs
for chunkStart,chunkSize in chunkify('twitter.txt'):
    jobs.append( pool.apply_async(process_wrapper,(chunkStart,chunkSize)) )

#wait for all jobs to finish
for job in jobs:
    job.get()

#clean up
pool.close()
