import logging
import requests
import typing

from datetime import datetime

logger = logging.getLogger(__name__)
COMMIT_DATE_FORMAT = '%Y-%m-%dT%H:%M:%SZ'
def find_earliest_date(issues: typing.Any, pull_requests: typing.Any, commits: typing.Any, releases: typing.Any, tags: typing.Any) -> str:
    """
    Scans all data-structures for keys that may represent a date
    """
    dates = [commit['commit']['author']['date'] for commit in commits]
    dates.extend([issue['created_at'] for issue in issues])
    dates.extend([pull_request['created_at'] for pull_request in pull_requests])
    dates.extend([release['created_at'] for release in releases])
    return sorted(dates, key=lambda x: datetime.strptime(x, COMMIT_DATE_FORMAT))[0]

def find_latest_date(issues: typing.Any, pull_requests: typing.Any, commits: typing.Any, releases: typing.Any, tags: typing.Any) -> str:
    dates = [commit['commit']['author']['date'] for commit in commits]
    dates.extend([issue['updated_at'] for issue in issues])
    dates.extend([pull_request['updated_at'] for pull_request in pull_requests])
    dates.extend([release['published_at'] for release in releases])
    return sorted(dates, key=lambda x: datetime.strptime(x, COMMIT_DATE_FORMAT))[-1]

def find_commit_authors(commits: typing.List[typing.Dict[str, str]]) -> typing.List[str]:
    return [author for author in {commit['commit']['author']['name'] for commit in commits}]

def find_issue_authors(issues: typing.List[typing.Dict[str, str]]) -> typing.List[str]:
    return [author for author in {issue['user']['login'] for issue in issues}]

def find_pull_request_authors(pull_requests: typing.List[typing.Dict[str, typing.Any]]) -> typing.List[str]:
    return [author for author in {pull_request['user']['login'] for pull_request in pull_requests}]

def find_release_authors(releases: typing.List[typing.Dict[str, typing.Any]]) -> typing.List[str]:
    return [author for author in {release['author']['login'] for release in releases}]

def find_tag_authors(tags: typing.List[typing.Dict[str, typing.Any]]) -> typing.List[str]:
    # https://developer.github.com/v3/git/tags/#get-a-tag
    # To completly implement this, we'll need to source each tag individually
    # See extractors.py for more details
    # return [tag['tagger']['name'] for tag in tags]
    return []

def find_latest_release_notes(commits: typing.Any, releases: typing.Any, tags: typing.List[typing.Any]) -> str:
    try:
        return releases[0]['body']
    except IndexError:
        pass

    # Extractor needs to be build for tags
    # if len(tags) > 0:
    #     import pdb; pdb.set_trace()
    #     pass

    return commits[0]['commit']['message']

def find_latest_release_author(commits: typing.List[typing.Any], releases: typing.List[typing.Any], tags: typing.List[typing.Any]) -> str:
    try:
        return releases[0]['author']['login']
    except IndexError:
        pass

    # Extractor needs to be build for tags
    # if len(tags) > 0:
    #     import pdb; pdb.set_trace()
    #     pass

    return commits[0]['commit']['author']['name']

