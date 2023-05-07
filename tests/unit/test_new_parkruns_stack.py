import aws_cdk as core
import aws_cdk.assertions as assertions

from new_parkruns.new_parkruns_stack import NewParkrunsStack

# example tests. To run these tests, uncomment this file along with the example
# resource in new_parkruns/new_parkruns_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = NewParkrunsStack(app, "new-parkruns")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
