import logging
import requests
import typing

from bert import aws

from requests.auth import HTTPBasicAuth

from sync_utils.datatypes import GithubConfig, APILimiter, ETLDataset

PWN = typing.TypeVar('PWN')
ENCODING = 'utf-8'
DELAY = 0.5
logger = logging.getLogger(__name__)

def github_repo(org: str, name: str, config: GithubConfig) -> None:
    url = config.repos_url(org, name)
    with APILimiter(url, DELAY) as api_limiter:
        with ETLDataset(url) as etl_dataset:
            response = requests.get(url, auth=config.auth(), headers=config.headers)
            if response.status_code != 200:
                raise NotImplementedError(f'{response.status_code}: {url}')

            etl_dataset.update(response.json())

import types

from urllib.parse import urlencode, urlparse

from requests.models import Response
def _handle_github_error(response: Response) -> None:
    if 'Must have push access to view repository collaborators' in response.json()['message']:
        path = urlparse(response.request.url).path
        logger.info(f'Unable to view Repo collaborators: {path}')

    else:
        logger.exception(f'Unabled Github API Error[{response.status_code}: {response.request.url}]: {response.content}')

def _sync_continuous_data(
        api_limiter: APILimiter,
        etl_dataset: ETLDataset,
        base_url: str,
        auth: HTTPBasicAuth,
        headers: typing.Dict[str, str] = {},
        params: typing.Dict[str, str] = {}) -> None:
    SYNC_DATA = True
    page = 1
    limit = 100
    request_params: typing.Dict[str, str] = {
        'state': 'all',
        'sort': 'created'
    }
    request_params.update(params)
    while SYNC_DATA:
        request_params['page'] = page
        request_params['limit'] = limit
        url = '?'.join([base_url, urlencode(request_params)])
        api_limiter.delay()
        logger.info(f'Pulling URL[{url}]')
        response = requests.get(url, headers=headers, auth=auth)
        if response.status_code in [200]:
            dataset = response.json()
            if len(dataset) == 0:
                SYNC_DATA = False
                break

            for entry in dataset:
                if etl_dataset.contains(entry) is False:
                    etl_dataset.add(entry)
                    yield entry

                else:
                    SYNC_DATA = False
                    break

            page += 1

        else:
            _handle_github_error(response)
            SYNC_DATA = False
            break

def github_commits(org: str, name: str, config: GithubConfig) -> str:
    url = config.commits_url(org, name)
    with APILimiter(url, DELAY) as api_limiter:
        with ETLDataset(url) as etl_dataset:
            for entry in _sync_continuous_data(api_limiter, etl_dataset, url, config.auth(), config.headers):
                pass

    return url

def github_issues(org: str, name: str, config: GithubConfig) -> str:
    url = config.issues_url(org, name)
    with APILimiter(url, DELAY) as api_limiter:
        with ETLDataset(url) as etl_dataset:
            for entry in _sync_continuous_data(api_limiter, etl_dataset, url, config.auth(), config.headers):
                pass

    return url

def github_pull_requests(org: str, name: str, config: GithubConfig) -> str:
    url = config.pull_requests_url(org, name)
    with APILimiter(url, DELAY) as api_limiter:
        with ETLDataset(url) as etl_dataset:
            for entry in _sync_continuous_data(api_limiter, etl_dataset, url, config.auth(), config.headers):
                pass

    return url

def github_releases(org: str, name: str, config: GithubConfig) -> str:
    url = config.releases_url(org, name)
    with APILimiter(url, DELAY) as api_limiter:
        with ETLDataset(url) as etl_dataset:
            for entry in _sync_continuous_data(api_limiter, etl_dataset, url, config.auth(), config.headers):
                pass

    return url

def github_collaborators(org: str, name: str, config: GithubConfig) -> str:
    url = config.collaborators_url(org, name)
    with APILimiter(url, DELAY) as api_limiter:
        with ETLDataset(url) as etl_dataset:
            for entry in _sync_continuous_data(api_limiter, etl_dataset, url, config.auth(), config.headers):
                pass

    return url

