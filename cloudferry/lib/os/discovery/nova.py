# Copyright 2016 Mirantis Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import itertools
import logging

from cloudferry.lib.os.discovery import cinder
from cloudferry.lib.os.discovery import glance
from cloudferry.lib.os.discovery import keystone
from cloudferry.lib.os.discovery import model

LOG = logging.getLogger(__name__)

HOST = 'OS-EXT-SRV-ATTR:host'
VOLUMES_ATTACHED = 'os-extended-volumes:volumes_attached'


class Flavor(model.Model):
    class Schema(model.Schema):
        object_id = model.PrimaryKey('id')

    @classmethod
    def load_missing(cls, cloud, object_id):
        compute_client = cloud.compute_client()
        raw_flavor = compute_client.flavors.get(object_id.id)
        return Flavor.load_from_cloud(cloud, raw_flavor)


class SecurityGroup(model.Model):
    class Schema(model.Schema):
        name = model.String(required=True)


class EphemeralDisk(model.Model):
    class Schema(model.Schema):
        path = model.String(required=True)
        size = model.Integer(required=True)


@model.type_alias('vms')
class Server(model.Model):
    class Schema(model.Schema):
        object_id = model.PrimaryKey('id')
        name = model.String(required=True)
        security_groups = model.Nested(SecurityGroup, many=True, missing=list)
        status = model.String(required=True)
        tenant = model.Dependency(keystone.Tenant)
        image = model.Dependency(glance.Image, allow_none=True)
        image_membership = model.Dependency(glance.ImageMember,
                                            allow_none=True)
        user_id = model.String(required=True)  # TODO: user reference
        key_name = model.String(required=True, allow_none=True)
        flavor = model.Dependency(Flavor)
        config_drive = model.String(required=True)
        availability_zone = model.String(required=True, allow_none=True)
        host = model.String(required=True)
        hypervisor_hostname = model.String(required=True)
        instance_name = model.String(required=True)
        metadata = model.Dict(missing=dict)
        ephemeral_disks = model.Nested(EphemeralDisk, many=True, missing=list)
        attached_volumes = model.Dependency(cinder.Volume, many=True,
                                            missing=list)
        # TODO: ports

        FIELD_MAPPING = {
            'host': HOST,
            'hypervisor_hostname': 'OS-EXT-SRV-ATTR:hypervisor_hostname',
            'instance_name': 'OS-EXT-SRV-ATTR:instance_name',
            'availability_zone': 'OS-EXT-AZ:availability_zone',
            'attached_volumes': VOLUMES_ATTACHED,
            'tenant': 'tenant_id',
        }
        FIELD_VALUE_TRANSFORMERS = {
            'image': lambda x: x or None
        }

    @classmethod
    def discover(cls, cloud):
        compute_client = cloud.compute_client()
        avail_hosts = list_available_compute_hosts(compute_client)
        with model.Session() as session:
            servers = []

            # Collect servers using API
            for tenant in session.list(keystone.Tenant, cloud.name):
                server_list = compute_client.servers.list(
                    search_opts={
                        'all_tenants': True,
                        'tenant_id': tenant.object_id.id,
                    })
                for raw_server in server_list:
                    host = getattr(raw_server, HOST)
                    if host not in avail_hosts:
                        LOG.warning('Skipping server %s, host not available.',
                                    host)
                        continue
                    # Workaround for grizzly lacking os-extended-volumes
                    overrides = {}
                    if not hasattr(raw_server, VOLUMES_ATTACHED):
                        overrides['attached_volumes'] = [
                            volume.id for volume in
                            compute_client.volumes.get_server_volumes(
                                raw_server.id)]
                    try:
                        srv = Server.load_from_cloud(cloud, raw_server,
                                                     overrides)
                        if srv.image and not srv.image.is_public \
                                and srv.image.tenant != srv.tenant:
                            srv.image_membership = glance.ImageMember.make(
                                cloud,
                                srv.image.object_id.id,
                                srv.tenant.object_id.id)
                            session.store(srv.image_membership)
                        servers.append(srv)
                        LOG.debug('Discovered: %s', srv)
                    except model.ValidationError as e:
                        LOG.warning('Server %s ignored: %s', raw_server.id, e)
                        continue

            # Discover ephemeral volume info using SSH
            servers.sort(key=lambda s: s.host)
            for host, host_servers in itertools.groupby(servers,
                                                        key=lambda s: s.host):
                with cloud.remote_executor(host, ignore_errors=True) as remote:
                    for srv in host_servers:
                        ephemeral_disks = _list_ephemeral(remote, srv)
                        if ephemeral_disks is not None:
                            srv.ephemeral_disks = ephemeral_disks
                            session.store(srv)

    def equals(self, other):
        # pylint: disable=no-member
        # TODO: consider comparing metadata
        # TODO: consider comparing security_groups
        if not self.tenant.equals(other.tenant):
            return False
        if not self.flavor.equals(other.flavor):
            return False
        if not self.image.equals(other.image):
            return False
        if self.key_name != other.key_name or self.name != other.name:
            return False
        return True


def _list_ephemeral(remote, server):
    result = []
    output = remote.sudo('virsh domblklist {instance}',
                         instance=server.instance_name)
    if not output.succeeded:
        LOG.warning('Unable to get ephemeral disks for server '
                    '%s, skipping.', server.object_id)
        return None
    volume_targets = set()
    for volume in server.attached_volumes:
        for attachment in volume.attachments:
            if attachment.server_id == server.object_id.id:
                volume_targets.add(attachment.device.replace('/dev/', ''))

    for line in output.splitlines():
        split = line.split(None, 1)
        if len(split) != 2:
            continue
        target, path = split
        if target in volume_targets or not path.startswith('/'):
            continue
        size_str = remote.sudo('stat -c %s {path}', path=path)
        if not size_str.succeeded:
            LOG.warning('Unable to get size of ephemeral disk "%s" for server '
                        '%s, skipping disk.', path, server.object_id)
            continue
        size = int(size_str.strip())
        eph_disk = EphemeralDisk.load({'path': path, 'size': size})
        result.append(eph_disk)
    return result


def list_available_compute_hosts(compute_client):
    return set(c.host
               for c in compute_client.services.list(binary='nova-compute')
               if c.state == 'up' and c.status == 'enabled')
