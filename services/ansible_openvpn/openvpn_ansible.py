#  BSD 3-Clause License
#
#  Copyright (c) 2023, University Gustave Eiffel
#  All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#
#   Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
#   Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
#   Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
#  AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#  DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
#  FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
#  DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
#  SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
#  CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#  OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
#  OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
import os


# This script convert OpenVPN status into a dynamic Ansible inventory
# It can use local /var/log/openvpn/openvpn-status.log file
# or OpenVPN telnet management console

def parse_openvpn_status(log_text):
    # Split the log text into lines
    lines = log_text.strip().split('\n')

    # Find the start and end indexes for the client list section
    start_index = lines.index('ROUTING TABLE') + 2
    end_index = lines.index('GLOBAL STATS', start_index)

    # Extract the lines containing client information
    client_lines = lines[start_index:end_index]

    # Create a dictionary to store the hosts and their attributes
    hosts = []
    fields = lines[start_index-1].split(",")

    for line in client_lines:
        # Split the line by commas
        parts = line.split(',')
        data = {}
        for index, field_name in enumerate(fields):
            data[field_name] = parts[index]
        hosts.append(data)

    return hosts


def write_to_ansible_inventory(inventory_text, filename):
    with open(filename, 'w') as file:
        file.write(inventory_text)
    os.chmod(filename, 664)


def main():
    # Replace this with the path to your openvpn-status.log file
    log_file_path = "openvpn-status.log"

    with open(log_file_path, 'r') as file:
        log_text = file.read()

    hosts = parse_openvpn_status(log_text)
    inventory_text = "\n".join(
        ["%s ansible_port=22 ansible_host=%s ansible_user=pi" % (
            host["Common Name"],
            host["Virtual Address"]) for host in hosts])

    # Replace this with the desired path for the Ansible inventory file
    ansible_inventory_file = "inventory.ini"
    write_to_ansible_inventory(inventory_text, ansible_inventory_file)


if __name__ == "__main__":
    main()
