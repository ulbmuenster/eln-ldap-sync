# elabFTW LDAP Sync Script

## Setup

Build Prerequisites for LDAP: https://www.python-ldap.org/en/python-ldap-3.3.0/installing.html#alpine

```
apk add build-base openldap-dev python3-dev
```

### Setup for Development

1. Get API Key in elabFTW: https://your-elab-instance.com/ucp.php?tab=4
2. Copy the `.env.example` file to `.env` and fill in your data
3. Set up a virtual Environment and install dependencies with pipen:
    ```bash
    pipenv install --dev
    pipenv shell
    ```
4. run the script: `elabftw`
   
## Usage

### Provide a CSV List of groups

See `group_whitelist.csv` for an example

## Adapt the script to use any Identity Provider other than LDAP

In the `for` loop that goers over each group read from the CSV whitelist in the `main.py/start_sync()` function LDAP gets called for all members of the group:

```python
ldap_users, leader_mail = process_ldap(
   ld,
   LDAP_BASE_DN,
   LDAP_SEARCH_GROUP.format(groupname=group["groupname"]),
   LDAP_SEARCH_USER_ATTRS.split(","),
   group["leader"],
)
```

replace this with custom code to output something like:

```
[
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
```

for `ldap_users` and a string for `leader_mail`.


 