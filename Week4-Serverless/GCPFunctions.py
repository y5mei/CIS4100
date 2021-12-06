"""
This is typically what a storage-triggerd GCP function get as a input variable
bucket:    cis4010-ymei
contentType:    image/jpeg
crc32c:    5NWKRg==
etag:    CJKy2fHYo/QCEAE=
generation:    1637299753736466
id:    cis4010-ymei/food.JPG/1637299753736466
kind:    storage#object
md5Hash:    3bWz92FI1vzlk/ket6yGgg==
mediaLink:    https://www.googleapis.com/download/storage/v1/b/cis4010-ymei/o/food.JPG?generation=1637299753736466&alt=media
metageneration:    1
name:    food.JPG
selfLink:    https://www.googleapis.com/storage/v1/b/cis4010-ymei/o/food.JPG
size:    79386
storageClass:    STANDARD
timeCreated:    2021-11-19T05:29:13.800Z
timeStorageClassUpdated:    2021-11-19T05:29:13.800Z
updated:    2021-11-19T05:29:13.800Z
"""


"""
Need the following in the requirement.txt file
google-cloud-storage
datetime
"""


from datetime import datetime
from google.cloud import storage
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



def hello_gcs(event, context):
    """Triggered by a change to a Cloud Storage bucket.
    Args:
         event (dict): Event payload.
         context (google.cloud.functions.Context): Metadata for the event.
    """
    file = event
    string_event = json_dict_flater(event)
    source_bucket_name = event["bucket"]
    source_file_name = event["name"]

    # make a log file:
    time_stamp = str(datetime.now()).replace(" ", "_").replace(":", "-")
    log_file_name = "Archive/"+time_stamp+".txt"

    logfile_content = ""
    logfile_content += "==========================================\n"
    logfile_content += "====== New File Added to Bucket ==========\n"
    logfile_content += "==========================================\n"
    logfile_content += "bucket_name: " + source_bucket_name + "\n"
    logfile_content += "==========================================\n"
    logfile_content += "file_name: " + source_file_name + "\n"
    logfile_content += "==========================================\n"
    logfile_content += "==========================================\n"
    logfile_content += "========== Detailed Info Below ===========\n"
    logfile_content += "==========================================\n"
    logfile_content += json_dict_flater(event)
    logfile_content += "==========================================\n"
    logfile_content += "==========================================\n"
    logfile_content += "==========================================\n"

    # copy the original file to the destination bucket
    storage_client = storage.Client()

    source_bucket = storage_client.get_bucket(source_bucket_name)
    source_blob = source_bucket.blob(source_file_name)

    dst_bucket_name = "cis4010-ymei-log"
    dst_bucket = storage_client.get_bucket(dst_bucket_name)
    dst_file_name = "archive_" + source_file_name

    # make the copy
    dst_blob = source_bucket.copy_blob(source_blob, dst_bucket, new_name=dst_file_name)

    # delete the source file
    # source_bucket.delete_blob(source_file_name)

    # save a log file in the dist bucket
    log_file_blob = dst_bucket.blob(log_file_name)
    log_file_blob.upload_from_string("logfile_content")

    # save another log in the log console
    print(f"Processing file: {file['name']}.")
    print("=====================================")
    print(logfile_content)

if __name__ == '__main__':
    print("Unit Test")