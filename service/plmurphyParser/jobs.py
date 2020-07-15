import typing

from bert import constants, utils, binding, aws

@binding.follow('noop')
def load_log_files():
    import glob
    import gzip
    import os
    work_queue, done_queue, ologger = utils.comm_binders(load_log_files)

    dirname: str = os.path.dirname(os.getcwd()).rsplit('/', 1)[1]
    dirname: str = os.path.dirname(__file__).rsplit('/', 1)[1]
    log_dir = os.path.join(os.getcwd(), dirname, 'logs')
    ologger.info(f'Scanning Directory[{log_dir}] for Nginx Logs')
    for filepath in glob.glob(f'{log_dir}/*'):
        if filepath.endswith('.log') or \
            filepath.endswith('.gz') and \
            not 'error' in filepath:
            done_queue.put({
                'filepath': filepath
            })

        else:
            ologger.info(f'Omitting file[{os.path.basename(filepath)}]')

def _load_channel_data(channel: str) -> typing.Dict[str, typing.Any]:
    import requests

    url = f'https://ssb.stsci.edu/{channel}/channeldata.json'
    response = requests.get(url)
    if response.status_code != 200:
        raise NotImplementedError(f'Invalid URL[{url}] Status Code[{response.status_code}]')

    package_details = {}
    subdir_details = {}
    for subdir in ['win-64', 'osx-64', 'linux-64']:
        subdir_url = f'https://ssb.stsci.edu/{channel}/{subdir}/repodata.json'
        subdir_response = requests.get(subdir_url)
        if subdir_response.status_code in [404]:
            continue

        elif subdir_response.status_code != 200:
            raise NotImplementedError(f'Invalid URL[{url}] Status Code[{subdir_response.status_code}]')

        subdir_details[subdir] = subdir_response.json()

    for package_name, reference in response.json()['packages'].items():
        home = reference.get('home', None) or \
                reference.get('source_git_url', None) or \
                reference.get('dev_url', None)

        source_url = reference.get('source_url', None)
        if isinstance(source_url, list):
            if len(source_url) > 1:
                import pdb; pdb.set_trace()
                import sys; sys.exit(1)

            home = source_url[0]
        elif isinstance(source_url, str):
            home = source_url

        package_details[package_name] = {
            'repo_home': home,
            'repo_git_url': reference.get('source_git_url', None),
            'repo_dev_url': reference.get('dev_url', None),
            'package_name': package_name,
            'versions': [],
            'version_latest': reference['version'],
            'timestamp': reference.get('timestamp', None),
            'os_support': reference.get('subdirs', []),
            'releases': [],
        }

    for subdir in subdir_details.keys():
        for download_name, download_details in subdir_details[subdir]['packages'].items():
            details = package_details.get(download_details['name'], {
                'releases': [],
            })
            details['releases'].append({
                'name': download_name,
                'sha': download_details['sha256'],
                'md5': download_details['md5'],
                'depends': download_details['depends'],
                'build': download_details['build'],
                'version': download_details['version'],
                'size': download_details['size'],
            })
            package_details[download_details['name']] = details

    release_data = {}
    ENCODING = 'utf-8'
    import hashlib
    import json
    def _hash_datum(datum: typing.Dict[str, typing.Any]) -> str:
        return hashlib.sha256(''.join(sorted(json.dumps(datum))).encode(ENCODING)).hexdigest()

    for package_name, details in package_details.items():
        for release_name in [rel['name'] for rel in details['releases']]:
            if release_name in release_data.keys():
                if _hash_datum(details) != _hash_datum(release_data[release_name]):
                    import pdb; pdb.set_trace()
                    import sys; sys.exit(1)

            release_data[release_name] = details.copy()

    return release_data

