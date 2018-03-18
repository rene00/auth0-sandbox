import json
from six.moves.urllib.request import urlopen
from functools import wraps
from flask import Flask, request, jsonify, _request_ctx_stack
from flask_cors import cross_origin
from jose import jwt
from dotenv import load_dotenv, find_dotenv
from os import environ as env

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)
AUTH0_DOMAIN = env.get("AUTH0_DOMAIN")
AUTH0_AUDIENCE = env.get("AUTH0_AUDIENCE")
ALGORITHMS = ["RS256"]

app = Flask(__name__)


class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


@app.errorhandler(AuthError)
def handle_auth_error(ex):
    response = jsonify(ex.error)
    response.status_code = ex.status_code
    return response


def get_token_auth_header():
    '''Obtains the Access Token from the Authorization Header.'''

    auth = request.headers.get('Authorization', None)
    if not auth:
        raise AuthError(
            {'code': 'authorization_header_missing',
             'description': 'Authorization header is expected'},
            401
        )

    parts = auth.split()

    if parts[0].lower() != 'bearer':
        raise AuthError(
            {'code': 'invalid_header',
             'description': 'Authorization header must start with Bearer'},
            401
        )
    elif len(parts) == 1:
        raise AuthError(
            {'code': 'invalid_header', 'description': 'Token not found'},
            401
        )
    elif len(parts) > 2:
        raise AuthError(
            {'code': 'invalid_header',
             'description': 'Authorization header must be a Bearer token'},
            401
        )

    token = parts[1]

    return token


def requires_auth(f):
    '''Determines if the Access Token is valid.'''
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_auth_header()
        jsonurl = urlopen('https://' + AUTH0_DOMAIN + '/.well-known/jwks.json')
        jwks = json.loads(jsonurl.read())
        try:
            unverified_header = jwt.get_unverified_header(token)
            if unverified_header['alg'] == 'HS256':
                raise jwt.JWTError()
        except jwt.JWTError:
            raise AuthError(
                {'code': 'invalid_header',
                 'description':
                    'Invalid header. Use an RS256 signed JWT Access Token'},
                401
            )

        rsa_key = {}

        for key in jwks['keys']:
            if key['kid'] == unverified_header['kid']:
                rsa_key = {
                    'kty': key['kty'], 'kid': key['kid'], 'use': key['use'],
                    'n': key['n'], 'e': key['e']
                }

        if rsa_key:
            try:
                payload = jwt.decode(
                    token, rsa_key, algorithms=ALGORITHMS,
                    audience=AUTH0_AUDIENCE,
                    issuer='https://' + AUTH0_DOMAIN + '/'
                )
            except jwt.ExpiredSignatureError:
                raise AuthError(
                    {'code': 'token_expired',
                     'description': 'token is expired'},
                    401
                )
            except jwt.JWTClaimsError:
                raise AuthError(
                    {'code': 'invalid_claims',
                     'description': ('incorrect claims, please check the '
                                     'audience and issuer')},
                    401
                )
            except Exception:
                raise AuthError(
                    {'code': 'invalid_header',
                     'description': 'Unable to parse authentication token.'},
                    401
                )
            _request_ctx_stack.top.current_user = payload
            return f(*args, **kwargs)
        raise AuthError(
            {'code': 'invalid_header',
             'description': 'UNable to find appropriate key'},
            401
        )
    return decorated


@app.route('/api/public')
@cross_origin(headers=['Content-Type', 'Authorization'])
def public():
    response = 'Hello from a public endpoint'
    return jsonify(message=response)


@app.route('/api/private')
@cross_origin(headers=['Content-Type', 'Authorization'])
@requires_auth
def private():
    response = 'Hello from a private endpoint'
    return jsonify(message=response)