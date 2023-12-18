# Automated EC2 Isolation For Incident Response
This Sample demonstrates how to deploy a solution for automatic isolation of Amazon EC2 behaving suspiciously

## Solution Overview
![Alt text](https://d195kho0tyqjph.cloudfront.net/GitHub/EC2-Isolation-Blogpost-Diagram.png? "Solution Overview")

In Amazon VPC, we have the functionality of Security Groups. They control incoming and outgoing traffic to applied resources. For example, when associating an EC2 instance with a Security Group, it acts as a stateful firewall to allow or deny external communication to that instance. Inbound rules control incoming traffic to the instance, and outbound rules control outgoing traffic from the instance. It is through the Security Group of the instance that is detected with suspicious behavior that the isolation action will be taken.

* Incident Response Pipeline: This component is responsible for detecting vulnerabilities and anomalies in the workload and, in turn, triggering the instance isolation process through the following services:
    1. Amazon GuardDuty: Service responsible for detecting potential threats. It continuously monitors malicious activities in AWS accounts, including Amazon EC2 instances, generating Findings.
    2. Amazon EventBridge: Service responsible for being the broker that sends the payload with GuardDuty findings to an AWS Lambda function, which will be responsible for executing instance isolation actions.
    3. AWS Lambda: Service responsible for executing the code that contains the business logic for isolating the EC2 instance.

* Forensic: After the potentially compromised instance has undergone the entire isolation process performed by AWS Lambda, the instance will be separated from the internet or the rest of the application environment, ready to initiate the investigation and forensic process using the AWS Systems Manager Session Manager service.

## Pre-requisites
* AWS [CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-welcome.html) with [credentials configured](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html) which will also be used by the CDK.
* Create and source a Python virtualenv on MacOS and Linux, and install python dependencies: 
<pre><code>python3 -m venv .env
source .env/bin/activate
pip install -r requirements.txt
</code></pre>

* Install the latest version of the AWS [CDK](https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html) CLI:
<pre><code>npm i -g aws-cdk</code></pre>
* [Bootstrapping](https://docs.aws.amazon.com/cdk/v2/guide/bootstrapping.html) your CDK with:
<pre><code>cdk bootstrap</code></pre>


## Running
Make sure you have AWS CDK installed and working, all the dependencies of this project defiend in the requirements.txt file.

Before deploy the application note that Amazon EventBridge is set to trigger AWS Lambda with any type of finding from Amazon GuardDuty by default. However, you can modify this in <code>/automated-ec2-isolation-for-incident-response/cdk_deploy_for_isolated_ec2/cdk_deploy_for_isolated_ec2_stack.py</code> in the <code>source</code> parameter of the <code>broker</code> object. Replace <code>"aws.guardduty"</code> with the specific finding you desire.
You can check the Finding types [here](https://docs.aws.amazon.com/guardduty/latest/ug/guardduty_finding-types-active.html)

1.
<pre><code>git clone https://github.com/aws-samples/automated-ec2-isolation-for-incident-response.git
cd automated-ec2-isolation-for-incident-response 
</code></pre>
2. Run <code>cdk deploy</code> and wait for the deployment to finish successfully;

## Testing
1. Open you AWS Console in the region where you deployed the application
2. [Launch an EC2 instance](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EC2_GetStarted.html#ec2-launch-instance) 
3. Connect to your instance from your [Linux or Mac](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/connect-linux-inst-ssh.html) local machine or [Windows](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/connect-linux-inst-from-windows.html)
4. [Genereta sample findings to your EC2 instance](https://docs.aws.amazon.com/guardduty/latest/ug/sample_findings.html#guardduty_findings-scripts)

After this steps, wait around 3 minutes and you can check that your SSH connection to your EC2 has been fineshed and and also the Security Group has changed.

## Cleaning Up
Open your terminal on the root of the clone repository and run this command:
<pre><code>
cdk destroy
</code></pre>

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

