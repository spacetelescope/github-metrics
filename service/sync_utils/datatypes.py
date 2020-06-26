import enum
import typing

from bert import aws

from requests.auth import HTTPBasicAuth

PWN = typing.TypeVar('PWN')
GITHUB_BASE_URL = 'https://api.github.com'
class GithubConfig(typing.NamedTuple):
    username: str
    password: str
    logger: typing.Any
    delay: int = 1
    headers: typing.Dict[str, str] = {
        'User-Agent': 'repostats-tool',
        'Accept': 'application/vnd.github.v3+json'
    }
    def auth(self: PWN) -> HTTPBasicAuth:
        with aws.kms('bert-etl') as key_handler:
            return HTTPBasicAuth(key_handler.decrypt(self.username), key_handler.decrypt(self.password))

    def repos_url(self: PWN, org: str, name: str) -> str:
        return f'{GITHUB_BASE_URL}/repos/{org}/{name}'

    def commits_url(self: PWN, org: str, name: str) -> str:
        return f'{GITHUB_BASE_URL}/repos/{org}/{name}/commits'

    def issues_url(self: PWN, org: str, name: str) -> str:
        return f'{GITHUB_BASE_URL}/repos/{org}/{name}/issues'

    def pull_requests_url(self: PWN, org: str, name: str) -> str:
        return f'{GITHUB_BASE_URL}/repos/{org}/{name}/pulls'

    def releases_url(self: PWN, org: str, name: str) -> str:
        return f'{GITHUB_BASE_URL}/repos/{org}/{name}/releases'

    def collaborators_url(self: PWN, org: str, name: str) -> str:
        return f'{GITHUB_BASE_URL}/repos/{org}/{name}/collaborators'


class GithubS3Key(enum.Enum):
    ISSUES = lambda owner, name: f'sync-utils/dataset/github/{owner}/{name}/issues.json'
    COMMITS = lambda owner, name: f'sync-utils/dataset/github/{owner}/{name}/commits.json'
    PULL_REQUESTS = lambda owner, name: f'sync-utils/dataset/github/{owner}/{name}/pull_requests.json'

ENCODING = 'utf-8'
import hashlib
import json
import os
import sync_utils

from botocore.exceptions import ClientError

RESET_ETL_STATE = True if os.environ.get('RESET_ETL_STATE', '').lower() in ['t', 'true'] else False
REQUEST_PAYER = 'requester' if os.environ.get('REQUEST_PAYER', '').lower() in ['t', 'true'] else ''

class ETLState:
    STATE_MODEL = {
      'contains': []
    }
    def _generate_s3_key(self: PWN, message: str) -> str:
        hashed_value = hashlib.sha256(message.encode(ENCODING)).hexdigest()
        return f'etl-state/{hashed_value}.json'

    def __init__(self: PWN, url: str) -> None:
        self._s3_key = self._generate_s3_key(url)
        self._changed = False

    def localize(self: PWN) -> PWN:
        if RESET_ETL_STATE:
            self.clear()
            return self

        try:
            self._state = sync_utils.download_dataset(self._s3_key, os.environ['DATASET_BUCKET'], dict)
        except ClientError:
            self.clear()

        else:
            self._state_hash = self._generate_hash(self._state)

        return self

    def synchronize(self: PWN) -> None:
        state_hash = self._generate_hash(self._state)
        # Check to see if the state hash changed
        if state_hash != self._state_hash:
            sync_utils.upload_dataset(self._state, self._s3_key, os.environ['DATASET_BUCKET'])

    def _generate_hash(self: PWN, datum: typing.Union[typing.Dict[str, typing.Any], typing.List[typing.Any], str, int, float]) -> bool:
        if isinstance(datum, (list, dict)):
            value = ''.join(sorted(json.dumps(datum)))
            return hashlib.sha256(value.encode(ENCODING)).hexdigest()

        else:
            raise NotImplementedError(datum.__class__)

    def contain(self: PWN, datum: typing.Union[typing.Dict[str, typing.Any], typing.List[typing.Any], str, int, float], *hash_keys: typing.List[str]) -> str:
        value_hash = self._generate_hash(datum)
        if not value_hash in self._state['contains']:
            self._state['contains'].append(value_hash)

        return value_hash

    def contains(self: PWN, datum: typing.Union[typing.Dict[str, typing.Any], typing.List[typing.Any], str, int, float], *hash_keys: typing.List[str]) -> bool:
        value_hash = self._generate_hash(datum)
        return value_hash in self._state['contains']

    def clear(self: PWN) -> None:
        self._state = self.STATE_MODEL.copy()
        self._state_hash = self._generate_hash(self._state)


