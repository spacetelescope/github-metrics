# Github Metrics

Github metrics provides a view into openrsource activity here at STScI

## Github Metrics Service

The service module contains a lambda deployment suitable for running processing stream-like data. Metrics are collected
and pushed into a database. Lather written to as S3 bucket

## Github Metrics Client

The client is a VueJS dashboard. Data is sourced from an S3 object stored in an s3 bucket that is accessable over HTTPS

