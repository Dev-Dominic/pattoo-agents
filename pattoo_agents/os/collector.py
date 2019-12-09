#!/usr/bin/env python3
"""Pattoo library collecting Linux data."""

# Standard libraries
import os
import re
import platform
import socket

# pip3 libraries
import psutil

# Pattoo libraries
from pattoo_shared.configuration import Config
from pattoo_shared.variables import (
    AgentKey, DataPoint, DataPointMetadata, TargetDataPoints, AgentPolledData)
from pattoo_shared.constants import (
    DATA_INT, DATA_COUNT64, DATA_FLOAT)


def poll(agent_program):
    """Get all agent data.

    Performance data on linux server on which this application is installed.

    Args:
        agentdata: AgentPolledData object for all data gathered by the agent

    Returns:
        None

    """
    # Initialize key variables.
    config = Config()

    # Initialize AgentPolledData
    agent_hostname = socket.getfqdn()
    agentdata = AgentPolledData(agent_program, config)

    # Intialize data gathering
    ddv = TargetDataPoints(agent_hostname)

    #########################################################################
    # Set non timeseries values
    #########################################################################

    metadata = []
    metadata.append(
        DataPointMetadata('operating_system_release', platform.release()))
    metadata.append(
        DataPointMetadata('operating_system_type', platform.system()))
    metadata.append(
        DataPointMetadata('operating_system_version', platform.version()))
    metadata.append(
        DataPointMetadata('operating_system_cpus', psutil.cpu_count()))
    metadata.append(
        DataPointMetadata('operating_system_hostname', socket.getfqdn()))

    #########################################################################
    # Get timeseries values
    #########################################################################

    performance = Performance()

    # Update agent with system data
    ddv.add(performance.stats_system())

    # Update agent with disk data
    ddv.add(performance.stats_disk_swap())
    ddv.add(performance.stats_disk_partitions())
    ddv.add(performance.stats_disk_io())

    # Update agent with network data
    ddv.add(performance.stats_network())

    # Add results to the AgentPolledData object for posting
    agentdata.add(ddv)
    return agentdata


