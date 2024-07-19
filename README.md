[![Build](https://github.com/whoschek/wbackup-zfs/actions/workflows/python-app.yml/badge.svg)](https://github.com/whoschek/wbackup-zfs/actions/workflows/python-app.yml)
wbackup-zfs
==========
*wbackup-zfs is a simple backup command line tool that reliably replicates ZFS snapshots from a (local or remote) source ZFS dataset (aka ZFS filesystem) and its descendant datasets to a (local or remote) destination ZFS dataset to make the destination dataset a recursively synchronized copy of the source dataset, using zfs send/receive/rollback/ destroy and ssh tunnel as directed. For example, wbackup-zfs can be used to incrementally replicate all ZFS snapshots since the most recent common snapshot from source to destination, in order to help protect against data loss or ransomware.*

When run for the first time, wbackup-zfs replicates the dataset and all its snapshots from the source to the destination. On subsequent runs, wbackup-zfs transfers only the data that has changed since the previous run, i.e. it incrementally replicates to the destination all intermediate snapshots that have been created on the source since the last run. Source ZFS snapshots older than the most recent common snapshot found on the destination are auto-skipped.

wbackup-zfs does not create or delete ZFS snapshots on the source - it assumes you have a ZFS snapshot management tool to do so, for example policy-driven Sanoid, pyznap, zrepl, zfs-auto-snapshot, manual zfs snapshot/destroy, etc. wbackup-zfs treats the source as read-only, thus the source remains unmodified. With the --dry-run flag, wbackup-zfs also treats the destination as read-only. In normal operation, wbackup-zfs treats the destination as append-only. Optional CLI flags are available to delete destination snapshots and destination datasets as directed, for example to make the destination identical to the source if the two have somehow diverged in unforeseen ways. This easily enables (re)synchronizing the backup from the production state, as well as restoring the production state from backup.

The source 'pushes to' the destination whereas the destination 'pulls from' the source. wbackup-zfs is installed and executed on the 'coordinator' host which can be either the host that contains the source dataset (push mode), or the destination dataset (pull mode), or both datasets (local mode, no network required, no ssh required), or any third-party (even non-ZFS) host as long as that host is able to SSH (via standard 'ssh' CLI) into both the source and destination host (pull-push mode). In Pull-push mode the source 'zfs send's the data stream to the coordinator which immediately pipes the stream (without storing it locally) to the destination host that 'zfs receive's it. Pull-push mode means that wbackup-zfs need not be installed or executed on either source or destination host. Only the underlying 'zfs' CLI must be installed on both source and destination host. wbackup-zfs can run as root or non-root user, in the latter case via a) sudo or b) when granted corresponding ZFS permissions by administrators via 'zfs allow' delegation mechanism.

Optionally, wbackup-zfs applies bandwidth rate-limiting and progress monitoring (via 'pv' CLI) during 'zfs send/receive' data transfers. When run across the network, wbackup-zfs also transparently inserts lightweight data compression (via 'zstd -1' CLI) and efficient data buffering (via 'mbuffer' CLI) into the pipeline between network endpoints during 'zfs send/receive' network transfers. If one of these utilities is not installed this is auto-detected, and the operation continues reliably without the corresponding auxiliary feature.


Example Usage
==========
Example in local mode (no network, no ssh) to replicate ZFS dataset tank1/foo/bar to tank2/boo/bar:

`    wbackup-zfs tank1/foo/bar tank2/boo/bar`

Same example in pull mode:

`    wbackup-zfs root@host1.example.com:tank1/foo/bar tank2/boo/bar`

Same example in push mode:

`    wbackup-zfs tank1/foo/bar root@host2.example.com:tank2/boo/bar`

Same example in pull-push mode:

`    wbackup-zfs root@host1:tank1/foo/bar root@host2:tank2/boo/bar`

Example in local mode (no network, no ssh) to recursively replicate ZFS dataset tank1/foo/bar and its descendant datasets to tank2/boo/bar:

`    wbackup-zfs tank1/foo/bar tank2/boo/bar --recursive`

Example that makes destination identical to source even if the two have drastically diverged:

`    wbackup-zfs tank1/foo/bar tank2/boo/bar --recursive --force --delete-missing-snapshots --delete-missing-datasets`

