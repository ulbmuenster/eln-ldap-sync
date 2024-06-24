# elabFTW LDAP Sync Script

## Setup

Build Prerequisites for LDAP: https://www.python-ldap.org/en/python-ldap-3.3.0/installing.html#alpine

```
apk add build-base openldap-dev python3-dev
```

### Development: Set Env-Variables in `.env`

1. Get API Key in elabFTW: https://your-elab-instance.com/ucp.php?tab=4
2. Set up a virtual Environment and install dependencies and run the script
    ```bash
    python -m venv venv
    . ./venv/bin/activate
    pip install -r requirements.txt
    python3 elabftw_usersync/main.py
    ```

    Alternatively:

    ```bash
    pipenv install
    pipenv shell
    elabftw
    ```
   
## Usage

### Provide a CSV List of groups

see `group_whitelist.csv` for an example

### Adapt the 

### Set Environment

   LDAP_HOST (LDAP URL)   
   
      LDAP_HOST: "ldaps://<HOST>:636" 

   LDAP_DN (Bind User)

      LDAP_DN: "cn=<user>,dc=example,dc=com"

   LDAP_PASSWORD (for Bind User)

      LDAP_PASSWORD: "<Secret>"

   LDAP_BASE_DN (Search Path)

      LDAP_BASE_DN: "ou=<accounts>,dc=example,dc=com"

   LDAP_SEARCH_GROUP (Where to find GroupName in memberOf Attribute)
    
      LDAP_SEARCH_GROUP: "memberof=cn={groupname},ou=<groups>,dc=example,dc=com"

   LDAP_SEARCH_USER_ATTRS (Which Attributes will be )

      LDAP_SEARCH_USER_ATTRS: "cn,sn,givenName,mail"

   ELABFTW_HOST (ELBAFTW Host URL)
        
      ELABFTW_HOST: "https://elabftw.example.com"
   
   ELABFTW_APIKEY (Sysadmin Api Key)

      ELABFTW_APIKEY: "<secret>"

   ROOT_CERTS_DIR (Default certs dir to check LDAP/Elabftw Host certs)

      ROOT_CERTS_DIR: "/etc/ssl/certs"