class Performance(object):
    """Operating system performance."""

    def __init__(self):
        """Initialize the class.

        Args:
            key: Metadata key
            value: Metadata value

        Returns:
            None

        """
        # Initialize variables
        self.create = AgentKey('agent_os')
        self.metadata = []
        self.metadata.append(
            DataPointMetadata(self.create.key('release'), platform.release()))
        self.metadata.append(
            DataPointMetadata(self.create.key('type'), platform.system()))
        self.metadata.append(
            DataPointMetadata(self.create.key('version'), platform.version()))
        self.metadata.append(
            DataPointMetadata(self.create.key('cpus'), psutil.cpu_count()))
        self.metadata.append(
            DataPointMetadata(self.create.key('hostname'), socket.getfqdn()))

    def stats_system(self):
        """Update agent with system data.

        Args:
            ddv: TargetDataPoints object

        Returns:
            result: List of DataPoint objects

        """
        #######################################################################
        # Set timeseries values (Integers)
        #######################################################################
        result = []

        result.append(
            DataPoint(
                self.create.key('process_count'),
                len(psutil.pids()),
                data_type=DATA_INT).add(self.metadata))

        # Load averages
        (la_01, la_05, la_15) = os.getloadavg()

        result.append(
            DataPoint(
                self.create.key('load_average_01min'),
                la_01,
                data_type=DATA_INT).add(self.metadata))

        result.append(
            DataPoint(
                self.create.key('load_average_05min'),
                la_05,
                data_type=DATA_INT).add(self.metadata))

        result.append(
            DataPoint(
                self.create.key('load_average_15min'),
                la_15,
                data_type=DATA_INT).add(self.metadata))

        #######################################################################
        # Set timeseries values (Named Tuples)
        #######################################################################

        # Percentage CPU utilization
        result.extend(_named_tuple_to_dv(
            psutil.cpu_times_percent(),
            self.create.key('cpu_times_percent'),
            data_type=DATA_FLOAT,
            metadata=self.metadata))

        # Get CPU runtimes
        result.extend(_named_tuple_to_dv(
            psutil.cpu_times(),
            self.create.key('cpu_times'),
            data_type=DATA_COUNT64,
            metadata=self.metadata))

        # Get CPU stats
        result.extend(_named_tuple_to_dv(
            psutil.cpu_stats(),
            self.create.key('cpu_stats'),
            data_type=DATA_COUNT64,
            metadata=self.metadata))

        # Get memory utilization
        result.extend(_named_tuple_to_dv(
            psutil.virtual_memory(),
            self.create.key('memory'),
            data_type=DATA_INT,
            metadata=self.metadata))

        # Return
        return result

    def stats_disk_swap(self):
        """Update agent with disk swap data.

        Args:
            ddv: TargetDataPoints object

        Returns:
            None

        """
        # Initialize key variables
        result = []

        # Get swap information
        system_list = psutil.swap_memory()._asdict()
        for key, value in system_list.items():
            # Different suffixes have different data types
            if key in ['sin', 'sout']:
                data_type = DATA_COUNT64
            else:
                data_type = DATA_INT

            # No need to specify a suffix as there is only one swap
            new_key = '{}_{}'.format(self.create.key('swap_memory'), key)
            _dv = DataPoint(new_key, value, data_type=data_type)
            _dv.add(self.metadata)
            result.append(_dv)

        # Add the result to data
        return result

    def stats_disk_partitions(self):
        """Update agent with disk partition data.

        Args:
            ddv: TargetDataPoints object

        Returns:
            None

        """
        # Initialize key variables
        result = []

        # Get filesystem partition utilization
        items = psutil.disk_partitions()
        # "items" is a list of named tuples describing partitions
        for item in items:
            # "source" is the partition mount point
            mountpoint = item.mountpoint
            if "docker" not in str(mountpoint):
                # Add more metadata
                meta = []
                meta.append(DataPointMetadata(
                    '{}_target'.format(self.create.key('disk_partition')),
                    item.target))
                meta.append(DataPointMetadata(
                    '{}_mountpoint'.format(self.create.key('disk_partition')),
                    item.mountpoint))
                meta.append(DataPointMetadata(
                    '{}_fstype'.format(self.create.key('disk_partition')),
                    item.fstype))
                meta.append(DataPointMetadata(
                    '{}_opts'.format(self.create.key('disk_partition')),
                    item.opts))

                # Get the partition data
                partition = psutil.disk_usage(mountpoint)._asdict()
                for key, value in partition.items():
                    _dv = DataPoint(
                        '{}_disk_usage_{}'.format(
                            self.create.key('disk_partition'), key),
                        value, data_type=DATA_INT)
                    _dv.add(meta)
                    _dv.add(self.metadata)
                    result.append(_dv)

        # Add the result to data
        return result

    def stats_disk_io(self):
        """Update agent with disk io data.

        Args:
            ddv: TargetDataPoints object

        Returns:
            None

        """
        # Initialize key variables
        regex = re.compile(r'^ram\d+$')
        result = []

        # Get disk I/O usage
        ioddv = psutil.disk_io_counters(perdisk=True)

        # "source" is disk name
        for disk, disk_named_tuple in ioddv.items():
            # No RAM pseudo disks. RAM disks OK.
            if bool(regex.match(disk)) is True:
                continue
            # No loopbacks
            if disk.startswith('loop') is True:
                continue

            # Populate data
            disk_dict = disk_named_tuple._asdict()
            for key, value in disk_dict.items():
                new_key = '{}_{}'.format(self.create.key('disk_io'), key)
                _dv = DataPoint(new_key, value, data_type=DATA_COUNT64)
                _dv.add(self.metadata)
                _dv.add(DataPointMetadata(
                    self.create.key('disk_partition'), disk))
                result.append(_dv)

        # Add the result to data
        return result

    def stats_network(self):
        """Update agent with network data.

        Args:
            ddv: TargetDataPoints object

        Returns:
            None

        """
        # Initialize key variables
        result = []

        # Get network utilization
        nicddv = psutil.net_io_counters(pernic=True)
        for nic, nic_named_tuple in nicddv.items():
            nic_dict = nic_named_tuple._asdict()
            for key, value in nic_dict.items():
                _dv = DataPoint(
                    '{}_{}'.format(self.create.key('network_io'), key),
                    value,
                    data_type=DATA_COUNT64)
                _dv.add(self.metadata)
                _dv.add(DataPointMetadata(
                    '{}_interface'.format(self.create.key('network_io')),
                    nic))
                result.append(_dv)

        # Add the result to data
        return result


def _named_tuple_to_dv(
        values, parameter_label, data_type=DATA_INT, metadata=None):
    """Convert a named tuple to a list of DataPoint objects.

    Args:
        values: Named tuple
        parameter_label: parameter_label
        data_type: Data type

    Returns:
        result: List of DataPoint

    """
    # Get data
    data_dict = values._asdict()
    result = []

    # Cycle through results
    for key, value in data_dict.items():
        _dv = DataPoint(
            '{}_{}'.format(parameter_label, key),
            value,
            data_type=data_type)
        _dv.add(metadata)
        result.append(_dv)

    # Return
    return result
