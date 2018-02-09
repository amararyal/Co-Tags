
#Run Kafka producer
peg sshcmd-node kafka-cluster 1 "python /home/ubuntu/producer.py &" 
# Run spark-streaming script 
peg sshcmd-node spark-cluster 1 "/usr/local/spark/bin/spark-submit --master spark://ip-10-0-0-13.ec2.internal:7077 --packages org.apache.spark:spark-streaming-kafka-0-8_2.11:2.0.2 spark_streaming.py &"
# Run Flask 
peg sshcmd-node cassandra-cluster 1 "python -E /usr/home/Flask/tornadoapp.py"
