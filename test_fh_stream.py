import boto3
from boto3 import Session


def get_or_create_fh(fh_name):
    stream = None
    try:
        stream = kinesis.describe_stream(stream_name)
        print (json.dumps(stream, sort_keys=True, indent=2,
            separators=(',', ': ')))
    except ResourceNotFoundException as rnfe:
        while (stream is None) or ('ACTIVE' not in stream['StreamDescription']['StreamStatus']):
            if stream is None:
                print ('Could not find ACTIVE stream:{0} trying to create.'.format(
                    stream_name))
                kinesis.create_stream(stream_name, shard_count)
            else:
                print ("Stream status: %s" % stream['StreamDescription']['StreamStatus'])
            time.sleep(1)
            stream = kinesis.describe_stream(stream_name)

    return stream


firehose_stream_name = 'esbi_fh'
interval = 1500
count = 100


fh_client = boto3.client('firehose', region_name='us-east-1')

response = fh_client.list_delivery_streams(
    Limit=123,
    DeliveryStreamType='DirectPut',
    ExclusiveStartDeliveryStreamName='string'
)

print(response)
