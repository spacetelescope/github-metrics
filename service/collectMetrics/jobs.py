from bert import constants, utils, binding, aws

@binding.follow('noop')
def collect_github_metrics():
    import os
    work_queue, done_queue, ologger = utils.comm_binders(collect_github_metrics)

    repo_urls_filepath: str = os.path.join(os.getcwd(), 'repo-urls.txt')
    with open(repo_urls_filepath, 'r') as stream:
        for repo_url in stream.read().split('\n'):
            if repo_url == '':
                continue

            url_base, org_name, repo_name = repo_url.rsplit('/', 2)
            done_queue.put({
                'url_base': url_base,
                'org_name': org_name,
                'repo_name': repo_name
            })

@binding.follow(collect_github_metrics)
def mine_github_repo():
    work_queue, done_queue, ologger = utils.comm_binders(mine_github_repo)

    import boto3
    import lzma
    import os
    import json
    import requests
    import time

    from bert import aws
    from datetime import datetime

    from collectMetrics import shortcuts

    from requests.auth import HTTPBasicAuth

    from urllib.parse import urlencode


    output_dir: str = os.path.join('/tmp', 'outputs')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    config = {}
    with aws.kms('bert-etl') as keymaster:
        config['username'] = keymaster.decrypt(os.environ['GITHUB_USERNAME'])
        config['password'] = keymaster.decrypt(os.environ['GITHUB_PASSWORD'])

    config['delay'] = 1
    config['base-url'] = 'https://api.github.com'
    config['headers'] = {
        'User-Agent': 'repostats-tool',
        'Accept': 'application/vnd.github.v3+json'
    }
    config['logger'] = ologger
    for details in work_queue:
        url: str = f'{config["base-url"]}/repos/{details["org_name"]}/{details["repo_name"]}'
        response = requests.get(url, auth=HTTPBasicAuth(config['username'], config['password']), headers=config['headers'])
        time.sleep(config['delay'])

        views = shortcuts.mine_repo_attribute(details['org_name'], details['repo_name'], 'traffic/views', {}, config)
        time.sleep(config['delay'])

        clones = shortcuts.mine_repo_attribute(details['org_name'], details['repo_name'], 'traffic/clones', {}, config)
        time.sleep(config['delay'])

        issues = shortcuts.mine_repo_attribute(details['org_name'], details['repo_name'], 'issues', {}, config)
        time.sleep(config['delay'])
        
        releases = shortcuts.mine_repo_attribute(details['org_name'], details['repo_name'], 'releases', {}, config)
        time.sleep(config['delay'])
        
        pull_requests = shortcuts.mine_repo_attribute(details['org_name'], details['repo_name'], 'pulls', {}, config)
        time.sleep(config['delay'])
        
        contributors = shortcuts.mine_repo_attribute(details['org_name'], details['repo_name'], 'contributors', {'anon': 'true'}, config)
        time.sleep(config['delay'])
        
        commits = shortcuts.mine_repo_attribute(details['org_name'], details['repo_name'], 'commits', {}, config)
        time.sleep(config['delay'])
        
        tags = shortcuts.mine_repo_attribute(details['org_name'], details['repo_name'], 'tags', {}, config)
        time.sleep(config['delay'])
        
        contents = shortcuts.mine_repo_attribute(details['org_name'], details['repo_name'], 'contents', {}, config)
        time.sleep(config['delay'])
        
        date: str = datetime.utcnow().strftime('%Y-%m-%d')
        filename: str = f'{details["org_name"]}-{details["repo_name"]}.json.xz'
        filepath: str = os.path.join(output_dir, date, filename)
        dir_path: str = os.path.dirname(filepath)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        with lzma.open(filepath, mode='w', format=lzma.FORMAT_XZ) as stream:
            data = json.dumps({
                'base': response.json(),
                'views': views,
                'clones': clones,
                'issues': issues,
                'releases': releases,
                'pull_requests': pull_requests,
                'contributors': contributors,
                'commits': commits,
                'tags': tags,
                'contents': contents,
            }).encode('utf-8')
            stream.write(data)

        s3_key: str = f'daily/{date}/{filename}'
        ologger.info(f'Saving Timeseries Data for Repo[{details["repo_name"]}] to S3 Key[{s3_key}]')
        s3_client = boto3.client('s3')
        response = s3_client.upload_file(filepath, os.environ['DATASET_BUCKET'], s3_key)
        done_queue.put({
            'key': s3_key,
            'filename': os.path.basename(filepath),
        })
        os.remove(filepath)

    else:
        outputs_dir: str = os.path.join('/tmp', 'outputs')
        latest_s3_key: str = f'cache/latest-date.txt'
        latest_filepath: str = os.path.join(outputs_dir, latest_s3_key)
        outputs_dir_path: str = os.path.dirname(latest_filepath)
        if not os.path.exists(outputs_dir_path):
            os.makedirs(outputs_dir_path)

        with open(latest_filepath, 'w') as stream:
            stream.write(date)

        s3_client.upload_file(latest_filepath, os.environ['DATASET_BUCKET'], latest_s3_key)

