v2.18.2 (2025-06-10)
-------------------------
 * Merge pull request #108 from rapidpro/dependabot/pip/requests-2.32.4
 * Bump requests from 2.32.3 to 2.32.4
 * Update CHANGELOG.md

v2.18.1 (2025-05-06)
-------------------------
 * Rename archive_type to type
 * Add support for type slug on channels endpoint

v2.18.0 (2025-05-06)
-------------------------
 * Remove fetching messages by broadcast, contact and label
 * Bump supported python versions

v2.17.0 (2025-02-21)
-------------------------
 * Merge pull request #103 from rapidpro/update-poetry-2
 * Adjust dependencies config
 * Update pyproject.toml for poetry 2

v2.16.0 (2024-12-03)
-------------------------
 * Remove input field on run values
 * Update dependencies

v2.15.0 (2024-04-16)
-------------------------
 * Merge pull request #93 from rapidpro/dependabot/pip/black-24.3.0
 * Merge pull request #94 from rapidpro/dependabot/pip/certifi-2023.7.22
 * Merge pull request #95 from rapidpro/dependabot/pip/urllib3-2.0.7
 * Merge pull request #96 from rapidpro/dependabot/pip/idna-3.7
 * Merge pull request #97 from rapidpro/dependabot/pip/requests-2.31.0
 * Bump requests from 2.30.0 to 2.31.0
 * Bump idna from 3.4 to 3.7
 * Bump urllib3 from 2.0.2 to 2.0.7
 * Bump certifi from 2023.5.7 to 2023.7.22
 * Bump black from 22.12.0 to 24.3.0
 * Merge pull request #92 from rapidpro/def-export
 * Add back get definitions

v2.14.0 (2024-04-10)
-------------------------
 * Remove get_channel_events and get_definitions

v2.13.0 (2024-03-07)
-------------------------
 * Replace deprecated pkg_resources
 * Remove use of pytz

v2.12.0 (2023-05-10)
-------------------------
 * Merge pull request #87 from rapidpro/fields-api
 * Fields API for create and update
 * Merge pull request #88 from rapidpro/transformers
 * Allow client to be created with a transformer function

v2.11.0 (2023-03-14)
-------------------------
 * Add message.flow

v2.10.0 (2023-02-22)
-------------------------
 * Add create_message

v2.9.0 (2023-01-17)
-------------------------
 * Update API fields
 * Update deps, add ruff, black and isort tools

v2.8.5
----------
 * Bump urllib3 from 1.26.4 to 1.26.5

v2.8.4
----------
 * Add paths parameter to get_runs

v2.8.3
----------
 * Add support for reverse ordering to contacts and runs

v2.8.2
----------
 * Update deps
 * Add exclude_active param to create_flow_start

v2.8.1
----------
 * Switch to new release system

2.8.0 (2020-08-28)
==================
* Update name of action for archiving messages

2.7.1 (2020-07-22)
==================
* Add UUID field to Org

2.7 (2020-02-19)
==================
* Drop support for API v1
* Add support for globals and classifiers (https://github.com/rapidpro/rapidpro-python/pull/68)
* Use flow_start.params instead of .extra (https://github.com/rapidpro/rapidpro-python/pull/69)

2.6.1 (2019-05-28)
==================
* Make Flow.FlowResult.node_uuids optional

2.6 (2019-05-28)
==================
* Add support to use flow results metadata

2.5.1 (2018-02-05)
==================
* Make broadcast.status optional

2.5 (2019-02-04)
==================
* Remove support for python 2

2.4 (2018-05-24)
==================
* Add input and name on run result (https://github.com/rapidpro/rapidpro-python/pull/58)
* Fix archives test data, period values

2.3 (2018-05-24)
==================
* Add support for the new archives endpoint (https://github.com/rapidpro/rapidpro-python/pull/56)

2.2 (2017-11-13)
==================
* Update campaign events to latest RapidPro changes (https://github.com/rapidpro/rapidpro-python/pull/52)

2.1.10 (2017-11-08)
==================
* Update campaigns to include archived field (https://github.com/rapidpro/rapidpro-python/pull/51)

2.1.9 (2017-10-25)
==================
* Support flow minor versions (https://github.com/rapidpro/rapidpro-python/pull/50)

2.1.8 (2017-06-26)
==================
* Add uuid field to flow starts (https://github.com/rapidpro/rapidpro-python/pull/49)

2.1.7 (2017-03-31)
==================
* Add verify_ssl arg to client constructor which controls SSL verification (https://github.com/rapidpro/rapidpro-python/pull/47)

2.1.6 (2017-03-02)
==================
* Fix to allow get_boundaries to specify the geometry parameter


2.1.5 (2017-02-06)
==================
* Add active run count to flow objects
* Start testing on Python 3.6
