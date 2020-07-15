import requests
import typing

from bert import constants, utils, binding, aws

from requests.auth import HTTPBasicAuth

from sync_utils.datatypes import GithubConfig

PWN = typing.TypeVar('PWN')
ENCODING = 'utf-8'

@binding.follow('noop')
def schedule_repo_urls():
    import os
    work_queue, done_queue, ologger = utils.comm_binders(schedule_repo_urls)

    filepath = os.path.join(os.getcwd(), 'repo-urls.txt')
    with open(filepath, 'r') as stream:
        for idx, repo_url in enumerate(stream.read().split('\n')):
            if repo_url == '':
                continue

            url_base, org_name, repo_name = repo_url.rsplit('/', 2)
            done_queue.put({
                'url_base': url_base,
                'org_name': org_name,
                'repo_name': repo_name
            })
            # if idx > 1 and constants.DEBUG:
            #     break

@binding.follow(schedule_repo_urls)
def extract_github_data():
    import os

    from collectGithubData import extractors

    work_queue, done_queue, ologger = utils.comm_binders(extract_github_data)

    local_cache_path = '/tmp/github-cache'
    if not os.path.exists(local_cache_path):
        os.makedirs(local_cache_path)

    config = GithubConfig(os.environ['GITHUB_USERNAME'], os.environ['GITHUB_PASSWORD'], ologger)
    for details in work_queue:
        org: str = details['org_name']
        name: str = details['repo_name']
        if name != 'jwst':
            continue

        details['etl'] = {
          'repo': extractors.github_repo(org, name, config),
          'commits': extractors.github_commits(org, name, config),
          'issues': extractors.github_issues(org, name, config),
          'pull-requests': extractors.github_pull_requests(org, name, config),
          'releases': extractors.github_releases(org, name, config),
          'collaborators': extractors.github_collaborators(org, name, config),
          'tags': extractors.github_tags(org, name, config),
        }
        done_queue.put(details)

