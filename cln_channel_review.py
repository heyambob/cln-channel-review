import json
import subprocess
from subprocess import PIPE, STDOUT
import time
from statistics import mean, median
from math import ceil
import numpy as np
import sys
from termcolor import colored

import argparse
 
parser = argparse.ArgumentParser(description="c-lightning channel review",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("--cli", default="lightning-cli", help="your lightning-cli command")
parser.add_argument("--cli-args", default=[], nargs='+', help="lightning-cli arguments ommitting --, for example --lightning-dir would be lightning-dir")
parser.add_argument("--xdays", default=30, type=int,help="last forward in xdays")
parser.add_argument("--peer-id", help="peer pubkey that you want to review otherwise it will review all your peers")
parser.add_argument("--recent-forward", help="review peers that forwards from i to j days")
parser.add_argument("--absent-forward", default=-1, type=int, help="review peers that have no forwards in the last n days")
cmd_args = parser.parse_args()
config = vars(cmd_args)

ONE_M=1000000000

clncli = [config["cli"]]+list(map((lambda a: "--"+a),config["cli_args"]))
xdays = config["xdays"]

def call_rpc(*args):
  args = clncli + list(args)
  j = subprocess.run(args, stdout=PIPE)
  return json.loads(j.stdout)

def peer_s_remote_ppms(peer_id):
  channels = call_rpc("listchannels","-k","destination="+peer_id)["channels"]

  return list(map(lambda c: c["fee_per_millionth"],channels))

mypubkey=call_rpc("getinfo")["id"]

if config["peer_id"] is None:
  all_peers = call_rpc("listpeers")["peers"] 

  if config["recent_forward"] is None and config["absent_forward"] == -1:
    pass
  elif config["recent_forward"] is not None and config["absent_forward"] != -1:
    raise "either recent_forward or absent_forward"
  else:
    channel_to_peer = {}
    for p in all_peers:
      if len(p["channels"]) == 1 and "short_channel_id" in p["channels"][0]:
        channel_to_peer[p["channels"][0]["short_channel_id"]]=p

    ct=int(time.time())
    want_peers= {}
    exclude_peers= {}

    if config["recent_forward"] is not None:
      tmp = config["recent_forward"].split(",",1) 
      if len(tmp) == 1:
        dfrom = 0
        dto = int(tmp[0])
      else:
        dfrom = int(tmp[0])
        dto = int(tmp[1])
    else:
      dfrom = 0
      dto = config["absent_forward"]


    for fw in call_rpc("listforwards","-k","status=settled")["forwards"]:
      ts = int(fw["resolved_time"])

      if ct-ts < 86400*dto:
        if fw["in_channel"] in channel_to_peer:
          if (ct-ts >= 86400*dfrom):
            want_peers[channel_to_peer[fw["in_channel"]]["id"]]=channel_to_peer[fw["in_channel"]]
          else:
            exclude_peers[channel_to_peer[fw["in_channel"]]["id"]]=channel_to_peer[fw["in_channel"]]

        if "out_channel" in fw:
          if fw["out_channel"] in channel_to_peer:
            if (ct-ts >= 86400*dfrom):
              want_peers[channel_to_peer[fw["out_channel"]]["id"]]=channel_to_peer[fw["out_channel"]]
            else:
              exclude_peers[channel_to_peer[fw["out_channel"]]["id"]]=channel_to_peer[fw["out_channel"]]

    if config["recent_forward"] is not None:
      all_peers=list(filter(lambda p: p["id"] not in exclude_peers, want_peers.values()))
    else:
      all_peers=list(filter(lambda p: p["id"] not in want_peers, all_peers))
      
else:
  all_peers = call_rpc("listpeers",config["peer_id"])["peers"]

progress = len(all_peers)
for peer in all_peers:
  if len(peer["channels"]) > 1:
    print("listpeers %s has more than 1 channels - how could that be? go investigate"%(peer["id"]))
  elif len(peer["channels"]) == 1 and "short_channel_id" in peer["channels"][0]:
    try:
      peerinfo = call_rpc("listnodes",peer["id"])["nodes"][0]
    except:
      peerinfo = {"alias": "node not exist in gossip"}

    channels = call_rpc("listchannels",peer["channels"][0]["short_channel_id"])["channels"]
    if len(channels) == 2:
      for channel in channels:
        if channel["source"] == mypubkey:
          local_fee_base = channel["base_fee_millisatoshi"]
          local_fee_ppm = channel["fee_per_millionth"]
        else:
          remote_fee_base = channel["base_fee_millisatoshi"]
          remote_fee_ppm = channel["fee_per_millionth"]

      channel_size = peer["channels"][0]["msatoshi_total"]
      channel_balance = peer["channels"][0]["msatoshi_to_us"]
      ratio = channel_balance/channel_size
      
      num_in_forward_last_xdays=0
      num_out_forward_last_xdays=0
      msat_earn_last_xdays=0
      ppm_out_last_xdays=[]
      last_in_forward=0
      last_out_forward=0
      last_ppm=0
      in_total_forward=0
      out_total_forward=0
      in_xdays_forward=0
      out_xdays_forward=0

      ct=int(time.time())

      for infw in call_rpc("listforwards","-k","status=settled","in_channel="+peer["channels"][0]["short_channel_id"])["forwards"]:
        ts = int(infw["resolved_time"])

        if ct-ts < 86400*xdays:
          num_in_forward_last_xdays += 1
          in_xdays_forward += int(infw["in_msat"][:-4])

        in_total_forward += int(infw["in_msat"][:-4])
        last_in_forward = max( int(infw.get("resolved_time", 0)), last_in_forward)

      for outfw in call_rpc("listforwards","-k","status=settled","out_channel="+peer["channels"][0]["short_channel_id"])["forwards"]:
        ts = int(outfw["resolved_time"])
        out_total_forward += int(infw["out_msat"][:-4])

        ppm = ceil(outfw["fee"]/outfw["out_msatoshi"]*1000000)
        if outfw["fee"] >= 1000:
           #if it's too small forward the fee isn't reliable
           last_ppm = ppm

        if ts > last_out_forward:
          last_out_forward = ts

        if ct-ts < 86400*xdays:
          num_out_forward_last_xdays += 1
          msat_earn_last_xdays += outfw["fee"]
          ppm_out_last_xdays += [ppm]
          out_xdays_forward += int(infw["out_msat"][:-4])

      colored_alias=colored(peerinfo["alias"],'green' if peer["connected"] else 'red')
      colored_ratio=colored("%.2f"%(ratio),('red' if ratio <= 0.2 else 'yellow' if ratio >= 0.8 else 'green'))
      colored_local_fee=colored("(%d,%d)"%(local_fee_base,local_fee_ppm),'magenta')
      colored_local_fee=colored("(%d,%d)"%(local_fee_base,local_fee_ppm),'magenta')
      colored_last_ppm=colored("%d"%(last_ppm),'green',attrs=["bold"])

      in_forward_days_ago=(ct-last_in_forward)/3600/24
      out_forward_days_ago=(ct-last_out_forward)/3600/24
      colored_in_forward_days_ago=colored("%d"%(in_forward_days_ago),'green' if in_forward_days_ago <= 7 else 'yellow' if in_forward_days_ago <= 20 else 'red')
      colored_out_forward_days_ago=colored("%d"%(out_forward_days_ago),'green' if out_forward_days_ago <= 7 else 'yellow' if out_forward_days_ago <= 20 else 'red')

      colored_num_in_forward_xdays=colored("%d"%(num_in_forward_last_xdays),'green' if num_in_forward_last_xdays >= 5 else 'yellow' if num_in_forward_last_xdays >= 2 else 'red')
      colored_num_out_forward_xdays=colored("%d"%(num_out_forward_last_xdays),'green' if num_out_forward_last_xdays >= 5 else 'yellow' if num_out_forward_last_xdays >=2 else 'red')


      print("%s(%s) - %d out of %d"%(peer["id"],colored_alias,progress,len(all_peers)))
      print("channel size: %.2fM, to_us %.4fM, ratio %s"%(channel_size/1000000000,channel_balance/1000000000,colored_ratio))
      print("local_fee%s remote_fee(%d,%d)"%(colored_local_fee,remote_fee_base,remote_fee_ppm))
      print("last ppm %s, in forward %s days ago, out forward %s days ago"%(colored_last_ppm, colored_in_forward_days_ago, colored_out_forward_days_ago))
      print("Msat in/out forwards (%.2f,%.2f) ; %s days ago (%.2f,%.2f)"%(in_total_forward/ONE_M,out_total_forward/ONE_M,xdays,in_xdays_forward/ONE_M,out_xdays_forward/ONE_M))
      print("last %s days num_forward(in %s, out %s)"%(xdays,colored_num_in_forward_xdays,colored_num_out_forward_xdays))
      print("last %d days fee earned %d"%(xdays,msat_earn_last_xdays/1000))
      if len(ppm_out_last_xdays) > 0:
        print("last %d days ppm min %d, avg %d, median %d, max %d"%(xdays,min(ppm_out_last_xdays),mean(ppm_out_last_xdays),median(ppm_out_last_xdays),max(ppm_out_last_xdays)))

      peer_fees = peer_s_remote_ppms(peer["id"])

      #print("peer's fees: "+ " ".join(map(str, peer_fees)))

      peer_fees = np.array(peer_fees)
      pf_pct = list(map(lambda n: (n,np.percentile(peer_fees, n)), [20, 30, 40, 50, 60, 70, 80]))

      print("remote peer's ppms distribution: "+ " ".join(map(lambda t: "%d:%s"%(t[0],colored("%d"%(t[1]),'yellow')), pf_pct)))

      print("Change PPM to [default=no change;base,pmm;ppm]: ",end='')
      sys.stdout.flush()
      line = sys.stdin.readline()
      new_ppm = line.rstrip()
      if new_ppm=="":
        pass
      else:
        try:
          [new_base,new_ppm]=list(map(int,line.split(",")))
        except:
          new_base = local_fee_base
          new_ppm = int(line)

        print(call_rpc("setchannelfee",peer["id"],str(new_base),str(new_ppm)))
    else:
      print("channel with %s(%s) is not ready - number of channels = %d"%(peerinfo["alias"],peer["id"],len(channels)))

    print("---")
  progress=progress-1
