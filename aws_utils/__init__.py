import json
import os

import boto3

from aws_utils.cloudsearch import Cloudsearch
from aws_utils.dynamodb import DynamoDb
from aws_utils.gateway import Gateway
from aws_utils.logs import Logs
from aws_utils.s3 import S3
from aws_utils.utils import import_env_vars


def client(session=None, profile_name=None, region_name='us-east-1'):
    aws = Aws(session, profile_name, region_name)
    if os.environ.get('SERVERTYPE', 'DEV') == 'DEV':
        aws.load_config()
    return aws


class Aws:
    def __init__(self, session=None, profile_name=None, region_name='us-east-1'):

        # load instance if available
        try:
            import instance
            profile_name = instance.PROFILE
            region_name = instance.REGION
        except BaseException:
            pass

        self.client = None
        self.session = session or boto3.session.Session(profile_name=profile_name, region_name=region_name)

    def __call__(self, service):
        return self.session.client(service)

    def load_config(self, bucket=None, key=None):

        # load config from db
        bucket = os.environ.get('CONFIG_BUCKET', bucket)
        key = os.environ.get('KEY', key)

        try:
            import instance
            bucket = instance.CONFIG_BUCKET
            key = instance.KEY
        except BaseException:
            pass

        config = self.s3.get_json_object(bucket, key)
        import_env_vars(config)

    def invoke_lambda(self, function_name, payload):
        response = self.session.client('lambda').invoke(
            FunctionName=function_name,
            Payload=json.dumps(payload)
        )
        return response['Payload'].read().decode('utf-8')

    def cloud_search(self, domain_name):
        return Cloudsearch(domain_name, self.session)

    @property
    def cognito(self):
        return self.__call__('cognito-idp')

    @property
    def gateway(self):
        return Gateway(self.session)

    @property
    def dydb(self):
        return DynamoDb(self.session)

    @property
    def logs(self):
        return Logs(self.session)

    @property
    def s3(self):
        return S3(self.session)
