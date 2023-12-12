# Automated EC2 Isolation For Incident Response
This Sample demonstrates how to deploy a solution for automatic isolation of compromised EC2 instances.

## Solution Overview
![Alt text](https://d195kho0tyqjph.cloudfront.net/GitHub/EC2-Isolation-Blogpost-Diagram.drawio.png? "Solution Overview")

The proposal of this solution is to automate your incident responses related to EC2 instances, with the Amazon GuardDuty monitoring, it is going to detect any anomalous or vulnerability in your EC2 instances through the Amazon GuardDuty Findings, the pipeline work this way:
1. Findings will be the producer of the Incident Response Pipeline
2. Amazon EventBridge is the broker that receives the Finding JSON, responsible to generate the trigger event to start the AWS Lambda function.
3. Trigger event starts the Lambda function and also contains EC2 instance ID, that will be used in the code to the isolate instance process

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

