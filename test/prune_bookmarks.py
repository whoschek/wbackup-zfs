#!/usr/bin/env python3
#
# Copyright 2024 Wolfgang Hoschek AT mac DOT com
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import subprocess
import time
from collections import defaultdict


def main():
    parser = argparse.ArgumentParser(
        description="Example ZFS bookmark pruning script that deletes the oldest bookmarks older than X days in a "
                    "given dataset and optionally also its descendant datasets, such that each dataset retains at "
                    "least N bookmarks.")
    parser.add_argument('--dataset', type=str, required=True,
                        help="Dataset to prune bookmarks for.")
    parser.add_argument('--recursive', '-r', action='store_true',
                        help="Include this flag to prune datasets recursively.")
    parser.add_argument('--days', type=int, default=90,
                        help="Number of days to retain bookmarks (default: 90).")
    parser.add_argument('--min-bookmarks-to-retain', type=int, default=100,
                        help="Minimum number of bookmarks to retain per dataset (default: 100).")
    parser.add_argument('--snapshot', '-s', action='store_true',
                        help="Actually delete snapshots instead of bookmarks.")
    parser.add_argument('--dry-run', '-n', action='store_true',
                        help="Include this flag to print what would happen if the command were to be run for real.")

    args = parser.parse_args()
    kind = 'snapshot' if args.snapshot else 'bookmark'
    cmd = ['zfs', 'list', '-t', kind, '-Hp', '-o', 'creation,name', '-s', 'name']
    if args.recursive:
        cmd.append('-r')
    cmd.append(args.dataset)
    datasets = defaultdict(list)
    for line in subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.splitlines():
        creation_time, bookmark = line.split('\t', 1)
        dataset = bookmark.split('@' if args.snapshot else '#', 1)[0]
        datasets[dataset].append((int(creation_time), bookmark))

    for dataset, bookmarks in sorted(datasets.items()):
        n = max(0, len(bookmarks) - args.min_bookmarks_to_retain)
        for bookmark in [bmark for ts, bmark in sorted(bookmarks) if ts < int(time.time()) - args.days * 86400][0:n]:
            msg = "Would delete" if args.dry_run else "Deleting"
            print(f"{msg} {kind}: {bookmark} ...")
            if not args.dry_run:
                subprocess.run(['sudo', 'zfs', 'destroy', bookmark], capture_output=True, text=True, check=True)


if __name__ == "__main__":
    main()
