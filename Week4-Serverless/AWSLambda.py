import json
import urllib.parse
import boto3
from datetime import datetime

print('Loading function')

s3 = boto3.client('s3')


# return a string of a flattend json dict
def json_dict_flater(d: dict, prefix=""):
    result = ""
    if not d:
        return result
    if type(d) is dict:
        for k in d:
            if not d[k]:  # if the value is empty
                d[k] = "Null"
            if type(d[k]) is list:  # if the value is a list of dictionary
                for i in d[k]:
                    result += json_dict_flater(i, prefix=str(k))
            elif type(d[k]) is not dict:  # if the value is just a string
                if not prefix:
                    header = str(k)
                else:
                    header = prefix + "___" + str(k)
                result += header + ":    " + str(d[k]) + "\n"
            else:
                result += json_dict_flater(d[k], prefix=str(k))  # if the value is a dictionary
    return result


# create a log file under the bucket's logfile folder
# using the resouce.Object() command to create the file objectr
# using the Object.put() command to put content into the logfile
def create_a_log_file(content, bucket_name, log_file_folder="logfile/"):
    time_stamp = str(datetime.now()).replace(" ", "_").replace(":", "-")
    s3 = boto3.resource("s3")
    object = s3.Object(bucket_name, log_file_folder + time_stamp + ".txt")
    object.put(Body=content)


# move a new created file to a backup folder
# using the Obbject.copy_from() command to make a copy
# using the Object.delete() command to delete the source file
def copy_to_backup_bucket(source_bucket, source_filename):
    distnation_bucket = source_bucket + "-backup"
    distnation_filename = source_filename

    # copy to distnation
    s3 = boto3.resource("s3")
    # create a source dictionary for the object that need to be copied
    copy_source = {
        'Bucket': source_bucket,
        'Key': source_filename,
    }
    # paste to the distnation bucket
    dist_bucket = s3.Bucket(distnation_bucket)
    dist_bucket.copy(copy_source, distnation_filename)


def lambda_handler(event, context):
    # print(type(event)) => Dict
    # print(type(context)) => LambdaContext
    # print("Received event: " + json.dumps(event, indent=2))

    # Get the object from the event and show its content type
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')

    try:
        # create a log file, under the logfile folder
        # must add an exception for the logfile
        if "logfile/" not in key:
            response = s3.get_object(Bucket=bucket, Key=key)

            logfile_content = ""
            logfile_content += "==========================================\n"
            logfile_content += "====== New File Added to Bucket ==========\n"
            logfile_content += "==========================================\n"
            logfile_content += "bucket_name: " + bucket + "\n"
            logfile_content += "==========================================\n"
            logfile_content += "file_name: " + key + "\n"
            logfile_content += "==========================================\n"
            logfile_content += "==========================================\n"
            logfile_content += "========== Detailed Info Below ===========\n"
            logfile_content += "==========================================\n"
            logfile_content += json_dict_flater(event)
            logfile_content += "==========================================\n"
            logfile_content += "==========================================\n"
            logfile_content += "==========================================\n"

            create_a_log_file(logfile_content, bucket)  # create a log file
            copy_to_backup_bucket(bucket, key)  # make a copy of the file to backup bucket

            print("CONTENT TYPE: " + response['ContentType'])
        return response['ContentType']
    except Exception as e:
        print(e)
        print(
            'Error getting object {} from bucket {}. Make sure they exist and your bucket is in the same region as this function.'.format(
                key, bucket))
        raise e


if __name__ == '__main__':
    print("Unit Test")
    event = {'Records': [{'eventVersion': '2.0', 'eventSource': 'aws:s3', 'awsRegion': 'us-east-1', 'eventTime': '1970-01-01T00:00:00.000Z', 'eventName': 'ObjectCreated:Put', 'userIdentity': {'principalId': 'EXAMPLE'}, 'requestParameters': {'sourceIPAddress': '127.0.0.1'}, 'responseElements': {'x-amz-request-id': 'EXAMPLE123456789', 'x-amz-id-2': 'EXAMPLE123/5678abcdefghijklambdaisawesome/mnopqrstuvwxyzABCDEFGH'}, 's3': {'s3SchemaVersion': '1.0', 'configurationId': 'testConfigRule', 'bucket': {'name': 'cis4010-test', 'ownerIdentity': {'principalId': 'EXAMPLE'}, 'arn': 'arn:aws:s3:::example-bucket'}, 'object': {'key': 'pic001.png', 'size': 1024, 'eTag': '0123456789abcdef0123456789abcdef', 'sequencer': '0A1B2C3D4E5F678901'}}}]}
    # lambda_handler(event, None)
    r = json_dict_flater(event)
    time_stamp = str(datetime.now()).replace(" ","_").replace(":","-")
    print(time_stamp)
    print(r)