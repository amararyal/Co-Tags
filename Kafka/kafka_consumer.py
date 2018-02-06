from kafka import KafkaConsumer, KafkaClient
import sys
import getopt
import json
from pprint import pformat
import uuid
from neo4j.v1 import GraphDatabase, basic_auth, TRUST_ON_FIRST_USE, CypherError
from ast import literal_eval as make_tuple
import numpy
import time
import pandas as pd



def kafka_consume_batch(consumer, batch_size):
    starttime = time.time()
    batch_dict = {}
    batch_liste = []
    batch_msg_consumed = 0
    for msg in consumer:
        if batch_msg_consumed >= batch_size:
	    print('break True')
            break
	a=make_tuple(msg[6])
	count=int(a[1])
	lista=[[a[0][0],a[0][1],count]]
	batch_liste.extend(lista)
	lista=[]
        batch_msg_consumed += 1
    return(batch_liste, batch_msg_consumed)


def kafka_consumer_performance(LOOP_LENGTH, topic):
    msg_consumed_count = 0
    batch_size = 2000
    batch_list = []
    nodes = 0
    rels = 0

    driver = GraphDatabase.driver("bolt://ec2-34-230-121-21.compute-1.amazonaws.com:7687",auth=basic_auth("neo4j", "123"),encrypted=False,trust=TRUST_ON_FIRST_USE)
    consumer = KafkaConsumer(bootstrap_servers='ec2-34-224-210-199.compute-1.amazonaws.com',auto_offset_reset='latest')
    consumer_start = time.time()

    # Subscribe to topics
    consumer.subscribe([topic])

    # consumer loop
    try:

        session = driver.session()
        while True:
            # Neo4j Graph update loop using Bolt
            try:
                batch_list, batch_msg_consumed = kafka_consume_batch(consumer, batch_size)
		#df = pd.DataFrame(batch_list)
                msg_consumed_count += batch_msg_consumed
	        with session.begin_transaction() as tx:
                    update_query = '''WITH {batch_list} AS batch_list
                                        UNWIND batch_list AS rows
                                        WITH rows, rows[0] AS Name
                                        MERGE (w:Word {name: rows[0]})
                                        ON MATCH SET w.value = w.value + rows[2] ON CREATE SET w.value = rows[2]
                                        MERGE (n:Word {name: rows[1]})
                                        ON MATCH SET n.value = n.value+ rows[2] ON CREATE SET w.value = rows[2]
                                        MERGE (w)-[r:OCCURS_WITH]-(n)
                                        ON MATCH SET r.frequency = r.frequency + rows[2] ON CREATE SET r.frequency = rows[2];
                                        '''

                    result = tx.run(update_query, {"batch_list": batch_list})
                    if msg_consumed_count >= LOOP_LENGTH:
                   	consumer.close()
                    	print(time.time() - consumer_start)
                   	break
            except CypherError as error:
		print("Error is: " + error.code)
                consumer.close()
    except CypherError as error:
        consumer.close()
        print('Error is: ' + error.code)

kafka_consumer_performance(2000000,"groups_count")

