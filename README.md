# cln-channel-review

A tool to help settting channel fees on C-lightning node (manually).

It gathers your in/out forwarding history along peers' fees of your peers to help you go through your channel fee settings one by one.
Once you figure out the patterns, hopefully eventually you can make some script to automate the process.

The goal is one simple script file that a simple guy can easily hack.
It does require many python lib on the headers, just pip instll until you can run.

Note that the calculations of feerates has an assumption of zero base fee to make it simple (well, my node is zero base fee,
I'm keen to put more effort to support non zero based)

## Usage

> python cln_channel_review.py --cli-args lightning-dir=_YOUR_CLN_DIR_ 

Review all your channels

> python cln_channel_review.py --cli-args lightning-dir=_YOUR_CLN_DIR_ --peer-id=_your_peer_pubkey_

Review one channel

> python cln_channel_review.py --cli-args lightning-dir=_YOUR_CLN_DIR_ --recent-forward=5

Review channels that have forwards(in/out) in the last 5 days

> python cln_channel_review.py --cli-args lightning-dir=_YOUR_CLN_DIR_ --recent-forward=3,10

Review channels that have forwards between 3 to 10 days

> python cln_channel_review.py --cli-args lightning-dir=_YOUR_CLN_DIR_ --absent-forward=20

Review channels that have no forwards the last 20 days

## How I use it ?

Initially I review all the channels.
Every 2 days. I run:

--recent-forward=2

to fine tuning busy channels

Occationally I run:

--recent-forward=2,7

mainly to lower fee of channels that I set too high on the busy channels then they stopped forwarding

Occationally I run:

--recent-forward=25

to try to get quiet channels going
