from aws_cdk import App

from nextshift.stack_core import CoreStack
from nextshift.stack_messaging import MessagingStack

app = App()
core = CoreStack(app, "nextshift-core")
messaging = MessagingStack(app, "nextshift-messaging", core)
app.synth()
