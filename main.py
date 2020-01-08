import boto3, argparse
from botocore.exceptions import ClientError

IS_DRY_RUN = False
TAG_KEY = 'isDefault'
TAG_VALUE = 'true'
REGIONS = [region['RegionName'] for region in boto3.client('ec2').describe_regions()['Regions']]

def parse_arg():
    global IS_DRY_RUN
    parser = argparse.ArgumentParser(description='Add AWS tag {isDefault: true} to default EC2 & RDS resources')
    parser.add_argument('-d', '--dryrun', action='store_true', help='set dry_run flag')
    IS_DRY_RUN = parser.parse_args().dryrun

def query_default_vpc(ec2):
    default_vpc = ec2.describe_vpcs(
        Filters=[{ 'Name': 'isDefault', 'Values': ['true']}]
    )
    if(len(default_vpc['Vpcs']) == 0):
        print('EC2: Default VPC not found.')
        return None
    return default_vpc['Vpcs'][0]['VpcId']

def query_defaultvpc_ec2_resources(ec2, vpc):
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
    default_domain_names=[region + '.compute.internal' for region in REGIONS] + ['ec2.internal']
    response = ec2.describe_dhcp_options(Filters=[
        {'Name': 'key', 'Values': ['domain-name']},
        {'Name': 'value', 'Values': default_domain_names}
    ])
    default_vpc_resources.extend(generate_resourceid_list(response, 'DhcpOptions', 'DhcpOptionsId'))

    return default_vpc_resources

def add_ec2_tag (ec2, resourcelist, tagkey, tagvalue):
    print('EC2: ' + ','.join(resourcelist))
    try:
        ec2.create_tags(
            DryRun=IS_DRY_RUN,
            Resources=resourcelist,
            Tags=[{'Key': tagkey, 'Value': tagvalue}]
        )
    except ClientError as e:
        if 'DryRunOperation' == e.response['Error']['Code']:
            print('EC2: '+ e.response['Error']['Message'])
        else:
            raise
    else:
        print('EC2: done')

def generate_resourceid_list(response, top_key, resourceid_key):
    return [item[resourceid_key] for item in response[top_key]]

def query_rds_defaultsg_list(rds):
    try:
        response =  rds.describe_db_security_groups(DBSecurityGroupName='default')
    except ClientError as e:
        if 'DBSecurityGroupNotFound' == e.response['Error']['Code']:
            print('RDS: '+ e.response['Error']['Message'])
        else:
            raise
    else:
        return response['DBSecurityGroups'][0]

def add_rds_tag (rds, resource_arn, tagkey, tagvalue):
    print('RDS: ' + resource_arn)
    if(IS_DRY_RUN):
        print('RDS: Request would have succeeded, but DryRun flag is set.')
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
            print('RDS: done')

def create_clients():
    ec2 = [boto3.client('ec2',region_name=region) for region in REGIONS]
    rds = [boto3.client('rds',region_name=region) for region in REGIONS]
    return {
        'ec2': ec2,
        'rds': rds
    }

def main():
    parse_arg()
    clients = create_clients()
    for ec2 in clients['ec2']:
        vpc = query_default_vpc(ec2)
        if (vpc):
            default_vpc_resources = query_defaultvpc_ec2_resources(ec2, vpc)
            add_ec2_tag(ec2, default_vpc_resources, TAG_KEY, TAG_VALUE)
    for rds in clients['rds']:
        rds_default_sg = query_rds_defaultsg_list(rds)
        if(rds_default_sg):
            add_rds_tag(rds, rds_default_sg['DBSecurityGroupArn'], TAG_KEY, TAG_VALUE)

if __name__ == "__main__":
    main()