import boto3
s3_client = boto3.client('s3')
class ETLDataset:
    def _clear_datasets(self: PWN):
        keys = []
        for page_idx, page in enumerate(s3_client.get_paginator('list_objects_v2').paginate(Bucket=os.environ['DATASET_BUCKET'], RequestPayer=REQUEST_PAYER, Prefix=self._prefix)):
            keys.extend([content['Key'] for content in page.get('Contents', [])])

        if len(keys) > 0:
            logger.info(f'Deleting keys[{len(keys)}] from Dataset[{self._hashed_message}]')
            s3_client.delete_objects(
                    Bucket=os.environ['DATASET_BUCKET'],
                    Delete={
                        'Objects': [{'Key': key} for key in keys]
                    },
                    RequestPayer=REQUEST_PAYER)

        self._state.clear()

    def _generate_next_s3_key(self: PWN) -> str:
        last_index = -1
        for page_idx, page in enumerate(s3_client.get_paginator('list_objects_v2').paginate(Bucket=os.environ['DATASET_BUCKET'], RequestPayer=REQUEST_PAYER, Prefix=self._prefix)):
            for content in page.get('Contents', []):
                content_index = int(content['Key'].replace(self._prefix, '').strip('/').rsplit('.json', 1)[0])
                if content_index > last_index:
                    last_index = content_index

        else:
            if last_index < 0:
                return f'{self._prefix}/0.json'

            else:
                next_index = last_index + 1
                return f'{self._prefix}/{next_index}.json'

    def __init__(self: PWN, message: str) -> None:
        self._state = ETLState(message)
        self._hashed_message = hashlib.sha256(message.encode(ENCODING)).hexdigest()
        self._prefix = f'etl-dataset/{self._hashed_message}'

    def __enter__(self: PWN) -> PWN:
        self.localize()
        self._state.localize()
        return self

    def __exit__(self: PWN, one, two, three) -> None:
        self.synchronize()
        self._state.synchronize()

    def localize(self: PWN) -> None:
        self._update = False
        self._dataset = []

    def synchronize(self: PWN) -> None:
        if len(self._dataset) == 0:
            return None

        if self._update is True:
            s3_key = f'{self._prefix}/0.json'
            self._clear_datasets()
            sync_utils.upload_dataset(self._dataset, s3_key, os.environ['DATASET_BUCKET'])

        else:
            s3_key = self._generate_next_s3_key()
            sync_utils.upload_dataset(self._dataset, s3_key, os.environ['DATASET_BUCKET'])

    def contains(self: PWN, datum: typing.Union[typing.Dict[str, typing.Any], typing.List[typing.Any], str, int, float], *hash_keys: typing.List[str]) -> bool:
        return self._state.contains(datum)

    def add(self: PWN, datum: typing.Union[typing.Dict[str, typing.Any], typing.List[typing.Any], str, int, float], *hash_keys: typing.List[str]) -> bool:
        self._state.contain(datum)
        self._update = False
        self._dataset.append(datum)

    def update(self: PWN, datum: typing.Union[typing.Dict[str, typing.Any], typing.List[typing.Any], str, int, float], *hash_keys: typing.List[str]) -> bool:
        """"
        Update takes the dataset and only manages one s3_key for the dataset. Rather than generating new s3_keys for each addition to the dataset
        """
        self._state.contain(datum)
        self._update = True
        self._dataset.append(datum)


import logging
import time
from urllib.parse import urlparse
logger = logging.getLogger(__name__)
class APILimiter:
    def __init__(self: PWN, url: str, delay: float) -> None:
        self._delay = delay
        self._netloc = urlparse(url).netloc

    def delay(self: PWN) -> None:
        logger.info(f'Delaying[{self._delay}] api execution for API[{self._netloc}]')
        time.sleep(self._delay)

    def __enter__(self: PWN) -> PWN:
        # Connect to networked resources to manage across processes
        return self

    def __exit__(self: PWN, one, two, three) -> None:
        # Disconnect
        pass


