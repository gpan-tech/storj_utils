#!/usr/bin/python3
import sys
import json
from datetime import datetime

class Line_buffer:

    def __init__(self):
        self.line   = None
        self._back1 = False
        self.isEOF  = False

    def go_back(self):
        if self._back1: raise ValueError('Line_buffer cannot back up twice')
        self._back1 = True

    def get_line(self):
        if self._back1:
            self._back1 = False
            return self.line
        else:
            try:
                line = input()
                while not line:
                    line = input()
                self.line = line
                return line
            except EOFError:
                self.isEOF = True
                return None

class Record:
    def __init__(self):
        self.date = 0
        self.up_ok          = 0
        self.up_ok_size     = 0
        self.up_fail        = 0
        self.up_cancel      = 0
        self.down_ok        = 0
        self.down_ok_size   = 0
        self.down_ok_unseen = 0
        self.down_fail        = 0
        self.down_fail_size   = 0
        self.down_fail_unseen = 0
        self.down_cancel        = 0
        self.down_cancel_size   = 0
        self.down_cancel_unseen = 0
        self.del_ok        = 0
        self.del_ok_size   = 0
        self.del_ok_unseen = 0

class Stats:

    def __init__(self, period):
        # seconds beteween records
        self.period = period
        # this buffer will help rewind 1 line after we read it
        self.line_buffer = Line_buffer()
        # maps piece id -> size
        self.pieces = {}
        # when piece size is not logged, we estimate based on hdd space difference
        self.available_space = 0
        self.pieces_no_size  = set()

    def get_all_records(self):
        records = []
        while not self.line_buffer.isEOF:
            print('Record', len(records), end='\r')
            records.append(self.get_1_record())
        return records

    def get_1_record(self):
        rec = Record()
        while True:
            line = self.line_buffer.get_line()
            if line is None:
                break
            try:
                parts = line.split('\t')
                date  = datetime.strptime(parts[0], '%Y-%m-%dT%H:%M:%S.%fZ').timestamp()
                if not rec.date:
                    rec.date = ((int(date) // self.period) + 1) * self.period
                elif date >= rec.date:
                    # oops, have read in the next period
                    self.line_buffer.go_back()
                    break
                module = parts[2]
                if module == 'piecestore':
                    event = parts[3]
                    data  = json.loads(parts[4])
                    pid   = data['Piece ID']
                    if event == 'upload started':
                        delta                = self.available_space - data['Available Space']
                        self.available_space = data['Available Space']
                        pieces_count         = len(self.pieces_no_size)
                        if pieces_count > 0:
                            # sometimes the delta is negative (something got deleted) or too large (disk used by non-storj files),
                            # so we can't estimate the upload size and will treat it as 'unseen'.
                            if 0 < delta < 10000000:
                                size = delta // pieces_count
                                for pid in self.pieces_no_size:
                                    rec.up_ok       += 1
                                    rec.up_ok_size  += size
                                    self.pieces[pid] = size
                            else:
                                # print('! Unrealistic available space delta', delta/1e6, file=sys.stderr)
                                pass
                            self.pieces_no_size = set()
                    elif event == 'uploaded':
                        size = data.get('Size')
                        if size is None: self.pieces_no_size.add(pid)
                        else:
                            rec.up_ok      += 1
                            rec.up_ok_size += size
                            self.pieces[pid] = size
                    elif event == 'upload failed':    rec.up_fail   += 1
                    elif event == 'upload canceled':  rec.up_cancel += 1
                    elif event == 'download started': pass
                    elif event == 'downloaded':
                        size = self.pieces.get(pid)
                        rec.down_ok += 1
                        if size is None: rec.down_ok_unseen += 1
                        else:            rec.down_ok_size   += size
                    elif event == 'download failed':
                        size = self.pieces.get(pid)
                        rec.down_fail += 1
                        if size is None: rec.down_fail_unseen += 1
                        else:            rec.down_fail_size   += size
                    elif event == 'download canceled':
                        size = self.pieces.get(pid)
                        rec.down_cancel += 1
                        if size is None: rec.down_cancel_unseen += 1
                        else:            rec.down_cancel_size   += size
                    else:
                        print('! Unexpected line:  ', line, file=sys.stderr)
                elif module == 'piecedeleter':
                    event = parts[3]
                    data  = json.loads(parts[4])
                    pid   = data['Piece ID']
                    if event in ('deleted', 'delete failed'):
                        size = self.pieces.pop(pid, None)
                        rec.del_ok += 1
                        if size is None: rec.del_ok_unseen += 1
                        else:            rec.del_ok_size   += size
                    else:
                        print('! Unexpected line:  ', line, file=sys.stderr)
                else:
                    pass
            except (IndexError, KeyError) as ex:
                print('! Bad line:  ', line, '  Error:', repr(ex), file=sys.stderr)
        # corrections
        rec.date        -= self.period
        rec.down_ok     -= rec.down_ok_unseen
        rec.down_fail   -= rec.down_fail_unseen
        rec.down_cancel -= rec.down_cancel_unseen
        rec.del_ok      -= rec.del_ok_unseen
        return rec

# Fit in 2 chars
def percent(a, b):
    if b == 0:      return '  '
    r = 100 * a / b
    if   r <   0.1: return '.0'
    elif r <   1.0: return '.{:1}'.format(int(r * 10))
    elif r < 100.0: return '{:2}'.format(int(r))
    else:           return '99'


days = int(sys.argv[1])
if days < 1:
    print('At least 1 day per period, not:', days)
    sys.exit(1)

stats   = Stats(days * 24 * 3600)
records = stats.get_all_records()

print('Completed', file=sys.stderr, flush=True)
print(flush=True)

print('## Uploads (ingress, PUT)')
print('Date UTC   | OK count |  % | Size GB | Failed  |  % | Canceled |  %')
print('-----------|----------|----|---------|---------|----|----------|---')
for rec in records:
    tot_up = rec.up_ok + rec.up_fail + rec.up_cancel
    print('{} | {:8} | {} | {:7.2f} | {:7} | {} | {:8} | {}'.format(
        datetime.utcfromtimestamp(rec.date).strftime('%Y-%m-%d'),
        rec.up_ok,     percent(rec.up_ok,     tot_up),
        rec.up_ok_size / 1e9,
        rec.up_fail,   percent(rec.up_fail,   tot_up),
        rec.up_cancel, percent(rec.up_cancel, tot_up)
    ))
print()

print('## Downloads (egress, GET)')
print('Date UTC   | OK count + Unseen |  % + % | Size GB |  % | Failed   + Unseen |  % + % | Size GB |  % | Canceled + Unseen |  % + % | Size GB |  %')
print('-----------|-------------------|--------|---------|----|-------------------|--------|---------|----|-------------------|--------|---------|---')
for rec in records:
    tot_down      = rec.down_ok + rec.down_ok_unseen + rec.down_fail + rec.down_fail_unseen + rec.down_cancel + rec.down_cancel_unseen
    tot_down_size = rec.down_ok_size             + rec.down_fail_size               + rec.down_cancel_size
    print('{} | {:8} +{:7} | {} +{} | {:7.2f} | {} | {:8} +{:7} | {} +{} | {:7.2f} | {} | {:8} +{:7} | {} +{} | {:7.2f} | {}'.format(
        datetime.utcfromtimestamp(rec.date).strftime('%Y-%m-%d'),
        rec.down_ok,     rec.down_ok_unseen,     percent(rec.down_ok,     tot_down), percent(rec.down_ok_unseen,     tot_down),
        rec.down_ok_size     / 1e9,              percent(rec.down_ok_size,                                           tot_down_size),
        rec.down_fail,   rec.down_fail_unseen,   percent(rec.down_fail,   tot_down), percent(rec.down_fail_unseen,   tot_down),
        rec.down_fail_size   / 1e9,              percent(rec.down_fail_size,                                         tot_down_size),
        rec.down_cancel, rec.down_cancel_unseen, percent(rec.down_cancel, tot_down), percent(rec.down_cancel_unseen, tot_down),
        rec.down_cancel_size / 1e9,              percent(rec.down_cancel_size,                                       tot_down_size)
    ))
print()

print('## Deletes')
print('Date UTC   | OK count + Unseen |  % + % | Size GB')
print('-----------|-------------------|--------|--------')
for rec in records:
    tot_del      = rec.del_ok + rec.del_ok_unseen
    tot_del_size = rec.del_ok_size
    print('{} | {:8} +{:7} | {} +{} | {:7.2f}'.format(
        datetime.utcfromtimestamp(rec.date).strftime('%Y-%m-%d'),
        rec.del_ok, rec.del_ok_unseen, percent(rec.del_ok, tot_del), percent(rec.del_ok_unseen, tot_del),
        rec.del_ok_size / 1e9
    ))
print()

print('## Other stats')
print('Seen pieces remaining: {:8}, {:7.2f} GB'.format(len(stats.pieces), sum(stats.pieces.values()) / 1e9))
print('Available Space: {:7.2f} GB'.format(stats.available_space / 1e9))

if stats.pieces_no_size:
    print('! Leftover pieces without known size:', stats.pieces_no_size)

print()
