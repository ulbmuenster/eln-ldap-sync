# Copyright (C) 2024 University of Münster
# elabftw-usersync is free software; you can redistribute it and/or modify it under the terms of the MIT License; see LICENSE file for more details.

import csv
import os
from unittest import mock
from unittest.mock import patch

import pytest
from hypothesis import given
from hypothesis import strategies as st

from elabftw_usersync.helper import (
    UserSyncException,
    diff_users,
    get_ldap_pseudo_mail,
    get_root_certs_dir,
    get_whitelist_filename,
    init_elabftw,
    init_ldap,
    parse_leader_mail_from_ldap,
    parse_users_from_ldap,
    read_whitelist,
)


def set_test_env_vars(do_not_set=[]):
    settings_vars = {}

    if "ROOT_CERTS_DIR" not in do_not_set:
        settings_vars["ROOT_CERTS_DIR"] = "/etc/ssl/certs"
    if "WHITELIST_FILENAME" not in do_not_set:
        settings_vars["WHITELIST_FILENAME"] = "test_whitelist.csv"
    if "LDAP_HOST" not in do_not_set:
        settings_vars["LDAP_HOST"] = "ldaps://ldap-as.ulb.uni-muenster.de:636"
    if "LDAP_DN" not in do_not_set:
        settings_vars["LDAP_DN"] = "user"
    if "LDAP_BASE_DN" not in do_not_set:
        settings_vars["LDAP_BASE_DN"] = "base_dn"
    if "LDAP_PASSWORD" not in do_not_set:
        settings_vars["LDAP_PASSWORD"] = "password"
    if "LDAP_SEARCH_GROUP" not in do_not_set:
        settings_vars["LDAP_SEARCH_GROUP"] = (
            "memberof=cn={groupname},ou=persongroup,dc=identity,dc=uni-muenster,dc=de"
        )
    if "LDAP_SEARCH_USER_ATTRS" not in do_not_set:
        settings_vars["LDAP_SEARCH_USER_ATTRS"] = "cn,sn,givenName,mail"
    if "LDAP_PSEUDO_MAIL" not in do_not_set:
        settings_vars["LDAP_PSEUDO_MAIL"] = "TRUE"
    if "ELABFTW_HOST" not in do_not_set:
        settings_vars["ELABFTW_HOST"] = "localhost"
    if "ELABFTW_APIKEY" not in do_not_set:
        settings_vars["ELABFTW_APIKEY"] = "apikey"

    return settings_vars


@pytest.fixture
def double_correct_whitelist(mocker):
    doubled_whitelist = mocker.mock_open(
        read_data="groupname,leader\nu0ubd21,sstimber\nu0ubd22,gressho\n"
    )
    mocker.patch("builtins.open", doubled_whitelist)


@st.composite
def get_ldap_user(draw):
    uni_id = draw(st.from_regex(r"^[a-z|_|0-9]{6,10}$"))

    ldap_user = (
        f"cn={uni_id},ou=person,dc=identity,dc=uni-muenster,dc=de",
        {
            "mail": [
                bytes(
                    draw(st.emails(domains=st.sampled_from(["uni-muenster.de"]))),
                    "utf8",
                )
            ],
            "givenName": [bytes(draw(st.text(min_size=1)), "utf8")],
            "sn": [bytes(draw(st.text(min_size=1)), "utf8")],
            "cn": [bytes(uni_id, "utf8")],
        },
    )

    return ldap_user


def ldap_users_list_strategy():
    ldap_users = st.lists(get_ldap_user(), min_size=0, max_size=15)

    return ldap_users


def get_ldap_users_example():
    ldap_users_obj = [
        (
            "cn=m_muster01,ou=person,dc=identity,dc=uni-muenster,dc=de",
            {
                "mail": [b"max.mustermann@uni-muenster.de"],
                "givenName": [b"Max"],
                "sn": [b"Mustermann"],
                "cn": [b"m_muster01"],
            },
        ),
        (
            "cn=e_beisp01,ou=person,dc=identity,dc=uni-muenster,dc=de",
            {
                "mail": [b"eva.beispiel@uni-muenster.de"],
                "givenName": [b"Eva"],
                "sn": [b"Beispiel"],
                "cn": [b"e_beisp02"],
            },
        ),
    ]

    return ldap_users_obj


