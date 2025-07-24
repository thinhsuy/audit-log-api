from core.config import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    AWS_REGION,
)
import json
import boto3
from botocore.exceptions import ClientError
from datetime import datetime
from core.config import logger


class SimpleQueueService:
    def __init__(self, queue_url: str):
        self.sqs = boto3.client(
            "sqs",
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION,
        )
        self.queue_url: str = queue_url

    def send_message(self, payload: dict) -> str:
        """Send message event to SQS server"""
        try:
            resp = self.sqs.send_message(
                QueueUrl=self.queue_url,
                MessageBody=json.dumps(
                    payload,
                    # auto convert datetime to ios string
                    default=lambda o: o.isoformat() if isinstance(o, datetime) else str(o)
                ),
                
            )
            msg_id = resp["MessageId"]
            logger.info(f"[SQS][SEND] Message: {payload}")
            return msg_id
        except ClientError as e:
            logger.error("[SQS][ERROR][send_message]", e)
            return None

    def receive_messages(
        self,
        max_messages: int = 1,
        wait_seconds: int = 5,
        visibility_timeout: int = 10,
    ):
        try:
            resp = self.sqs.receive_message(
                QueueUrl=self.queue_url,
                MaxNumberOfMessages=max_messages,
                WaitTimeSeconds=wait_seconds,
                VisibilityTimeout=visibility_timeout,
            )
            msgs = resp.get("Messages", [])
            for m in msgs:
                logger.info("[RECEIVE][MESSAGE]: " + m["Body"])
            return msgs
        except ClientError as e:
            logger.error("[RECEIVE][MESSAGE][ERROR][receive_messages]", e)
            raise

    def delete_message(self, receipt_handle: str):
        try:
            self.sqs.delete_message(
                QueueUrl=self.queue_url, ReceiptHandle=receipt_handle
            )
            logger.info(f"[DELETE] Success for handle {receipt_handle[:10]}")
        except ClientError as e:
            logger.error("[DELETE][MESSAGE][ERROR]", e)
            raise

    def clear_queue(self, batch_size=10):
        while True:
            resp = self.sqs.receive_message(
                QueueUrl=self.queue_url,
                MaxNumberOfMessages=batch_size,
                WaitTimeSeconds=1,
            )
            msgs = resp.get("Messages", [])
            if not msgs:
                break
            entries = [
                {
                    "Id": m["MessageId"],
                    "ReceiptHandle": m["ReceiptHandle"],
                }
                for m in msgs
            ]
            print("Delete Message:", msgs.get("Body"))
            self.sqs.delete_message_batch(
                QueueUrl=self.queue_url, Entries=entries
            )
        print("Already delete all messages!")
