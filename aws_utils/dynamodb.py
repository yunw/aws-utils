import datetime
import os
import uuid

from boto3.dynamodb.conditions import Key

from aws_utils.utils import convert_types, projection_string


class DynamoDb:
    def __init__(self, session):
        self.client = session.client("dynamodb")
        self.resource = session.resource("dynamodb")

    def post_item(self, table, key, item, **kwargs):
        item["created_on"] = datetime.datetime.utcnow().isoformat()
        item.update(key)
        item = convert_types(item)
        table = self.resource.Table(os.environ[table])
        response = table.put_item(Item=item, ReturnValues='ALL_OLD', **kwargs)
        response['Key'] = key
        return response

    def get_item(self, table, key, **kwargs):
        kwargs = projection_string(kwargs)
        table = self.resource.Table(os.environ[table])
        response = table.get_item(Key=key, **kwargs)
        if "Item" in response and response["Item"]:
            return response["Item"]

    def delete_item(self, table, key, **kwargs):
        table = self.resource.Table(os.environ[table])
        response = table.delete_item(Key=key, ReturnValues='ALL_OLD', **kwargs)
        response['Key'] = key
        return response

    def query(self, table, key, **kwargs):
        kwargs = projection_string(kwargs)
        key1, val1 = key.popitem()
        key_exp = Key(key1).eq(val1)
        if key:
            key2, val2 = key.popitem()
            key_exp = key_exp + '&' + Key(key2).eq(val2)
        table = self.resource.Table(os.environ[table])
        response = table.query(KeyConditionExpression=key_exp, **kwargs)
        if "Items" in response and response["Items"]:
            return response["Items"]

    def update_item(self, table, key, updates=None, deletes=None, **kwargs):
        exp = ""
        names = {}
        values = {}
        updates = updates or {}
        deletes = deletes or []
        updates = convert_types(updates)
        updates["updated_on"] = datetime.datetime.utcnow().isoformat()

        def random_id():
            return str(uuid.uuid4()).split('-')[0]

        def add_attribute(attribute):
            if '.' in attribute:
                return _add_nested_attribute(attribute)
            return _add_attribute(attribute)

        def add_value(value):
            val_placeholder = ':val' + random_id()
            values[val_placeholder] = value
            return val_placeholder

        def _add_attribute(attribute):
            attr_placeholder = '#attr' + random_id()
            names[attr_placeholder] = attribute
            return attr_placeholder

        def _add_nested_attribute(attribute):
            attributes = attribute.split('.')
            for _idx, _val in enumerate(attributes):
                attr_placeholder = '#attr' + random_id()
                attributes[_idx] = attr_placeholder
                names[attr_placeholder] = _val
            return '.'.join(attributes)

        if updates:
            for key, val in dict(updates).items():
                updates[add_attribute(key)] = add_value(val)
                del updates[key]
            exp += 'SET '
            exp += ', '.join("{}={}".format(key, val) for (key, val) in updates.items())
            exp += ' '
        if deletes:
            for index, value in enumerate(deletes):
                deletes[index] = add_attribute(value)
            exp += 'REMOVE '
            exp += ', '.join(deletes)
            exp += ' '
        table = self.resource.Table(os.environ[table])
        response = table.update_item(Key=key, UpdateExpression=exp, ExpressionAttributeNames=names,
                                     ExpressionAttributeValues=values, ReturnValues='ALL_NEW', **kwargs)
        response['Key'] = key
        return response