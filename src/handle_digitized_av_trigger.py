#!/usr/bin/env python3

import json
import logging
import traceback
from os import environ

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

FORMAT_MAP = {
    'rac-prod-av-upload-audio': 'audio',
    'rac-dev-av-upload-audio': 'audio',
    'rac-prod-av-upload-video': 'video',
    'rac-dev-av-upload-video': 'video',
}

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
        ssm_client = boto3.client(
            'ssm',
            region_name=environ.get('AWS_DEFAULT_REGION', 'us-east-1'))

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


def run_task(ecs_client, config, task_definition, environment):
    return ecs_client.run_task(
        cluster=config.get('ECS_CLUSTER'),
        launchType='FARGATE',
        networkConfiguration={
            'awsvpcConfiguration': {
                'subnets': [config.get('ECS_SUBNET')],
                'securityGroups': [],
                'assignPublicIp': 'DISABLED'
            }
        },
        taskDefinition=task_definition,
        count=1,
        startedBy='lambda/digitized_av_trigger',
        overrides={
            'containerOverrides': [
                {
                    "name": task_definition,
                    "environment": environment
                }
            ]
        }
    )


def lambda_handler(event, context):
    """Triggers ECS task."""

    config = get_config(full_config_path)
    ecs_client = boto3.client(
        'ecs',
        region_name=environ.get('AWS_DEFAULT_REGION', 'us-east-1'))

    if event['Records'][0].get('s3'):
        """Handles events from S3 buckets."""

        bucket = event['Records'][0]['s3']['bucket']['name']
        object = event['Records'][0]['s3']['object']['key']
        format = FORMAT_MAP[bucket]

        logger.info(
            "Running validation task for event from object {} in bucket {} with format {}".format(
                object,
                bucket,
                format))

        environment = [
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

        response = run_task(
            ecs_client,
            config,
            'digitized_av_validation',
            environment)

    elif event['Records'][0].get('Sns'):
        """Handles events from SNS."""

        attributes = event['Records'][0]['Sns']['MessageAttributes']

        response = f'Nothing to do for SNS event: {event}'

        if ((attributes['service']['Value'] == 'qc') and (
                attributes['outcome']['Value'] == 'SUCCESS')):
            """Handles QC approval events."""

            format = attributes['format']['Value']
            refid = attributes['refid']['Value']
            rights_ids = attributes['rights_ids']['Value']

            logger.info(
                "Running packaging task for event from object {} with format {}".format(
                    refid,
                    format))

            environment = [
                {
                    "name": "FORMAT",
                    "value": format
                },
                {
                    "name": "REFID",
                    "value": refid
                },
                {
                    "name": "RIGHTS_IDS",
                    "value": rights_ids
                }
            ]

            response = run_task(
                ecs_client,
                config,
                'digitized_av_packaging',
                environment)

    else:
        raise Exception('Unsure how to parse message')

    return json.dumps(response, default=str)
