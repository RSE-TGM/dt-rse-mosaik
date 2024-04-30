import os
from io import BytesIO
from typing import Union, BinaryIO

from minio import Minio
#from minio.error import NoSuchKey 
from minio.error import  S3Error

#from config import config

MINIO_ENDPOINT = "localhost:9000"
MINIO_ACCESS_KEY = "4K10mbUN3FxVsDxtDYSh"
MINIO_SECRET_KEY = "sI0zu0b4DlR2Vs0JyO6KhJZzws1w5eL1GzthLtPD"
MINIO_SECURE = False

class _MinioClient:
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

    def upload_directory(self, local_directory, bucket, dst_directory):
        for file_name in os.listdir(local_directory):
            src_file_path = os.path.join(local_directory, file_name)

            # Not handling sub directories at this moment
            if not os.path.isfile(src_file_path):
                continue

            dst_file_path = os.path.join(dst_directory, file_name)
            with open(src_file_path, 'rb') as f:
                self.write_object(bucket, dst_file_path, f,
                                  length=os.stat(src_file_path).st_size)

    def download_directory(self, bucket, remote_directory, dst_local_directory):
        list_objects = self.client.list_objects(bucket, f'{remote_directory.strip("/")}/')
        files_to_download = [f for f in list_objects if not f.is_dir]
        if not os.path.exists(dst_local_directory):
            os.mkdir(dst_local_directory)

        for file in files_to_download:
            dst_local_file = os.path.join(dst_local_directory, os.path.basename(file.object_name))
            with open(dst_local_file, 'wb') as f:
                data = self.read_object(file.bucket_name, file.object_name)
                f.write(data)

    def read_object(self, bucket, obj_path):
        return self.client.get_object(bucket, obj_path).read()

    def write_object(self, bucket, obj_path, data: Union[str, bytes, BinaryIO], length=None):
        """
        Length is required when using a file
        """
        stream = data
        if isinstance(data, str):
            stream = BytesIO(data.encode('utf-8'))
        elif isinstance(data, bytes):
            stream = BytesIO(data)

        if length is None:
            length = stream.getbuffer().nbytes

        with stream:
            return self.client.put_object(bucket, obj_path, stream, length)


minio_client = _MinioClient()
source_path = "/home/antonio/dtwin/dt-rse-mosaik/mosaik/configuration"
bucket_name = "sda-dt"
minio_path = "confX"
minio_client.upload_directory(local_directory=source_path, bucket=bucket_name, dst_directory=minio_path)


bucket_name = "sda-dt"
minio_path = "confX"
dst_local_directory = "/home/antonio/testDIR"
minio_client.download_directory(bucket=bucket_name, remote_directory=minio_path, dst_local_directory=dst_local_directory)