@binding.follow(extract_github_data)
def generate_stats():
    import hashlib
    import json
    import os
    import sync_utils

    from datetime import timedelta, datetime
    from collectGithubData import reducers

    download_details = reducers.obtain_channel_download_details()
    work_queue, done_queue, ologger = utils.comm_binders(generate_stats)
    repo_list = []
    entry_keys = []
    for details in work_queue:
        org = details['org_name']
        name = details['repo_name']
        repo_list.append([org, name])
        ologger.info(f'Loading Details for Github Repo:{org}/{name}')
        with details['etl']['repo'] as etl_dataset_reader:
            try:
                repo_data = [entry for entry in etl_dataset_reader][0]
            except IndexError:
                ologger.error(f'Unable to load entry[{org}-{name}]')
                continue

        with details['etl']['commits'] as etl_dataset_reader:
            commits = [entry for entry in etl_dataset_reader]
        with details['etl']['issues'] as etl_dataset_reader:
            issues = [entry for entry in etl_dataset_reader]
        with details['etl']['pull-requests'] as etl_dataset_reader:
            pull_requests = [entry for entry in etl_dataset_reader]
        with details['etl']['releases'] as etl_dataset_reader:
            releases = [entry for entry in etl_dataset_reader]
        with details['etl']['collaborators'] as etl_dataset_reader:
            collaborators = [entry for entry in etl_dataset_reader]
        with details['etl']['tags'] as etl_dataset_reader:
            tags = [entry for entry in etl_dataset_reader]

        dataset_template = {
            'url': f'https://github.com/{org}/{name}/',
            'package_name': name,
            'org': org,
            'description': repo_data['description'],
            'authors_commit': reducers.find_commit_authors(commits),
            'authors_issue': reducers.find_issue_authors(issues),
            'authors_pull_request': reducers.find_pull_request_authors(pull_requests),
            'authors_release': reducers.find_release_authors(releases),
            'authors_tag': reducers.find_tag_authors(tags),
            'archived': repo_data['archived'],
            'date_earliest': reducers.find_earliest_date(issues, pull_requests, commits, releases, tags),
            'date_latest': reducers.find_latest_date(issues, pull_requests, commits, releases, tags),
            'release_authors': reducers.find_release_authors(releases),
            'release_latest_notes': reducers.find_latest_release_notes(commits, releases, tags),
            'release_latest_author': reducers.find_latest_release_author(commits, releases, tags),
            'license': repo_data['license']['name'] if repo_data['license'] else None,
            'is_private': repo_data['private'],
            'count_forks': repo_data['forks'],
            'count_watchers': repo_data['watchers'],
            'count_issues_open': len([issue for issue in issues if issue['state'] == 'open']),
            'count_issues_closed': len([issue for issue in issues if issue['state'] == 'closed']),
            'count_issues_total': len(issues),
            'count_pull_requests_open': len([pr for pr in pull_requests if pr['state'] == 'open']),
            'count_pull_requests_closed': len([pr for pr in pull_requests if pr['state'] == 'closed']),
            'count_pull_requests_total': len(pull_requests),

            'count_commits_total': len(commits),
            'count_releases_total': len(releases),
            'count_tags_total': len(tags),

            'pull_requests_open_url': f'https://github.com/{org}/{name}/pulls?q=is%3Apr+is%3Aopen',
            'pull_requests_closed_url': f'https://github.com/{org}/{name}/pulls?q=is%3Apr+is%3Aclosed',
            'issues_open_url': f'https://github.com/{org}/{name}/issues?q=is%3Aissue+is%3Aopen',
            'issues_closed_url': f'https://github.com/{org}/{name}/issues?q=is%3Aissue+is%3Aclosed',

            'badges': [],
            'download_channel': {},
        }
        for badge_name, badge_links in reducers.find_badge_locations(org, name).items():
            dataset_template['badges'].append({
                'name': badge_name,
                'src': badge_links['src'],
                'anchor': badge_links['anchor'],
            })

        entry_key = f'{org}-{name}'.lower()
        entry_keys.append(entry_key)
        entry_download_details = download_details.get(entry_key, None)
        if entry_download_details is None:
            ologger.info(f'Unable pull Download Details for Repo[{org}-{name}]')

        else:
            for channel in entry_download_details.get('channels', []):
                dataset_downloads_channel_details = dataset_template['download_channel'].get(channel, {
                    'count': 0,
                    'homes': [],
                })
                if not entry_download_details['home'] in dataset_downloads_channel_details['homes']:
                    dataset_downloads_channel_details['homes'].append(entry_download_details['home'])
                    dataset_downloads_channel_details['count'] += entry_download_details['count']

                else:
                    import pdb; pdb.set_trace()
                    import sys; sys.exit(1)

                dataset_template['download_channel'][channel] = dataset_downloads_channel_details


        stats_s3_key = f'stsci-tools/stats/{org}/{name}.json'
        sync_utils.upload_dataset(dataset_template, stats_s3_key, os.environ['DATASET_BUCKET'])
        # Upload base-repo information

        COMMIT_DATE_FORMAT: str = '%Y-%m-%dT%H:%M:%SZ'
        date_interval = timedelta(days=1)
        date_earliest = datetime.strptime(dataset_template['date_earliest'], COMMIT_DATE_FORMAT)
        date_latest = datetime.strptime(dataset_template['date_latest'], COMMIT_DATE_FORMAT)
        date_range = date_latest - date_earliest
        window_stat_collection = []
        for window_index in range(0, date_range.days):
            window_start = date_earliest + timedelta(days=window_index)
            window_stop = date_earliest + timedelta(days=window_index + 1)
            window_stats = {
                'window_start': window_start.strftime(COMMIT_DATE_FORMAT),
                'window_stop': window_stop.strftime(COMMIT_DATE_FORMAT),
                'count_commits': 0,
                'count_issues_open': 0,
                'count_issues_closed': 0,
                'count_pull_requests_open': 0,
                'count_pull_requests_closed': 0,
                'count_releases': 0,
                'count_tags': 0,
            }
            for commit in commits:
                commit_date = datetime.strptime(commit['commit']['author']['date'], COMMIT_DATE_FORMAT)
                if commit_date >= window_start and commit_date < window_stop:
                    window_stats['count_commits'] = window_stats['count_commits'] + 1

            for issue in issues:
                issue_created = datetime.strptime(issue['created_at'], COMMIT_DATE_FORMAT)
                issue_updated = datetime.strptime(issue['updated_at'], COMMIT_DATE_FORMAT)
                if (issue_created >= window_start and issue_created < window_stop) \
                    or (issue_updated >= window_start and issue_updated < window_stop):
                    if issue['state'] == 'closed':
                        window_stats['count_issues_closed'] = window_stats['count_issues_closed'] + 1

                    elif issue['state'] == 'open':
                        window_stats['count_issues_open'] = window_stats['count_issues_open'] + 1

                    else:
                        raise NotImplementedError(f'Issue State: {issue["state"]}')

            for pr in pull_requests:
                pr_created = datetime.strptime(pr['created_at'], COMMIT_DATE_FORMAT)
                pr_updated = datetime.strptime(pr['updated_at'], COMMIT_DATE_FORMAT)
                if (pr_created >= window_start and pr_created < window_stop) \
                    or (pr_updated >= window_start and pr_updated < window_stop):
                    if pr['state'] == 'closed':
                        window_stats['count_pull_requests_closed'] = window_stats['count_pull_requests_closed'] + 1

                    elif pr['state'] == 'open':
                        window_stats['count_pull_requests_open'] = window_stats['count_pull_requests_open'] + 1

                    else:
                        raise NotImplementedError(f'PR State: {pr["state"]}')

            for release in releases:
                release_created = datetime.strptime(release['created_at'], COMMIT_DATE_FORMAT)
                release_published = datetime.strptime(release['published_at'], COMMIT_DATE_FORMAT)
                if release_published >= window_start and release_published <= window_stop:
                    window_stats['count_releases'] = window_stats['count_releases'] + 1

            for tag in tags:
                # Update Extractor to pull tag-dates
                pass

            window_stat_collection.append(window_stats)

        window_stat_collection_s3_key = f'stsci-tools/window-stats/{org}/{name}.json'
        sync_utils.upload_dataset(window_stat_collection, window_stat_collection_s3_key, os.environ['DATASET_BUCKET'])

