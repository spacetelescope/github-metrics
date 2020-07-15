import logging
import requests
import typing
import types

from bert import aws
from bert.etl import ETLReference, APILimiter, ETLDataset

from requests.auth import HTTPBasicAuth
from requests.models import Response

from sync_utils.datatypes import GithubConfig

from urllib.parse import urlencode, urlparse

PWN = typing.TypeVar('PWN')
ENCODING = 'utf-8'
DELAY = 0.5
logger = logging.getLogger(__name__)

def github_repo(org: str, name: str, config: GithubConfig) -> ETLReference:
    url = config.repos_url(org, name)
    with APILimiter(url, DELAY) as api_limiter:
        with ETLDataset(url) as etl_dataset:
            response = requests.get(url, auth=config.auth(), headers=config.headers)
            if response.status_code in [404]:
                logger.error(f'User[{config.username}] may not have access to Repo[{org}/{name}]')

            elif response.status_code in [200]:
                etl_dataset.update(response.json())

            else:
                raise NotImplementedError(f'{response.status_code}: {url}')

    return ETLReference(url)


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

def _sync_github_tags(
    api_limiter: APILimiter,
    etl_dataset: ETLDataset,
    auth: HTTPBasicAuth,
    headers: typing.Dict[str, str],
    tags: typing.List[typing.Dict[str, typing.Any]]) -> types.GeneratorType:
    for tag in tags:
        if etl_dataset.contains(tag) is False:
            etl_dataset.add(tag)
            yield tag 


def github_commits(org: str, name: str, config: GithubConfig) -> ETLReference:
    url = config.commits_url(org, name)
    with APILimiter(url, DELAY) as api_limiter:
        with ETLDataset(url) as etl_dataset:
            for entry in _sync_continuous_data(api_limiter, etl_dataset, url, config.auth(), config.headers):
                pass

    return ETLReference(url)

def github_issues(org: str, name: str, config: GithubConfig) -> ETLReference:
    url = config.issues_url(org, name)
    with APILimiter(url, DELAY) as api_limiter:
        with ETLDataset(url) as etl_dataset:
            for entry in _sync_continuous_data(api_limiter, etl_dataset, url, config.auth(), config.headers):
                pass

    return ETLReference(url)

def github_pull_requests(org: str, name: str, config: GithubConfig) -> ETLReference:
    url = config.pull_requests_url(org, name)
    with APILimiter(url, DELAY) as api_limiter:
        with ETLDataset(url) as etl_dataset:
            for entry in _sync_continuous_data(api_limiter, etl_dataset, url, config.auth(), config.headers):
                pass

    return ETLReference(url)

def github_releases(org: str, name: str, config: GithubConfig) -> ETLReference:
    url = config.releases_url(org, name)
    with APILimiter(url, DELAY) as api_limiter:
        with ETLDataset(url) as etl_dataset:
            for entry in _sync_continuous_data(api_limiter, etl_dataset, url, config.auth(), config.headers):
                pass

    return ETLReference(url)

def github_collaborators(org: str, name: str, config: GithubConfig) -> ETLReference:
    url = config.collaborators_url(org, name)
    with APILimiter(url, DELAY) as api_limiter:
        with ETLDataset(url) as etl_dataset:
            for entry in _sync_continuous_data(api_limiter, etl_dataset, url, config.auth(), config.headers):
                pass

    return ETLReference(url)

def github_tags(org: str, name: str, config: GithubConfig) -> ETLReference:
    url = config.tags_url(org, name)
    with APILimiter(url, DELAY) as api_limiter:
        with ETLDataset(url) as etl_dataset:
            for entry in _sync_continuous_data(api_limiter, etl_dataset, url, config.auth(), config.headers):
                pass
            # Bulid an abstraction that'll update a list of times in place.
            # /tags dosen't return enough data, we'll need to call /tags/:sha to have a more complete dataset

    return ETLReference(url)

