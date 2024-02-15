import io
from minio import Minio
from minio import Minio

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