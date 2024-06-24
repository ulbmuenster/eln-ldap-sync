# Copyright (C) 2024 University of Münster
# elabftw-usersync is free software; you can redistribute it and/or modify it under the terms of the MIT License; see LICENSE file for more details.
"""This module contains the LDAP class for the user synchronization script."""
import ldap

from elabftw_usersync.helper import get_root_certs_dir


class LDAP:
    """Class to handle LDAP connections."""

    conn = None

    def __init__(self, host_url, dn, password):
        """
        LDAP class for IDM.

        :param host_url: LDAP host url
        :param dn: LDAP DN
        :param password: LDAP password
        """
        ld = ldap.initialize(host_url)

        # Tell python-ldap where root certificates are stored and how to check them
        ldap.set_option(ldap.OPT_X_TLS_CACERTDIR, get_root_certs_dir())
        ldap.set_option(ldap.OPT_PROTOCOL_VERSION, 3)
        ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_HARD)

        # Apply changes to TLS context
        ldap.set_option(ldap.OPT_X_TLS_NEWCTX, 0)

        ld.simple_bind_s(dn, password)

        self.conn = ld

    def search(self, base_dn, filter_str: str = None, attrslist: list = None) -> list:
        """
        Search LDAP for all users within a group.

        :param base_dn: LDAP BaseDN
        :param filter_str: LDAP filter eg. "cn=user@mail.com"
        :param attrslist: LDAP attributes eg. ["uni_id", "mail", "givenName", "forename"]
        :return: list of users in ldap format
        """
        if attrslist is None:
            attrslist = []

        results = self.conn.search_s(base_dn, ldap.SCOPE_SUBTREE, filter_str, attrslist)
        return results