@mock.patch.dict(os.environ, set_test_env_vars(), clear=True)
def test_env_vars_are_set():
    assert os.getenv("WHITELIST_FILENAME") == "test_whitelist.csv"
    assert os.getenv("ROOT_CERTS_DIR") == "/etc/ssl/certs"

    assert os.getenv("LDAP_HOST") == "ldaps://ldap-as.ulb.uni-muenster.de:636"
    assert os.getenv("LDAP_DN") == "user"
    assert os.getenv("LDAP_BASE_DN") == "base_dn"
    assert os.getenv("LDAP_PASSWORD") == "password"
    assert (
        os.getenv("LDAP_SEARCH_GROUP")
        == "memberof=cn={groupname},ou=persongroup,dc=identity,dc=uni-muenster,dc=de"
    )
    assert os.getenv("LDAP_SEARCH_USER_ATTRS") == "cn,sn,givenName,mail"
    assert os.getenv("LDAP_PSEUDO_MAIL") == "TRUE"

    assert os.getenv("ELABFTW_HOST") == "localhost"
    assert os.getenv("ELABFTW_APIKEY") == "apikey"


@mock.patch.dict(os.environ, set_test_env_vars(), clear=True)
def test_init_ldap_returns_vars():
    (
        LDAP_HOST,
        LDAP_DN,
        LDAP_BASE_DN,
        LDAP_PASSWORD,
        LDAP_SEARCH_GROUP,
        LDAP_SEARCH_USER_ATTRS,
    ) = init_ldap()

    assert LDAP_HOST == "ldaps://ldap-as.ulb.uni-muenster.de:636"
    assert LDAP_DN == "user"
    assert LDAP_BASE_DN == "base_dn"
    assert LDAP_PASSWORD == "password"
    assert (
        LDAP_SEARCH_GROUP
        == "memberof=cn={groupname},ou=persongroup,dc=identity,dc=uni-muenster,dc=de"
    )
    assert LDAP_SEARCH_USER_ATTRS == "cn,sn,givenName,mail"


@mock.patch.dict(os.environ, set_test_env_vars(["LDAP_HOST"]), clear=True)
def test_init_ldap_error_if_host_unset(capfd):
    (
        LDAP_HOST,
        LDAP_DN,
        LDAP_BASE_DN,
        LDAP_PASSWORD,
        LDAP_SEARCH_GROUP,
        LDAP_SEARCH_USER_ATTRS,
    ) = init_ldap()

    out, err = capfd.readouterr()

    assert LDAP_HOST is None
    assert err == "Environment variable LDAP_HOST is not set\n"


@mock.patch.dict(os.environ, set_test_env_vars(), clear=True)
def test_get_whitelist_filename_returns_var(capfd):
    whitelist_filename = get_whitelist_filename()

    out, err = capfd.readouterr()

    assert whitelist_filename == "test_whitelist.csv"
    assert err == ""


@mock.patch.dict(os.environ, set_test_env_vars(["WHITELIST_FILENAME"]), clear=True)
def test_get_whitelist_filename_return_default_if_env_var_unset(capfd):
    whitelist_filename = get_whitelist_filename()

    out, err = capfd.readouterr()

    assert whitelist_filename == "group_whitelist.csv"
    assert err == ""


@mock.patch.dict(os.environ, set_test_env_vars(), clear=True)
def test_get_root_certs_dir_returns_var(capfd):
    root_certs_dir = get_root_certs_dir()

    out, err = capfd.readouterr()

    assert root_certs_dir == "/etc/ssl/certs"
    assert err == ""


