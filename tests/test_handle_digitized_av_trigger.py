#!/usr/bin/env python3

import json
from pathlib import Path

import boto3
from moto import mock_ecs
from moto.core import DEFAULT_ACCOUNT_ID

from src.handle_digitized_av_trigger import lambda_handler


@mock_ecs
def test_args():
    client = boto3.client("ecs", region_name="us-east-1")
    test_cluster_name = "default"
    client.create_cluster(clusterName=test_cluster_name)
    client.register_task_definition(
        family="digitized_av_validation",
        containerDefinitions=[
            {
                "name": "digitized_av_validation",
                "image": "docker/hello-world:latest",
                "cpu": 1024,
                "memory": 400,
            }
        ],
    )

    for fixture, expected_args in [
            ('put_audio.json', 'audio_args.json'), ('put_video.json', 'video_args.json')]:
        with open(Path('fixtures', fixture), 'r') as df:
            message = json.load(df)
            response = json.loads(lambda_handler(message, None))
            assert len(response['tasks']) == 1
            assert response['tasks'][0]['startedBy'] == 'lambda/digitized_av_trigger'
            assert response['tasks'][0][
                'taskDefinitionArn'] == f"arn:aws:ecs:us-east-1:{DEFAULT_ACCOUNT_ID}:task-definition/digitized_av_validation:1"
            with open(Path('fixtures', expected_args), 'r') as af:
                args = json.load(af)
                assert response['tasks'][0]['overrides'] == args
