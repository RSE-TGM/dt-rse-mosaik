import io
from minio import Minio
import glob
import os
from minio.error import  S3Error

# Create client with anonymous access.
client = Minio("localhost:9000", access_key="4K10mbUN3FxVsDxtDYSh", secret_key="sI0zu0b4DlR2Vs0JyO6KhJZzws1w5eL1GzthLtPD", secure=False)



result = client.put_object(
    "sda-dt", "my-object", io.BytesIO(b"hello"), 5,
)
print(
    "created {0} object; etag: {1}, version-id: {2}".format(
        result.object_name, result.etag, result.version_id,
    ),
)



MINIO_ENDPOINT = "localhost:9000"
MINIO_ACCESS_KEY = "4K10mbUN3FxVsDxtDYSh"
MINIO_SECRET_KEY = "sI0zu0b4DlR2Vs0JyO6KhJZzws1w5eL1GzthLtPD"
MINIO_SECURE = False

class MinioClient:
    def __init__(self):
        self.client = Minio(MINIO_ENDPOINT,
                            access_key=MINIO_ACCESS_KEY,
                            secret_key=MINIO_SECRET_KEY,
                            secure=MINIO_SECURE)

    def object_exists(self, bucket, obj_path) -> bool:
        try:
            self.client.stat_object(bucket, obj_path)
            return True
        except S3Error as _:
            return False

    def upload_to_minio(self, local_path, bucket_name, minio_path):
        assert os.path.isdir(local_path)
        for local_file in glob.glob(local_path + '/**'):
            local_file = local_file.replace(os.sep, "/") # Replace \ with / on Windows
            if not os.path.isfile(local_file):
                self.upload_to_minio(
                    local_file, bucket_name, minio_path + "/" + os.path.basename(local_file))
            else:
                remote_path = os.path.join(
                    minio_path, local_file[1 + len(local_path):])
                remote_path = remote_path.replace(
                    os.sep, "/")  # Replace \ with / on Windows
                self.client.fput_object(bucket_name, remote_path, local_file)

    def download_from_minio(self, minio_path, bucket_name, dst_local_path):
        assert os.path.isdir(dst_local_path)
    # for bucket_name in client.list_buckets():
        for item in client.list_objects(bucket_name, prefix=minio_path, recursive=True):
            full_path = os.path.join( dst_local_path, item.object_name)
            print(item.object_name)
            self.client.fget_object(bucket_name,item.object_name,full_path)


minio_client = MinioClient()

local_path = "/home/antonio/dtwin/dt-rse-mosaik/mosaik/configuration"
bucket_name = "sda-dt"
minio_path = "conf1"

minio_client.upload_to_minio(local_path, bucket_name, minio_path)


minio_path = "configuration/"
dst_local_path = "/home/antonio/temp4"
minio_client.download_from_minio(minio_path, bucket_name, dst_local_path)


# result = client.put_object(
#     "sda-dt", "my-object", io.BytesIO(b"hello"), 5,
# )
# print(
#     "created {0} object; etag: {1}, version-id: {2}".format(
#         result.object_name, result.etag, result.version_id,
#     ),
# )
# for bucket in client.list_buckets():
#     for item in client.list_objects(bucket.name,recursive=True):
#         client.fget_object(bucket.name,item.object_name,item.object_name)