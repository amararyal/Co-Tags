#!/bin/bash
#Install Pegasus https://github.com/InsightDataScience/pegasus
#Set up Spark <masters.yml and workers.yml contain the information about Spark Cluster>
peg up master.yml
peg up woarkers.yml

#Set Up Kafka
peg up kafka.yml

#Set Up Cassandra
peg up cassandra.yml
