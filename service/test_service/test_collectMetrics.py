
def test_head_badge_locations():
    from collectMetrics import shortcuts
    org_name = 'spacetelescope'
    package_name = 'hstcal'
    for key, links in shortcuts.badge_locations(org_name, package_name).items():
        assert len(links.keys()) > 0


def test_last_week_dataset_pandas():
    import os
    import requests

    from collectMetrics import shortcuts
    from datetime import datetime, timedelta

    import pandas as pd

    DATE_FORMAT = '%Y-%m-%d'

    start_date = datetime.now() - timedelta(days=7)
    end_date = datetime.now()
    url = 'https://github-metrics-stsci-edu-prod.s3.amazonaws.com/timeseries/github-metrics.csv'
    filepath = '/tmp/awe.csv'
    if not os.path.exists(filepath):
        response = requests.get(url)
        with open(filepath, 'wb') as stream:
            stream.write(response.content)

    df = pd.read_csv(filepath, index_col='date_weekly', parse_dates=True)
    subset = df.loc[start_date.strftime(DATE_FORMAT): end_date.strftime(DATE_FORMAT)]
    data = []
    for entry in subset.values:
        data.append({key: entry[idx] for idx, key in enumerate(subset.keys())})

    import pdb; pdb.set_trace()
    pass

def test_last_week_dataset():
    import csv
    import os
    import requests

    from collectMetrics import shortcuts
    from datetime import datetime, timedelta

    COMMIT_DATE_FORMAT: str = '%Y-%m-%dT%H:%M:%SZ'

    start_date = datetime.now() - timedelta(days=8)
    end_date = datetime.now()
    filepath = '/tmp/awe.csv'
    if not os.path.exists(filepath):
        url = 'https://github-metrics-stsci-edu-prod.s3.amazonaws.com/timeseries/github-metrics.csv'
        response = requests.get(url)
        with open(filepath, 'wb') as stream:
            stream.write(response.content)

    with open(filepath, 'r') as stream:
        stream.seek(0)
        reader = csv.DictReader(stream)
        last_week = shortcuts.last_week_entries(reader)
        import pdb; pdb.set_trace()
        assert len(last_week) > 0

