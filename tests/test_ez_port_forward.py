# unittests
from ez_port_forward.ez_port_forward import parse_protocols, parse_yaml, build_command, write_container_commands

def test_parse_protocols():
    # check none
    assert parse_protocols(None) == None
    # check invalid datatypes
    assert parse_protocols(1.0) == None
    assert parse_protocols([1,2,34]) == None
    assert parse_protocols(["123,344,554"]) == None
    assert parse_protocols(True) == None

    # check valid inputs
    package = {123:345, 324:5445}
    result = parse_protocols(package)
    assert result == package

    package = {123: "123", "345":345, "567":"567"}
    result = parse_protocols(package)
    assert result == {123: 123, 345:345, 567:567}

    package = "123, 456 ,789"
    result = parse_protocols(package)
    assert result == {123:123, 456:456, 789:789}

    package = 123
    result = parse_protocols(package)
    assert result == {123:123}

def test_build_command():

    from ipaddress import ip_address
    result = build_command("tcp", "eno1", ip_address("10.0.0.1"), 123, 456)
    assert result == \
    "        post-up iptables -t nat -A PREROUTING -i eno1 -p tcp --dport 456 -j DNAT --to 10.0.0.1:123\n"

    result = build_command("tcp", "eno1", ip_address("10.0.0.1"), 123)
    assert result == \
    "        post-up iptables -t nat -A PREROUTING -i eno1 -p tcp --dport 123 -j DNAT --to 10.0.0.1:123\n"
    




