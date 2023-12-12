import json
import boto3
import os 
import uuid


ec2Client = boto3.client('ec2')
asgClient = boto3.client('autoscaling')

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
    print(message)

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

    print(message)

def createSecurityGroup(vpcID, string):
    newSecurityGroup = ec2Client.create_security_group(
        Description='Security Group created by Incedent Response Lambda',
        GroupName='Isolated Security Group-{}'.format(string),
        VpcId=vpcID,
    )
    return newSecurityGroup


def untrackSecurityGroup(securityGroup):
    ec2Client.authorize_security_group_ingress(
        GroupId=securityGroup['GroupId'],
        IpPermissions=[
            {
                'FromPort': 22,
                'IpProtocol': 'tcp',
                'IpRanges': [
                    {
                        'CidrIp': '0.0.0.0/0',
                        'Description': 'SSH untracked access',
                    },
                ],
                'ToPort': 22,
            },
        ],
    )

def lambda_handler(event, context):
    instanceID = event['detail']['resource']['instanceDetails']['instanceId']
    vpcID = identifyInstanceVpcId(instanceID)
    unique_id = str(uuid.uuid4())
    #detaching from an ASG
    detachASG(instanceID)
    #blocking ec2 termination
    setTerminationProtection(instanceID)

    #creating a new security group for untracking
    untrackSG = createSecurityGroup(vpcID, 'tmp')
    #untracking security group 
    untrackSecurityGroup(untrackSG)
    #attaching the new security group on ec2 instance
    ec2Client.modify_instance_attribute(InstanceId=instanceID, Groups=[untrackSG['GroupId']])

    #creating a new security group for tracking
    trackSG = createSecurityGroup(vpcID, unique_id)

    #attaching the track security group with no inbound rules and deleting the untrack securitygroup
    ec2Client.modify_instance_attribute(InstanceId=instanceID, Groups=[trackSG['GroupId']])  
    ec2Client.delete_security_group(GroupId=untrackSG['GroupId'])
    
    return {
        'statusCode': 200,
        'body': json.dumps('Success!')
    }
    
