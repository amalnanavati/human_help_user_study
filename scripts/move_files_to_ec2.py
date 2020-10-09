import os

for uuid, gid in [(1483,2)]:#[(691,2),(668,2),(702,0),(664,1),(684,0),(671,1),(656,2),(666,0),(686,2),(696,1),(705,2),(673,0),(703,1),(655,1),(672,2),(654,0),(683,0)]:
    cmd = "scp -i ~/Documents/AWS/AmalOnlineGameHCRLabAccountKeyPair.pem /Users/amaln/Documents/PRL/human_help_user_study/flask/ec2_outputs_evaluation/{}/{}_policy_output_fixed.json ec2-user@ec2-52-12-119-96.us-west-2.compute.amazonaws.com:human_help_user_study/flask/outputs/{}/{}_policy_output_fixed.json".format(uuid, gid, uuid, gid)
    os.system(cmd)

cmd = "scp -i ~/Documents/AWS/AmalOnlineGameHCRLabAccountKeyPair.pem /Users/amaln/Documents/PRL/human_help_user_study/flask/ec2_outputs_evaluation/1483/2_data_fixed.json ec2-user@ec2-52-12-119-96.us-west-2.compute.amazonaws.com:human_help_user_study/flask/outputs/1483/2_data_fixed.json"
os.system(cmd)
