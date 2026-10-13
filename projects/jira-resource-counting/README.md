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

## Evidence status
This case study reflects the project description published on my [LinkedIn projects page](https://www.linkedin.com/in/dolapo-adeniyi/details/projects/). The original script and demonstration CSV have not yet been added to this repository.
