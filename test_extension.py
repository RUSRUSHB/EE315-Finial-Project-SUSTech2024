import os
from switch import Host, Switch, generate_key
from ee315_24_lib import SwitchFabric, Packet


def test_switch_functionality():
    total_score = 0
    fabric = SwitchFabric()
    switch = Switch(fabric)

    # Create and connect hosts
    host1 = Host("00:00:00:00:00:01", 0)
    host2 = Host("00:00:00:00:00:02", 1)
    host3 = Host("00:00:00:00:00:03", 2)

    fabric.connect_host_to_switch(host1, switch)
    fabric.connect_host_to_switch(host2, switch)
    fabric.connect_host_to_switch(host3, switch)

    # Test 1: Initial Flooding (20 points)
    print("\nTesting Initial Flooding (20 points)...")
    try:
        open(fabric.log_file, 'w').close()  # Clear log
        packet = Packet(src="00:00:00:00:00:01", dst="00:00:00:00:00:02", payload="Test Packet")
        host1.send_packet("00:00:00:00:00:02", "Test flooding", switch)

        with open(fabric.log_file, 'r') as f:
            log_content = f.read()
            # 检查是否转发到所有其他接口
            assert "Packet forwarded - Interface: 1" in log_content, "Packet not flooded to interface 1"
            assert "Packet forwarded - Interface: 2" in log_content, "Packet not flooded to interface 2"
            assert host3.buffer == [], "Packet incorrectly received by unrelated host"
        total_score += 20
        print("✓ Initial Flooding test passed")
    except AssertionError as e:
        print(f"✗ Initial Flooding test failed: {str(e)}")

    # return
    # Test 2: MAC Learning (20 points)
    print("\nTesting MAC Learning (20 points)...")
    try:
        # host1已经发送过数据包，检查switch是否学习了MAC地址
        assert host1.mac in switch.mac_table, "Switch failed to learn source MAC"
        assert switch.mac_table[host1.mac] == 0, "Switch learned incorrect interface for host1"

        # 让host2发送数据包，进一步验证学习功能
        host2.send_packet("00:00:00:00:00:03", "Test learning", switch)
        assert host2.mac in switch.mac_table, "Switch failed to learn second host MAC"
        assert switch.mac_table[host2.mac] == 1, "Switch learned incorrect interface for host2"

        total_score += 20
        print("✓ MAC Learning test passed")
    except AssertionError as e:
        print(f"✗ MAC Learning test failed: {str(e)}")

    # Test 3: Selective Forwarding (20 points)
    print("\nTesting Selective Forwarding (20 points)...")
    try:
        open(fabric.log_file, 'w').close()  # Clear log
        # host3向已知的host2发送数据包
        host3.send_packet("00:00:00:00:00:02", "Test selective", switch)
        print(f'host2.buffer[0].payload: {host2.buffer[0].payload}')

        with open(fabric.log_file, 'r') as f:
            log_content = f.read()
            # 验证只转发到了正确的接口
            assert "Packet forwarded - Interface: 1" in log_content, "Packet not forwarded to correct interface"
            assert "Packet forwarded - Interface: 0" not in log_content, "Packet incorrectly forwarded to interface 0"
            assert log_content.count("Packet forwarded") == 1, "Packet forwarded to multiple interfaces"

        total_score += 20
        print("✓ Selective Forwarding test passed")
    except AssertionError as e:
        print(f"✗ Selective Forwarding test failed: {str(e)}")

    print(f"\nTotal Score: {total_score}/60")
    # -----------------------------------------------------------------------
    bonus_score = 0
    print("\nTesting Extensions")
    print("\n\nExtension 1: Testing VLAN")
    switch.configure_interface_vlan(0, 10)  # host1 on VLAN 10
    switch.configure_interface_vlan(1, 20)  # host2 on VLAN 20
    switch.configure_interface_vlan(2, 10)  # host3 on VLAN 10
    host1.buffer = []
    host2.buffer = []
    host3.buffer = []

    try:
        open(fabric.log_file, 'w').close()  # Clear log
        host1.send_packet("00:00:00:00:00:02", "Test VLAN", switch)
        print(f"host2 buffer: {host2.buffer}")
        host1.send_packet("00:00:00:00:00:03", "Test VLAN", switch)
        print(f"host3 received: {host3.buffer[0].payload}")
        with open(fabric.log_file, 'r') as f:
            log_content = f.read()
            assert "Packet forwarded - Interface: 1" not in log_content, "Packet incorrectly forwarded to different VLAN"
            assert "Packet forwarded - Interface: 2" in log_content, "Packet failed to forwarded to same VLAN"
        print("✓ VLAN test passed")
    except AssertionError as e:
        print(f"✗ VLAN test failed: {str(e)}")

    # -----------------------------------------------------------------------

    print("\n\nExtension 2: Testing Encryption")
    switch.configure_interface_vlan(1, 10)
    host1.buffer = []
    host2.buffer = []
    host3.buffer = []
    key1 = generate_key("114514")
    key2 = generate_key("1919810")
    host1.update_key(key1)
    host2.update_key(key1)
    host3.update_key(key2)

    host1.send_packet("00:00:00:00:00:02", "Correct Encryption Key", switch, encrypt=True)

    print(f"host2 buffer: {host2.buffer[0].payload}")
    try:
        host1.send_packet("00:00:00:00:00:03", "Wrong Encryption Key", switch, encrypt=True)
    except Exception as e:
        print(f"Encryption failed as expected: {e}")
    print(f'host3 buffer: {host3.buffer}')
    print("Failure as expected")

    try:
        assert host2.buffer[0].payload == "Correct Encryption Key", "Decryption failed"
        assert host3.buffer == [], "Decrypt packet with wrong key"
    except AssertionError as e:
        print(f"✗ Encryption test failed: {str(e)}")

    print("✓ Encryption test passed")

    # -------------------------------
    print("\n\nExtension 3: Testing Modulation")
    host1.buffer = []
    host2.buffer = []

    host1.send_packet("00:00:00:00:00:02", "Encrypted and modulated signal", switch, encrypt=True, modulate=True)
    print(f"host2 buffer: {host2.buffer[0].payload}")
    assert host2.buffer[0].payload == "Encrypted and modulated signal", "Demodulation failed"

    print("✓ Modulation test passed")
    return total_score


if __name__ == "__main__":
    test_switch_functionality()
