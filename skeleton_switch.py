from wheel.cli import pack_f

from ee315_24_lib import SwitchFabric, Packet
import re


class Host:
    def __init__(self, mac, interface):
        if not re.match(r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$', mac):
            raise ValueError("Invalid MAC address format")
        self.mac = mac
        self.interface = interface
        self.buffer = []

    def send_packet(self, dst_mac, payload, switch):
        # TODO: ...student to implement...
        # packet: src, dst, payload

        packet = Packet(src=self.mac, dst=dst_mac, payload=payload)
        switch.handle_packet(packet)

    def receive_packet(self, packet):
        # TODO: ...student to implement...
        # packet: src, dst, payload

        if packet.dst == self.mac:
            self.buffer.append(packet)


class Switch:
    def __init__(self, fabric, num_interfaces=8):
        self.num_interfaces = num_interfaces
        self.interfaces = {}
        self.mac_table = {}
        self.fabric = fabric
        for i in range(self.num_interfaces):
            self.interfaces[i] = None

    def handle_packet(self, packet):
        # packet: src, dst, payload
        # TODO: ...student to implement...
        # 1. MAC Learning
        # interface -> host mapping

        for interface, host in self.interfaces.items():
            if host and host.mac == packet.src:
                # print(f'host.mac: {host.mac}')
                self.mac_table[packet.src] = interface
                break

        dst_interface = self.mac_table.get(packet.dst)
        # print(f'dst_interface: {dst_interface}')
        if dst_interface is not None:
            self.fabric.forward_to_interface(packet, dst_interface)
        else:
            # Broadcast
            for interface, host in self.interfaces.items():
                if host and host.mac != packet.src:  # Don't send to self
                    self.fabric.forward_to_interface(packet, interface)

        pass


# 创建网络
shared_fabric = SwitchFabric()
switch = Switch(shared_fabric)

host1 = Host("00:00:00:00:00:01", 0)
host2 = Host("00:00:00:00:00:02", 1)
host3 = Host("00:00:00:00:00:03", 2)

# Connect hosts directly through fabric
shared_fabric.connect_host_to_switch(host1, switch)
shared_fabric.connect_host_to_switch(host2, switch)
shared_fabric.connect_host_to_switch(host3, switch)

# 模拟通信
host1.send_packet("00:00:00:00:00:02", "Hello from A", switch)
host2.send_packet("00:00:00:00:00:03", "Hello from B", switch)
host1.send_packet("00:00:00:00:00:03", "Hello from A", switch)
host3.send_packet("00:00:00:00:00:01", "Hello from C", switch)
host3.send_packet("00:00:00:00:00:02", "Hello from C", switch)
