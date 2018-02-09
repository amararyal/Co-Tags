# Install Hadoop and Spark
CLUSTER_NAME=spark-cluster
peg fetch ${CLUSTER_NAME}
# Set up Passwordless Connection
peg install ${CLUSTER_NAME} ssh
# install all environment 
peg install $(CLUSTER_NAME) environment
peg install ${CLUSTER_NAME} aws
wait
#Install Hadoop and Spark
peg install ${CLUSTER_NAME} hadoop
peg install ${CLUSTER_NAME} spark



# Install Kafka
CLUSTER_NAME1=kafka-cluster
peg fetch ${CLUSTER_NAME1}
# Set up Passwordless Connection
peg install ${CLUSTER_NAME1} ssh
# install all environment 
peg install $(CLUSTER_NAME1) environment
peg install ${CLUSTER_NAME1} aws
wait
#Install Zookeeper and Kafka
peg install ${CLUSTER_NAME1} Zookeeper
peg install ${CLUSTER_NAME1} Kafka



#Install Cassandra
CLUSTER_NAME2=cassandra-cluster
peg fetch ${CLUSTER_NAME2}
# Set up Passwordless Connection
peg install ${CLUSTER_NAME2} ssh
# install all environment 
peg install $(CLUSTER_NAME2) environment
peg install ${CLUSTER_NAME2} aws
wait
#Install Cassandra
peg install ${CLUSTER_NAME} Cassandra




