import boto3
import json
import os
import requests
import time
import typing

from bert import constants

from datetime import datetime

from requests.auth import HTTPBasicAuth

from urllib.parse import urlencode

BASE_URL: str = 'https://api.github.com'
HEADERS = {
    'User-Agent': 'repostats-tool',
    'Accept': 'application/vnd.github.v3+json'
}
OUTPUTS_PATH: str = os.path.join('/tmp', 'github-metrics', 'outputs')
CACHE_KEY: str = 'cache'
ASCII_DATE_FORMAT: str = '%Y-%m-%d'

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

        # sample the pull requests to see if we're repeatly pulling the same data
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