Example with further options:

`    wbackup-zfs tank1/foo/bar root@host2.example.com:tank2/boo/bar --recursive --exclude-dataset /tank1/foo/bar/temporary --exclude-dataset /tank1/foo/bar/baz/trash --exclude-dataset-regex '!(.*/)?public' --exclude-dataset-regex '(.*/)?[Tt][Ee]?[Mm][Pp][0-9]*' --ssh-private-key /root/.ssh/id_rsa`


How To Install, Run and Test
==========
Here is how to install and run the program as well as Unit tests:
```
    # Ubuntu / Debian:
    sudo apt-get -y install zfsutils-linux python3 # ensure zfs and python are installed
    sudo apt-get -y install zstd pv mbuffer # auxiliary helpers are optional

    git clone https://github.com/whoschek/wbackup-zfs.git
    cd wbackup-zfs
    ./wbackup-zfs --help # Run the CLI
    sudo cp wbackup-zfs /usr/local/bin/ # Optional system installation

    # Run Unit tests:
    # export wbackup_zfs_test_ssh_port=12345 # set this for unit tests if sshd is on a non-standard port (default is 22)
    ssh -p $wbackup_zfs_test_ssh_port 127.0.0.1 echo hello # verify user can ssh in via loopback interface & private key
    zfs --version # verify zfs is installed
    python3 --version # verify python 3.7 or higher is installed
    sudo ls # verify sudo is working
    test/test_wbackup_zfs.py # Run Unit tests
```


