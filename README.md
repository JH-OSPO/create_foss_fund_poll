# FOSS Fund Standup Script

## Description
A python script that replicates a working process recommended by OpenCollective to hold Funding Poll Events.

## How to Use
- Checkout this repository `git clone https://github.com/jh-ospo/open_collective_poll)`
- Enter the directory `cd open_collective_poll`
- Create a python virtual environment `python -m venv venv`
- Activate the virtual environment `source venv/bin/activate` or whatever scripts works for your environment
- Install the required libraries `pip install -r requirements.txt`
- Ensure that you are on the VPN (connect to Hopkins via the PulseSecure VPN client)
- Set your environment variables
  - GITHUB_TOKEN
	This is the token that you generate in your github account, it must have access to the enterprise functionality
  - JHED_PASSWORD
	This is, unfortunately, needed for the LDAP connection. (maybe we can prompt for it in the future)
  - JHED_ID
	Your JHED username (jhedid@jh.edu)
  - GH_SLUG
	This is your GitHub Enterprise slug, johns-hopkins-university for example
- Run the script `python main.py`

## Currently Working
- Reaches out to our GitHub Enterprise account and pulls a list of all Enterprise members
- Takes the output of the GitHub API call and passes each user through our LDAP server, pulling back email address

## TODO
