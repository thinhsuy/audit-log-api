from core.config import os
import json
import boto3
from botocore.exceptions import ClientError

class SQSService:
    def __init__(self):
        self.sqs = boto3.client(
            "sqs",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION")
        )
        self.queue_url: str = os.environ.get("SQS_QUEUE_URL", "")
    
    def send_message(self, payload: dict) -> str:
        try:
            resp = self.sqs.send_message(
                QueueUrl=self.queue_url,
                MessageBody=json.dumps(payload)
            )
            msg_id = resp["MessageId"]
            print(f"[SQS][SEND] MessageId: {msg_id}")
            return msg_id
        except ClientError as e:
            print("[SQS][ERROR][send_message]", e)
            raise

    def receive_messages(self, max_messages=1, wait_seconds=5):
        try:
            resp = self.sqs.receive_message(
                QueueUrl=self.queue_url,
                MaxNumberOfMessages=max_messages,
                WaitTimeSeconds=wait_seconds,      # long polling
                VisibilityTimeout=30               # giấu message trong 30s
            )
            msgs = resp.get("Messages", [])
            print(f"[RECEIVE] Got {len(msgs)} message(s)")
            for m in msgs:
                print("  - ReceiptHandle:", m["ReceiptHandle"])
                print("    Body:", m["Body"])
            return msgs
        except ClientError as e:
            print("[ERROR][receive_messages]", e)
            raise


    def delete_message(self, receipt_handle: str):
        try:
            self.sqs.delete_message(
                QueueUrl=self.queue_url,
                ReceiptHandle=receipt_handle
            )
            print(f"[DELETE] Success for handle {receipt_handle}")
        except ClientError as e:
            print("[ERROR][delete_message]", e)
            raise

    def clear_queue(self, batch_size=10):
        while True:
            resp = self.sqs.receive_message(
                QueueUrl=self.queue_url,
                MaxNumberOfMessages=batch_size,
                WaitTimeSeconds=1
            )
            msgs = resp.get("Messages", [])
            if not msgs:
                break
            entries = [{
                "Id": m["MessageId"],
                "ReceiptHandle": m["ReceiptHandle"]
            } for m in msgs]
            print("Delete Message:", msgs.get("Body"))
            self.sqs.delete_message_batch(QueueUrl=self.queue_url, Entries=entries)
        print("Already delete all messages!")
