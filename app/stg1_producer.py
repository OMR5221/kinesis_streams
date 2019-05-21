from lib.api.archive_results import GetArchiveValue
from lib.aws_cli import *
from sqlalchemy import (create_engine, MetaData, Table, Column, ForeignKey, select, func, Integer, String, DateTime)
from sqlalchemy.ext.automap import automap_base
import cx_Oracle
from sqlalchemy.orm import (sessionmaker, Session)
from datetime import date, datetime, timedelta
from sqlalchemy.ext.declarative import declarative_base
from pandas import DataFrame, merge
import pandas as pd
import requests
# Parse response for the needed values to load into STG1 table:
from bs4 import BeautifulSoup
import json
import boto3
from boto3 import Session
import uuid
# from botocore.config import Config
import requests
import random


# Define configuration settings that can be used to control the queries that call the process:
INTERVAL = 1 # days
MINUTES = 5 # 60 * 24 = # of minutes in a day


orc_es_dw_engine = create_engine('oracle://SCHEMA_NAME:password@DB')
es_dw_conn = orc_es_dw_engine.connect()

# produce our own MetaData object
es_dw_metadata = MetaData()
es_dw_metadata.reflect(orc_es_dw_engine, only=['es_tags_dim', 'es_plant_dim'])

# we can then produce a set of mappings from this MetaData.
es_dw_base = automap_base(metadata=es_dw_metadata)

# calling prepare() just sets up mapped classes and relationships.
es_dw_base.prepare()

# mapped classes are now created with names by default
# matching that of the table name.
tags_dim = es_dw_base.classes.es_tags_dim
plant_dim = es_dw_base.classes.es_plant_dim

Session = sessionmaker(bind=orc_es_dw_engine)
session = Session()

# Test session access:
pf_recs = session.query(tags_dim.tag_id, tags_dim.tag_name, tags_dim.plant_id, tags_dim.server_name, tags_dim.pi_method).limit(100)

es_tags_dim_res = es_dw_conn.execute("select td.* from ES_TAGS_DIM td JOIN ES_PLANT_DIM pd ON td.PLANT_ID = pd.PLANT_ID AND pd.status = 'A'")

es_tags_df = pd.DataFrame(es_tags_dim_res.fetchall())
es_tags_df.columns = [k.upper() for k in es_tags_dim_res.keys()]

# 3. Expression: Add Time Fields
# Add End_Time, Incremenetal_Time, End_Date_Interpolated
# Using some $$START_TIME Parameter possibly set in configuration file?

minutes_in_timerange = INTERVAL * MINUTES
today = datetime.utcnow().date()
start_dt = datetime.strptime('2018-12-01', '%Y-%m-%d')
# end_dt = datetime(today.year, today.month, today.day)
# start_dt = end_dt - timedelta(days=INTERVAL)

timerange_list = {i: start_dt + timedelta(minutes=i) for i in range(minutes_in_timerange)}

dateranges = []

for key, value in timerange_list.items():
    row = {}
    row['DateId'] = key
    row['DateStr'] = value.strftime('%Y-%m-%d %H:%M:%S')
    row['DateVal'] = value
    # print(row)
    dateranges.append(row)

daterange_df = pd.DataFrame(dateranges)

tags_tf_df = es_tags_df.assign(foo=1).merge(daterange_df.assign(foo=1)).drop('foo', 1)


# 5. HTTP Extract:
# Make respective calls to the API
# MAKE SOAP REQUEST: GetArchiveValue

firehose_stream_name = 'esbi_fh'
interval = 1500

#val_dict = dict.fromkeys(['SERVERNAME','TAGNAME','TIMESTAMP','VALUE', 'VALUESTRING'])
output_headers = ('SERVERNAME', 'TAGNAME', 'TIMESTAMP', 'VALUE', 'VALUESTRING')
final_out = []
final_out.append(output_headers)

delim = ','
firehose = boto3.client('firehose', region_name='us-east-1')

records = []

num_rows = tags_tf_df.shape[0]
write_count = min(10000, (num_rows * 0.10))

for index, rec in tags_tf_df.iterrows():

    print(str(index))

    u = GetArchiveValue(rec['SERVER_NAME'], rec['TAG_NAME'], rec['DateStr'])

    try:
        pi_resp = u.post()
        putString = str(rec['SERVER_NAME'] + delim + rec['TAG_NAME'] + delim + rec['DateStr'] + delim + pi_resp.body.value.text + delim + pi_resp.body.valuestring.text + "\n")
        # print(putString)
        records.append({'Data': putString.encode('utf-8')})

        if (int(index) > 0 and int(index) % write_count == 0) or (num_rows-1) == int(index):
            print('WRITING TO S3:')
            try:
                response = firehose.put_record_batch(DeliveryStreamName=firehose_stream_name, Records=records) #, PartitionKey=part_key)
                print(response)
                print('WROTE TO FIREHOSE')
                records = []
            except:
                print('ERROR: Failed to write to S3')
    except:
        continue
