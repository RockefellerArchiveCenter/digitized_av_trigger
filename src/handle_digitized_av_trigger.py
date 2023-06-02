#!/usr/bin/env python3

import json
import logging
import traceback
from os import environ

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

FORMAT_MAP = {
    'rac-av-upload-audio': 'audio',
    'rac-av-upload-video': 'video'
}

ssm_client = boto3.client('ssm')
full_config_path = f"/{environ.get('ENV')}/{environ.get('APP_CONFIG_PATH')}"


def get_config(ssm_parameter_path):
    """Fetch config values from Parameter Store.

    Args:
        ssm_parameter_path (str): Path to parameters

    Returns:
        configuration (dict): all parameters found at the supplied path.
    """
    configuration = {}
    try:
        param_details = ssm_client.get_parameters_by_path(
            Path=ssm_parameter_path,
            Recursive=False,
            WithDecryption=True)

        for param in param_details.get('Parameters', []):
            param_path_array = param.get('Name').split("/")
            section_position = len(param_path_array) - 1
            section_name = param_path_array[section_position]
            configuration[section_name] = param.get('Value')

    except BaseException:
        print("Encountered an error loading config from SSM.")
        traceback.print_exc()
    finally:
        return configuration


def lambda_handler(event, context):
    """Triggers ECS task."""

    bucket = event['Records'][0]['s3']['bucket']['name']
    object = event['Records'][0]['s3']['object']['key']
    format = FORMAT_MAP[bucket]

    config = get_config(full_config_path)
    ecs_client = boto3.client(
        'ecs',
        region_name=config.get('AWS_REGION'))

    logger.info(
        "Running task for event from object {} in bucket {} with format {}".format(
            object,
            bucket,
            format))

    response = ecs_client.run_task(
        cluster=config.get('ECS_CLUSTER'),
        launchType='FARGATE',
        networkConfiguration={
            'awsvpcConfiguration': {
                'subnets': [config.get('ECS_SUBNET')],
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
