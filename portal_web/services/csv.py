# For copyright and license terms, see COPYRIGHT.rst (top level of repository)
# Repository: https://github.com/C3S/portal_web

import os
import csv

config_defaults = {
    'delimiter': ',',
    'quotechar': '"'
}


def csv_import(path, **kwargs):

    # sanity checks
    if not os.path.isfile(path):
        IOError("File not found: " + path)
    cfg = config_defaults.copy()
    if kwargs:
        cfg.update(kwargs)

    # read
    with open(path, 'r') as csvfile:
        reader = csv.DictReader(csvfile, **cfg)
        return list(reader)


def csv_export(path, row, mode='a', **kwargs):

    # sanity checks
    if not row:
        return
    supported_modes = ('w', 'a')
    if mode not in supported_modes:
        KeyError(
            'mode "' + mode + '" not supported. '
            'supported modes: ' + supported_modes + ')'
        )
    cfg = config_defaults.copy()
    if kwargs:
        cfg.update(kwargs)
    if not cfg.get('fieldnames'):
        KeyError('argument "fieldnames" ist missing.')
    fieldnames = cfg.get('fieldnames')
    del cfg['fieldnames']

    # write
    write_header = (not os.path.isfile(path))
    with open(path, mode) as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames, **cfg)
        if write_header:
            writer.writeheader()
        writer.writerow(row)
