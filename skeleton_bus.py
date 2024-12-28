import re
from ee315_24_lib import Bus, Packet


class Host:
    def __init__(self, mac):
        if not re.match(r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$', mac):
            raise ValueError("Invalid MAC address format")
        self.mac = mac
        self.buffer = []

    def send_packet(self, dst_mac, payload, bus):
        packet = Packet(src=self.mac, dst=dst_mac, payload=payload)
        bus.broadcast(packet)
        pass

    def receive_packet(self, packet):
        if packet.dst == self.mac:
            self.buffer.append(packet)
        pass


# Example usage
if __name__ == "__main__":
    bus = Bus()
    host1 = Host("00:00:00:00:00:01")
    host2 = Host("00:00:00:00:00:02")
    host3 = Host("00:00:00:00:00:03")
    host4 = Host("00:00:00:00:00:04")

    bus.connect_host(host1)
    bus.connect_host(host2)
    bus.connect_host(host3)

    host1.send_packet("00:00:00:00:00:02", "Hello from host1", bus)
    host2.send_packet("00:00:00:00:00:03", "Hello from host2", bus)
    host3.send_packet("00:00:00:00:00:01", "Hello from host3", bus)
    host4.send_packet("00:00:00:00:00:01", "Hello from host4", bus)
