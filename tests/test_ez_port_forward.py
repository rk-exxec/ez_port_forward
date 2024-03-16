# unittests
from unittest.mock import patch
from pathlib import Path
from ez_port_forward.ez_port_forward import parse_tcpudp_protocols, parse_ssh_protocol, parse_yaml, build_command, write_container_commands, main

def test_parse_tcpudp_protocols():
    # check none
    assert parse_tcpudp_protocols(None) == None
    # check invalid datatypes
    assert parse_tcpudp_protocols(1.0) == None
    assert parse_tcpudp_protocols([1,2,34]) == None
    assert parse_tcpudp_protocols(["123,344,554"]) == None
    assert parse_tcpudp_protocols(True) == None

    # check valid inputs
    package = {123:345, 324:5445}
    result = parse_tcpudp_protocols(package)
    assert result == package

    package = {123: "123", "345":345, "567":"567"}
    result = parse_tcpudp_protocols(package)
    assert result == {123: 123, 345:345, 567:567}

    package = "123, 456 ,789"
    result = parse_tcpudp_protocols(package)
    assert result == {123:123, 456:456, 789:789}

    package = 123
    result = parse_tcpudp_protocols(package)
    assert result == {123:123}

    package = {123: 1.0, "foo":"bar", 222:False, 12.1:True}
    result = parse_tcpudp_protocols(package)
    assert result == None

def test_parse_ssh_protocol():
    assert parse_ssh_protocol(None, 100) == {10022:22}
    assert parse_ssh_protocol(True, 100) == {10022:22}
    assert parse_ssh_protocol(23, 100) == {10023:23}
    # check invalid datatypes
    assert parse_ssh_protocol(1.0, 100) == None
    assert parse_ssh_protocol([1,2,34], 100) == None
    assert parse_ssh_protocol(["123,344,554"], 100) == None
    assert parse_ssh_protocol(False, 100) == None
    assert parse_ssh_protocol(23424, 100) == None
    assert parse_ssh_protocol(22, 100000) == None

def test_build_command():

    from ipaddress import ip_address
    result = build_command("tcp", "eno1", ip_address("10.0.0.1"), 123, 456)
    assert result == \
    "        post-up iptables -t nat -A PREROUTING -i eno1 -p tcp --dport 456 -j DNAT --to 10.0.0.1:123\n"

    result = build_command("tcp", "eno1", ip_address("10.0.0.1"), 123)
    assert result == \
    "        post-up iptables -t nat -A PREROUTING -i eno1 -p tcp --dport 123 -j DNAT --to 10.0.0.1:123\n"


def test_whole_files():
    import filecmp
    main(["./tests/port_conf_test.yaml", "-o", "./tests/port_forwards"])

    assert Path("tests/port_forwards").exists(), "File was not created"
    assert filecmp.cmp("tests/port_forwards", "tests/port_forwards_ok"), "Output not ok"

    
