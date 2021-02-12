# FOSS Fund Standup Script

## Description
A python script that replicates a working process recommended by OpenCollective to hold Funding Poll Events.

## Currently Working
- Reaches out to our GitHub Enterprise account and pulls a list of all Enterprise members
- Takes the output of the GitHub API call and passes each user through our LDAP server, pulling back email address
- Passes GitHub Login and Email to [Starfish](https://github.com/indeedeng/starfish) and takes the output and prints email address

## TODO
- Pick a poll provider and integrate creating Poll and uploading Email addresses
- Generalize the process, possibly modularize so this is usable by the rest of the Open Source Community