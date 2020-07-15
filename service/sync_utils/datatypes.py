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

    def tags_url(self: PWN, org: str, name: str) -> str:
        return f'{GITHUB_BASE_URL}/repos/{org}/{name}/tags'


