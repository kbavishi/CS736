#! /usr/bin/python

"""An example of constructing a profile with an x86_64 PC which was Ubuntu
16.04 installed.

Instructions:
Wait for the profile instance to start, and then log in to either PC via the
ssh ports specified below.
"""

import geni.portal as portal
import geni.rspec.pg as rspec

request = portal.context.makeRequestRSpec()

pc = portal.Context()

longDesc = "A specific hardware type to use for each node.  Cloudlab clusters "
"all have machines of specific types.  When you set this field to a value that "
"is a specific hardware type, you will only be able to instantiate this profile "
"on clusters with machines of that type.  If unset, when you instantiate the "
"profile, the resulting experiment may have machines of any available type "
"allocated."

pc.defineParameter("osNodeType", "Hardware type of node",
                   portal.ParameterType.NODETYPE, "c220g1",
                   longDescription=longDesc)

params = pc.bindParameters()

# Create the RawPC nodes.
node = request.RawPC("node%d" % i)
if params.osNodeType:
	node.hardware_type = params.osNodeType

# Use Ubuntu 16.04 image
node.disk_image = "urn:publicid:IDN+wisc.cloudlab.us+image+netopt-PG0:2pc_ubuntu16_04:0"

portal.context.printRequestRSpec()