@binding.follow(load_log_files, pipeline_type=constants.PipelineType.CONCURRENT)
def parse_log_file():
    import boto3
    import gzip
    import json
    import os
    import requests
    import sync_utils
    import tempfile
    import typing

    from datetime import datetime
    from urllib.parse import urlparse
    work_queue, done_queue, ologger = utils.comm_binders(parse_log_file)

    ENCODING = 'utf-8'
    ASTROCONDA_DOWNLOADS = {}
    ASTROCONDA_CHANNEL_DATA = _load_channel_data('astroconda')
    ASTROCONDA_ETC_DOWNLOADS = {}
    ASTROCONDA_ETC_CHANNEL_DATA = _load_channel_data('astroconda-etc')
    # ASTROCONDA_TOMB_DOWNLOADS = {}
    # ASTROCONDA_TOMB_CHANNEL_DATA = _load_channel_data('astroconda-tomb')
    CONDA_DEV_DOWNLOADS = {}
    # CONDA_DEV_CHANNEL_DATA = _load_channel_data('conda-dev')

    def _parse_line(line: str) -> typing.Dict[str, typing.Any]:
        clone = list(line)
        line_parts = []
        char_arr = []
        CONTAINERS = [('[', ']'), ('"', '"')]
        BREAK_CHAR = [' ']
        inside_container = False
        while True:
            try:
                char = clone.pop(0)
            except IndexError:
                break

            else:
                if inside_container is False and not char in BREAK_CHAR and not char in [c[0] for c in CONTAINERS]:
                    char_arr.append(char)

                elif inside_container is False and char in [c[0] for c in CONTAINERS]:
                    inside_container = True
                    continue

                elif inside_container is True and char in [c[1] for c in CONTAINERS]:
                    inside_container = False
                    line_parts.append(''.join(char_arr))
                    char_arr = []
                    continue

                elif inside_container is False and char in BREAK_CHAR:
                    line_parts.append(''.join(char_arr))
                    char_arr = []

                else:
                    char_arr.append(char)


        try:
            method, path, protocol = line_parts[5].split(' ') 
        except ValueError:
            return None

        else:
            # https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods
            if not method.lower() in ['get', 'post', 'delete', 'head', 'put', 'connect', 'options', 'trace', 'patch']:
                return None

            path = urlparse(path).path

        try:
            return {
                'ipaddress': line_parts[0],
                'timestamp': datetime.strptime(line_parts[3], '%d/%b/%Y:%H:%M:%S %z'),
                'method': method,
                'path': path,
                'protocol': protocol,
                'status_code': int(line_parts[7]),
                'byte_length': line_parts[8],
                'user_agent': line_parts[11]
            }
        except IndexError as err:
            ologger.exception(f'Unable to parse Line[{line}]')
            return None
        except ValueError as err:
            ologger.exception(f'Unable to parse Line[{line}]')
            import pdb; pdb.set_trace()
            return None


    def parse_logfile_stream(stream: 'io-file-stream') -> None:
        for ldx, line in enumerate(stream.readlines()):
            try:
                line = line.decode(ENCODING)
            except UnicodeDecodeError:
                import pdb; pdb.set_trace()
                pass

            result = _parse_line(line)
            if result is None:
                continue

            package_name = result['path'].rsplit('/', 1)[-1]
            if package_name.startswith('index.'):
                continue

            if result['path'].endswith('.json'):
                continue

            if result['path'].endswith('json.bz2'):
                continue

            if result['path'].endswith('/'):
                continue

            if result['path'].startswith('/astroconda-staging/'):
                continue

            if result['path'].startswith('/astroconda-staging-d/'):
                continue

            if result['path'].startswith('/astroconda-tomb/'):
                continue

            if result['method'].lower() == 'get' and \
                any([
                    'linux-64' in result['path'],
                    'osx-64' in result['path']
                ]) and \
                result['status_code'] == 200:

                if result['path'].startswith('/astroconda-etc/'):
                    home = ASTROCONDA_ETC_CHANNEL_DATA[package_name].get('repo_home', None)
                    if isinstance(home, list):
                        import pdb; pdb.set_trace()
                        pass

                    if home is None:
                        ologger.info(f'Home not found for Package[{package_name}]')
                        continue

                    entry = ASTROCONDA_ETC_DOWNLOADS.get(package_name, {
                        'count': 0,
                        'home': home
                    })
                    entry['count'] += 1
                    ASTROCONDA_ETC_DOWNLOADS[package_name] = entry

                # elif result['path'].startswith('/astroconda-tomb/'):
                #     home = ASTROCONDA_TOMB_CHANNEL_DATA[package_name].get('linux-64', {}).get('repo_home', None) or \
                #             ASTROCONDA_TOMB_CHANNEL_DATA[package_name].get('osx-64', {}).get('repo_home', None) or \
                #             ASTROCONDA_TOMB_CHANNEL_DATA[package_name].get('win-64', {}).get('repo_home', None)

                #     entry = ASTROCONDA_TOMB_DOWNLOADS.get(package_name, {
                #         'count': 0,
                #         'home': home
                #     })
                #     entry['count'] += 1
                #     ASTROCONDA_TOMB_DOWNLOADS[package_name] = entry

                elif result['path'].startswith('/astroconda/'):
                    home = ASTROCONDA_CHANNEL_DATA[package_name].get('repo_home', None)

                    if isinstance(home, list):
                        import pdb; pdb.set_trace()
                        pass

                    if home is None:
                        ologger.info(f'Home not found for Package[{package_name}]')
                        continue

                    entry = ASTROCONDA_DOWNLOADS.get(package_name, {
                        'count': 0,
                        'home': home
                    })
                    entry['count'] += 1
                    ASTROCONDA_DOWNLOADS[package_name] = entry

                elif result['path'].startswith('/conda-dev'):
                    count = CONDA_DEV_DOWNLOADS.get(package_name, 0) + 1
                    CONDA_DEV_DOWNLOADS[package_name] = count

                else:
                    raise NotImplementedError(result)


    for idx, details in enumerate(work_queue):
        ologger.info(f'Parsing Logfile[{details["filepath"]}]')
        if details['filepath'].endswith('.gz'):
            with gzip.open(details['filepath'], 'rb') as stream:
                parse_logfile_stream(stream)

        else:
            with open(details['filepath'], 'rb') as stream:
                parse_logfile_stream(stream)

    sync_utils.upload_downloads_dataset({
      'channels': {
        'astroconda-etc': ASTROCONDA_ETC_DOWNLOADS,
        'astroconda': ASTROCONDA_DOWNLOADS
      },
      'data': {
        'astroconda-etc': ASTROCONDA_ETC_CHANNEL_DATA,
        'astroconda': ASTROCONDA_CHANNEL_DATA,
      }
    })

