#!/usr/bin/env python3
import argparse
import sys
import uuid

from models import User

parser = argparse.ArgumentParser(description='Add a new user.')

parser.add_argument('username', metavar='username')
parser.add_argument('color', metavar='color')
parser.add_argument('--number', metavar='number', default='',
                    help="Mobile number for SMS feature")

args = parser.parse_args()

user_id = uuid.uuid4()
user = User(args.username, args.color, args.number, user_id).save()

url = "http://localhorst.duckdns.org:8080/{0}".format(str(user_id))
print("Added user {0} ({1})".format(args.username, url))

sys.exit(0)
