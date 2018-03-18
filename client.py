import argparse
from dotenv import load_dotenv, find_dotenv
import requests
from os import environ as env
import sys


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--endpoint', required=True)
    parser.add_argument('--client-dotenv', default='.env.client')
    return parser.parse_args()


class ClientError(Exception):
    pass


def main():
    args = parse_args()
    env_file = find_dotenv(args.client_dotenv)
    load_dotenv(env_file)

    # obtain access token
    data = {
        'client_id': env.get('CLIENT_ID'),
        'client_secret': env.get('CLIENT_SECRET'),
        'audience': env.get('CLIENT_AUDIENCE'),
        'grant_type': 'client_credentials',
    }

    headers = {'content-type': 'application/json'}

    url = 'https://{0}/oauth/token'.format(env.get('CLIENT_DOMAIN'))
    r = requests.post(url, json=data, headers=headers)
    resp = r.json()
    access_token = resp['access_token']

    headers = {'authorization': 'Bearer {0}'.format(access_token)}
    r = requests.get(args.endpoint, headers=headers)
    print(r.json())

if __name__ == '__main__':
    sys.exit(main())
