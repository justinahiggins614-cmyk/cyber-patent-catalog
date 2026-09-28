#!/usr/bin/env python3
"""
Stateful inspection firewall — working demonstration.
Related patent: US 5,606,668 (Check Point "INSPECT" engine): a state
table tracks every active connection; packets are judged against
session context, not in isolation. Educational model, NOT a real
firewall.
"""
from dataclasses import dataclass, field


@dataclass
class Packet:
    src: str
    dst: str
    sport: int
    dport: int
    flags: str  # "SYN", "SYN-ACK", "ACK", "FIN", "DATA"


@dataclass
class StatefulFirewall:
    state_table: dict = field(default_factory=dict)

    def _key(self, p: Packet):
        return (p.src, p.dst, p.sport, p.dport)

    def _revkey(self, p: Packet):
        return (p.dst, p.src, p.dport, p.sport)

    def _internal(self, ip: str) -> bool:
        # Demo policy: sessions may only be initiated from the trusted LAN.
        return ip.startswith("10.")

    def inspect(self, p: Packet) -> str:
        key, rev = self._key(p), self._revkey(p)
        if p.flags == "SYN" and key not in self.state_table and rev not in self.state_table:
            if self._internal(p.src):
                self.state_table[key] = "SYN_SENT"
                return f"ALLOW  new session started: {p.src}:{p.sport} -> {p.dst}:{p.dport}"
            return f"DROP   unsolicited inbound SYN (no session): {p.src} -> {p.dst}:{p.dport}"
        if key in self.state_table:
            st = self.state_table[key]
            if p.flags == "FIN":
                del self.state_table[key]
                return "ALLOW  session closed (FIN)"
            if st == "SYN_SENT" and p.flags == "ACK":
                self.state_table[key] = "ESTABLISHED"
                return "ALLOW  handshake completed, session ESTABLISHED"
            if st == "ESTABLISHED":
                return "ALLOW  data on established session"
            return f"ALLOW  in-session packet [{p.flags}]"
        if rev in self.state_table:
            st = self.state_table[rev]
            if p.flags == "FIN":
                del self.state_table[rev]
                return "ALLOW  session closed by peer (FIN)"
            return f"ALLOW  return traffic on session ({st})"
        # Packet matches nothing: drop (this is what blocks spoofed scans)
        return f"DROP   no matching session state: {p.src}:{p.sport} -> {p.dst}:{p.dport} [{p.flags}]"


def firewall_demo():
    fw = StatefulFirewall()
    trace = [
        Packet("10.0.0.5", "93.184.216.34", 51234, 443, "SYN"),      # legit outbound
        Packet("93.184.216.34", "10.0.0.5", 443, 51234, "SYN-ACK"),  # server reply
        Packet("10.0.0.5", "93.184.216.34", 51234, 443, "ACK"),      # handshake done
        Packet("10.0.0.5", "93.184.216.34", 51234, 443, "DATA"),     # data flows
        Packet("203.0.113.9", "10.0.0.5", 666, 22, "SYN"),           # spoofed probe, no session
        Packet("10.0.0.5", "93.184.216.34", 51234, 443, "FIN"),      # close
        Packet("93.184.216.34", "10.0.0.5", 443, 51234, "DATA"),     # late packet, session gone
    ]
    decisions = [fw.inspect(p) for p in trace]
    for d in decisions:
        print(d)
    assert decisions[0].startswith("ALLOW")
    assert decisions[4].startswith("DROP"), "unsolicited inbound SYN must be dropped"
    assert decisions[6].startswith("DROP"), "packet for closed session must be dropped"
    print("Self-checks OK: sessions tracked, spoofed/orphan packets dropped.")


if __name__ == "__main__":
    firewall_demo()
    print("Self-test: PASS")
