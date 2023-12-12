#!/usr/bin/env python3
import os

import aws_cdk as cdk

from cdk_deploy_for_isolated_ec2.cdk_deploy_for_isolated_ec2_stack import CdkDeployForIsolatedEc2Stack


app = cdk.App()
CdkDeployForIsolatedEc2Stack(app, "CdkDeployForIsolatedEc2Stack",)

app.synth()
