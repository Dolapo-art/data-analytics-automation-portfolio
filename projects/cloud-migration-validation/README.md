# Cloud Migration Data Validation and Site Analysis

## Purpose
Support Jira migration readiness through documented data checks and user acceptance testing.

## My contribution
Compared source and target resource counts across major categories, including issues, projects, custom fields, workflows and users. Recorded checks and explanatory notes in structured Confluence tables.

Built and maintained UAT tables with pass/fail indicators for issue-level checks covering summary, status, assignee, comments, history and attachments. Also assessed marketplace app compatibility and possible cloud alternatives for unsupported plugins.

## Validation approach
Count differences need interpretation: a target instance may already contain resources, and some differences may be expected. Interpreting these differences requires explanatory notes and issue-level checks alongside resource totals.

## Tools
Jira · Confluence · resource reconciliation · UAT · compatibility assessment

## Deliverable
Documented validation and UAT checks supporting migration review. Collaborative project associated with Alluvium.

## Evidence and example

Original employer validation tables are not distributed. [Run the separate Python/SQL reconciliation example](../../examples/migration-reconciliation/README.md) to inspect missing-category handling and count comparisons using synthetic data. This new, AI-assisted example illustrates the approach; it is not recovered code from the original engagement.

[Back to portfolio](../../README.md)