Automated Test Runs
==========
Results of automated test runs on a matrix of various old and new versions of ZFS/Python/Linux/FreeBSD/Solaris are
[here](https://github.com/whoschek/wbackup-zfs/actions/workflows/python-app.yml), as generated by
[this script](https://github.com/whoschek/wbackup-zfs/blob/main/.github/workflows/python-app.yml).
The script also demonstrates complete and functioning installation steps on Ubuntu, FreeBSD, Solaris, etc.

The gist is that it should work on any flavor, with python (3.7 or higher, no additional python packages required)
only needed on the coordinator host.


Usage
==========
```
usage: wbackup-zfs [-h] [--recursive]
                   [--include-dataset DATASET [DATASET ...]]
                   [--exclude-dataset DATASET [DATASET ...]]
                   [--include-dataset-regex REGEX [REGEX ...]]
                   [--exclude-dataset-regex REGEX [REGEX ...]]
                   [--include-snapshot-regex REGEX [REGEX ...]]
                   [--exclude-snapshot-regex REGEX [REGEX ...]] [--force]
                   [--force-once]
                   [--skip-missing-snapshots [{true,false,error}]]
                   [--skip-replication] [--delete-missing-snapshots]
                   [--delete-missing-datasets] [--ssh-config-file FILE]
                   [--ssh-private-key FILE] [--ssh-cipher STRING]
                   [--ssh-src-user STRING] [--ssh-dst-user STRING]
                   [--ssh-src-host STRING] [--ssh-dst-host STRING]
                   [--ssh-src-port INT] [--ssh-dst-port INT]
                   [--ssh-src-extra-opt STRING]
                   [--ssh-dst-extra-opt STRING] [--max-retries INT]
                   [--bwlimit STRING] [--no-privilege-elevation] [--dry-run]
                   [--verbose] [--quiet] [--version]
                   SRC_DATASET DST_DATASET
```

  SRC_DATASET           Source ZFS dataset (and its descendants) that will be replicated. Format is [[user@]host:]dataset. The host name can also be an IPv4 address. If the host name is '-', the dataset will be on the local host, and the corresponding SSH leg will be omitted. The same is true if the host is omitted and the dataset does not contain a ':' colon at the same time. Local dataset examples: `tank1/foo/bar`, `tank1`, `-:tank1/foo/bar:baz:boo` Remote dataset examples: `host:tank1/foo/bar`, `host.example.com:tank1/foo/bar`, `root@host:tank`, `root@host.example.com:tank1/foo/bar`, `user@127.0.0.1:tank1/foo/bar:baz:boo`. The first component of the ZFS dataset name is the ZFS pool name, here `tank1`.

  DST_DATASET           Destination ZFS dataset for replication. Has same naming format as SRC_DATASET. During replication, destination datasets that do not yet exist are created as necessary, along with their parent and ancestors.

  -h, --help            show this help message and exit

  --recursive, -r       During replication, also include descendant datasets, i.e. datasets within the dataset tree, including children, and children of children, etc.

  --include-dataset DATASET [DATASET ...]
                        During replication, include any ZFS dataset (and its descendants) that is contained within SRC_DATASET if its dataset name is one of the given include dataset names but none of the exclude dataset names. A dataset name is absolute if the specified dataset is prefixed by `/`, e.g. `/tank/baz/tmp`. Otherwise the dataset name is relative wrt. source and destination, e.g. `baz/tmp` if the source is `tank`. This option is automatically translated to an --include-dataset-regex (see below) and can be specified multiple times. If the option starts with a `@` prefix then dataset names are read from the newline-separated UTF-8 file given after the `@` prefix. Examples: `/tank/baz/tmp` (absolute), `baz/tmp` (relative), `@dataset_names.txt`, `@/path/to/dataset_names.txt`

  --exclude-dataset DATASET [DATASET ...]
                        Same syntax as --include-dataset (see above) except that the option is automatically translated to an --exclude-dataset-regex (see below).

  --include-dataset-regex REGEX [REGEX ...]
                        During replication, include any ZFS dataset (and its descendants) that is contained within SRC_DATASET if its relative dataset path (e.g. `baz/tmp`) wrt SRC_DATASET matches at least one of the given include regular expressions but none of the exclude regular expressions. This option can be specified multiple times. A leading `!` character indicates logical negation, i.e. the regex matches if the regex with the leading `!` character removed does not match. Default: `.*` (include all datasets). Examples: `baz/tmp`, `(.*/)?doc[^/]*/(private|confidential).*`, `!public`

  --exclude-dataset-regex REGEX [REGEX ...]
                        Same syntax as --include-dataset-regex (see above) except that the default is `(.*/)?[Tt][Ee]?[Mm][Pp][0-9]*`

  --include-snapshot-regex REGEX [REGEX ...]
                        During replication, include any ZFS snapshot that has a name (i.e. the part after the '@') that matches at least one of the given include regular expressions but none of the exclude regular expressions. This option can be specified multiple times. A leading `!` character indicates logical negation, i.e. the regex matches if the regex with the leading `!` character removed does not match. Default: `.*` (include all snapshots). Examples: `test_.*`, `!prod_.*`, `.*_(hourly|frequent)`, `!.*_(weekly|daily)`

  --exclude-snapshot-regex REGEX [REGEX ...]
                        Same syntax as --include-snapshot-regex (see above) except that the default is to exclude no snapshots.

  --force               Before replication, delete destination ZFS snapshots that are more recent than the most recent common snapshot found on the source ('conflicting snapshots') and rollback the destination dataset correspondingly before starting replication. Also, if no common snapshot is found then delete all destination snapshots before starting replication. Without the --force flag, the destination dataset is treated as append-only, hence no destination snapshot that already exists is deleted, and instead the operation is aborted with an error when encountering a conflicting snapshot.

  --force-once, -f1     Use the --force option at most once to resolve a conflict, then abort with an error on any subsequent conflict. This helps to interactively resolve conflicts, one conflict at a time.

  --skip-missing-snapshots [{true,false,error}]
                        Default is 'true'. During replication, handle source datasets that have no snapshots as follows: a) 'error': Abort with an error if --recursive. b) 'true': Skip the source dataset and its descendants with a warning if --recursive. c) otherwise (regardless of --recursive flag): If destination snapshots exist, delete them (with --force) or abort with an error (without --force). Create empty destination dataset and ancestors if they do not yet exist and source dataset has at least one descendant with a snapshot.

  --skip-replication    Skip replication step (see above) and proceed to the optional --delete-missing-snapshots step immediately (see below).

  --delete-missing-snapshots
                        After successful replication, delete existing destination snapshots that do not exist within the source dataset if they match at least one of --include-snapshot-regex but none of --exclude-snapshot-regex and the destination dataset is included via --{include|exclude}-dataset-regex --{include|exclude}-dataset policy.

  --delete-missing-datasets
                        After successful replication step and successful --delete-missing-snapshots step, if any, delete existing destination datasets that do not exist within the source dataset if they are included via --{include|exclude}-dataset-regex --{include|exclude}-dataset policy. Also delete an existing destination dataset that has no snapshot if all descendants of that dataset do not have a snapshot either (again, only if the existing destination dataset is included via --{include|exclude}-dataset-regex --{include|exclude}-dataset policy). Does not recurse without --recursive.

  --ssh-config-file FILE
                        Path to SSH ssh_config(5) file (optional); will be passed into ssh -F CLI.

  --ssh-private-key FILE
                        Path to SSH private key file on local host (optional); will be passed into ssh -i CLI. default: $HOME/.ssh/id_rsa

  --ssh-cipher STRING   Name of SSH cipher specification for encrypting the session (optional); will be passed into ssh -c CLI. (default: aes256-gcm@openssh.com)

  --ssh-src-user STRING Remote SSH username of source host to connect to (optional). Overrides username given in SRC_DATASET.

  --ssh-dst-user STRING Remote SSH username of destination host to connect to (optional). Overrides username given in DST_DATASET.

  --ssh-src-host STRING Remote SSH hostname of source host to connect to (optional). Can also be an IPv4 or IPv6 address. Overrides hostname given in SRC_DATASET.

  --ssh-dst-host STRING Remote SSH hostname of destination host to connect to (optional). Can also be an IPv4 or IPv6 address. Overrides hostname given in DST_DATASET.

  --ssh-src-port INT    Remote SSH port of source host to connect to (optional).

  --ssh-dst-port INT
                        Remote SSH port of destination host to connect to (optional).

  --ssh-src-extra-opt STRING
                        Additional option to be passed to ssh CLI when connecting to source host (optional). This option can be specified multiple times. Example: `-v -v --ssh-src-extra-opt '-v -v'` to debug ssh config issues.

  --ssh-dst-extra-opt STRING
                        Additional option to be passed to ssh CLI when connecting to destination host (optional). This option can be specified multiple times. Example: `-v -v --ssh-dst-extra-opt '-v -v'` to debug ssh config issues.

  --max-retries INT     The number of times a zfs send/receive data transfer shall be retried if it fails across the network (default: 0).

  --bwlimit STRING     'pv' bandwidth rate limit for zfs send/receive data transfer (optional). Example: `100m` to cap throughput at 100 MB/sec. Default is unlimited. Also see https://linux.die.net/man/1/pv

  --no-privilege-elevation, -p
                        Do not attempt to run state changing ZFS operations 'zfs create/rollback/destroy/send/receive' as root (via 'sudo -u root' elevation granted by appending this to /etc/sudoers: `<NON_ROOT_USER_NAME> ALL=NOPASSWD:/path/to/zfs`). Instead, the --no-privilege-elevation flag is for non-root users that have been granted corresponding ZFS permissions by administrators via 'zfs allow' delegation mechanism, like so: sudo zfs allow -u $NON_ROOT_USER_NAME send,hold,bookmark $SRC_DATASET; sudo zfs allow -u $NON_ROOT_USER_NAME mount,create,receive,rollback,destroy,canmount,mountpoint,readonly,compression,encryption,keylocation,recordsize $DST_DATASET_OR_POOL; If you do not plan to use the --force flag or --delete-missing-snapshots or --delete-missing-dataset then ZFS permissions 'rollback,destroy' can be omitted. If you do not plan to customize the respective ZFS dataset property then ZFS permissions 'canmount,mountpoint,readonly,compression,encryption,keylocation,recordsize' can be omitted. Also see https://tinyurl.com/yuyj23pz and https://tinyurl.com/9h97kh8n and https://github.com/openzfs/zfs/issues/13024

  --dry-run, -n         Do a dry-run (aka 'no-op') to print what operations would happen if the command were to be executed for real. This option treats both the ZFS source and destination as read-only.

  --verbose, -v         Print verbose information. This option can be specified multiple times to increase the level of verbosity. To print what ZFS/SSH operation exactly is happening (or would happen), add the `-v -v` flag, maybe along with --dry-run. ERROR, WARN, INFO, DEBUG, TRACE output lines are identified by [E], [W], [I], [D], [T] prefixes, respectively.

  --quiet, -q           Suppress non-error, info, debug, and trace output.

  --version             Display version information and exit.
