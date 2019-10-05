# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/portal_web

import os
import time
import datetime
import logging

from . import (
    csv_import,
    csv_export
)

benchmark_file = "/ado/tmp/benchmark/benchmark.csv"
csv_config = {
    'delimiter': ',',
    'quotechar': '"'
}
csv_fieldnames = [
    'name',
    'uid',
    'start',
    'end',
    'time',
    'normalize',
    'scale',
    'result'
]

log = logging.getLogger(__name__)


class benchmark():
    def __init__(self, request, name,
                 uid=datetime.datetime.now().strftime('%a, %d %b %Y %H:%M:%S'),
                 normalize=1.0, scale=1.0, environment='development'):
        self.request = request
        self.skip = False
        if self.request.registry.settings['env'] != environment:
            self.skip = True
        if self.request.registry.settings.get(
                'benchmark.' + name) != 'true':
            self.skip = True
        if self.skip:
            return
        self.name = name
        self.uid = uid
        self.scale = scale
        if hasattr(normalize, 'read'):
            # file descriptor implies filesize in bytes
            normalize.seek(0, os.SEEK_END)
            self.normalize = normalize.tell()
            normalize.seek(0)
        elif isinstance(
                normalize, basestring   # noqa: F821
             ) and os.path.isfile(normalize):
            # valid path implies filesize in bytes
            self.normalize = os.path.getsize(normalize)
        else:
            self.normalize = normalize
        if not self.normalize or not self.scale:
            self.skip = True
        # check paths
        if not os.path.exists(os.path.dirname(benchmark_file)):
            os.makedirs(os.path.dirname(benchmark_file))

    def __enter__(self):
        if self.skip:
            return
        self.start = time.time()

    def __exit__(self, ty, val, tb):
        if self.skip:
            return
        self.end = time.time()
        self.time = self.end - self.start
        if self.time:
            self.result = self.time / self.normalize * self.scale
            row = {
                'name': self.name,
                'uid': self.uid,
                'start': self.start,
                'end': self.end,
                'time': '%f' % self.time,
                'normalize': self.normalize,
                'scale': self.scale,
                'result': '%f' % self.result
            }
            csv_export(
                path=benchmark_file,
                row=row,
                fieldnames=csv_fieldnames,
                **csv_config
            )
        return False


def benchmarks(delete=False):
    if delete and os.path.isfile(benchmark_file):
        os.remove(benchmark_file)
    if not os.path.isfile(benchmark_file):
        return {'benchmarks': None, 'results': None}

    # import
    rows = csv_import(benchmark_file, **csv_config)

    # details
    benchmarks = {}
    for row in rows:
        if not benchmarks.get(row['name']):
            benchmarks[row['name']] = {}
        if not benchmarks[row['name']].get(row['uid']):
            benchmarks[row['name']][row['uid']] = []
        benchmarks[row['name']][row['uid']].append({
            'start': row['start'],
            'end': row['end'],
            'time': row['time'],
            'normalize': row['normalize'],
            'scale': row['scale'],
            'result': row['result']
        })

    # results
    results = {}
    for name in benchmarks:
        benchmark = benchmarks[name]
        results[name] = {'means': {}, 'sums': {}}
        for uid in benchmark:
            runs = benchmark[uid]
            uidsum = 0
            for run in runs:
                uidsum += float(run['result'])
            results[name]['sums'][uid] = uidsum
            results[name]['means'][uid] = uidsum / float(len(runs))
        means = results[name]['means']
        sums = results[name]['sums']
        results[name]['sum'] = '%f' % sum(sums.values())
        results[name]['mean'] = '%f' % (
            sum(means.values()) / float(len(means)))
        for uid in benchmark:
            results[name]['sums'][uid] = '%f' % results[name]['sums'][uid]
            results[name]['means'][uid] = '%f' % results[name]['means'][uid]

    return {'benchmarks': benchmarks, 'results': results}
