#!/usr/bin/env python3
"""
RBAC access-control simulator (educational).
Covers CPC G06F21/60 / H04L63/10 (authorization, role-based access
control): users get roles, roles get permissions, requests are
allowed only when a role grants (resource, action). Includes
role hierarchy and a deny-override rule.
"""
from dataclasses import dataclass, field


@dataclass
class RBAC:
    role_perms: dict = field(default_factory=dict)   # role -> set[(resource, action)]
    user_roles: dict = field(default_factory=dict)   # user -> set[roles]
    role_parents: dict = field(default_factory=dict) # role -> parent roles
    denies: set = field(default_factory=set)         # set[(role, resource, action)]

    def grant(self, role, resource, action):
        self.role_perms.setdefault(role, set()).add((resource, action))

    def deny(self, role, resource, action):
        self.denies.add((role, resource, action))

    def assign(self, user, role):
        self.user_roles.setdefault(user, set()).add(role)

    def inherit(self, role, parent):
        self.role_parents.setdefault(role, set()).add(parent)

    def _roles_of(self, user):
        roles, stack = set(), list(self.user_roles.get(user, ()))
        while stack:
            r = stack.pop()
            if r not in roles:
                roles.add(r)
                stack.extend(self.role_parents.get(r, ()))
        return roles

    def allowed(self, user, resource, action) -> bool:
        roles = self._roles_of(user)
        if any((r, resource, action) in self.denies for r in roles):
            return False  # explicit deny wins
        return any((resource, action) in self.role_perms.get(r, ())
                   for r in roles)


def demo():
    rbac = RBAC()
    rbac.grant("analyst", "alerts", "read")
    rbac.grant("analyst", "alerts", "ack")
    rbac.grant("admin", "firewall", "write")
    rbac.inherit("admin", "analyst")          # admins inherit analyst perms
    rbac.deny("contractor", "firewall", "write")
    rbac.assign("manon", "admin")
    rbac.assign("guest1", "contractor")
    rbac.grant("contractor", "alerts", "read")

    checks = [
        ("manon", "alerts", "read", True),
        ("manon", "alerts", "ack", True),     # inherited
        ("manon", "firewall", "write", True),
        ("guest1", "alerts", "read", True),
        ("guest1", "firewall", "write", False),  # denied
        ("stranger", "alerts", "read", False),    # no roles
    ]
    for user, res, act, expect in checks:
        got = rbac.allowed(user, res, act)
        print(f"{user:8} {act:5} {res:8} -> {'ALLOW' if got else 'DENY'}")
        assert got == expect, (user, res, act)
    print("Self-test: PASS")


if __name__ == "__main__":
    demo()