@mock.patch.dict(os.environ, set_test_env_vars(["ROOT_CERTS_DIR"]), clear=True)
def test_get_root_certs_dir_return_default_if_env_var_unset(capfd):
    root_certs_dir = get_root_certs_dir()

    out, err = capfd.readouterr()

    assert root_certs_dir == "/etc/ssl/certs"
    assert err == ""


@mock.patch.dict(os.environ, set_test_env_vars(), clear=True)
def test_get_ldap_pseudo_mail_returns_var(capfd):
    ldap_pseudo_mail = get_ldap_pseudo_mail()

    out, err = capfd.readouterr()

    assert ldap_pseudo_mail == "TRUE"
    assert err == ""


@mock.patch.dict(os.environ, set_test_env_vars(["LDAP_PSEUDO_MAIL"]), clear=True)
def test_get_ldap_pseudo_mail_return_default_if_env_var_unset(capfd):
    ldap_pseudo_mail = get_ldap_pseudo_mail()

    out, err = capfd.readouterr()

    assert ldap_pseudo_mail == "FALSE"
    assert err == ""


@mock.patch.dict(os.environ, set_test_env_vars(), clear=True)
def test_init_elabftw_returns_vars():
    (ELABFTW_HOST, ELABFTW_APIKEY) = init_elabftw()

    assert ELABFTW_HOST == "localhost"
    assert ELABFTW_APIKEY == "apikey"


@mock.patch.dict(os.environ, set_test_env_vars(["ELABFTW_HOST"]), clear=True)
def test_init_elabftw_error_if_host_unset(capfd):
    (ELABFTW_HOST, ELABFTW_APIKEY) = init_elabftw()

    out, err = capfd.readouterr()

    assert ELABFTW_HOST is None
    assert err == "Environment variable ELABFTW_HOST is not set\n"


def test_read_whitelist(double_correct_whitelist):
    data_dict = read_whitelist()

    assert len(data_dict) == 2
    assert data_dict == [
        {"groupname": "u0ubd21", "leader": "sstimber"},
        {"groupname": "u0ubd22", "leader": "gressho"},
    ]


@mock.patch.dict(os.environ, set_test_env_vars(["WHITELIST_FILENAME"]), clear=True)
@mock.patch.dict(
    os.environ, {"WHITELIST_FILENAME": "non_existent_file.csv"}, clear=True
)
def test_read_whitelist_no_file(capfd):
    whitelist_filename = get_whitelist_filename()
    data_dict = read_whitelist()
    out, err = capfd.readouterr()

    assert whitelist_filename == "non_existent_file.csv"
    assert len(data_dict) == 0
    assert data_dict == []
    assert (
        f"File not found: Processing file on path ./{whitelist_filename} raised exception\n"
        in err
    )


def test_read_whitelist_malformed_csv(capfd):
    with patch("builtins.open", side_effect=csv.Error):
        read_whitelist()
        out, err = capfd.readouterr()
    assert (
        f"CSV Error: Processing file on path ./{get_whitelist_filename()} raised exception\n"
        in err
    )


def test_read_whitelist_input_not_csv(capfd):
    with patch("builtins.open", side_effect=Exception()):
        read_whitelist()
        out, err = capfd.readouterr()
    assert (
        f"Error: Processing file on path ./{get_whitelist_filename()} raised exception\n"
        in err
    )


def test_parse_users_from_ldap():
    ldap_users_obj = get_ldap_users_example()

    assert parse_users_from_ldap(ldap_users_obj) == [
        {
            "email": "max.mustermann@uni-muenster.de",
            "firstname": "Max",
            "lastname": "Mustermann",
            "uni_id": "m_muster01",
        },
        {
            "email": "eva.beispiel@uni-muenster.de",
            "firstname": "Eva",
            "lastname": "Beispiel",
            "uni_id": "e_beisp02",
        },
    ]


def test_parse_users_from_ldap_empty_list():
    ldap_users_obj = []

    assert parse_users_from_ldap(ldap_users_obj) == []


