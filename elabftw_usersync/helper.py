import csv
import os
import sys

from progress.bar import Bar


class UserSyncException(Exception):
    def __init__(self, msg):
        self.msg = msg


def error_print(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def init_ldap():
    ldap_host = os.getenv("LDAP_HOST")
    ldap_dn = os.getenv("LDAP_DN")
    ldap_base_dn = os.getenv("LDAP_BASE_DN")
    ldap_password = os.getenv("LDAP_PASSWORD")
    ldap_search_group = os.getenv("LDAP_SEARCH_GROUP")
    ldap_search_user_attrs = os.getenv("LDAP_SEARCH_USER_ATTRS")

    if ldap_host is None:
        error_print("Environment variable LDAP_HOST is not set")
    if ldap_dn is None:
        error_print("Environment variable LDAP_DN is not set")
    if ldap_base_dn is None:
        error_print("Environment variable LDAP_BASE_DN is not set")
    if ldap_password is None:
        error_print("Environment variable LDAP_PASSWORD is not set")
    if ldap_search_group is None:
        error_print("Environment variable LDAP_SEARCH_GROUP is not set")
    if ldap_search_user_attrs is None:
        error_print("Environment variable LDAP_SEARCH_USER_ATTRS is not set")

    return (
        ldap_host,
        ldap_dn,
        ldap_base_dn,
        ldap_password,
        ldap_search_group,
        ldap_search_user_attrs,
    )


def get_root_certs_dir():
    return os.getenv("ROOT_CERTS_DIR") or "/etc/ssl/certs"


def get_whitelist_filename():
    return os.getenv("WHITELIST_FILENAME") or "group_whitelist.csv"


def get_ldap_pseudo_mail():
    return os.getenv("LDAP_PSEUDO_MAIL") or "FALSE"


def init_elabftw():
    elabftw_host = os.getenv("ELABFTW_HOST")
    elabftw_apikey = os.getenv("ELABFTW_APIKEY")

    if elabftw_host is None:
        error_print("Environment variable ELABFTW_HOST is not set")
    if elabftw_apikey is None:
        error_print("Environment variable ELABFTW_APIKEY is not set")

    return elabftw_host, elabftw_apikey


def read_whitelist() -> list:
    """
    Read the group whitelist from a file

    :return: list of dicts of the groups and leaders
    """
    whitelist_path = f"./{get_whitelist_filename()}"
    data = []
    try:
        with open(whitelist_path, "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                data.append(dict(row))
    except FileNotFoundError as e:
        error_print(
            f"File not found: Processing file on path {whitelist_path} raised exception\n{e}."
        )
    except csv.Error as e:
        error_print(
            f"CSV Error: Processing file on path {whitelist_path} raised exception\n{e}."
        )
    except Exception as e:
        error_print(
            f"Error: Processing file on path {whitelist_path} raised exception\n{e}."
        )
    return data


def parse_users_from_ldap(ldap_users_obj: list) -> list:
    """
    Parse user from an LDAP object
    """
    users = []

    with Bar("Parsing users from LDAP", max=len(ldap_users_obj)) as bar:
        for user in ldap_users_obj:
            user_attrs = user[1]

            uni_id = user_attrs["cn"][0].decode()

            # If no user mail address can be obtained use cn for pseudo mail (only if env var is TRUE)
            try:
                user_mail = user_attrs["mail"][0].decode()
            except KeyError:
                if get_ldap_pseudo_mail() == "TRUE":
                    user_mail = f"{uni_id}@pseudomail.uni-muenster.de"
                else:
                    raise UserSyncException(
                        f'Error: No mail address could be obtained from LDAP for user with university id "{uni_id}"!'
                    )

            users.append(
                {
                    "email": user_mail,
                    "firstname": user_attrs["givenName"][0].decode(),
                    "lastname": user_attrs["sn"][0].decode(),
                    "uni_id": uni_id,
                }
            )
            bar.next()

    return users


def parse_leader_mail_from_ldap(parsed_users: list, leader_acc: str) -> str:
    leader_mail = None

    for user in parsed_users:
        if user["uni_id"] == leader_acc:
            leader_mail = user["email"]
            break

    if not leader_mail:
        error_print(
            f"No leader mail address for ID {leader_acc} could be obtained from the LDAP server."
        )

    return leader_mail


def diff_users(ldap_users: list, elabftw_users: list) -> (list, list):
    """
    Calculate the difference between the users from ldap and elabftw

    :param ldap_users: list of users from ldap
    :param elabftw_users: list of users from elabftw
    :return: tuple of lists. First list is the users to add, second list is the users to remove
    """

    # Because we operate on sets, we can use the difference operator for disjunction
    # if an account exists only in elabftw, we need to remove it
    # if an account exists only in ldap, we need to add it
    add = list(set(ldap_users) - set(elabftw_users))
    remove = list(set(elabftw_users) - set(ldap_users))

    return add, remove