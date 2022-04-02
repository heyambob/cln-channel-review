# cln-channel-review

A tool to help setting channel fees on core-lightning (manually, channel by channel)

It displays informations to help deciding what fee to set on each channel.

These informations are:
 * forwarding frequency
 * statistic of fees in the past that make successful forwarding
 * percentiles of feerate that the peers of your peer set towards your peer
 
Once you figure out the patterns, hopefully, eventually you can make some script to automate the process.

The goal is one simple script file that a simple guy can easily hack.
It does require many python libs on the header, just pip instll until you can run.

Note that the calculations of feerate has an assumption of zero base fee to keep it simple


## Usage

Review all your channels

> python cln_channel_review.py --cli-args lightning-dir=_YOUR_CLN_DIR_ 

Review one channel

> python cln_channel_review.py --cli-args lightning-dir=_YOUR_CLN_DIR_ --peer-id=_your_peer_pubkey_

Review channels that have forwards(in/out) in the last 5 days

> python cln_channel_review.py --cli-args lightning-dir=_YOUR_CLN_DIR_ --recent-forward=5

Review channels that have forwards between 3 to 10 days

> python cln_channel_review.py --cli-args lightning-dir=_YOUR_CLN_DIR_ --recent-forward=3,10

Review channels that have no forwards the last 20 days

> python cln_channel_review.py --cli-args lightning-dir=_YOUR_CLN_DIR_ --absent-forward=20

There's also --xdays parameter that has a default of 30 days

## How am I using it ?

Initially I review all the channels.
Every 2 days. I run:

--recent-forward=2

to raise the fee on busy channels

Occationally I run:

--recent-forward=2,7

to lower the rate of channels that I bump too high that they stop forwarding

Occationally I run:

--recent-forward=25

to try to get quiet channels going

## Demo
(there's color highlight if you run on a supported terminal)

```
--recent-forward 1

03axx(PeerX) - 47 out of 47
channel size: 12.10M, to_us 9.9016M, ratio 0.82
local_fee(0,135) remote_fee(899,5)
last ppm 128, in forward 0 days ago, out forward 4 days ago
last 30 days num_forward(in 65, out 60)
last 30 days fee earned 232
last 30 days ppm min 24, avg 31, median 30, max 128
remote peer's ppms distribution: 20:5 30:20 40:40 50:70 60:116 70:179 80:300
Change PPM to [default=no change;base,pmm;ppm]: 131
---
03bxxx(PeerY) - 46 out of 47
channel size: 7.10M, to_us 0.5374M, ratio 0.08
local_fee(0,9999) remote_fee(0,30)
last ppm 20, in forward 0 days ago, out forward 0 days ago
last 30 days num_forward(in 42, out 112)
last 30 days fee earned 352
last 30 days ppm min 9, avg 30, median 20, max 95
remote peer's ppms distribution: 20:5 30:21 40:55 50:96 60:120 70:200 80:311
Change PPM to [default=no change;base,pmm;ppm]: 
--
03cxx(PeerZ) - 45 out of 47
channel size: 10.00M, to_us 9.8687M, ratio 0.99
local_fee(0,651) remote_fee(10000,10000)
last ppm 710, in forward 0 days ago, out forward 3 days ago
last 30 days num_forward(in 30, out 9)
last 30 days fee earned 25
last 30 days ppm min 710, avg 710, median 710, max 710
remote peer's ppms distribution: 20:1 30:8 40:84 50:200 60:418 70:610 80:1000
Change PPM to [default=no change;base,pmm;ppm]: 601
```
