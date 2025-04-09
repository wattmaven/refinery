import boto3

from refinery.settings import settings


def create_s3_client():
    """
    Create an S3 client.

    Will use the configured environment variables if they are set.
    """
    return boto3.client(
        "s3",
        endpoint_url=settings.refinery_s3_endpoint_url,
        aws_access_key_id=settings.refinery_s3_access_key_id,
        aws_secret_access_key=settings.refinery_s3_secret_access_key,
    )


async def get_object(bucket: str, key: str):
    """
    Get an object from S3.

    Args:
        bucket: The name of the bucket to get the object from.
        key: The key of the object to get.

    Returns:
        The object from S3.
    """
    s3 = create_s3_client()
    object = s3.get_object(Bucket=bucket, Key=key)
    print(object)
    return object
