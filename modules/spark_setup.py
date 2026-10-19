import os
import sys
import pyspark
from pyspark.sql import SparkSession


def get_spark(app_name="IND320"):
    env = {
        "JAVA_HOME": r"C:\Program Files\Microsoft\jdk-17.0.20.101-hotspot",
        "SPARK_HOME": os.path.dirname(pyspark.__file__),
        "PYSPARK_PYTHON": sys.executable,
        "PYSPARK_DRIVER_PYTHON": sys.executable,
        "TEMP": r"C:\tmp",
        "TMP": r"C:\tmp",
        "HADOOP_HOME": r"C:\hadoop\hadoop-3.3.1",
        "SPARK_LOCAL_IP": "127.0.0.1",
    }
    os.environ.update(env)
    os.environ["PATH"] = env["HADOOP_HOME"] + r"\bin;" + os.environ["PATH"]
    os.makedirs(r"C:\tmp", exist_ok=True)   # Spark trenger mappen

    conf = {
        "spark.jars.packages": "com.datastax.spark:spark-cassandra-connector_2.12:3.5.1",
        "spark.cassandra.connection.host": "localhost",
        "spark.cassandra.connection.port": "9042",
        "spark.sql.extensions": "com.datastax.spark.connector.CassandraSparkExtensions",
        "spark.sql.catalog.mycatalog": "com.datastax.spark.connector.datasource.CassandraCatalog",
        "spark.driver.host": "127.0.0.1",
        "spark.sql.execution.arrow.pyspark.enabled": "true",
    }

    builder = SparkSession.builder.appName(app_name)
    for key, value in conf.items():
        builder = builder.config(key, value)
    return builder.getOrCreate()