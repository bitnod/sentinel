#!/usr/bin/env python

import argparse
import sys
sys.path.append("lib")
sys.path.append("scripts") 

import cmd
import misc
import mysql
import config
import crontab
import cmd, sys
import govtypes
import time

from governance import GovernanceObject, GovernanceObjectMananger, Setting, Event
from dashd import CTransaction

parent = GovernanceObject()
parent.init()

db = mysql.connect(config.hostname, config.username, config.password, config.database)

commands = {}

"""

    Sentinel - v1
    --------------------------------    

     - this is an exact copy of our existing functionality, just reimplemented in python using sentinel

    old commands: 
        mnbudget prepare beer-reimbursement2 www.dashwhale.org/p/beer-reimbursement2 1 481864 XfoGXXFJtobHvjwfszWnbMNZCBAHJWeN6G 50
        mnbudget submit beer-reimbursement2 www.dashwhale.org/p/beer-reimbursement2 1 481864 XfoGXXFJtobHvjwfszWnbMNZCBAHJWeN6G 50 REPLACE_WITH_COLLATERAL_HASH

    1. contract --create --name="beer-reimbursement" --description_url="www.dashwhale.org/p/beer-reimbursement" --contract_url="beer-reimbursement.com/001.pdf" --start-date="2017/1/1" --end-date="2017/6/1"
    2. cron process (will automatically submit the proposal to the network)

"""

"""

    Sentinel Autocomplete
    --------------------------------
"""

' contract --create [...] '
commands["contract"] = [
    "--create",
    "--name",
    "--description_url",
    "--contract_url",
    "--start_date",
    "--end_date"
]

' crontab --task="(prepare_events|submit_events)"'
commands["crontab"] = [
    "--clear_events",
    "--prepare_events",
    "--submit_events"
]

"""

    Sentinel Shell (CLI)
"""

class SentinelShell(cmd.Cmd):
    intro = 'Welcome to the sentinel shell.   Type help or ? to list commands.\n'
    prompt = '(sentinel) '
    file = None

    """
        Network Contract Tasks

    """
    def do_contract(self, arg):
        'contract'
        '  user --create --name="beer-reimbursement" --description_url="www.dashwhale.org/p/beer-reimbursement" --contract_url="beer-reimbursement.com/001.pdf" --start-date="2017/1/1" --end-date="2017/6/1"'

        parser = argparse.ArgumentParser(description='Create a dash contract')

        # desired action
        parser.add_argument('-a', '--create', help="create", action='store_true')

        # object identity (existentially... what does it mean to be a pubkey?)
        parser.add_argument('-k', '--pubkey', help='your public key for this username (only required for --create)')

        # meta data (create or amend)
        parser.add_argument('-n', '--name', help='your evolution name')
        parser.add_argument('-d', '--description_url', help='your proposals url where a description of the project can be found')
        parser.add_argument('-c', '--contract_url', help='the url where a pdf of the signed contract can be found')
        parser.add_argument('-s', '--start_date', help='starting data, must be the first of the month. Example : 2017/1/1')
        parser.add_argument('-e', '--end_date', help='ending data, must be the first of the month. Example : 2017/6/1')

        # process

        args = None
        try:
            args = parser.parse_args(parse(arg))
        except:
            pass

        if not args:
            return

        ### ------ CREATE METHOD -------- ####

        if args.create:
            #--create --revision=1 --pubkey=XPubkey --username="user-cid" 
            if not args.username:
                print "user creation requires a username"
                return

            fee_tx = CTransaction()

            newObj = GovernanceObject()
            newObj.create_new(parent, args.username, govtypes.user, args.revision, args.pubkey, fee_tx)
            last_id = newObj.save()

            if last_id != None:
                event = Event()
                event.create_new(last_id)
                event.save()

                print "event queued successfully"
            else:
                print "error:", newObj.last_error()

            return

        ### ------- ELSE PRINT HELP --------------- ### 

        parser.print_help()

        ### ------ CREATE METHOD -------- ####


    """
        Contract Tasks

    """
    def do_crontab(self, arg):
        ' crontab [--clear_events --prepare_events --submit_events]"'

        parser = argparse.ArgumentParser(description='Do a crontab task')

        # meta data (create or amend)
        parser.add_argument('-p', '--prepare_events', help="Submit any queued governance objects pending submission (stage 2: submission of colateral tx and governance object)", action="store_true")
        parser.add_argument('-s', '--submit_events', help="Process any queued events pending creation (stage 1: prepare colateral tx)", action="store_true")
        parser.add_argument('-c', '--clear_events', help="Clear event queue (for testing only)", action="store_true")
        parser.add_argument('-r', '--reset', help="Hard reset (for testing only)", action="store_true")
        
        args = None
        try:
            args = parser.parse_args(parse(arg))
        except:
            pass

        if not args:
            return
    
        ### ------ NAME METHOD -------- ####

        if args.clear_events:
            count = crontab.clear_events()
            print count, "events cleared"
            return

        if args.reset:
            print "Hard Reset:"
            count = crontab.clear_events()
            print count, "events cleared"
            count = crontab.clear_governance_objects()
            print count, "governance objects cleared"
            return

        if args.prepare_events:
            count = crontab.prepare_events()
            print count, "events successfully prepared (stage 1)"
            return

        elif args.submit_events:
            count = crontab.submit_events()
            print count, "events successfully submitted (stage 2)"
            return
        else:
            print "unknown command"
            return

        ### ------- ELSE PRINT HELP --------------- ### 

        parser.print_help()

    def complete_crontab(self, text, line, start_index, end_index):
        if text:
            return [command for command in commands["crontab"]
                    if command.startswith(text)]
        else:
            return commands

    """

        Vote on a specific contract

    """

    def do_vote(self, arg):
        'Command action on the dash network'
        ' __internal_vote --times=22 --type=funding --outcome=yes [--hash=governance-hash --name=obj-name --pubkey]'

        parser = argparse.ArgumentParser(description='Vote on governance objects and signal what dash should do with them.')

        #voting
        parser.add_argument('-t', '--times')
        parser.add_argument('-p', '--type')
        parser.add_argument('-o', '--outcome')
        parser.add_argument('-n', '--hash')
        parser.add_argument('-k', '--pubkey')

        ### ------- ELSE PRINT HELP --------------- ### 

        parser.print_help()

    # ----- quit the program -----
    def do_quit(self, arg):
        ' bye, see you later!'

        print "Goodbye! See you soon!"
        sys.exit(0)
        return

