# Point-in-Time Feature Audit

Feature families with unverifiable source timing are excluded from strict model frames.
A current ClinicalTrials.gov record is not treated as a historical snapshot.

## Summary

- violations: 15
- unverified: 122
- affected_catalysts: 122
- by_check: {'exposure_after_cutoff': 1, 'fundamental_filed_after_cutoff': 3, 'trial_first_posted_after_cutoff': 11, 'trial_snapshot_observed_after_cutoff': 122}

## Findings

catalyst_id                                check   severity         observed_at cutoff_date
   CAT-C087                exposure_after_cutoff       FAIL          2022-04-04  2021-11-19
   CAT-C038       fundamental_filed_after_cutoff       FAIL          2018-07-26  2018-06-16
   CAT-C084       fundamental_filed_after_cutoff       FAIL          2022-02-18  2021-12-12
   CAT-C087       fundamental_filed_after_cutoff       FAIL          2022-02-18  2021-11-19
   CAT-C014 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 21:07:44  2016-05-31
   CAT-C009 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 21:07:44  2016-06-05
   CAT-C011 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 21:07:44  2013-06-02
   CAT-C007 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 21:07:44  2014-12-09
   CAT-C005 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 21:07:44  2015-10-24
   CAT-F001 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 21:37:18  2018-06-03
   CAT-F002 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 21:37:19  2016-06-20
   CAT-F003 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 21:37:19  2013-05-01
   CAT-F004 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 21:37:21  2018-08-23
   CAT-C003 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 21:43:13  2012-10-18
   CAT-C004 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 21:43:14  2014-05-19
   CAT-C008 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 21:43:16  2012-04-30
   CAT-C015 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 21:43:18  2016-04-20
   CAT-C016 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 21:43:19  2015-09-29
   CAT-C017 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 21:43:20  2015-11-18
   CAT-C018 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 21:43:21  2012-11-18
   CAT-C019 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 21:43:22  2013-10-31
   CAT-C025 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 21:43:26  2010-02-03
   CAT-C026 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 21:43:28  2013-10-13
   CAT-C027 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 21:43:30  2013-09-11
   CAT-F005 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 21:43:33  2013-09-09
   CAT-F007 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 21:43:34  2016-03-01
   CAT-F008 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 21:43:35  2016-05-24
   CAT-F009 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 21:43:38  2019-06-13
   CAT-F010 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 21:43:39  2015-08-16
   CAT-C029 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 21:43:39  2018-08-26
   CAT-C030 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 21:43:40  2019-01-14
   CAT-C006 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 21:49:18  2014-06-09
   CAT-C010 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 21:49:19  2018-06-17
   CAT-C021 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 21:49:20  2017-07-31
   CAT-C022 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 21:49:22  2019-03-12
   CAT-C002 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 21:49:24  2014-09-09
   CAT-C001 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 21:49:26  2012-12-17
   CAT-C020 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 21:49:26  2017-06-05
   CAT-C023 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 21:49:28  2009-12-31
   CAT-C024 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 21:49:29  2014-11-30
   CAT-F011 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 21:49:32  2010-05-31
   CAT-F012 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 21:51:23  2013-06-16
   CAT-C031 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:02:08  2013-06-01
   CAT-C032 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:02:09  2014-06-01
   CAT-C034 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:02:11  2012-12-07
   CAT-C035 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:02:12  2021-12-11
   CAT-C036 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:02:13  2014-12-05
   CAT-C040 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:02:19  2014-04-29
   CAT-C041 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:02:21  2016-05-04
   CAT-C042 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:02:22  2015-09-25
   CAT-C044 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:02:26  2012-08-21
   CAT-C045 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:02:26  2012-11-18
   CAT-C046 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:02:28  2014-07-30
   CAT-C048 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:02:31  2014-11-22
   CAT-C050 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:02:33  2012-09-21
   CAT-C051 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:02:34  2017-02-07
   CAT-C052 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:02:37  2025-01-13
   CAT-C054 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:02:39  2011-11-16
   CAT-C057 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:02:42  2011-08-22
   CAT-C059 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:02:44  2017-05-07
   CAT-C060 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:02:45  2016-05-25
   CAT-C061 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:02:47  2015-01-22
   CAT-C062 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:02:48  2017-06-20
   CAT-C063 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:02:50  2018-05-28
   CAT-C064 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:02:50  2025-05-30
   CAT-C065 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:02:52  2026-04-15
   CAT-F013 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:02:54  2015-10-20
   CAT-F014 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:02:55  2013-04-23
   CAT-F015 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:02:56  2011-12-22
   CAT-F017 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:03:00  2015-10-14
   CAT-F021 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:03:06  2016-11-21
   CAT-F023 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:03:08  2013-06-23
   CAT-F026 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:03:11  2018-04-15
   CAT-F027 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:03:12  2018-04-18
   CAT-F028 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:03:13  2019-01-07
   CAT-F033 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:03:20  2020-12-01
   CAT-F034 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:03:22  2021-05-19
   CAT-F037 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:03:25  2012-05-23
   CAT-C033 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:11:51  2014-06-01
   CAT-C037 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:11:53  2017-12-07
   CAT-C038 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:11:53  2018-06-16
   CAT-C039 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:11:56  2026-03-19
   CAT-C043 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:11:57  2021-05-23
   CAT-C047 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:11:58  2014-11-22
   CAT-C055 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:12:01  2017-05-07
   CAT-C058 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:12:03  2017-06-22
   CAT-F022 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:12:07  2012-06-23
   CAT-F029 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:12:11  2016-02-08
   CAT-F030 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:12:12  2019-03-24
   CAT-C066 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:12:19  2024-06-24
   CAT-C067 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:12:20  2024-05-30
   CAT-C068 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:12:21  2016-12-04
   CAT-C069 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:12:22  2024-04-17
   CAT-C070 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:12:23  2022-12-28
   CAT-C071 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:12:24  2015-04-14
   CAT-C072 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:12:25  2019-07-23
   CAT-C073 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:12:26  2022-07-14
   CAT-C074 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:12:28  2025-11-04
   CAT-C075 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:12:29  2018-04-24
   CAT-C076 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:12:30  2018-03-05
   CAT-C077 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:12:32  2016-12-02
   CAT-C078 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:12:34  2022-03-13
   CAT-C080 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:12:36  2019-07-14
   CAT-C081 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:12:37  2022-06-07
   CAT-C082 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:12:38  2019-07-04
   CAT-C083 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:12:40  2022-11-30
   CAT-C084 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:12:42  2021-12-12
   CAT-C085 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:12:45  2024-12-17
   CAT-C086 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:12:47  2017-08-14
   CAT-C087 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:12:49  2021-11-19
   CAT-C088 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:12:50  2021-01-19
   CAT-C089 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:12:52  2018-09-24
   CAT-C090 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:12:53  2022-05-31
   CAT-F043 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:12:56  2019-03-24
   CAT-F044 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:12:57  2020-06-30
   CAT-F045 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-19 22:12:58  2017-04-09
 CAT-GH0003 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-20 02:16:29  2015-07-31
 CAT-GH0008 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-20 02:16:42  2016-01-07
 CAT-GH0012 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-20 02:16:35  2016-06-05
 CAT-GH0019 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-20 02:16:41  2016-06-29
 CAT-GH0020 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-20 02:16:42  2016-07-10
 CAT-GH0021 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-20 02:16:43  2016-07-13
 CAT-GH0024 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-20 02:16:47  2016-08-11
 CAT-GH0001 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-20 02:17:11  2015-03-16
 CAT-GH0006 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-20 02:17:16  2015-10-26
 CAT-GH0017 trial_snapshot_observed_after_cutoff UNVERIFIED 2026-08-20 02:17:28  2016-06-15
   CAT-C008      trial_first_posted_after_cutoff       FAIL          2012-07-02  2012-04-30
   CAT-C016      trial_first_posted_after_cutoff       FAIL          2015-10-15  2015-09-29
   CAT-C019      trial_first_posted_after_cutoff       FAIL          2013-12-09  2013-10-31
   CAT-C025      trial_first_posted_after_cutoff       FAIL          2010-03-05  2010-02-03
   CAT-F008      trial_first_posted_after_cutoff       FAIL          2016-06-08  2016-05-24
   CAT-C021      trial_first_posted_after_cutoff       FAIL          2019-01-31  2017-07-31
   CAT-C024      trial_first_posted_after_cutoff       FAIL          2015-04-13  2014-11-30
   CAT-F011      trial_first_posted_after_cutoff       FAIL          2010-06-14  2010-05-31
   CAT-F012      trial_first_posted_after_cutoff       FAIL          2013-06-20  2013-06-16
 CAT-GH0024      trial_first_posted_after_cutoff       FAIL          2019-03-25  2016-08-11
 CAT-GH0006      trial_first_posted_after_cutoff       FAIL          2016-10-11  2015-10-26