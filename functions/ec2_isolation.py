import json
import boto3
import uuid
import time
from botocore.exceptions import ClientError

ec2Client = boto3.client('ec2')
asgClient = boto3.client('autoscaling')



#Identify which is the VPC Id of the compromised instance 
def identifyInstanceVpcId(instanceId):
    instanceReservations = ec2Client.describe_instances(InstanceIds=[instanceId])['Reservations']
    for instanceReservation in instanceReservations:
        instancesDescription = instanceReservation['Instances']
        for instance in instancesDescription:
            return instance['VpcId']
        
# Checking to see if instance is part of an ASG. If it is then remove it from ASG
def detachASG(instance_id):
    print("Checking to see if instance is part of ASG")
    try:
        response = asgClient.describe_auto_scaling_instances(
            InstanceIds=[
                instance_id
            ]
        )
    except ValueError as e:
        message = 'Unable to describe ASG instances. Raw: ' + str(e['ErrorMessage'])

    if 'AutoScalingInstances' in response and len(response['AutoScalingInstances']) > 0:
        if 'AutoScalingGroupName' in response['AutoScalingInstances'][0]:
            asg_name = response['AutoScalingInstances'][0]['AutoScalingGroupName']
        else:
            message = 'Unable to obtain ASG name... will not be able to deregister instance. Exiting.'
        try:
            response = asgClient.detach_instances(
                InstanceIds=[
                    instance_id,
                ],
                AutoScalingGroupName=asg_name,
                ShouldDecrementDesiredCapacity=False
            )
            message = 'Success in detaching instance ' + instance_id + ' from ASG,' + asg_name
        except ValueError as e:
            message = 'Unable to remove ' + instance_id + ' from ' + asg_name + '. Error: ' + str(e['ErrorMessage'])
    else:
        message = 'Instance ' + instance_id + ' does not seem to be part of an ASG.'

# Setting termination protection for the instance. Ensuring nobody can accidently
# terminate the instance.
def setTerminationProtection(instance_id):
    print("Setting termination protection for the instance")
    try:
        response = ec2Client.modify_instance_attribute(
            InstanceId=instance_id,
            DisableApiTermination={
                'Value': True
            }
        )
        message = "Termination protection enabled for instance" + instance_id
    except ValueError as e:
        message = "Unable to set Termination protection for instance" + instance_id + str(e['ErrorMessage'])
   
#creates a new security group
def createSecurityGroup(vpcID, string):
    newSecurityGroup = ec2Client.create_security_group(
        Description='Security Group created by Incedent Response Lambda',
        GroupName='Isolated Security Group-{}'.format(string),
        VpcId=vpcID,
    )
    return newSecurityGroup

#untrack the security group allowing any inbound rule
def untrackSecurityGroup(securityGroup):
    ec2Client.authorize_security_group_ingress(
        GroupId=securityGroup['GroupId'],
        IpPermissions=[
            {
                'FromPort': -1,
                'IpProtocol': '-1',
                'IpRanges': [
                    {
                        'CidrIp': '0.0.0.0/0',
                        'Description': 'untracked access',
                    },
                ],
                'ToPort': -1,
            },
        ],
    )

    
def revokeOutRules(boolean, sgID):
    if boolean == 0:
        ec2Client.revoke_security_group_egress(
            GroupId=sgID,
            IpPermissions=[
                {
                    'IpProtocol': '-1',  # All protocols
                    'IpRanges': [
                        {
                            'CidrIp': '0.0.0.0/0' 
                        }
                    ]
                }
            ]
        )

def lambda_handler(event, context):
    instanceID = event['detail']['resource']['instanceDetails']['instanceId']
    vpcID = identifyInstanceVpcId(instanceID)
    unique_id = str(uuid.uuid4())
    instanceAttributes = ec2Client.describe_instances(InstanceIds=[instanceID])
    networkInterfaceID = instanceAttributes['Reservations'][0]['Instances'][0]['NetworkInterfaces'][0]['NetworkInterfaceId']
    
    #detaching from an ASG
    detachASG(instanceID)
    
    #blocking ec2 termination
    setTerminationProtection(instanceID)

    #creating a new security group for untracking
    untrackSG = createSecurityGroup(vpcID, 'tmp')
    
    #untracking security group 
    untrackSecurityGroup(untrackSG)
    
    
    #creating a new security group for tracking
    trackSG = createSecurityGroup(vpcID, unique_id)
    
    #revoking the outbound rules of the new security group to end the comunication with anything
    revokeOutRules(0, trackSG['GroupId'])
    
    #attaching the untrack security group on ec2 instance
    ec2Client.modify_network_interface_attribute(NetworkInterfaceId=networkInterfaceID, Groups=[untrackSG['GroupId']])
    
    time.sleep(180)
    
    #attaching the track security group with no inbound and outbound rules
    ec2Client.modify_network_interface_attribute(NetworkInterfaceId=networkInterfaceID, Groups=[trackSG['GroupId']])  
    
    #deleting the untrack securitygroup
    ec2Client.delete_security_group(GroupId=untrackSG['GroupId'])
    
    
    
    return {
        'statusCode': 200,
        'body': json.dumps('Success!')
    }
    