def test_parse_users_from_ldap_non_ascii():
    ldap_users_obj = [
        (
            "cn=e_beisp01,ou=person,dc=identity,dc=uni-muenster,dc=de",
            {
                "mail": [b"anna.weiss@uni-muenster.de"],
                "givenName": [b"Anna"],
                "sn": [b"Wei\xc3\x9f"],
                "cn": [b"a_weiss03"],
            },
        ),
    ]

    assert parse_users_from_ldap(ldap_users_obj) == [
        {
            "email": "anna.weiss@uni-muenster.de",
            "firstname": "Anna",
            "lastname": "Weiß",
            "uni_id": "a_weiss03",
        }
    ]


@mock.patch.dict(os.environ, set_test_env_vars(), clear=True)
def test_parse_users_from_ldap_no_mail():
    ldap_users_obj = [
        (
            "cn=e_beisp01,ou=person,dc=identity,dc=uni-muenster,dc=de",
            {
                "givenName": [b"Anna"],
                "sn": [b"Weiss"],
                "cn": [b"a_weiss03"],
            },
        ),
    ]

    assert get_ldap_pseudo_mail() == "TRUE"
    assert parse_users_from_ldap(ldap_users_obj) == [
        {
            "email": "a_weiss03@pseudomail.uni-muenster.de",
            "firstname": "Anna",
            "lastname": "Weiss",
            "uni_id": "a_weiss03",
        }
    ]


@mock.patch.dict(os.environ, set_test_env_vars(["LDAP_PSEUDO_MAIL"]), clear=True)
def test_parse_users_from_ldap_no_mail_no_pseudo():
    ldap_users_obj = [
        (
            "cn=e_beisp01,ou=person,dc=identity,dc=uni-muenster,dc=de",
            {
                "givenName": [b"Anna"],
                "sn": [b"Weiss"],
                "cn": [b"a_weiss03"],
            },
        ),
    ]

    # LDAP_PSEUDO_MAIL is set to FALSE as a default
    assert get_ldap_pseudo_mail() == "FALSE"

    with pytest.raises(UserSyncException) as e_info:
        parse_users_from_ldap(ldap_users_obj)
        assert (
            e_info.msg
            == 'Error: No mail address could be obtained from LDAP for user with university id "a_weiss03"!'
        )


@given(ldap_users_list_strategy())
def test_parse_ldap_users_properties(ldap_users_obj):
    """Make sure any kind of user info is accepted and does not throw exceptions."""

    parsed_users = parse_users_from_ldap(ldap_users_obj)

    assert len(ldap_users_obj) == len(parsed_users)


def test_parse_leader_mail_from_ldap():
    parsed_ldap_users = parse_users_from_ldap(get_ldap_users_example())

    assert (
        parse_leader_mail_from_ldap(parsed_ldap_users, "e_beisp02")
        == "eva.beispiel@uni-muenster.de"
    )


def test_parse_leader_mail_from_ldap_leader_not_in_ldap(capfd):
    parsed_ldap_users = parse_users_from_ldap(get_ldap_users_example())
    leader_acc = "a_weiss03"

    parse_leader_mail_from_ldap(parsed_ldap_users, leader_acc)

    out, err = capfd.readouterr()

    assert (
        err
        == f"No leader mail address for ID {leader_acc} could be obtained from the LDAP server.\n"
    )


def test_parse_leader_mail_from_ldap_empty_list(capfd):
    parsed_ldap_users = []
    leader_acc = "m_muster01"

    parse_leader_mail_from_ldap(parsed_ldap_users, leader_acc)

    out, err = capfd.readouterr()

    assert (
        err
        == f"No leader mail address for ID {leader_acc} could be obtained from the LDAP server.\n"
    )


def test_diff_users():
    ldap_users = []
    elabftw_users = []
    assert diff_users(ldap_users, elabftw_users) == ([], [])


def test_diff_users_example_1():
    ldap_users_obj = []
    parsed_obj = parse_users_from_ldap(ldap_users_obj)
    elabftw_users = []

    assert diff_users(parsed_obj, elabftw_users) == ([], [])
