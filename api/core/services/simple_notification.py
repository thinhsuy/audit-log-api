from core.config import os
import json
import boto3
from botocore.exceptions import ClientError

class SimpleNotificationService:
    def __init__(self):
        self.sns = boto3.client(
            "sns",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION")
        )
        self.topic_arn = os.getenv("SNS_TOPIC_ARN", "")

    def publish_event(self, payload: dict, attributes: dict = None) -> str:
        """
        payload: dict sẽ được JSON hóa thành message
        attributes: dict theo cấu trúc boto3 MessageAttributes
        """
        try:
            params = {
                "TopicArn": self.topic_arn,
                "Message": json.dumps(payload)
            }
            if attributes:
                params["MessageAttributes"] = attributes
            resp = self.sns.publish(**params)
            msg_id = resp["MessageId"]
            print(f"[SNS][PUBLISH] MessageId: {msg_id}")
            return msg_id
        except ClientError as e:
            print("[SNS][ERROR][publish_event]", e)
            raise