@binding.follow(mine_github_repo)
def map_s3_bucket():
    import copy
    import csv
    import os
    import boto3
    import json
    import lzma
    import requests
    import time
    import typing

    from bert import aws

    from collectMetrics import shortcuts

    from datetime import datetime, timedelta

    from requests.auth import HTTPBasicAuth

    from urllib.parse import urlencode

    work_queue, done_queue, ologger = utils.comm_binders(map_s3_bucket)
    outputs_dir: str = os.path.join('/tmp', 'outputs')
    if not os.path.exists(outputs_dir):
        os.makedirs(outputs_dir)

    ascii_date: str = shortcuts.obtain_latest_ascii_date(outputs_dir)
    config = {}
    with aws.kms('bert-etl') as master_key:
        config['username'] = master_key.decrypt(os.environ['GITHUB_USERNAME'])
        config['password'] = master_key.decrypt(os.environ['GITHUB_PASSWORD'])
        config['delay'] = 1
        config['logger'] = ologger
        config['headers'] = {}

    astroconda_contrib_repos = shortcuts.org_name_contents('astroconda-contrib', {}, config)
    astroconda_dev_repos = shortcuts.org_name_contents('astroconda-dev', {}, config)
    shortcuts.sync_s3_datum('astroconda-contrib-repos', astroconda_contrib_repos)
    shortcuts.sync_s3_datum('astroconda-dev-repos', astroconda_dev_repos)

    for details in work_queue:
        done_queue.put(details)

