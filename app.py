#!/usr/bin/env python3
import os

import aws_cdk as cdk

from new_parkruns.new_parkruns_stack import NewParkrunsStack


app = cdk.App()
NewParkrunsStack(
    app,
    "NewParkrunsStack",
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"), region=os.getenv("CDK_DEFAULT_REGION")
    ),
)

app.synth()
