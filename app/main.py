import requests
import json
import boto3
import os

s3 = boto3.resource("s3")

UK_EVENT_URL = "https://www.parkrun.org.uk/{event}/course/"


class Events:
    object = s3.Object(os.environ["S3_BUCKET"], os.environ["S3_KEY"])

    @classmethod
    def save(cls, events: list[str]):
        cls.object.put(
            Body=json.dumps(events).encode("utf-8"), ServerSideEncryption="AES256"
        )

    @classmethod
    def load(cls) -> set[str]:
        try:
            return set(json.loads(cls.object.get()["Body"].read()))
        except s3.meta.client.exceptions.NoSuchKey:
            return set()


def send_notification(message, subject):
    boto3.client("sns").publish(
        TopicArn=os.environ["TOPIC"], Message=message, Subject=subject
    )


def handler(*args, **kwargs):
    events = requests.get("https://images.parkrun.com/events.json").json()

    existing = Events.load()

    uk_events = {
        _["properties"]["eventname"]: _["properties"]["EventLongName"]
        for _ in events["events"]["features"]
        if _["properties"]["countrycode"] == 97
        and not _["properties"]["eventname"].endswith("-juniors")
    }

    new_events = []

    for event, friendly_name in uk_events.items():
        if event not in existing:
            new_events.append(f"{friendly_name}: {UK_EVENT_URL.format(event=event)}")

    if new_events:
        send_notification(subject="New Parkruns Found!", message="\n".join(new_events))
        Events.save(list(uk_events))


if __name__ == "__main__":
    handler()
