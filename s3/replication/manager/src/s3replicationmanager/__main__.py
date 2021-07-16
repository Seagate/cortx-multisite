#
# Copyright (c) 2021 Seagate Technology LLC and/or its Affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.
#

import argparse
import os
from s3replicationmanager.app import ReplicationManagerApp


def setup_args(parser):
    """Defines program arguments."""
    # adding an arguments
    parser.add_argument(
        '--configfile',
        type=str,
        metavar='path',
        help='Path to configuration file(format: yaml).\n'
        'Provide config file path starting with root "/".\n'
        'e.g. : "/home/path/to/my_config.yaml"')

    parser.add_argument(
        '--logconfig',
        type=str,
        metavar='path',
        help='Path to log config properties file(format: yaml)')


if __name__ == '__main__':
    # create parser object
    parser = argparse.ArgumentParser(
        description='''Replication manager help''',
        formatter_class=argparse.RawTextHelpFormatter)

    # Define the args
    setup_args(parser)

    # parsing arguments
    args = parser.parse_args()

    # Setup default log file path if not specified.
    if args.logconfig is None:
        args.logconfig = os.path.join(os.path.dirname(__file__),
                                      '..', 'config', 'logger_config.yaml')

    print("Using Configuration from {}".format(args.logconfig))
    print("Using log configuration from {}".format(args.logconfig))
    ReplicationManagerApp(args.configfile, args.logconfig).run()
