Github Metrics
##############

This service directory has taken on many forms. In this attempt to update the documentation, I'll cover the differnt
bert-etl streams that run to build the Github Metric Stats

bert-etl streams
****************

* collectGithubData
* plmurphyParser


collectGithubData
-----------------

collectGithubData does exactly what it says it does. It collects data out of Github and stores the data in s3. In the
second stream-job, it'll build the stats required to display to the Dashboard

plmurphyParser
--------------


plmurphyParser syncs down the latest data from S3 to a local log directory, parses the inputs and pushes the stats
back up to s3 for later processing

