#!/usr/bin/env python3.6

import boto3
import collections
import pprint
import dateutil.parser
import os
import re


ReservationType = collections.namedtuple('ReservationType', ['size', 'location', 'tenancy', 'product'])
Instance = collections.namedtuple('Instance', ['type', 'status'])
ReservedInstance = collections.namedtuple('ReservedInstance', ['type', 'count'])


ec2 = boto3.client('ec2')
cloudwatch = boto3.client('cloudwatch')


REGION_NAME=boto3._get_default_session().region_name
METRIC_NAMESPACE=os.environ.get('METRIC_NAMESPACE', 'Trackit')
METRIC_NAME_INSTANCES=os.environ.get('METRIC_NAME_INSTANCES', 'Instance count')
METRIC_NAME_RESERVED_INSTANCES=os.environ.get('METRIC_NAME_RESERVED_INSTANCES', 'Reserved instance count')


_az_to_region_re = re.compile(r'^(.+?)[a-z]?$')
def _az_to_region(az):
    return _az_to_region_re.match(az).group(1)
    

def _get_instances():
    instance_paginator = ec2.get_paginator('describe_instances')
    return [
        Instance(
            type=ReservationType(
                size=instance['InstanceType'],
                location=instance['Placement']['AvailabilityZone'],
                tenancy=instance['Placement']['Tenancy'],
                product=instance.get('Platform', 'Linux/UNIX'),
            ),
            status=instance['State']['Name'],
        )
        for page in instance_paginator.paginate(Filters=[{'Name': 'instance-state-name', 'Values': ['pending', 'running']}])
        for reservation in page['Reservations']
        for instance in reservation['Instances']
        if instance.get('InstanceLifecycle', 'ondemand') == 'ondemand'
    ]


def _get_reserved_instances():
    return [
        ReservedInstance(
            type=ReservationType(
                size=reserved_instance['InstanceType'],
                location=reserved_instance.get('AvailabilityZone', REGION_NAME),
                tenancy=reserved_instance['InstanceTenancy'],
                product=reserved_instance['ProductDescription'],
            ),
            count=reserved_instance['InstanceCount'],
        )
        for reserved_instance in ec2.describe_reserved_instances()['ReservedInstances']
    ]


def _aggregated_reserved_instances(reserved_instances):
    agg = collections.defaultdict(int)
    for reserved_instance in reserved_instances:
        agg[reserved_instance.type] += reserved_instance.count
    return [
        ReservedInstance(
            type=type,
            count=count,
        )
        for type, count in agg.items()
    ]


def _aggregated_instances(instances):
    agg = collections.defaultdict(int)
    for instance in instances:
        agg[instance.type] += 1
    return [
        (type, count)
        for type, count in agg.items()
    ]


def _make_reserved_instances_metric_data(now, reserved_instances):
    return [
        {
            'MetricName': METRIC_NAME_RESERVED_INSTANCES,
            'Timestamp': now,
            'Value': reserved_instance.count,
            'Unit': 'Count',
            'Dimensions': [
                { 'Name': 'InstanceType', 'Value': reserved_instance.type.size },
                { 'Name': 'Region'      , 'Value': _az_to_region(reserved_instance.type.location) },
                { 'Name': 'Location'    , 'Value': reserved_instance.type.location },
                { 'Name': 'Tenancy'     , 'Value': reserved_instance.type.tenancy },
                { 'Name': 'Product'     , 'Value': reserved_instance.type.product },
            ],
        }
        for reserved_instance in _aggregated_reserved_instances(reserved_instances)
    ]


def _make_instances_metric_data(now, instances):
    return [
        {
            'MetricName': METRIC_NAME_INSTANCES,
            'Timestamp': now,
            'Value': count,
            'Unit': 'Count',
            'Dimensions': [
                { 'Name': 'InstanceType', 'Value': instance_type.size },
                { 'Name': 'Region'      , 'Value': _az_to_region(instance_type.location) },
                { 'Name': 'Location'    , 'Value': instance_type.location },
                { 'Name': 'Tenancy'     , 'Value': instance_type.tenancy },
                { 'Name': 'Product'     , 'Value': instance_type.product },
            ],
        }
        for instance_type, count in _aggregated_instances(instances)
    ]


def _put_metrics(metric_data):
    cloudwatch.put_metric_data(
        Namespace=METRIC_NAMESPACE,
        MetricData=metric_data,
    )


def lambda_handler(event, context):
    now = dateutil.parser.parse(event['time'])
    instances = _get_instances()
    reserved_instances = _get_reserved_instances()
    instances_metric_data = _make_instances_metric_data(now, instances)
    reserved_instances_metric_data = _make_reserved_instances_metric_data(now, reserved_instances)
    _put_metrics(instances_metric_data + reserved_instances_metric_data)


if __name__ == '__main__':
    import datetime
    now = datetime.datetime.now()
    lambda_handler({
        'time': now.isoformat(),
    }, None)
