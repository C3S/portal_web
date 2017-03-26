# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/collecting_society.portal

import os
import time
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


class benchmark(object):
    def __init__(self, request, name, uid, normalize=1.0, scale=1.0,
                 environment='development'):
        self.request = request
        if self.request.registry.settings.get('benchmark.' + name) != 'true':
            self.skip = True
            return
        self.skip = (self.request.registry.settings['env'] != environment)
        self.name = name
        self.uid = uid
        self.scale = scale
        if hasattr(normalize, 'read'):
            # file descriptor implies filesize in bytes
            normalize.seek(0, os.SEEK_END)
            self.normalize = normalize.tell()
            normalize.seek(0)
        elif isinstance(normalize, basestring) and os.path.isfile(normalize):
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
                'time': self.time,
                'normalize': self.normalize,
                'scale': self.scale,
                'result': self.result
            }
            csv_export(
                path=benchmark_file,
                row=row,
                fieldnames=csv_fieldnames,
                **csv_config
            )
        return False


def benchmarks():
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
        results[name] = {'means': {}}
        for uid in benchmark:
            runs = benchmark[uid]
            uidsum = 0
            for run in runs:
                uidsum += float(run['result'])
            results[name]['means'][uid] = uidsum / float(len(runs))
        means = results[name]['means']
        results[name]['mean'] = sum(means.values()) / float(len(means))

    return {'benchmarks': benchmarks, 'results': results}
