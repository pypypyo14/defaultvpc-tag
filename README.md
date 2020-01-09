# defaultvpc-tag

```
$ python main.py -h
usage: main.py [-h] [-d] [--profile PROFILE]

Add AWS tag {isDefault: true} to default EC2 & RDS resources

optional arguments:
  -h, --help         show this help message and exit
  -d, --dryrun       set dry_run flag
  --profile PROFILE  set aws profile
```

## about

- AWSアカウント作成時にデフォルトで存在するリソースにタグ付け(`{isDefault: true}`)するスクリプト
  - Default VPCとそれに紐づく以下のリソース
    - Subnet*
    - Security Groups*
    - Network ACL*
    - Route Table*
    - Internet Gateway*
  - デフォルトで作成されるDHCP Option Set
  - デフォルトで作成されるDBSecurityGroup
- 手動作成したDefault VPCにもタグが付く
- Default VPC内に手動で作った上記`*`印のリソースにもタグが付く
  - 厳密に管理したい場合は本スクリプトのDryRunや本スクリプト実行後にタグエディタなどから対象の確認をおすすめします

## 実行例

```
$ python main.py
INFO:EC2:eu-north-1: Tag on vpc-xxxxxxxx,subnet-xxxxxxxx,subnet-xxxxxxxx,subnet-xxxxxxxx,sg-xxxxxxxx,acl-xxxxxxxx,rtb-xxxxxxxx,igw-xxxxxxxx,dopt-xxxxxxxx
INFO:EC2:eu-north-1: Success!
INFO:RDS:eu-north-1: Tag on arn:aws:rds:eu-north-1:000000000000:secgrp:default
INFO:RDS:eu-north-1: Success!
INFO:EC2:ap-south-1: Tag on vpc-xxxxxxxx,subnet-xxxxxxxx,subnet-xxxxxxxx,subnet-xxxxxxxx,sg-xxxxxxxx,acl-xxxxxxxx,rtb-xxxxxxxx,igw-xxxxxxxx,dopt-xxxxxxxx
INFO:EC2:ap-south-1: Success!
INFO:RDS:ap-south-1: Tag on arn:aws:rds:ap-south-1:000000000000:secgrp:default
INFO:RDS:ap-south-1: Success!
INFO:EC2:eu-west-3: Tag on vpc-xxxxxxxx,subnet-xxxxxxxx,subnet-xxxxxxxx,subnet-xxxxxxxx,sg-xxxxxxxx,acl-xxxxxxxx,rtb-xxxxxxxx,igw-xxxxxxxx,dopt-xxxxxxxx
INFO:EC2:eu-west-3: Success!
INFO:RDS:eu-west-3: Tag on arn:aws:rds:eu-west-3:000000000000:secgrp:default
INFO:RDS:eu-west-3: Success!
(snip)
```