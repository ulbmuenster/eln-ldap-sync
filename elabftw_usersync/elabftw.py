# Copyright (C) 2024 University of Münster
# elabftw-usersync is free software; you can redistribute it and/or modify it under the terms of the MIT License; see LICENSE file for more details.
"""This module provides a class for interacting with an ElabFTW server."""

import requests
from progress.bar import Bar

from elabftw_usersync.helper import UserSyncException
from elabftw_usersync.logger_config import logger


class ElabFTW:
    """Class for interacting with an ElabFTW server."""

    session = None
    host_url = None

    def __init__(self, host_url, apikey):
        """
        Initialize an instance of the ElabFTW class.

        Args:
            host_url (str): The URL of the ElabFTW server.
            apikey (str): The API key used for authentication.

        """
        self.host_url = host_url
        self.session = requests.Session()
        self.session.headers.update({"Authorization": apikey})
        self.all_users = None
        self.user_data_list = None

    def check_connection(self):
        """Check if the connection to ElabFTW is working.

        Return True if the connection is working, otherwise raises a UserSyncException
        """
        try:
            resp = self.session.get(self.host_url + "/api/v2/info")
        except requests.exceptions.ConnectionError:
            raise UserSyncException("Error connecting to ElabFTW: Connection refused")
        else:
            if resp.status_code != 200:
                raise UserSyncException("Error connecting to ElabFTW: " + resp.text)
            else:
                return True

    def get_all_users(self):
        """Get all users from ElabFTW as JSON."""
        logger.info("Getting all users from ElabFTW...")
        resp = self.session.get(self.host_url + "/api/v2/users?includeArchived=1")
        if resp.status_code != 200:
            logger.error("Error getting users: " + resp.text)

        return resp.json()

    def create_users_dict(self):
        """
        Retrieve user data for all users and returns a list of user dictionaries.

        Return:
            list: A list of user dictionaries containing user data.
        """
        user_data_list = []
        user_ids = [user["userid"] for user in self.all_users]

        with Bar("Initial crawling of userdata...", max=len(self.all_users)) as bar:
            for user_id in user_ids:
                user_resp = self.session.get(self.host_url + f"/api/v2/users/{user_id}")
                if user_resp.status_code != 200:
                    logger.error("Error get user object: " + user_resp.text)
                else:
                    user_data_list.append(user_resp.json())
                bar.next()
        return user_data_list

    def get_userarchive_id(self):
        """
        Retrieve the userarchive ID from the team ID.

        Return:
            int: The userarchive ID.
        """
        self.userarchiv_id = self.get_team_id("userarchiv")
        return self.userarchiv_id

    def get_users_for_team(self, team_id: int) -> list[dict]:
        """
        Get all users from a team in ElabFTW.

        :return: list of users
        """
        users_in_team = []
        for user in self.user_data_list:
            for team in user["teams"]:
                if team["id"] == team_id:
                    user_dict = {}
                    user_dict["user_mail"] = user["email"]
                    user_dict["user_id"] = user["userid"]
                    user_dict["orgid"] = user["orgid"]
                    users_in_team.append(user_dict)
        return users_in_team

    def create_user(
        self,
        email: str,
        firstname: str,
        lastname: str,
        uni_id: str,
        team: int = None,
        valid_until: str = None,
        usergroup: int = None,
        return_id: bool = True,
    ) -> str | int:
        """
        Create user in ElabFTW.

        :param firstname: User's first name.
        :param lastname: User's last name.
        :param email: User's email address.
        :param team: optional, The team id.
        :param valid_until: optional, Date in the YYYY-MM-DD format for account expiration date.
        :param usergroup: optional: permissions level the user will get. 1: Sysadmin, 2: Admin, 4: user (default)
        :param return_id: Set to false, if you want to get the location
        :return: the id or the location of the created user
        """
        data = {
            "firstname": firstname,
            "lastname": lastname,
            "email": email,
            "orgid": uni_id,
        }

        if team is not None:
            data["team"] = team
        if valid_until is not None:
            data["valid_until"] = valid_until
        if usergroup is not None:
            data["usergroup"] = usergroup

        # Create User
        post_user_resp = self.session.post(self.host_url + "/api/v2/users", json=data)

        if post_user_resp.status_code != 201:
            logger.error("Error creating user: " + post_user_resp.text)
            # break somehow?
            # return None

        try:
            user_id = int(post_user_resp.headers["location"].rsplit("/", 1)[-1])
        except KeyError:
            user_id = post_user_resp.headers.get("location", None)
        logger.info(f"User {email} created with id {user_id}")
        # add the user to self.all_users
        newly_created_user = {
            "userid": user_id,
            "firstname": firstname,
            "lastname": lastname,
            "orgid": uni_id,
            "email": email,
            "fullname": firstname + " " + lastname,
        }
        self.all_users.append(newly_created_user)
        self.user_data_list.append(
            {
                "userid": user_id,
                "firstname": firstname,
                "lastname": lastname,
                "email": email,
                "fullname": firstname + " " + lastname,
                "team": 1,
                "teams": [],
            }
        )

        return user_id

    def toggle_user_archived(self, user_id: int):
        """
        Toggle the archived status of a user.

        Args:
            user_id (int): The ID of the user to toggle.

        Returns:
            dict or None: If the user is successfully unarchived, the JSON response from the server is returned as a dictionary.
                          If there is an error unarchiving the user, None is returned.
        """
        modify_user_resp = self.session.patch(
            self.host_url + f"/api/v2/users/{user_id}", json={"action": "archive"}
        )

        if modify_user_resp.status_code != 200:
            logger.error("Error unarchiving user: " + modify_user_resp.text)
            return None
        else:
            return modify_user_resp.json()

    def get_user_id(self, uniid: str) -> tuple[int, bool]:
        """
        Get user id from ElabFTW.

        :param email: The email address of the user
        :return: the id of the user
        """
        uid = None
        for user in self.all_users:
            if user["orgid"] == uniid:
                uid = user["userid"]
                is_archived = user["archived"] == 1
                break
        if uid is None:
            return None, False
        else:
            return uid, is_archived

    def get_user_id_or_create(
        self,
        email: str,
        firstname: str,
        lastname: str,
        uni_id: str,
        team_id: int = None,
    ) -> tuple[int, bool]:
        """
        Get user id from ElabFTW or create it.

        :param firstname: User's first name.
        :param lastname: User's last name.
        :param email: User's email address.
        :return: tuple: user id (int) and true/false if the user was archived/unarchived
        """
        uid, is_archived = self.get_user_id(uni_id)
        if uid is not None:
            if is_archived:
                logger.info(f"User {email} is archived. Unarchiving it.")
                if self.toggle_user_archived(uid) is not None:
                    unarchived = True
            else:
                unarchived = False
        else:
            logger.info(f"User not found: {email}. Creating it.")
            uid = self.create_user(email, firstname, lastname, uni_id, team_id)
            unarchived = False

        return uid, unarchived

    def add_user_to_team(self, user_id: int, team_id: int) -> dict:
        """
        Add a team to a user.

        :param user_id: User id
        :param team_id: Team id
        :return: dict pf the updated user
        """
        data = {"action": "add", "team": team_id}
        resp = self.session.patch(self.host_url + f"/api/v2/users/{user_id}", json=data)

        if resp.status_code != 200:
            logger.error("Error updating user: " + resp.text)

        return resp.json()

    def get_all_teams(self) -> list:
        """
        Get all teams from ElabFTW.

        Return: list of teams
        """
        resp = self.session.get(self.host_url + "/api/v2/teams")

        if resp.status_code != 200:
            logger.error("Error getting teams: " + resp.text)

        return resp.json()

    def get_team_id(self, name: str) -> int:
        """
        Get team id from ElabFTW.

        :param name: Team name
        :return: int of the team id
        """
        teams = self.get_all_teams()
        for team in teams:
            if team["orgid"] == name:
                return team["id"]
        else:
            return None

    def get_team_owners(self, team_id: int) -> int:
        """
        Get the team owner of a team.

        :param team_id: The team id
        :return: The user id of the team owner
        """
        team_owners = []
        team_users = self.get_users_for_team(team_id)
        for user in team_users:
            user_resp = self.session.get(
                self.host_url + f"/api/v2/users/{user['user_id']}"
            )
            if user_resp.status_code != 200:
                logger.error("Error get user object: " + user_resp.text)
            user = user_resp.json()
            for i, team in enumerate(user["teams"]):
                if team["id"] == team_id:
                    if team["is_owner"] == 1:
                        team_owners.append(user["userid"])
        return team_owners

    def remove_user_as_teamowner(self, user_id: int, team_id: int) -> bool:
        """
        Remove a user as a team owner.

        Args:
            user_id (int): The ID of the user.
            team_id (int): The ID of the team.

        Returns:
            bool: True if the user was successfully removed as a team owner, False otherwise.
        """
        if isinstance(user_id, tuple):
            user_id = user_id[0]
        # get user data from self.user_data_list
        user = next(
            (user for user in self.user_data_list if user["userid"] == user_id), None
        )

        for i, team in enumerate(user["teams"]):
            if team["id"] == team_id:
                # looking at the team we are working with
                if team["is_owner"] == 1:
                    logger.info(
                        f"User {user_id} will not be owner of team {team_id} anymore."
                    )
                    # the user is owner: we need to remove that!
                    patchuser_unmake_owner_payload = {
                        "action": "patchuser2team",
                        "userid": user_id,
                        "team": team_id,
                        "target": "is_owner",
                        "content": False,
                    }
                    resp = self.session.patch(
                        self.host_url + f"/api/v2/users/{user_id}",
                        json=patchuser_unmake_owner_payload,
                    )

                    if resp.status_code != 200:
                        logger.error("Error setting owner of a team: " + resp.text)

                    patchuser_make_user_instead_admin_payload = {
                        "action": "patchuser2team",
                        "userid": user_id,
                        "team": team_id,
                        "target": "group",
                        "content": 4,
                    }
                    resp2 = self.session.patch(
                        self.host_url + f"/api/v2/users/{user_id}",
                        json=patchuser_make_user_instead_admin_payload,
                    )

                    if resp2.status_code != 200:
                        logger.error("Error setting owner of a team: " + resp2.text)

    def ensure_single_teamowner(self, new_owner_id: int, team_id: int):
        """Ensure that only one person at a time is the teamowner.

        Keyword arguments:
        argument -- description
        Return: return_description
        """
        # get the teams current owner
        team_owners = self.get_team_owners(team_id)
        if len(team_owners) == 0:
            logger.info("Team had no owner, setting new one")
            self.set_teamowner(new_owner_id, team_id)
        elif len(team_owners) > 1:
            logger.info("Team has more than one owner, unsetting all")
            for user in team_owners:
                self.remove_user_as_teamowner(user, team_id)
            logger.info("Setting new team owner")
            self.set_teamowner(new_owner_id, team_id)
        else:
            # team_owner == 1
            # check if the current owner differs from the new owner
            if team_owners[0] != new_owner_id:
                logger.info("Change in ownership detected")
                # if yes, remove the current owner
                self.remove_user_as_teamowner(team_owners[0], team_id)
                # Set the new owner as owner
                self.set_teamowner(new_owner_id, team_id)
            else:
                logger.info(
                    "The new owner is the same as current owner. Doing nothing."
                )

    def set_teamowner(self, user_id: int, team_id: int) -> bool:
        """
        Set the given user as team lead and team admin for team_id.

        :param user_id: The user which will be the team lead
        :param team_id: The team
        :return: True for success otherwise False. If something goes wrong, an error message is printed to STD ERR.
        """
        if isinstance(user_id, tuple):
            user_id = user_id[0]
        # get user data from self.user_data_list
        user = next(
            (user for user in self.user_data_list if user["userid"] == user_id), None
        )
        already_owner = False
        for i, team in enumerate(user["teams"]):
            if team["id"] == team_id:
                if team["is_owner"] == 1:
                    # the user is already owner, we don't need to patch it
                    already_owner = True
                    break
                else:
                    # the user is not owner of the team, so we need to patch it
                    already_owner = False

        if already_owner is True:
            return False
        else:
            # patch the user in elabftw
            patchuser_make_owner_payload = {
                "action": "patchuser2team",
                "userid": user_id,
                "team": team_id,
                "target": "is_owner",
                "content": True,
            }

            resp = self.session.patch(
                self.host_url + f"/api/v2/users/{user_id}",
                json=patchuser_make_owner_payload,
            )

            if resp.status_code != 200:
                logger.error("Error setting owner of a team: " + resp.text)
            else:
                for t in resp.json()["teams"]:
                    if t["id"] == team_id:
                        if t["is_owner"] == 1:
                            # make shure that the new owner is also the team admin
                            patchuser_make_admin_payload = {
                                "action": "patchuser2team",
                                "userid": user_id,
                                "team": team_id,
                                "target": "group",
                                "content": 2,
                            }
                            resp = self.session.patch(
                                self.host_url + f"/api/v2/users/{user_id}",
                                json=patchuser_make_admin_payload,
                            )
                            if resp.status_code != 200:
                                logger.error(
                                    "Error setting admin of a team: " + resp.text
                                )
                            else:
                                logger.success(
                                    f"Sucessfully set user {user_id} as admin of team {team_id}."
                                )
                                return True
                        else:
                            logger.error(
                                f"Error while setting user with the id {user_id} as owner of the team {team_id}"
                            )

    def remove_users_from_team(self, uni_ids: list, team_name: str) -> list:
        """
        Remove users from a given team in ElabFTW.

        :param uni_ids: list of uni_ids
        :param team: The team id
        :return: list of dicts of the archived users
        """
        removed_users = []
        with Bar("Removing users from team", max=len(uni_ids)) as bar:
            for uni_id in uni_ids:
                user_id = self.get_user_id(uni_id)[0]
                removed_users.append(self.remove_user_from_team(user_id, team_name))
                bar.next()

        return removed_users

    def get_teams_for_user(self, user_id: int) -> dict:
        """For a given user_id get all associated team_ids."""
        data = []
        if isinstance(user_id, tuple):
            user_id = user_id[0]
        # get user data from self.user_data_list
        user = next(
            (user for user in self.user_data_list if user["userid"] == user_id), None
        )
        for team in user["teams"]:
            tdict = {"name": "", "id": None}
            tdict["id"] = team["id"]
            tdict["name"] = team["name"]
            data.append(tdict)
        return data

    def remove_user_from_team(self, user_id: int, team_name: str) -> dict:
        """
        Remove user from a team in ElabFTW.

        :param user_id: User id
        :team_id: The team id
        :return: dict of the archived user
        """
        logger.info(f"Removing user {user_id} from team {team_name}")
        team_id = self.get_team_id(team_name)
        # first check if the user is only assigned to one team. If yes, add the user to the team `userarchiv` and remove the user from the team
        user_teams = self.get_teams_for_user(user_id)
        if len(user_teams) == 1:
            userarchive_id = self.get_userarchive_id()
            # Add user to team `userarchiv` so that the user is always in a team.
            # It's been the last team the user was in, so now we archive it.
            self.add_user_to_team(user_id, userarchive_id)
            remove_user_from_team_payload = {
                "action": "unreference",
                "team": team_id,
            }
            resp = self.session.patch(
                self.host_url + f"/api/v2/users/{user_id}",
                json=remove_user_from_team_payload,
            )

            if resp.status_code != 200:
                logger.error("Error removing user from team: " + resp.text)
            if self.toggle_user_archived(user_id) is not None:
                logger.info(f"User {user_id} was archived.")

        else:
            # User is in more than one team. We can remove the user from the team without adding it to the team `userarchiv`.
            remove_user_from_team_payload = {
                "action": "unreference",
                "userid": user_id,
                "team": team_id,
            }
            resp = self.session.patch(
                self.host_url + f"/api/v2/users/{user_id}",
                json=remove_user_from_team_payload,
            )

            if resp.status_code != 200:
                logger.error("Error removing user from team: " + resp.text)

        return resp.json()
