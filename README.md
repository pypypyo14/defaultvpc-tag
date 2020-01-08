# defaultvpc-tag

## ABOUT
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

## USAGE
```
usage: main.py [-h] [-d]

Add AWS tag {isDefault: true} to default EC2 & RDS resources

optional arguments:
  -h, --help    show this help message and exit
  -d, --dryrun  set dry_run flag
```