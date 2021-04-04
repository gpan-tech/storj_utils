# Storj node operator (SNO) utils

Small utils/scripts for Storj node related tasks.

**Don't use if you don't understand what the scripts do!**  
**Some may take a lot of memory and/or cpu time, so it's better to not run them on the same machine as the node (if possible).**

### Script 1: [log_stats.py](log_stats.py)

Typical usage (weekly stats):
```
cat somewhere/node*.log | python3 log_stats.py 7
```

Syntax:
```
log_stats.py <days>
```

Reads the node's log and prints out useful stats per `<days>` days. Days start at 00:00 UTC.

Sample output:
```
Completed

## Uploads (ingress, PUT)
Date UTC   | OK count |  % | Size GB | Failed  |  % | Canceled |  %
-----------|----------|----|---------|---------|----|----------|---
2021-02-11 |    48298 | 99 |   16.95 |      52 | .1 |      203 | .4
2021-02-18 |   124496 | 97 |  158.96 |     104 | .0 |     3018 |  2
2021-02-25 |   119926 | 98 |  122.28 |     132 | .1 |     1586 |  1
2021-03-04 |   183422 | 99 |   85.44 |     134 | .0 |     1023 | .5
2021-03-11 |   260570 | 99 |  118.77 |     217 | .0 |     1167 | .4
2021-03-18 |   228673 | 99 |   82.73 |     129 | .0 |     1028 | .4

## Downloads (egress, GET)
Date UTC   | OK count + Unseen |  % + % | Size GB |  % | Failed   + Unseen |  % + % | Size GB |  % | Canceled + Unseen |  % + % | Size GB |  %
-----------|-------------------|--------|---------|----|-------------------|--------|---------|----|-------------------|--------|---------|---
2021-02-11 |    23628 +   1171 | 88 + 4 |   14.45 | 84 |      384 +     24 |  1 +.0 |    0.62 |  3 |     1535 +     66 |  5 +.2 |    1.99 | 11
2021-02-18 |    27714 +   1261 | 88 + 4 |   17.28 | 85 |      517 +     25 |  1 +.0 |    0.75 |  3 |     1809 +     60 |  5 +.1 |    2.24 | 11
2021-02-25 |    20713 +   1074 | 87 + 4 |   15.25 | 86 |      379 +      9 |  1 +.0 |    0.55 |  3 |     1451 +     65 |  6 +.2 |    1.76 | 10
2021-03-04 |    22810 +    705 | 91 + 2 |   14.14 | 89 |      263 +      9 |  1 +.0 |    0.36 |  2 |     1098 +     38 |  4 +.1 |    1.25 |  7
2021-03-11 |    11116 +    486 | 89 + 3 |   10.34 | 90 |      181 +      5 |  1 +.0 |    0.27 |  2 |      677 +     24 |  5 +.1 |    0.87 |  7
2021-03-18 |     6077 +    315 | 88 + 4 |    8.01 | 92 |       74 +      7 |  1 +.1 |    0.12 |  1 |      351 +      7 |  5 +.1 |    0.54 |  6

## Deletes
Date UTC   | OK count + Unseen |  % + % | Size GB
-----------|-------------------|--------|--------
2021-02-11 |    29249 +    381 | 98 + 1 |    5.85
2021-02-18 |    84084 +   2586 | 97 + 2 |   35.48
2021-02-25 |    84236 +   2124 | 97 + 2 |   32.57
2021-03-04 |   133439 +   2143 | 98 + 1 |   31.54
2021-03-11 |   185262 +   3138 | 98 + 1 |   43.30
2021-03-18 |   106875 +   1860 | 98 + 1 |   26.58

## Other stats
Seen pieces remaining:  1572415, 1150.77 GB
Available Space: 1955.64 GB
```

The columns show either number of pieces or GB.  
'Unseen' are the pieces that were downloaded/deleted but the matching upload line couldn't be found in the log, so the piece's size couldn't be determined.  
The log shows the size of each piece when it was uploaded, but in the past it didn't, so in that case, the scipt tries to guess based on the available disk space before and after the upload. This may not always work, so a piece might be marked as 'Unseen' even if there is a matching 'uploaded' line in the log.

## Other useful utils [links]

[Storj Earnings Calculator](https://github.com/ReneSmeekes/storj_earnings), [forum](https://forum.storj.io/t/earnings-calculator-update-2021-03-05-v10-1-1-detailed-payout-information-now-includes-comparison-to-actual-payout-postponed-payouts-due-to-threshold-and-transaction-links/1794)
[Success rate script](https://github.com/ReneSmeekes/storj_success_rate), [forum](https://forum.storj.io/t/success-rate-script-now-updated-for-new-terminology-in-logs-after-update-to-0-34-6-or-later/5114)
