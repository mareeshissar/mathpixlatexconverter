# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Command to update labels for external VPN gateway."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.external_vpn_gateways import external_vpn_gateways_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.external_vpn_gateways import flags as external_vpn_gateway_flag
from googlecloudsdk.command_lib.util.args import labels_util


_EXTERNAL_VPN_GATEWAY_ARG = (
    external_vpn_gateway_flag.ExternalVpnGatewayArgument())


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Update(base.UpdateCommand):
  r"""Update a Google Compute Engine external VPN gateway.

  *{command}* updates labels for a Google Compute Engine External VPN gateway.
  For example:

    $ {command} example-gateway \
      --update-labels=k0=value1,k1=value2 --remove-labels=k3

  will add/update labels ``k0'' and ``k1'' and remove labels with key ``k3''.

  Labels can be used to identify the External VPN gateway and to filter them
  as in

    $ {parent_command} list --filter='labels.k1:value2'

  To list existing labels

    $ {parent_command} describe example-gateway --format='default(labels)'

  """

  @classmethod
  def Args(cls, parser):
    """Adds arguments to the supplied parser.

    Args:
      parser: The argparse parser to add arguments to.
    """
    _EXTERNAL_VPN_GATEWAY_ARG.AddArgument(parser, operation_type='update')
    labels_util.AddUpdateLabelsFlags(parser)

  def Run(self, args):
    """Issues API requests to update a External VPN gateway.

    Args:
      args: argparse.Namespace, The arguments received by this command.
    Returns:
      [protorpc.messages.Message], A list of responses returned
      by the compute API.
    """
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    messages = holder.client.messages
    helper = external_vpn_gateways_utils.ExternalVpnGatewayHelper(holder)
    external_gateway_ref = _EXTERNAL_VPN_GATEWAY_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(holder.client))

    labels_diff = labels_util.Diff.FromUpdateArgs(args)
    if not labels_diff.MayHaveUpdates():
      raise calliope_exceptions.RequiredArgumentException(
          'LABELS', 'At least one of --update-labels or '
                    '--remove-labels must be specified.')

    external_vpn_gateway = helper.Describe(external_gateway_ref)
    labels_update = labels_diff.Apply(
        messages.GlobalSetLabelsRequest.LabelsValue,
        external_vpn_gateway.labels)

    if not labels_update.needs_update:
      return external_vpn_gateway

    operation_ref = helper.SetLabels(external_gateway_ref,
                                     external_vpn_gateway.labelFingerprint,
                                     labels_update.labels)
    return helper.WaitForOperation(
        external_gateway_ref, operation_ref,
        'Updating labels of External VPN Gateway [{0}]'.format(
            external_gateway_ref.Name()))