@binding.follow(map_s3_bucket, pipeline_type=constants.PipelineType.CONCURRENT)
def process_s3_bucket_contents():
    import boto3
    import copy
    import csv
    import hashlib
    import json
    import lzma
    import os
    import typing

    from botocore.exceptions import ClientError
    from collectMetrics import shortcuts

    from datetime import datetime, timedelta

    COMMIT_DATE_FORMAT: str = '%Y-%m-%dT%H:%M:%SZ'
    CACHE_DIR = '/tmp/github-metrics-cache'

    work_queue, done_queue, ologger = utils.comm_binders(process_s3_bucket_contents)
    outputs_dir: str = os.path.join('/tmp', 'outputs', 'process-contents')
    astroconda_contrib_repos = shortcuts.obtain_s3_datum('astroconda-contrib-repos')
    astroconda_dev_repos = shortcuts.obtain_s3_datum('astroconda-dev-repos')
    ascii_date: str = shortcuts.obtain_latest_ascii_date(outputs_dir)
    s3_client = boto3.client('s3')

    filepaths: typing.List[typing.Any] = []
    latest_dataset: typing.Dict[str, typing.Any] = []
    # Debugging logic
    # ascii_date: str = '2019-11-12'
    # contents = []
    # for page in s3_client.get_paginator('list_objects_v2').paginate(Bucket=os.environ['DATASET_BUCKET'], Prefix=f'daily/{ascii_date}'):
    #     for item in page['Contents']:
    #         filename: str = os.path.basename(item['Key'])
    #         filepath: str = os.path.join(outputs_dir, ascii_date, filename)
    #         file_dir: str = os.path.dirname(filepath)
    #         if not os.path.exists(file_dir):
    #             os.makedirs(file_dir)

    #         s3_key: str = f'daily/{ascii_date}/{filename}'
    #         s3_client.download_file(os.environ['DATASET_BUCKET'], s3_key, filepath)
    #         with lzma.open(filepath, 'r', format=lzma.FORMAT_XZ) as stream:
    #             data = json.loads(stream.read())
    #             contents.append(data)

    # for data in contents:
    # end Debugging logic

    for details in work_queue:
        filename: str = os.path.basename(details['key'])
        filepath: str = os.path.join(outputs_dir, ascii_date, filename)
        file_dir: str = os.path.dirname(filepath)
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)

        s3_key: str = f'daily/{ascii_date}/{filename}'
        try:
            s3_client.download_file(os.environ['DATASET_BUCKET'], s3_key, filepath)
        except ClientError:
            ologger.error(f'Unable to download key[{s3_key} to file[{filepath}]')
            import pdb; pdb.set_trace()
            pass

        else:
            with lzma.open(filepath, 'r', format=lzma.FORMAT_XZ) as stream:
                data = json.loads(stream.read())

            os.remove(filepath)
            try:
                data['base']['name']
            except KeyError as err:
                continue

            try:
                rtcname: str = data['releases'][0]['name']
                rtcname_url: str = data['releases'][0]['html_url']
            except IndexError:
                try:
                    rtcname: str = data['tags'][0]['name']
                    rtcname_url: str = f'https://github.com/{data["base"]["owner"]["login"]}/{data["base"]["name"]}/releases/tag/{data["tags"][0]["name"]}'
                except IndexError:
                    rtcname: str = 'latest commit'
                    rtcname_url: str = data['commits'][0]['html_url']

            try:
                descrip: str = data['releases'][0]['body'].strip()
            except IndexError:
                try:
                    descrip: str = [comm for comm in data['commits'] if comm['sha'] == data['tags'][0]['commit']['sha']][0]['commit']['message'].strip()
                except IndexError:
                    descrip: str = 'N\A'

            try:
                date: str = data['releases'][0]['created_at']
            except IndexError:
                try:
                    date: str = [comm for comm in data['commits'] if comm['sha'] == data['tags'][0]['commit']['sha']][0]['commit']['author']['date']
                except IndexError:
                    try:
                        date: str = data['commits'][0]['commit']['author']['date']
                    except IndexError:
                        date: str = 'N\A'

            try:
                author_name = data['releases'][0]['author']['login']
                author_login = data['releases'][0]['author']['login']
                author_url: str = f'https://github.com/{author_login}'
            except IndexError:
                try:
                    author_commit = [comm for comm in data['commits'] if comm['sha'] == data['tags'][0]['commit']['sha']][0]
                    author_name: str = author_commit['author'].get('name', author_commit['author'].get('login', None))
                    author_login: str = author_commit['author'].get('login', '')
                    author_url: str = f'https://github.com/{author_login}'
                except IndexError:
                    author_commit: str = data['commits'][0]['commit']
                    author_name: str = author_commit['author'].get('name', author_commit['author'].get('login', None))
                    author_login: str = author_commit['author'].get('login', '')
                    author_url: str = f'https://github.com/{author_login}'

            try:
                last_commit_date: str = data['commits'][0]['commit']['author']['date']
                last_commit_hash: str = data['commits'][0]['sha']
            except IndexError:
                last_commit_date: str = 'N\A'
                last_commit_hash = None


            try:
                top_contributor: str = data['contributors'][0]['login']
                top_contributor_contributations: int = data['contributors'][0]['contributions']
            except (IndexError, KeyError):
                try:
                    top_contributor: str = data['contributors'][0]['name']
                    top_contributor_contributations: int = data['contributors'][0]['contributions']
                except IndexError:
                    last_contributor: str = 'N\A'
                    top_contributor_contributations: int = 0

            try:
                license: str = data['base']['license']['name']
            except (TypeError, KeyError):
                license: str = 'None'

            ologger.info(f'Building Timeseries Data for Org[{data["base"]["owner"]["login"]}]/Repo[{data["base"]["name"]}]')
            dataset_template = {
                'package_name': data['base']['name'],
                'repo_url': f'https://github.com/{data["base"]["owner"]["login"]}/{data["base"]["name"]}/',
                'owner': data['base']['owner']['login'],
                'archived': data['base']['archived'],
                'astroconda_contrib_repo': data['base']['name'] in [repo['name'] for repo in astroconda_contrib_repos],
                'astroconda_dev_repo': data['base']['name'] in [repo['name'] for repo in astroconda_dev_repos],
                'rtcname': rtcname,
                'rtcname_url': rtcname_url,
                'pulse_monthly': f'https://github.com/{data["base"]["owner"]["login"]}/{data["base"]["name"]}/pulse/monthly',
                'pulse_weekly': f'https://github.com/{data["base"]["owner"]["login"]}/{data["base"]["name"]}/pulse/monthly',
                'descrip': descrip,
                'description': data['base']['description'],
                'date': date,
                'author': author_name,
                'author_login': author_login,
                'author_url': author_url,
                'last_commit': last_commit_date,
                'last_commit_date': last_commit_date,
                'last_commit_hash': last_commit_hash,
                'count_commits': len(data['commits']),
                'count_issues': len(data['issues']),
                'count_pull_requests': len(data['pull_requests']),
                'count_contributors': len(data['contributors']),
                'count_contents': len(data['contents']),
                'count_tags': len(data['tags']),
                'count_forks': data['base']['forks'],
                'count_watchers': data['base']['subscribers_count'],
                'count_stars': data['base']['stargazers_count'],
                'count_open_issues': data['base']['open_issues'],
                'is_private': data['base']['private'],
                'top_contributor': top_contributor,
                'top_contributor_contributations': top_contributor_contributations,
                'total_contributors': len(data['contributors']),
                'travis_badge': f'https://img.shields.io/travis/{data["base"]["owner"]["login"]}/{data["base"]["name"]}.svg',
                'rtd_badge': f'https://readthedocs.org/projects/{data["base"]["name"]}/badge/?version=latest',
                'license': license,
                'forks': data['base']['forks'],
                'watchers': data['base']['watchers'],
                'issues_open': len([issue for issue in data['issues'] if issue['state'] == 'open']),
                'issues_open_url': f'https://github.com/{data["base"]["owner"]["login"]}/{data["base"]["name"]}/issues?q=is%3Aissue+is%3Aopen',
                'issues_closed': len([issue for issue in data['issues'] if issue['state'] == 'closed']),
                'issues_closed_url': f'https://github.com/{data["base"]["owner"]["login"]}/{data["base"]["name"]}/issues?q=is%3Aissue+is%3Aclosed',
                'pull_requests_open': len([pr for pr in data['pull_requests'] if pr['state'] == 'open']),
                'pull_requests_open_url': f'https://github.com/{data["base"]["owner"]["login"]}/{data["base"]["name"]}/pulls?q=is%3Apr+is%3Aopen',
                'pull_requests_closed': len([pr for pr in data['pull_requests'] if pr['state'] == 'closed']),
                'pull_requests_closed_url': f'https://github.com/{data["base"]["owner"]["login"]}/{data["base"]["name"]}/pulls?q=is%3Apr+is%3Aclosed',
                'badges': [],
            }
            for badge_name, links in shortcuts.badge_locations(data['base']['owner']['login'], data['base']['name']).items():
                dataset_template['badges'].append({
                    'name': badge_name,
                    'src': links['src'],
                    'anchor': links['anchor']
                })

            dataset_template['key'] = hashlib.md5(json.dumps(dataset_template).encode('utf-8')).hexdigest()
            # Find latest commits, issues, and pulls
            now: datetime = datetime.utcnow()
            last_week: datetime = datetime.utcnow() + timedelta(days=7)
            last_month: datetime = datetime.utcnow() + timedelta(days=30)

            dataset_template['commits_last_week'] = 0
            dataset_template['commits_last_month'] = 0
            for commit in data['commits']:
                commit_date: datetime = datetime.strptime(commit['commit']['author']['date'], COMMIT_DATE_FORMAT)
                if commit_date > last_week and commit_date < now:
                    dataset_template['commits_last_week'] += 1

                elif commit_date > last_month and commit_date < now:
                    dataset_template['commits_last_month'] += 1

            dataset_template['pull_requests_opened_last_week'] = 0
            dataset_template['pull_requests_opened_last_month'] = 0
            dataset_template['pull_requests_closed_last_week'] = 0
            dataset_template['pull_requests_closed_last_month'] = 0
            for pull_request in data['pull_requests']:
                created_at: datetime = datetime.strptime(pull_request['created_at'], COMMIT_DATE_FORMAT)
                if created_at > last_week and created_at < now:
                    dataset_template['pull_requests_opened_last_week'] += 1

                if created_at > last_month and created_at < now:
                    dataset_template['pull_requests_opened_last_month'] +=1

                try:
                    closed_at: datetime = datetime.strptime(pull_request['closed_at'], COMMIT_DATE_FORMAT)
                except TypeError:
                    closed_at = None

                else:
                    if closed_at > last_week and closed_at < now:
                        dataset_template['pull_requests_closed_last_week'] += 1

                    if closed_at > last_month and closed_at < now:
                        dataset_template['pull_requests_closed_last_month'] += 1


            dataset_template['issues_opened_last_week'] = 0
            dataset_template['issues_opened_last_month'] = 0
            dataset_template['issues_closed_last_week'] = 0
            dataset_template['issues_closed_last_month'] = 0
            for issue in data['issues']:
                created_at: datetime = datetime.strptime(issue['created_at'], COMMIT_DATE_FORMAT)
                if created_at > last_week and created_at < now:
                    dataset_template['issues_opened_last_week'] += 1

                if created_at > last_month and created_at < now:
                    dataset_template['issues_opened_last_month'] += 1

                try:
                    closed_at: datetime = datetime.strptime(issue['closed_at'], COMMIT_DATE_FORMAT)
                except TypeError:
                    closed_at = None

                else:
                    if closed_at > last_week and closed_at < now:
                        dataset_template['issues_closed_last_week'] += 1

                    if closed_at > last_month and closed_at < now:
                        dataset_template['issues_closed_last_month'] += 1


            # Building sliding window
            first_commit_date: datetime = datetime.strptime(data['commits'][-1]['commit']['author']['date'], COMMIT_DATE_FORMAT)
            last_commit_date: datetime = datetime.strptime(data['commits'][0]['commit']['author']['date'], COMMIT_DATE_FORMAT)
            commit_date_step: timedelta = timedelta(days=7)
            date_steps: typing.list[datetime] = [first_commit_date]
            while True:
                next_commit_boundry = date_steps[-1] + commit_date_step
                if next_commit_boundry > last_commit_date:
                    date_steps.append(last_commit_date)
                    break

                else:
                    date_steps.append(next_commit_boundry)

            fitted_commits: typing.List[typing.Any] = []
            fitted_pull_requests: typing.List[typing.Dict[str, int]] = []
            fitted_pull_requests_avg: typing.List[int] = []
            fitted_issues: typing.List[typing.Dict[str, int]] = []
            fitted_issues_avg: typing.List[int] = []
            for idx, next_commit_boundry in enumerate(date_steps[1:], 0):
                previous_commit_boundry = date_steps[idx]
                fitted_commit: typing.List[typing.Any] = []
                for commit in data['commits']:
                    commit_date: datetime = datetime.strptime(commit['commit']['author']['date'], COMMIT_DATE_FORMAT)
                    if previous_commit_boundry <= commit_date and next_commit_boundry >= commit_date:
                        fitted_commit.append(commit['sha'])

                else:
                    fitted_commits.append(fitted_commit)

                fitted_pull_requests_opened: int = 0
                fitted_pull_requests_closed: int = 0
                fitted_pull_requests_avg_open: float = 0.0
                for pull_request in data['pull_requests']:
                    created_at: datetime = datetime.strptime(pull_request['created_at'], COMMIT_DATE_FORMAT)
                    try:
                        closed_at: datetime = datetime.strptime(pull_request['closed_at'], COMMIT_DATE_FORMAT)
                    except TypeError:
                        closed_at: datetime = None

                    if created_at >= previous_commit_boundry and created_at <= next_commit_boundry:
                        fitted_pull_requests_opened += 1

                    if not closed_at is None:
                        if closed_at >= previous_commit_boundry and closed_at <= next_commit_boundry:
                            fitted_pull_requests_closed += 1

                        fitted_pull_requests_avg_open += (closed_at - created_at).total_seconds()

                else:
                    fitted_pull_requests.append({
                      'opened': fitted_pull_requests_opened,
                      'closed': fitted_pull_requests_closed,
                    })
                    if len(data['pull_requests']) == 0:
                        fitted_pull_requests_avg.append(0)

                    else:
                        pull_request_dom: float = 3600.0 * 24.0 * len(data['pull_requests'])
                        fitted_pull_requests_avg.append(fitted_pull_requests_avg_open / pull_request_dom)

                fitted_issues_opened: int = 0
                fitted_issues_closed: int = 0
                fitted_issues_avg_open: float = 0.0
                for issue in data['issues']:
                    created_at: datetime = datetime.strptime(issue['created_at'], COMMIT_DATE_FORMAT)
                    try:
                        closed_at: datetime = datetime.strptime(issue['closed_at'], COMMIT_DATE_FORMAT)
                    except TypeError:
                        clased_at: datetime = None

                    if created_at >= previous_commit_boundry and created_at <= next_commit_boundry:
                        fitted_issues_opened += 1

                    if not closed_at is None:
                        if closed_at >= previous_commit_boundry and closed_at <= next_commit_boundry:
                            fitted_issues_closed += 1

                        fitted_issues_avg_open += (closed_at - created_at).total_seconds()

                else:
                    fitted_issues.append({
                        'opened': fitted_issues_opened,
                        'closed': fitted_issues_closed,
                    })
                    if len(data['issues']) == 0:
                        fitted_issues_avg.append(0)

                    else:
                        issue_dom = 3600.0 * 24.0 * len(data['issues'])
                        fitted_issues_avg.append(fitted_issues_avg_open / issue_dom)

                dataset = copy.deepcopy(dataset_template)
                dataset['pull_requests_opened_weekly'] = fitted_pull_requests_opened
                dataset['pull_requests_closed_weekly'] = fitted_pull_requests_closed
                dataset['avg_pr_time_weekly'] = fitted_pull_requests_avg_open
                dataset['issues_opened_weekly'] = fitted_issues_opened
                dataset['issues_closed_weekly'] = fitted_issues_closed
                dataset['avg_issue_time_weekly'] = fitted_issues_avg_open
                dataset['date_weekly'] = previous_commit_boundry.strftime(COMMIT_DATE_FORMAT)
                dataset['commits_weekly'] = len(fitted_commit)
                done_queue.put({
                    'dataset': dataset
                })


