#!/usr/bin/env python3

import json
import logging
from os import environ

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

FORMAT_MAP = {
    'rac-av-upload-audio': 'audio',
    'rac-av-upload-video': 'video'
}


def lambda_handler(event, context):
    """Main handler for function."""

    bucket = event['Records'][0]['s3']['bucket']['name']
    object = event['Records'][0]['s3']['object']['key']
    format = FORMAT_MAP[bucket]
    client = boto3.client(
        'ecs', region_name=environ.get(
            'AWS_REGION', 'us-east-1'))

    logger.info(
        "Running task for event from object {} in bucket {} with format {}".format(
            object,
            bucket,
            format))

    response = client.run_task(
        cluster=environ.get('ECS_CLUSTER'),
        launchType='FARGATE',
        networkConfiguration={
            'awsvpcConfiguration': {
                'subnets': [environ.get('ECS_SUBNET')],
                'securityGroups': [],
                'assignPublicIp': 'DISABLED'
            }
        },
        taskDefinition='digitized_av_validation',
        count=1,
        startedBy='lambda/digitized_av_trigger',
        overrides={
            'containerOverrides': [
                {
                    "name": "digitized_av_validation",
                    "environment": [
                        {
                            "name": "FORMAT",
                            "value": format
                        },
                        {
                            "name": "AWS_SOURCE_BUCKET",
                            "value": bucket
                        },
                        {
                            "name": "SOURCE_FILENAME",
                            "value": object
                        }
                    ]
                }
            ]
        }
    )

    return json.dumps(response, default=str)
