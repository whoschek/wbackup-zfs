#!/usr/bin/env sh
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

# Note: csh syntax following here as default shell on freebsd <= 13 is csh instead of sh
pkg install -y python3 sudo zstd pv mbuffer devel/py-coverage
id -u -n
uname -a
zfs --version
python3 --version
ssh -V
zstd --version
pv --version | head -n 1
mbuffer --version | head -n 1
command -v sh | xargs ls -l
sudo command -v sh | xargs ls -l

mkdir -p $HOME/.ssh
rm -f $HOME/.ssh/id_rsa $HOME/.ssh/id_rsa.pub
ssh-keygen -t rsa -f $HOME/.ssh/id_rsa -q -N ""  # create private key and public key
cat $HOME/.ssh/id_rsa.pub >> $HOME/.ssh/authorized_keys
ls -al $HOME
chsh -s /bin/sh

echo "Now running tests as root user"; ./test.sh; if ($status != 0) exit 1
echo "Now running coverage"; ./coverage.sh; if ($status != 0) exit 1

echo "Now running tests as non-root user:"
set tuser = test
set thome = /home/$tuser
#pw userdel -n $tuser
pw useradd $tuser -d $thome -m
echo "$tuser ALL=NOPASSWD:`command -v zfs`,`command -v zpool`" >> /usr/local/etc/sudoers

mkdir -p $thome/.ssh
cp -p $HOME/.ssh/id_rsa $HOME/.ssh/id_rsa.pub $HOME/.ssh/authorized_keys $thome/.ssh/
chmod go-rwx $thome/.ssh/authorized_keys
chown -R $tuser $thome/.ssh

cp -Rp . $thome/wbackup-zfs # if running with Github Action
# cp -Rp wbackup-zfs $thome/ # if running with https://github.com/vmactions/shell-freebsd
chown -R $tuser $thome/wbackup-zfs
chsh -s /bin/sh $tuser
sudo -u $tuser sh -c "cd $thome/wbackup-zfs; ./test.sh"; if ($status != 0) exit 1
echo "wbackup-zfs-testrun-success"
