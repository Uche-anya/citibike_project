import sys
import os
import pytest

sys.path.append(os.getcwd())

# Returning a Spark session fixture for testing
@pytest.fixture()
def spark():
   try:
        from databricks.connect import DatabricksSession
        spark = DatabricksSession.builder.getOrCreate()
   except ImportError:
        try:
            from pyspark.sql import SparkSession
            spark = SparkSession.builder.getOrCreate()
        except:
            raise ImportError("Could not import SparkSession or DatabricksSession. Ensure PySpark is installed and configured correctly.")
   return spark