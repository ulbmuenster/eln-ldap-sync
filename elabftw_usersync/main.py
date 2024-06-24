# Copyright (C) 2024 University of Münster
# elabftw-usersync is free software; you can redistribute it and/or modify it under the terms of the MIT License; see LICENSE file for more details.
"""This module is the entry point for the user synchronization script."""
import os

import click
import ldap
from dotenv import load_dotenv

from elabftw_usersync.elabftw import ElabFTW
from elabftw_usersync.helper import (
    UserSyncException,
    init_elabftw,
    init_ldap,
    read_whitelist,
)
from elabftw_usersync.idm_ldap import LDAP
from elabftw_usersync.logger_config import logger
from elabftw_usersync.processing import (
    process_elabftw,
    process_ldap,
    process_removed_users,
)


@click.command()
@click.option("--whitelist", required=False, type=str, help="Path to the whitelist.")
def start_sync(whitelist):
    """Provide main function to start the synchronization process."""
    # read .env file
    load_dotenv()
    logger.info("Starting user synchronization...")
    if whitelist is not None:
        os.environ["WHITELIST_FILENAME"] = whitelist
    # make sure the whitelist is set and readable
    group_dicts = read_whitelist()
    # --------------------------------------------------
    (
        LDAP_HOST,
        LDAP_DN,
        LDAP_BASE_DN,
        LDAP_PASSWORD,
        LDAP_SEARCH_GROUP,
        LDAP_SEARCH_USER_ATTRS,
    ) = init_ldap()

    logger.info(f"Connecting to LDAP at {LDAP_HOST}...")
    try:
        ld = LDAP(LDAP_HOST, LDAP_DN, LDAP_PASSWORD)
    except ldap.SERVER_DOWN:
        raise UserSyncException(
            "Error connecting to LDAP: SERVER DOWN (check for a potential configuration issue)"
        )
    except ldap.INVALID_CREDENTIALS:
        raise UserSyncException("Error connecting to LDAP: INVALID CREDENTIALS")
    # --------------------------------------------------
    ELABFTW_HOST, ELABFTW_APIKEY = init_elabftw()
    logger.info(
        f"Connecting to ElabFTW at {ELABFTW_HOST} and gathering data about all users..."
    )
    elabftw = ElabFTW(ELABFTW_HOST, ELABFTW_APIKEY)

    try:
        elabftw.check_connection()
        # check if connection to elabftw is possible

    except Exception as e:
        raise UserSyncException(e.msg)
    else:
        # if it is, get user data
        elabftw.all_users = elabftw.get_all_users()
        elabftw.user_data_list = elabftw.create_users_dict()
    # --------------------------------------------------
    # Next steps: For each group in the whitelist we need to get the ldap users and the leader mail address.

    for group in group_dicts:
        logger.info(f"Processing team {group['groupname']}")
        ldap_users, leader_mail = process_ldap(
            ld,
            LDAP_BASE_DN,
            LDAP_SEARCH_GROUP.format(groupname=group["groupname"]),
            LDAP_SEARCH_USER_ATTRS.split(","),
            group["leader"],
        )
        team = group["groupname"]

        ldap_users_uniid = []
        ldap_users_uniid += list({user["uni_id"] for user in ldap_users})

        if process_elabftw(elabftw, ldap_users, team, leader_mail):
            process_removed_users(elabftw, team, ldap_users_uniid)


if __name__ == "__main__":
    start_sync()