def parse(arg):
    'Convert a series of zero or more numbers to an argument tuple'
    return tuple(map(str, arg.split()))


"""

    Run the main cli
"""

import sys
args = sys.argv[1:]

misc.add_sentinel_option("clear_events")
misc.add_sentinel_option("prepare_events")
misc.add_sentinel_option("submit_events")
misc.startup()

if __name__ == '__main__':

    if len(args) > 1:
        if args[0] == "user":
            SentinelShell().do_user(" ".join(args[1:]))
        elif args[0] == "project":
            SentinelShell().do_project(" ".join(args[1:]))
        elif args[0] == "vote":
            SentinelShell().do_vote(" ".join(args[1:]))
        elif args[0] == "payday":
            SentinelShell().do_payday(" ".join(args[1:]))
        elif args[0] == "crontab":
            SentinelShell().do_crontab(" ".join(args[1:]))
    else:
        SentinelShell().cmdloop()

"""
    Test Flow (to be moved into unit tests):

    1.)  create our required users
         user --create --revision=1 --pubkey=XPubkey --username="user-terra"
         user --create --revision=1 --pubkey=XPubkey --username="user-cid"

    2.)  self-promote our people
         user --amend --revision=2 --name="user-terra" --subclass="manager" --managed_by="user-cyan"
         user --amend --revision=2 --name="user-cid" --subclass="employee" --managed_by="user-cid"

    3.)  manual masternode action
         # masternodes will vote valid=yes on rev=1 and valid=no on all others
         user --set-best-revision=2 --name="user-terra" 
         user --set-best-revision=2 --name="user-cid" 

    4.) cid & terra privately make a deal for compensation
         payday --name="user-terra" --date="2017-1-1" --income="333 USD" --expense="0 USD" --signature1="HEXSIGNATURE" --signature2="HEXSIGNATURE2"
         payday --name="user-cid" --date="2017-1-1" --income="999 USD" --expense="0 USD" --signature1="HEXSIGNATURE" --signature2="HEXSIGNATURE2"

         # expenses and income are signed off on, the network will automatically switch revisions in this case

    5.) cid & terra privately make a deal for expenses
         payday --name="user-terra" --date="2017-01-15" --income="0 USD" --expense="333 USD" --signature1="HEXSIGNATURE" --signature2="HEXSIGNATURE2"
         payday --name="user-cid" --date="2017-01-15" --income="0 USD" --expense="999 USD" --signature1="HEXSIGNATURE" --signature2="HEXSIGNATURE2"

         

"""