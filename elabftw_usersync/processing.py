# Copyright (C) 2024 University of Münster
# elabftw-usersync is free software; you can redistribute it and/or modify it under the terms of the MIT License; see LICENSE file for more details.
"""This module contains the processing logic for the user synchronization script."""
from progress.bar import Bar

from elabftw_usersync.helper import (
    UserSyncException,
    diff_users,
    parse_leader_mail_from_ldap,
    parse_users_from_ldap,
)
from elabftw_usersync.idm_ldap import LDAP
from elabftw_usersync.logger_config import logger


def process_ldap(
    ld: LDAP,
    ldap_base_dn: str,
    ldap_search_group: str,
    ldap_search_user_attrs: list,
    leader_acc: str,
) -> (list, str):
    """
    Return a list of users from LDAP, already parsed into a dev-friendly format and the leader mail of given leader_acc.

    The leader mail is None, if the leader is not listed in the given ldap group.

    :param ld: The configured LDAP instance to be used
    :param ldap_base_dn: base domain name to start the search from
    :param ldap_search_group: The LDAP search string for the group, we want to pull the users from
    :param ldap_search_user_attrs: The LDAP attributes, which should be pulled from the user
    :return: list of dict of users and the team leader mail
    """
    logger.info("Pull team from LDAP...")
    users_results = ld.search(
        ldap_base_dn,
        ldap_search_group,
        attrslist=ldap_search_user_attrs,
    )
    logger.info("Parse users from LDAP...")
    parsed_ldap_users = parse_users_from_ldap(users_results)

    logger.info("Search for team leader email...")
    team_leader_mail = parse_leader_mail_from_ldap(parsed_ldap_users, leader_acc)

    logger.success("Done processing LDAP search results.")

    return parsed_ldap_users, team_leader_mail


def process_elabftw(
    elabftw,
    parsed_ldap_users: list,
    team_name: str,
    leader_mail: str,
):
    """
    Process the users from LDAP and add them to ElabFTW.

    :param elabftw_host: The ElabFTW host eg. https://elabftw.example.com:1234
    :param elabftw_apikey: The ElabFTW API key
    :param parsed_ldap_users: The list of users from LDAP, already parsed into a dev-friendly format
    :param team_name: The name of the team, the users should be added to
    :return: None
    """
    if not leader_mail:
        logger.error(
            f"Skipping the team {team_name} because no leader mail adress could be obtained from LDAP."
        )
        return False

    # --------------------------------------------------
    logger.info("Get Team ID...")
    team_id = elabftw.get_team_id(team_name)

    if not team_id:
        logger.error(
            f"Skipping the team {team_name} because it could not be found in this Instance of ElabFTW. Please make sure the team exists."
        )
        return False

    # --------------------------------------------------
    logger.info("Get Team Leader ID...")
    # check if the leader is already in ElabFTW
    team_leader = None
    for u in parsed_ldap_users:
        if u["email"] == leader_mail:
            team_leader = u
            break

    if not team_leader:
        logger.error(
            f"Skipping the team {team_name} because the leader {leader_mail} could not be found in LDAP."
        )
        return False

    # --------------------------------------------------

    # make sure that the team leader exists in elabFTW. Get the user_id.
    team_leader_id = elabftw.get_user_id_or_create(
        leader_mail,
        team_leader["firstname"],
        team_leader["lastname"],
        team_leader["uni_id"],
        team_id,
    )[0]
    # make sure that the leader is in the team he/she is the leader of
    elabftw.add_user_to_team(team_leader_id, team_id)
    # remove the leader from parsed_ldap_users to avoid adding him/her again
    parsed_ldap_users = [
        user for user in parsed_ldap_users if user["email"] != leader_mail
    ]

    # --------------------------------------------------
    # process all other users
    with Bar("Processing users in elabFTW", max=len(parsed_ldap_users)) as bar:
        for user in parsed_ldap_users:
            user_id, unarchived = elabftw.get_user_id_or_create(
                user["email"],
                user["firstname"],
                user["lastname"],
                user["uni_id"],
                team_id,
            )
            # Add user to the team (will skip if user is already part of the team

            try:
                elabftw.add_user_to_team(user_id, team_id)
            except UserSyncException as e:
                logger.info(e.msg)
                exit(1)
            else:
                # unarchive the user if he/she was archived before
                if unarchived is True:
                    elabftw.remove_user_from_team(user_id, "userarchiv")
            bar.next()

    # --------------------------------------------------
    # setting the team leader
    logger.info(
        f"Making sure that {team_leader['firstname']} {team_leader['lastname']} is the sole team leadder for team {team_name}..."
    )
    try:
        elabftw.ensure_single_teamowner(team_leader_id, team_id)
    except UserSyncException as e:
        logger.info(e.msg)
        exit(1)
    else:
        logger.info("Teamowner set successfully.")
        return True


def process_removed_users(elabftw, team, seen_uniids_from_ldap: list):
    """
    Compare the users from LDAP-Group with the Users assigned to the ElabFTW-team and archive the users in ElabFTW which are not in LDAP anymore.

    :param elabftw_host:
    :param elabftw_apikey:
    :param seen_mail_address_from_ldap:
    :return: None
    """
    logger.info("Pull current users for the team from ElabFTW to calculate changes...")
    team_users = elabftw.get_users_for_team(elabftw.get_team_id(team))
    # team_users is a list of dicts
    team_users_orgids = [x["orgid"] for x in team_users]
    add, list_of_orgids_to_remove = diff_users(seen_uniids_from_ldap, team_users_orgids)

    if len(list_of_orgids_to_remove) > 0:
        logger.info(
            f"Removing {len(list_of_orgids_to_remove)} users(s) from team {team}..."
        )
        elabftw.remove_users_from_team(list_of_orgids_to_remove, team)
    else:
        logger.info("No changes in users detected.")
