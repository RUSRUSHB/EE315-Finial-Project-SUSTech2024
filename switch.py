import base64

from cryptography.fernet import Fernet

from ee315_24_lib import SwitchFabric, Packet
import re

is_debug = 0


class Modem:
    @staticmethod
    def modulate(data):
        return ''.join(format(ord(char), '08b') for char in data)

    @staticmethod
    def demodulate(signal):
        return ''.join(chr(int(signal[i:i + 8], 2)) for i in range(0, len(signal), 8))


def generate_key(string_key):
    padded_key = string_key.ljust(32)[:32]
    return base64.urlsafe_b64encode(padded_key.encode())


class Host:
    def __init__(self, mac, interface):
        if not re.match(r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$', mac):
            raise ValueError("Invalid MAC address format")
        self.mac = mac
        self.interface = interface
        self.buffer = []
        self.key = None
        self.cipher = None

    def update_key(self, key):
        self.key = key
        self.cipher = Fernet(self.key)

    def send_packet(self, dst_mac, payload, switch, encrypt=False, modulate=False):
        # packet: src, dst, payload

        if encrypt:
            payload = self.cipher.encrypt(payload.encode()).decode()
        if modulate:
            payload = Modem.modulate(payload)
            print(f'Modulated payload: {payload}')

        packet = Packet(src=self.mac, dst=dst_mac, payload=payload, is_encrypted=encrypt, is_modulated=modulate)
        switch.handle_packet(packet)

    def receive_packet(self, packet):
        if packet.dst == self.mac:
            if packet.is_modulated:
                packet.payload = Modem.demodulate(packet.payload)
            if packet.is_encrypted:
                try:
                    packet.payload = self.cipher.decrypt(packet.payload.encode()).decode()
                except Exception:
                    print(f'Failed to decrypt packet.')
                    return
            self.buffer.append(packet)


class Switch:
    def __init__(self, fabric, num_interfaces=8):
        self.num_interfaces = num_interfaces
        self.interfaces = {}
        self.mac_table = {}
        self.fabric = fabric
        self.interface_vlan_table = {}  # NEW
        for i in range(self.num_interfaces):
            self.interfaces[i] = None

    def configure_interface_vlan(self, interface, vlan_id):  # NEW
        self.interface_vlan_table[interface] = vlan_id

    def handle_packet(self, packet):
        # packet: src, dst, payload
        # 1. MAC Learning
        # interface -> host mapping
        for interface, host in self.interfaces.items():
            if host and host.mac == packet.src:
                # print(f'host.mac: {host.mac}')
                self.mac_table[packet.src] = interface
                break

        src_interface = self.mac_table.get(packet.src)
        src_vlan = self.interface_vlan_table.get(src_interface)
        dst_interface = self.mac_table.get(packet.dst)
        dst_vlan = self.interface_vlan_table.get(dst_interface)
        global is_debug
        if is_debug:
            print(f'src_interface: {src_interface}, src_vlan: {src_vlan}')
            print(f'dst_interface: {dst_interface}, dst_vlan: {dst_vlan}')

        if dst_interface is not None:
            if src_vlan == dst_vlan:
                self.fabric.forward_to_interface(packet, dst_interface)
        else:
            # Broadcast
            for interface, host in self.interfaces.items():
                if host and host.mac != packet.src:  # Don't send to self
                    if src_vlan == dst_vlan:
                        self.fabric.forward_to_interface(packet, interface)

        pass

# 创建网络
