import boto3
import hashlib
import logging
import json
import os
import requests
import time
import typing

from bert import constants

from datetime import datetime, timedelta

from requests.auth import HTTPBasicAuth

from urllib.parse import urlencode

BASE_URL: str = 'https://api.github.com'
HEADERS = {
    'User-Agent': 'https://www.stsci.edu/~DATB/index.html',
    'Accept': 'application/vnd.github.v3+json'
}
OUTPUTS_PATH: str = os.path.join('/tmp', 'github-metrics', 'outputs')
CACHE_KEY: str = 'cache'
CACHE_DIR = '/tmp/github-metrics-cache-dir'
ASCII_DATE_FORMAT: str = '%Y-%m-%d'
ENCODING = 'utf-8'
COMMIT_DATE_FORMAT: str = '%Y-%m-%dT%H:%M:%SZ'

logger = logging.getLogger(__name__)

def mine_repo_attribute(org_name: str, repo_name: str, attribute: str, params: typing.Dict[str, str], config: typing.Any) -> typing.Dict[str, typing.Any]:
    logger = config['logger']
    page = 1
    limit = 50
    url_base: str = f'{BASE_URL}/repos/{org_name}/{repo_name}/{attribute}'
    results: typing.Dict[str, typing.Any] = []
    request_params = {
        'state': 'all',
        'sort': 'created',
    }
    while True:
        request_params['page'] = page
        request_params['per_page'] = limit
        for key, value in params.items():
            request_params[key] = value

        url: str = '?'.join([url_base, urlencode(request_params)])
        logger.info(f'Pulling URL[{url}]')
        response = requests.get(url, auth=HTTPBasicAuth(config['username'], config['password']), headers=config['headers'])
        if response.status_code != 200:
            logger.warning(f'Unable to load URL[{url}]')
            return results

        if attribute in ['traffic/views', 'traffic/clones']:
            return response.json()

        if len(response.json()) == 0:
            return results

        # Sample the pull requests to see if we're repeatly pulling the same data
        if attribute in ['tags']:
            if response.json()[0]['name'] in [item['name'] for item in results]:
                return results

        else:
            try:
                if response.json()[0]['url'] in [item['url'] for item in results]:
                    return results

            except KeyError as err:
                try:
                    # attribute = contributors
                    if response.json()[0]['email'] in [item['email'] for item in results]:
                        return results

                except KeyError:
                    try:
                        if response.json()[0]['login'] in [item.get('login', None) for item in results]:
                            return results

                    except KeyError:
                        try:
                            if response.json()[0]['type'] == 'Anonymous':
                                return results

                        except KeyError:
                            import pdb; pdb.set_trace()
                            pass

        page = page + 1
        results.extend(response.json())
        if len(response.json()) < limit:
            return results

        time.sleep(config['delay'])

def org_name_contents(org_name: str, params: typing.Dict[str, str], config: typing.Dict[str, typing.Any]) -> None:
    base_url: str = f'https://api.github.com/repos/astroconda/{org_name}/contents'
    page: int = 1
    limit: int = 100
    results: typing.List[typing.Any] = []
    request_params = {
        'state': 'all',
        'sort': 'created',
    }
    while True:
        request_params['page'] = page
        request_params['per_page'] = limit
        for key, value in params.items():
            request_params[key] = value

        url: str = '?'.join([base_url, urlencode(request_params)])
        config['logger'].info(f'Calling Url[{url}]')
        response = requests.get(url, auth=HTTPBasicAuth(config['username'], config['password']), headers=config['headers'])
        if response.status_code != 200:
            import ipdb; ipdb.set_trace()
            pass

        if len(response.json()) == 0:
            return results

        page = page + 1
        results.extend(response.json())
        if len(response.json()) < limit:
            return results

        repo_names: typing.List[str] = [item for item in {repo['name'] for repo in results}]
        # Handle the edge-case where exactly the limit comes back
        if len(repo_names) < len(results):
            dup: typing.List[str] = []
            overflow: typing.List[typing.Any] = []
            for repo in results:
                if not repo['name'] in dup:
                    overflow.append(repo)
                    dup.append(repo['name'])

            return overflow

        time.sleep(config['delay'])

def obtain_latest_ascii_date(outputs_dir: str) -> str:
    s3_client: typing.Any = boto3.client('s3')
    latest_date_s3_key: str = 'cache/latest-date.txt'
    latest_date_filepath: str = os.path.join(outputs_dir, latest_date_s3_key)
    latest_date_file_dir: str = os.path.dirname(latest_date_filepath)
    if not os.path.exists(latest_date_file_dir):
        os.makedirs(latest_date_file_dir)

    if os.path.exists(latest_date_filepath):
        os.remove(latest_date_filepath)

    s3_client.download_file(os.environ['DATASET_BUCKET'], latest_date_s3_key, latest_date_filepath)

    with open(latest_date_filepath, 'r') as stream:
        latest_date = datetime.strptime(stream.read(), ASCII_DATE_FORMAT)

    return latest_date.strftime(ASCII_DATE_FORMAT)

