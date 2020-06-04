from bert import constants, utils, binding, aws

@binding.follow('noop')
def obatin_repos():
    import boto3
    import json
    import os
    import requests
    import tempfile

    ENCODING = 'utf-8'
    S3_KEY = 'release/repos.json'
    BUCKET_NAME = os.environ['DATASET_BUCKET']
    s3_client = boto3.client('s3')

    url = 'https://raw.githubusercontent.com/spacetelescope/github-metrics/master/service/repo-urls.txt'
    filepath = tempfile.NamedTemporaryFile().name
    response = requests.get(url, headers={
        'Accept': 'application/json',
    })
    if response.status_code != 200:
        raise NotImplementedError(f'Url: {response.url}, Code: {response.status_code}')

   
    repo_list = {}
    for repo_url in response.content.decode(ENCODING).split('\n'):
        if repo_url == '':
            continue

        url_base, org_name, repo_name = repo_url.rsplit('/', 2)
        org_repo_list = repo_list.get(org_name, [])
        if not repo_name in org_repo_list:
            org_repo_list.append(repo_name)

        repo_list[org_name] = org_repo_list

    # Structure the file for public-release
    repo_list = {
        'orgs': repo_list
    }
    with open(filepath, 'w') as stream:
        stream.write(json.dumps(repo_list, indent=2))

    s3_client.upload_file(filepath, BUCKET_NAME, S3_KEY, ExtraArgs={'ACL': 'public-read'})

