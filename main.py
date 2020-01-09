import boto3, argparse, sys
from botocore.exceptions import ClientError

PROFILE = ''
IS_DRY_RUN = False
TAG_KEY = 'isDefault'
TAG_VALUE = 'true'

def parse_arg():
    global IS_DRY_RUN, PROFILE
    parser = argparse.ArgumentParser(description='Add AWS tag {isDefault: true} to default EC2 & RDS resources')
    parser.add_argument('-d', '--dryrun', action='store_true', help='set dry_run flag')
    parser.add_argument('--profile', action='store', help='set aws profile')
    profile = parser.parse_args().profile
    PROFILE = 'default' if profile is  None else profile
    IS_DRY_RUN = parser.parse_args().dryrun

def query_default_vpc(ec2, region):
    default_vpc = ec2.describe_vpcs(
        Filters=[{ 'Name': 'isDefault', 'Values': ['true']}]
    )
    if(len(default_vpc['Vpcs']) == 0):
        print('INFO:EC2:' + region + ': Default VPC not found.')
        return None
    return default_vpc['Vpcs'][0]['VpcId']

def query_defaultvpc_ec2_resources(ec2, vpc, region):
    default_vpc_condition = [{
        'Name': 'vpc-id',
        'Values': [vpc]
    }]
    default_vpc_resources = [vpc]

    # Subnet
    response = ec2.describe_subnets(Filters=default_vpc_condition)
    default_vpc_resources.extend(generate_resourceid_list(response, 'Subnets', 'SubnetId'))

    # SecurityGroups
    response = ec2.describe_security_groups(Filters=default_vpc_condition)
    default_vpc_resources.extend(generate_resourceid_list(response, 'SecurityGroups', 'GroupId'))

    # ACL
    response = ec2.describe_network_acls(Filters=default_vpc_condition)
    default_vpc_resources.extend(generate_resourceid_list(response, 'NetworkAcls', 'NetworkAclId'))

    # RouteTable
    response = ec2.describe_route_tables(Filters=default_vpc_condition)
    default_vpc_resources.extend(generate_resourceid_list(response, 'RouteTables', 'RouteTableId'))

    # InternetGateway
    response = ec2.describe_internet_gateways(Filters=[
        {'Name': 'attachment.vpc-id', 'Values': [vpc]}
    ])
    default_vpc_resources.extend(generate_resourceid_list(response, 'InternetGateways', 'InternetGatewayId'))

    # DHCP optionset
    response = ec2.describe_dhcp_options(Filters=[
        {'Name': 'key', 'Values': ['domain-name']},
        {'Name': 'value', 'Values': [region+'.compute.internal','ec2.internal'] }
    ])
    default_vpc_resources.extend(generate_resourceid_list(response, 'DhcpOptions', 'DhcpOptionsId'))

    return default_vpc_resources

def add_ec2_tag (ec2, resourcelist, tagkey, tagvalue, region):
    print('INFO:EC2:' + region + ': Tag on '+ ','.join(resourcelist))
    try:
        ec2.create_tags(
            DryRun=IS_DRY_RUN,
            Resources=resourcelist,
            Tags=[{'Key': tagkey, 'Value': tagvalue}]
        )
    except ClientError as e:
        if 'DryRunOperation' == e.response['Error']['Code']:
            print('INFO:EC2:' + region + ': '+ e.response['Error']['Message'])
        else:
            raise
    else:
        print('INFO:EC2:' + region + ': Success!')

def generate_resourceid_list(response, top_key, resourceid_key):
    return [item[resourceid_key] for item in response[top_key]]

def query_rds_defaultsg_list(rds, region):
    try:
        response =  rds.describe_db_security_groups(DBSecurityGroupName='default')
    except ClientError as e:
        if 'DBSecurityGroupNotFound' == e.response['Error']['Code']:
            print('INFO:RDS:' + region + ': ' + e.response['Error']['Message'])
        else:
            raise
    else:
        return response['DBSecurityGroups'][0]

def add_rds_tag (rds, resource_arn, tagkey, tagvalue, region):
    print('INFO:RDS:' + region + ': Tag on ' + resource_arn)
    if(IS_DRY_RUN):
        print('INFO:RDS:'+ region +': Request would have succeeded, but DryRun flag is set.')
        return
    else:
        try:
            rds.add_tags_to_resource(
                ResourceName=resource_arn,
                Tags=[{'Key': tagkey, 'Value': tagvalue}]
            )
        except:
            raise
        else:
            print('INFO:RDS:' + region + ': Success!')

def create_clients():
    try:
        session = boto3.Session(profile_name=PROFILE)
    except Exception as e:
        print(e)
        sys.exit()
    regions = [region['RegionName'] for region in session.client('ec2', region_name='us-east-1').describe_regions()['Regions']]
    ec2 = [session.client('ec2',region_name=region) for region in regions]
    rds = [session.client('rds',region_name=region) for region in regions]
    return list(zip(regions, ec2, rds))

def main():
    parse_arg()
    clients = create_clients()
    for client in clients:
        region, ec2, rds = client
        vpc = query_default_vpc(ec2, region)
        if (vpc):
            default_vpc_resources = query_defaultvpc_ec2_resources(ec2, vpc, region)
            add_ec2_tag(ec2, default_vpc_resources, TAG_KEY, TAG_VALUE, region)
        rds_default_sg = query_rds_defaultsg_list(rds,region)
        if(rds_default_sg):
            add_rds_tag(rds, rds_default_sg['DBSecurityGroupArn'], TAG_KEY, TAG_VALUE,region)

if __name__ == "__main__":
    main()