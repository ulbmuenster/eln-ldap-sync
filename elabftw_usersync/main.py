# Copyright (C) 2024 - 2025 University of Münster
# elabftw-usersync is free software; you can redistribute it and/or modify it under the terms of the MIT License; see LICENSE file for more details.
"""This module is the entry point for the user synchronization script."""
import os
import sys

import click
import ldap
from dotenv import load_dotenv

from elabftw_usersync.elabftw import ElabFTW
from elabftw_usersync.helper import init_elabftw, init_ldap, read_whitelist
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
    # Make sure the whitelist is set and readable
    if whitelist is not None:
        os.environ["WHITELIST_FILENAME"] = whitelist
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
        logger.critical(
            "Error connecting to LDAP: SERVER DOWN (check for a potential configuration issue)"
        )
        sys.exit(1)
    except ldap.INVALID_CREDENTIALS:
        logger.critical("Error connecting to LDAP: INVALID CREDENTIALS")
        sys.exit(1)
    # --------------------------------------------------
    ELABFTW_HOST, ELABFTW_APIKEY = init_elabftw()
    logger.info(
        f"Connecting to ElabFTW at {ELABFTW_HOST} and gathering data about all users..."
    )
    elabftw = ElabFTW(ELABFTW_HOST, ELABFTW_APIKEY)

    elabftw.check_connection()

    elabftw.all_users = (
        elabftw.get_all_users()
    )  # Cache all user data to speed up processing later on
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

    logger.success("Successfully finished user synchronization.")


if __name__ == "__main__":
    start_sync()
