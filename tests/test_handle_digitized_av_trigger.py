#!/usr/bin/env python3

import json
from pathlib import Path
from unittest.mock import patch

import boto3
from moto import mock_aws
from moto.core import DEFAULT_ACCOUNT_ID

from src.handle_digitized_av_trigger import (calculate_gb_needed, get_config,
                                             lambda_handler)


def setup_ecs_cluster(cluster_name, task_name):
    client = boto3.client("ecs", region_name="us-east-1")
    client.create_cluster(clusterName=cluster_name)
    client.register_task_definition(
        family=task_name,
        containerDefinitions=[
            {
                "name": task_name,
                "image": "docker/hello-world:latest",
                "cpu": 1024,
                "memory": 400,
            }
        ],
    )
    return client


def get_mock_config(cluster_name):
    return {
        "AWS_REGION": "us-east-1",
        "ECS_CLUSTER": cluster_name,
        "ECS_SUBNET": "subnet",
        "QC_ECS_SERVICE": "digitized_av_qc",
        "EBS_STORAGE_MOUNT_PATH": "/ebs",
        "EBS_VOLUME_ROLE": "arn:aws:iam:role/123456789",
        "ECS_SECURITY_GROUP": "sg-123456789",
        "WAIT_DELAY": "5",
        "WAIT_MAX_ATTEMPTS": "30",
        "EXPANSION_RATIO": "1.5"}


@mock_aws
@patch('src.handle_digitized_av_trigger.get_config')
def test_s3_audio_args(mock_config):
    test_cluster_name = "default"
    client = setup_ecs_cluster(test_cluster_name, 'digitized_av_validation')
    mock_config.return_value = get_mock_config(test_cluster_name)

    with open(Path('fixtures', 's3_put_audio.json'), 'r') as df:
        message = json.load(df)
        lambda_handler(message, None)

        tasks = client.list_tasks(cluster=test_cluster_name)
        assert len(tasks['taskArns']) == 1

        task_response = client.describe_tasks(
            cluster=test_cluster_name,
            tasks=[tasks['taskArns'][0]])

        assert task_response['tasks'][0]['startedBy'] == 'lambda/digitized_av_trigger'
        assert task_response['tasks'][0][
            'taskDefinitionArn'] == f"arn:aws:ecs:us-east-1:{DEFAULT_ACCOUNT_ID}:task-definition/digitized_av_validation:1"
        with open(Path('fixtures', 's3_audio_args.json'), 'r') as af:
            args = json.load(af)
            assert task_response['tasks'][0]['overrides'] == args

        client.stop_task(
            cluster=test_cluster_name,
            task=tasks['taskArns'][0])


@mock_aws
@patch('src.handle_digitized_av_trigger.get_config')
def test_s3_video_args(mock_config):
    test_cluster_name = "default"
    client = setup_ecs_cluster(test_cluster_name, 'digitized_av_validation')
    mock_config.return_value = get_mock_config(test_cluster_name)

    with open(Path('fixtures', 's3_put_video.json'), 'r') as df:
        message = json.load(df)
        lambda_handler(message, None)

        tasks = client.list_tasks(cluster=test_cluster_name)
        assert len(tasks['taskArns']) == 1

        task_response = client.describe_tasks(
            cluster=test_cluster_name,
            tasks=[tasks['taskArns'][0]])

        assert task_response['tasks'][0]['startedBy'] == 'lambda/digitized_av_trigger'
        assert task_response['tasks'][0][
            'taskDefinitionArn'] == f"arn:aws:ecs:us-east-1:{DEFAULT_ACCOUNT_ID}:task-definition/digitized_av_validation:1"
        with open(Path('fixtures', 's3_video_args.json'), 'r') as af:
            args = json.load(af)
            assert task_response['tasks'][0]['overrides'] == args

        client.stop_task(
            cluster=test_cluster_name,
            task=tasks['taskArns'][0])