from bert.etl.functools import cache_function_results
from requests.exceptions import ConnectionError
ENCODING = 'utf-8'
HEADERS = {
    'User-Agent': 'https://www.stsci.edu/~DATB/index.html',
    'Accept': 'application/vnd.github.v3+json',
}
TIMEOUT = 5
@cache_function_results
def find_badge_locations(org: str, name: str, branch_name: str='master', version: str='latest') -> typing.List[typing.Dict[str, str]]:
    # travis, appveyor, coveralls, rtd, pypi, conda
    badges = {
        'travis': {
            'src': f'https://api.travis-ci.org/{ org }/{ name }.svg?branch={ branch_name }',
            'anchor': f'https://travis-ci.org/{ org }/{ name }',
        },
        'appveyor': {
            'src': f'https://img.shields.io/appveyor/build/{ org }/{ name }/{ branch_name }.svg',
            'anchor': f'https://ci.appveyor.com/project/{ org }/{ name }?branch={ branch_name }',
        },
        'codecov': {
            'src': f'https://codecov.io/gh/{ org }/{ name }/branch/{ branch_name }/graph/badge.svg',
            'anchor': f'https://codecov.io/gh/{ org }/{ name }?branch={ branch_name }',
        },
        'rtd': {
            'src': f'https://readthedocs.org/projects/{ name }/badge/?version=latest', 
            'anchor': f'https://{ name }.readthedocs.io/en/{ version }/',
        },
        'pypi': {
            'src': f'https://img.shields.io/pypi/v/{ name }.svg',
            'anchor': f'https://pypi.org/project/{ name }',
        },
        'conda': {
            'anchor': f'https://anaconda.org/{ org }/{ name }',
            'src': f'https://anaconda.org/{ org }/{ name }/badges/version.svg',
        }
    }

    available = {}
    for name, links in badges.items():
        logger.info(f'Heading Links: {links}')
        try:
            image_response = requests.get(links['src'], headers=HEADERS, timeout=TIMEOUT)
        except ConnectionError:
            logging.error(f'Unable to source Badge[{name}]')
            continue

        if image_response.status_code != 200:
            continue

        elif name == 'appveyor' and 'project not found or access denied' in image_response.content.decode(ENCODING):
            continue

        elif name == 'codecov' and 'unknown' in image_response.content.decode(ENCODING):
            continue

        elif name == 'pypi' and 'package or version not found' in image_response.content.decode(ENCODING):
            continue

        anchor_response = requests.head(links['anchor'], headers=HEADERS, timeout=TIMEOUT)
        available[name] = links.copy()

    available = {key: available[key] for key in sorted(available.keys())}
    return available

# @cache_function_results
def obtain_channel_download_details() -> typing.Dict[str, typing.Any]:
    # plmurphy Downloads Dataset
    import os
    import re

    from urllib.parse import urlparse
    from bert.etl import sync_utils

    logger = logging.getLogger(__name__)

    JS_SAFE_CHARS = re.compile('[^A-Za-z0-9]+')
    s3_key = 'sync-utils/datasets/conda-channel-downloads.json'
    downloads_dataset = {}
    channel_data = sync_utils.download_dataset(s3_key, os.environ['DATASET_BUCKET'], dict)
    for idx, (channel, channel_details) in enumerate(channel_data['channels'].items()):
    # for idx, (channel, channel_details) in enumerate(sync_utils.download_dataset(s3_key, os.environ['DATASET_BUCKET'], dict).items()):
        for package_name, package_details in channel_details.items():
            package_name_js_safe = JS_SAFE_CHARS.sub('_', package_name)
            home_parts = urlparse(package_details['home'])
            if home_parts.netloc in [
                    'pypi.python.org',
                    'wwwsearch.sourceforge.net',
                    'readthedocs.org',
                    'pyparsing.wikispaces.com',
                    'www.djangoproject.com',
                    'downloads.sourceforge.net',
                    'www.modwsgi.org',
                ]:
                logger.info(f'Skipping Home[{home_parts.netloc}]')
                continue

            elif home_parts.netloc in [
                    'github.com'
                ]:
                try:
                    github_org, github_name = [path for path in home_parts.path.split('/', 3) if path]
                except ValueError:
                    github_org, github_name = [path for path in home_parts.path.split('/', 2) if path]
                    github_name = github_name.split('/', 1)[0]

                entry_key = f'{github_org}-{github_name}'.lower()
                entry = downloads_dataset.get(entry_key, {
                    'count': package_details['count'],
                    'home': package_details['home'],
                    'channels': []
                })
                if channel not in entry['channels']:
                    entry['channels'].append(channel)

                downloads_dataset[entry_key] = entry

            else:
                logger.warn(f'Home[{home_parts.netloc}] not implemented')
                continue

    return downloads_dataset

