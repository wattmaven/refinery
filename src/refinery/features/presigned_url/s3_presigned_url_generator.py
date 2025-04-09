import boto3


class S3PresignedUrlGenerator:
    """
    A class for generating presigned URLs for S3 objects.
    """

    # The boto3 client to use for the presigned URL generation.
    boto3_client: boto3.client

    def __init__(self, boto3_client: boto3.client):
        self.boto3_client = boto3_client

    def generate_presigned_url(self, bucket: str, key: str) -> str:
        """
        Generate a presigned URL for an S3 object.
        """
        return self.boto3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            # 5 minutes
            ExpiresIn=60 * 5,
        )
