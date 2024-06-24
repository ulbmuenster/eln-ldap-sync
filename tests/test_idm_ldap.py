# Copyright (C) 2024 University of Münster

import unittest

import ldap
from ldap_faker import LDAPFakerMixin

from elabftw_usersync.idm_ldap import LDAP


class LDAPTest(LDAPFakerMixin, unittest.TestCase):
    ldap_modules = ["elabftw_usersync.idm_ldap"]
    ldap_fixtures = "ldap_objects.json"

    def test_auth_works(self):
        LDAP(
            "ldaps://fake_url",
            "cn=m_muster01,ou=person,dc=identity,dc=uni-muenster,dc=de",
            "1234",
        )
        conn = self.get_connections()[0]
        self.assertLDAPConnectionMethodCalled(
            conn,
            "simple_bind_s",
            {
                "who": "cn=m_muster01,ou=person,dc=identity,dc=uni-muenster,dc=de",
                "cred": "1234",
            },
        )

    def test_correct_connection_options_were_set(self):
        LDAP(
            "ldaps://fake_url",
            "cn=m_muster01,ou=person,dc=identity,dc=uni-muenster,dc=de",
            "1234",
        )

        self.assertEqual(ldap.get_option(ldap.OPT_X_TLS_CACERTDIR), "/etc/ssl/certs")
        self.assertEqual(ldap.get_option(ldap.OPT_PROTOCOL_VERSION), 3)
        self.assertEqual(
            ldap.get_option(ldap.OPT_X_TLS_REQUIRE_CERT), ldap.OPT_X_TLS_HARD
        )
        self.assertEqual(ldap.get_option(ldap.OPT_X_TLS_NEWCTX), 0)

    def test_search_gets_correct_results(self):
        my_ldap = LDAP(
            "ldaps://fake_url",
            "cn=m_muster01,ou=person,dc=identity,dc=uni-muenster,dc=de",
            "1234",
        )

        results = my_ldap.search(
            "ou=person,dc=identity,dc=uni-muenster,dc=de",
            "(cn=m_muster01)",
            ["cn", "sn", "givenName", "mail"],
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0][0], "cn=m_muster01,ou=person,dc=identity,dc=uni-muenster,dc=de"
        )
        self.assertEqual(len(results[0][1]), 4)
        self.assertEqual(
            results[0][1],
            {
                "cn": [b"m_muster01"],
                "givenName": [b"Max"],
                "mail": [b"max.muster@uni-muenster.de"],
                "sn": [b"Muster"],
            },
        )

    def test_search_gets_correct_results_non_ascii(self):
        my_ldap = LDAP(
            "ldaps://fake_url",
            "cn=m_muster01,ou=person,dc=identity,dc=uni-muenster,dc=de",
            "1234",
        )

        results = my_ldap.search(
            "ou=person,dc=identity,dc=uni-muenster,dc=de",
            "(cn=a_weiss01)",
            ["cn", "sn", "givenName", "mail"],
        )
        print(results)

        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0][0], "cn=a_weiss01,ou=person,dc=identity,dc=uni-muenster,dc=de"
        )
        self.assertEqual(len(results[0][1]), 4)
        self.assertEqual(
            results[0][1],
            {
                "cn": [b"a_weiss01"],
                "givenName": [b"Anna"],
                "mail": [b"anna.weiss@uni-muenster.de"],
                "sn": [b"Wei\xc3\x9f"],
            },
        )