@mock_aws
@patch('src.handle_digitized_av_trigger.get_config')
def test_sns_audio_args(mock_config):
    test_cluster_name = "default"
    client = setup_ecs_cluster(test_cluster_name, 'digitized_av_packaging')
    mock_config.return_value = get_mock_config(test_cluster_name)
    client.create_service(
        cluster=test_cluster_name,
        serviceName='digitized_av_qc')

    with open(Path('fixtures', 'sns_audio_accept.json'), 'r') as df:
        message = json.load(df)
        lambda_handler(message, None)

        tasks = client.list_tasks(
            cluster=test_cluster_name,
            desiredStatus='RUNNING')
        assert len(tasks['taskArns']) == 1

        task_response = client.describe_tasks(
            cluster=test_cluster_name,
            tasks=[tasks['taskArns'][0]])

        assert task_response['tasks'][0]['startedBy'] == 'lambda/digitized_av_trigger'
        assert task_response['tasks'][0][
            'taskDefinitionArn'] == f"arn:aws:ecs:us-east-1:{DEFAULT_ACCOUNT_ID}:task-definition/digitized_av_packaging:1"
        with open(Path('fixtures', 'sns_audio_args.json'), 'r') as af:
            args = json.load(af)
            assert task_response['tasks'][0]['overrides'] == args

    for fixture in ['sns_audio_reject.json', 'sns_audio_reject.json']:
        with open(Path('fixtures', fixture), 'r') as df:
            message = json.load(df)
            lambda_handler(message, None)

            tasks = client.list_tasks(cluster=test_cluster_name)
            assert len(tasks['taskArns']) == 1


@mock_aws
@patch('src.handle_digitized_av_trigger.get_config')
def test_sns_video_args(mock_config):
    test_cluster_name = "default"
    mock_config.return_value = get_mock_config(test_cluster_name)
    client = setup_ecs_cluster(test_cluster_name, 'digitized_av_packaging')
    client.create_service(
        cluster=test_cluster_name,
        serviceName='digitized_av_qc')

    with open(Path('fixtures', 'sns_video_accept.json'), 'r') as df:
        message = json.load(df)
        lambda_handler(message, None)

        tasks = client.list_tasks(cluster=test_cluster_name,)
        assert len(tasks['taskArns']) == 1

        task_response = client.describe_tasks(
            cluster=test_cluster_name,
            tasks=[tasks['taskArns'][0]])

        assert task_response['tasks'][0]['startedBy'] == 'lambda/digitized_av_trigger'
        assert task_response['tasks'][0][
            'taskDefinitionArn'] == f"arn:aws:ecs:us-east-1:{DEFAULT_ACCOUNT_ID}:task-definition/digitized_av_packaging:1"
        with open(Path('fixtures', 'sns_video_args.json'), 'r') as af:
            args = json.load(af)
            assert task_response['tasks'][0]['overrides'] == args

    with open(Path('fixtures', 'sns_video_valid.json'), 'r') as df:
        created = client.describe_services(services=['digitized_av_qc'])
        assert created['services'][0]['desiredCount'] == 0

        message = json.load(df)
        lambda_handler(message, None)

        created = client.describe_services(services=['digitized_av_qc'])
        assert created['services'][0]['desiredCount'] == 1


@mock_aws
@patch('src.handle_digitized_av_trigger.get_config')
def test_sns_complete(mock_config):
    test_cluster_name = "default"
    mock_config.return_value = get_mock_config(test_cluster_name)
    client = setup_ecs_cluster(test_cluster_name, 'digitized_av_packaging')
    client.create_service(
        cluster=test_cluster_name,
        serviceName='digitized_av_qc')

    with open(Path('fixtures', 'sns_complete.json'), 'r') as df:
        client.update_service(
            service='digitized_av_qc',
            desiredCount=1)
        created = client.describe_services(services=['digitized_av_qc'])
        assert created['services'][0]['desiredCount'] == 1

        message = json.load(df)
        lambda_handler(message, None)

        complete = client.describe_services(services=['digitized_av_qc'])
        assert complete['services'][0]['desiredCount'] == 0


@mock_aws
def test_config():
    ssm = boto3.client('ssm', region_name='us-east-1')
    path = "/dev/digitized_av_trigger"
    for name, value in [("foo", "bar"), ("baz", "buzz")]:
        ssm.put_parameter(
            Name=f"{path}/{name}",
            Value=value,
            Type="SecureString",
        )
    config = get_config(path)
    assert config == {'foo': 'bar', 'baz': 'buzz'}


def test_calculate_gb_needed():
    """Asserts GB needed are correctly calculated."""
    for input, expected in [
            (1000000000, 3),
            (1900000000, 5),
            (3900000000, 10)]:
        output = calculate_gb_needed(input, 1.5)
        assert output == expected
    for input, expected in [
            (1000000000, 3),
            (1900000000, 6),
            (3900000000, 11)]:
        output = calculate_gb_needed(input)
        assert output == expected
