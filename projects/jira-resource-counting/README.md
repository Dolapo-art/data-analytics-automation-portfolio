# Automated Jira Resource Counting with Python & PostgreSQL

## Purpose
Create a repeatable operational snapshot of a Jira instance without manually inspecting each resource category.

## My contribution
Built a Python script, `jira_resource_counts.py`, that connected to a PostgreSQL Jira database using psycopg2. The script ran a structured SQL query covering more than 15 resource categories, loaded the result into a Pandas DataFrame using `pandas.read_sql_query()`, and exported a CSV using `.to_csv()`.

Categories described in the project included projects, issue types, workflows, custom fields, filters, dashboards, users and resolutions. Practical troubleshooting covered environment-variable configuration and host resolution.

## Tools
Python · psycopg2 · Pandas · PostgreSQL · SQL · CSV

## Deliverable
An automated resource-count snapshot suitable for analysis and operational reporting. Project associated with Alluvium.

## Evidence

An edited recording is available in the [demonstration index](../../demonstrations/README.md), together with its scope and limitations. Original employer source code and CSV data are not distributed.

[Back to portfolio](../../README.md)
