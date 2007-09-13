# Copyright (C) 2007 Google Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.


"""Cluster related QA tests.

"""

import tempfile

from ganeti import utils

import qa_config
import qa_utils
import qa_error

from qa_utils import AssertEqual, StartSSH


def TestClusterInit():
  """gnt-cluster init"""
  master = qa_config.GetMasterNode()

  cmd = ['gnt-cluster', 'init']

  if master.get('secondary', None):
    cmd.append('--secondary-ip=%s' % master['secondary'])

  bridge = qa_config.get('bridge', None)
  if bridge:
    cmd.append('--bridge=%s' % bridge)
    cmd.append('--master-netdev=%s' % bridge)

  cmd.append(qa_config.get('name'))

  AssertEqual(StartSSH(master['primary'],
                       utils.ShellQuoteArgs(cmd)).wait(), 0)


def TestClusterVerify():
  """gnt-cluster verify"""
  cmd = ['gnt-cluster', 'verify']
  master = qa_config.GetMasterNode()

  AssertEqual(StartSSH(master['primary'],
                       utils.ShellQuoteArgs(cmd)).wait(), 0)


def TestClusterInfo():
  """gnt-cluster info"""
  cmd = ['gnt-cluster', 'info']
  master = qa_config.GetMasterNode()

  AssertEqual(StartSSH(master['primary'],
                       utils.ShellQuoteArgs(cmd)).wait(), 0)


def TestClusterBurnin():
  """Burnin"""
  master = qa_config.GetMasterNode()

  # Get as many instances as we need
  instances = []
  try:
    num = qa_config.get('options', {}).get('burnin-instances', 1)
    for _ in xrange(0, num):
      instances.append(qa_config.AcquireInstance())
  except qa_error.OutOfInstancesError:
    print "Not enough instances, continuing anyway."

  if len(instances) < 1:
    raise qa_error.Error("Burnin needs at least one instance")

  # Run burnin
  try:
    script = qa_utils.UploadFile(master['primary'], '../tools/burnin')
    try:
      cmd = [script,
             '--os=%s' % qa_config.get('os'),
             '--os-size=%s' % qa_config.get('os-size'),
             '--swap-size=%s' % qa_config.get('swap-size')]
      cmd += [inst['name'] for inst in instances]
      AssertEqual(StartSSH(master['primary'],
                           utils.ShellQuoteArgs(cmd)).wait(), 0)
    finally:
      cmd = ['rm', '-f', script]
      AssertEqual(StartSSH(master['primary'],
                           utils.ShellQuoteArgs(cmd)).wait(), 0)
  finally:
    for inst in instances:
      qa_config.ReleaseInstance(inst)


def TestClusterMasterFailover():
  """gnt-cluster masterfailover"""
  master = qa_config.GetMasterNode()

  failovermaster = qa_config.AcquireNode(exclude=master)
  try:
    cmd = ['gnt-cluster', 'masterfailover']
    AssertEqual(StartSSH(failovermaster['primary'],
                         utils.ShellQuoteArgs(cmd)).wait(), 0)

    cmd = ['gnt-cluster', 'masterfailover']
    AssertEqual(StartSSH(master['primary'],
                         utils.ShellQuoteArgs(cmd)).wait(), 0)
  finally:
    qa_config.ReleaseNode(failovermaster)


def TestClusterCopyfile():
  """gnt-cluster copyfile"""
  master = qa_config.GetMasterNode()

  # Create temporary file
  f = tempfile.NamedTemporaryFile()
  f.write("I'm a testfile.\n")
  f.flush()
  f.seek(0)

  # Upload file to master node
  testname = qa_utils.UploadFile(master['primary'], f.name)
  try:
    # Copy file to all nodes
    cmd = ['gnt-cluster', 'copyfile', testname]
    AssertEqual(StartSSH(master['primary'],
                         utils.ShellQuoteArgs(cmd)).wait(), 0)
  finally:
    # Remove file from all nodes
    for node in qa_config.get('nodes'):
      cmd = ['rm', '-f', testname]
      AssertEqual(StartSSH(node['primary'],
                           utils.ShellQuoteArgs(cmd)).wait(), 0)


def TestClusterDestroy():
  """gnt-cluster destroy"""
  cmd = ['gnt-cluster', 'destroy', '--yes-do-it']
  master = qa_config.GetMasterNode()

  AssertEqual(StartSSH(master['primary'],
                       utils.ShellQuoteArgs(cmd)).wait(), 0)
