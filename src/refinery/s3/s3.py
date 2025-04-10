import boto3
from botocore.config import Config

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
        config=Config(signature_version="s3v4"),
    )


async def get_object_presigned_url(bucket: str, key: str):
    """
    Get a presigned URL for an object from S3.

    Args:
        bucket: The name of the bucket to get the object from.
        key: The key of the object to get.

    Returns:
        The presigned URL for the object.
    """
    s3 = create_s3_client()
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        # Only need for 5 minutes
        ExpiresIn=60 * 5,
    )