def sync_s3_datum(filename: str, datum: typing.Dict[str, typing.Any]) -> None:
    filepath: str = os.path.join(OUTPUTS_PATH, filename)
    filepath_key: str = os.path.join(CACHE_KEY, filename)
    filepath_dir: str = os.path.dirname(filepath)
    if not os.path.exists(filepath_dir):
        os.makedirs(filepath_dir)

    with open(filepath, 'wb') as stream:
        stream.write(json.dumps(datum).encode(constants.ENCODING))

    s3_client: typing.Any = boto3.client('s3')
    s3_client.upload_file(filepath, os.environ['DATASET_BUCKET'], filepath_key)

def obtain_s3_datum(filename: str) -> typing.Dict[str, typing.Any]:
    filepath: str = os.path.join(OUTPUTS_PATH, filename)
    filepath_key: str = os.path.join(CACHE_KEY, filename)
    if not os.path.exists(filepath):
        s3_client: typing.Any = boto3.client('s3')
        s3_client.download_file(os.environ['DATASET_BUCKET'], filepath_key, filepath)

    with open(filepath, 'rb') as stream:
        return json.loads(stream.read().decode(constants.ENCODING))


def load_cache(datum_key: str) -> typing.Dict[str, typing.Any]:
    filekey: str = hashlib.sha256(datum_key.encode(ENCODING)).hexdigest()
    filepath = os.path.join(CACHE_DIR, filekey)
    if os.path.exists(filepath):
        with open(filepath, 'r') as stream:
            return json.loads(stream.read())

def stow_cache(datum_key: str, value: typing.Dict[str, typing.Any]) -> None:
    filekey: str = hashlib.sha256(datum_key.encode(ENCODING)).hexdigest()
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

    filepath = os.path.join(CACHE_DIR, filekey)
    with open(filepath, 'w') as stream:
        stream.write(json.dumps(value, indent=2))

def badge_locations(org_name: str, package_name: str, branch_name: str = 'master', version: str = 'latest') -> typing.Dict[str, typing.Any]:
    datum_key = f'{ org_name }-{ package_name }-{ branch_name }-badge_locations'

    cached = load_cache(datum_key)
    if cached:
        return cached

    # travis, appveyor, coveralls, rtd, pypi, conda
    badges = {
        'travis': {
            'src': f'https://api.travis-ci.org/{ org_name }/{ package_name }.svg?branch={ branch_name }',
            'anchor': f'https://travis-ci.org/{ org_name }/{ package_name }',
        },
        'appveyor': {
            'src': f'https://img.shields.io/appveyor/build/{ org_name }/{ package_name }/{ branch_name }.svg',
            'anchor': f'https://ci.appveyor.com/project/{ org_name }/{ package_name }?branch={ branch_name }',
        },
        'codecov': {
            'src': f'https://codecov.io/gh/{ org_name }/{ package_name }/branch/{ branch_name }/graph/badge.svg',
            'anchor': f'https://codecov.io/gh/{ org_name }/{ package_name }?branch={ branch_name }',
        },
        'rtd': {
            'src': f'https://readthedocs.org/projects/{ package_name }/badge/?version=latest', 
            'anchor': f'https://{ package_name }.readthedocs.io/en/{ version }/',
        },
        'pypi': {
            'src': f'https://img.shields.io/pypi/v/{ package_name }.svg',
            'anchor': f'https://pypi.org/project/{ package_name }',
        },
        'conda': {
            'anchor': f'https://anaconda.org/{ org_name }/{ package_name }',
            'src': f'https://anaconda.org/{ org_name }/{ package_name }/badges/version.svg',
        }
    }

    available = {}
    for name, links in badges.items():
        logger.info(f'Heading Links: {links}')
        image_response = requests.get(links['src'], headers=HEADERS)
        if image_response.status_code != 200:
            continue

        elif name == 'appveyor' and 'project not found or access denied' in image_response.content.decode(ENCODING):
            continue

        elif name == 'codecov' and 'unknown' in image_response.content.decode(ENCODING):
            continue

        elif name == 'pypi' and 'package or version not found' in image_response.content.decode(ENCODING):
            continue

        anchor_response = requests.head(links['anchor'], headers=HEADERS)
        available[name] = links.copy()

    available = {key: available[key] for key in sorted(available.keys())}
    stow_cache(datum_key, available)
    return available

def last_week_entries(full_dataset: typing.List[typing.Dict[str, typing.Any]]) -> None:
    last_week_entries = []
    start_date = datetime.now() - timedelta(days=8)
    end_date = datetime.now()
    for entry in full_dataset:
        index_value = datetime.strptime(entry['date_weekly'], COMMIT_DATE_FORMAT)
        if index_value < start_date:
            continue

        if index_value > end_date:
            continue

        last_week_entries.append(entry)

    entries = {}
    for entry in last_week_entries:
        name = entry['package_name']
        if not name in entries.keys():
            entries[name] = entry
            continue
          
        found_datetime = datetime.strptime(entries[name]['date_weekly'], COMMIT_DATE_FORMAT)
        new_datetime = datetime.strptime(entry['date_weekly'], COMMIT_DATE_FORMAT)
        if new_datetime < found_datetime:
            entries[name] = entry
            continue

    return [e for e in entries.values()]