@binding.follow(process_s3_bucket_contents)
def finalize_contents():
    import boto3
    import csv
    import json
    import os
    import tempfile
    import typing

    from collectMetrics import shortcuts

    s3_client = boto3.client('s3')
    work_queue, done_queue, ologger = utils.comm_binders(finalize_contents)
    outputs_dir: str = os.path.join('/tmp', 'outputs', 'finalize_contents')
    if not os.path.exists(outputs_dir):
        os.makedirs(outputs_dir)

    latest_dataset: typing.List[typing.Dict[str, typing.Any]] = []
    for details in work_queue:
        latest_dataset.append(details['dataset'])

    # import ipdb; ipdb.set_trace()
    # s3_keys: typing.List[str] = [item for item in {
    ascii_date: str = shortcuts.obtain_latest_ascii_date(outputs_dir)
    timeseries_filename: str = 'github-metrics.csv'
    timeseries_s3_key: str = f'timeseries/{timeseries_filename}'
    timeseries_filepath: str = os.path.join(outputs_dir, 'timeseries', timeseries_filename)
    timeseries_dir: str = os.path.dirname(timeseries_filepath)
    if not os.path.exists(timeseries_dir):
        os.makedirs(timeseries_dir)

    ologger.info(f'Writing dataset to file[{timeseries_filepath}]')
    with open(timeseries_filepath, 'w') as stream:
        writer = csv.DictWriter(stream, fieldnames=latest_dataset[0].keys())
        writer.writeheader()
        for entry in latest_dataset:
            writer.writerow(entry)

    ologger.info(f'Uploading file[{timeseries_filepath}] to s3 bucket[{os.environ["DATASET_BUCKET"]}] key[{timeseries_s3_key}]')
    s3_client.upload_file(timeseries_filepath, os.environ['DATASET_BUCKET'], timeseries_s3_key, ExtraArgs={'ACL': 'public-read'})

    last_week_entries_filepath = tempfile.NamedTemporaryFile().name
    last_week_entries_s3_key = 'timeseries/last-week-entries.json'
    ologger.info(f'Writing Last Week Entries to file[{last_week_entries_filepath}]')
    last_week_entries = shortcuts.last_week_entries(latest_dataset)
    with open(last_week_entries_filepath, 'w') as stream:
        stream.write(json.dumps(last_week_entries))

    ologger.info(f'Uploading Last Week Entries to S3Key[{last_week_entries_s3_key}]')
    s3_client.upload_file(last_week_entries_filepath, os.environ['DATASET_BUCKET'], last_week_entries_s3_key, ExtraArgs={'ACL': 'public-read'})

    latest_index_filename: str = 'latest.json'
    latest_index_filepath: str = os.path.join(outputs_dir, latest_index_filename)
    latest_index_s3_key: str = f'timeseries/{latest_index_filename}'
    ologger.info(f'Building Latest Index for date[{ascii_date}]')
    unique_dataset: typing.List[typing.Dict[str, typing.Any]] = []
    unique_dataset_index: typing.List[str] = []
    for entry in latest_dataset:
        entry_key: str = f'{entry["owner"]}-{entry["package_name"]}'
        if not entry_key in unique_dataset_index:
            del entry['pull_requests_opened_weekly']
            del entry['pull_requests_closed_weekly']
            del entry['issues_opened_weekly']
            del entry['issues_closed_weekly']
            del entry['date_weekly']
            del entry['commits_weekly']

            unique_dataset.append(entry)
            unique_dataset_index.append(entry_key)

    with open(latest_index_filepath, 'w') as stream:
        stream.write(json.dumps(unique_dataset))

    ologger.info(f'Uploading file[{latest_index_filepath}] to s3 bucket[{os.environ["DATASET_BUCKET"]}] key[{latest_index_s3_key}]')
    s3_client.upload_file(latest_index_filepath, os.environ['DATASET_BUCKET'], latest_index_s3_key, ExtraArgs={'ACL':'public-read'})



@binding.follow(finalize_contents)
def clean_up_s3():
    import boto3
    import os
    import typing

    s3_client = boto3.client('s3')
    object_keys: typing.List[str] = ['cache/astroconda-contrib-repos', 'cache/astroconda-dev-repos', 'cache/latest-date.txt']
    for page in s3_client.get_paginator('list_objects_v2').paginate(Bucket=os.environ['DATASET_BUCKET'], Prefix=f'daily/'):
        for item in page['Contents']:
            object_keys.append(item['Key'])

    else:
        s3_client.delete_objects(
            Bucket=os.environ['DATASET_BUCKET'],
            Delete={
                'Objects': [{'Key': s3_key} for s3_key in object_keys],
                'Quiet': True
            })


