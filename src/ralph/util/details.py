#!/usr/bin/env python
# -*- coding: utf-8 -*-

# !!! IMPORTANT !!!
# This file contains leftovers from 'src/ralph/util/pricing.py'.
# If you find that something here should be removed, feel free to do it.

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.core.urlresolvers import reverse_lazy
from django.utils.html import escape

from ralph.discovery.models import (
    DeviceType,
    DiskShare,
    EthernetSpeed,
)


def details_dev(dev):
    yield {
        'label': 'Device',
        'model': dev.model,
        'serial': dev.sn,
        'href': '/admin/discovery/device/%d/' % dev.id,
        'hrefinfo': reverse_lazy('search', kwargs={
            'details': 'info',
            'device': dev.id})
    }
    if dev.model is None:
        return
    if dev.model.type == DeviceType.blade_system.id:
        for d in dev.child_set.filter(deleted=False):
            if d.model.type == DeviceType.blade_server.id:
                yield {
                    'label': escape('Blade server %s' % d.name),
                    'model': d.model,
                    'icon': 'fugue-server-medium',
                    'serial': d.sn,
                    'hrefinfo': reverse_lazy('search', kwargs={
                        'details': 'info',
                        'device': d.id})
                }
            else:
                yield {
                    'label': d.name,
                    'model': d.model,
                    'serial': d.sn,
                    'hrefinfo': reverse_lazy('search', kwargs={
                        'details': 'info',
                        'device': d.id})
                }
    elif dev.model.type == DeviceType.blade_server.id:
        yield {
            'label': escape('Blade server %s' % dev.name),
            'model': dev.parent.model,
            'icon': 'fugue-servers',
            'serial': dev.parent.sn,
            'href': '/admin/discovery/device/%d/' % dev.parent.id,
            'hrefinfo': reverse_lazy('search', kwargs={
                'details': 'info',
                'device': dev.id})
        }


def details_cpu(dev):
    for cpu in dev.processor_set.all():
        speed = cpu.model.speed if (cpu.model and
                                    cpu.model.speed) else cpu.speed
        yield {
            'label': cpu.label,
            'model': cpu.model,
            'size': '%d core(s)' % cpu.get_cores(),
            'speed': '%d Mhz' % speed if speed else None,
        }


def details_mem(dev):
    for mem in dev.memory_set.all():
        speed = mem.model.speed if (mem.model and
                                    mem.model.speed) else mem.speed
        yield {
            'label': mem.label,
            'model': mem.model,
            'size': '%d MiB' % mem.get_size(),
            'speed': '%d Mhz' % speed if speed else None,
        }


def details_disk(dev):
    for disk in dev.storage_set.all():
        if disk.model:
            size = '%d MiB' % disk.get_size()
            yield {
                'label': disk.label,
                'model': disk.model,
                'serial': disk.sn or '',
                'size': size,
            }
    for mount in dev.disksharemount_set.all():
        total = mount.get_total_mounts()
        if mount.size:
            name = '%s (%d of %d MiB)' % (
                mount.share.label, mount.size, mount.share.size)
        elif total > 1:
            name = '%s (1/%d of %d MiB)' % (
                mount.share.label, total, mount.share.size)
        else:
            name = '%s (%d MiB)' % (mount.share.label, mount.share.size)
        if mount.is_virtual:
            name = '[Virtual Mount] %s' % name
        yield {
            'label': name,
            'model': mount.share.model,
            'size': mount.get_size(),
            'serial': mount.share.wwn,
            'count': total,
            'href': '/admin/discovery/diskshare/%d/' % mount.share.id,
        }
    # Exported shares
    for share in dev.diskshare_set.order_by('label').all():
        count = share.disksharemount_set.exclude(device=None).count()
        if share.disksharemount_set.exclude(server=dev).exclude(
                server=None).count():
            icon = 'fugue-globe-share'
        elif not share.full:
            icon = 'fugue-databases'
        else:
            icon = 'fugue-database'
        yield {
            'label': share.label,
            'size': share.get_total_size(),
            'count': count,
            'model': share.model,
            'serial': share.wwn,
            'icon': icon,
            'href': '/admin/discovery/diskshare/%d/' % share.id,
        }
    # Exported network shares
    for mount in dev.servermount_set.distinct().values(
            'volume', 'share', 'size'):
        share = DiskShare.objects.get(pk=mount['share'])
        yield {
            'label': mount['volume'] or share.label,
            'size': mount['size'] or share.get_total_size(),
            'count': share.disksharemount_set.exclude(device=None).count(),
            'serial': share.wwn,
            'model': share.model,
            'icon': 'fugue-globe-share',
            'href': '/admin/discovery/diskshare/%d/' % share.id,
        }


def details_software(dev):
    for soft in dev.software_set.order_by('path'):
        yield {
            'label': soft.label,
            'model': soft.model,
            'serial': soft.sn,
            'version': soft.version,
        }


def details_other(dev):
    for fc in dev.fibrechannel_set.all():
        if fc.model:
            yield {
                'label': fc.label,
                'model': fc.model,
                'serial': fc.physical_id,
            }
    for c in dev.genericcomponent_set.order_by('model', 'label').all():
        if c.model:
            yield {
                'label': c.label,
                'model': c.model,
                'serial': c.sn,
                'href': '/admin/discovery/genericcomponent/%d/' % c.id,
            }
    for eth in dev.ethernet_set.order_by('label'):
        yield {
            'label': eth.label,
            'model_name': 'Speed %s' % EthernetSpeed.NameFromID(eth.speed),

            'serial': eth.mac,
            'icon': 'fugue-network-ethernet',
        }
    for os in dev.operatingsystem_set.order_by('label'):
        details = []
        if os.cores_count:
            details.append('cores count: %d' % os.cores_count)
        if os.memory:
            details.append('memory: %d MiB' % os.memory)
        if os.storage:
            details.append('storage size: %d MiB' % os.storage)
        if details:
            label = "%s (%s)" % (os.label, ', '.join(details))
        else:
            label = os.label
        model = os.model if os else None
        yield {
            'label': label,
            'model': model,
        }


def details_all(dev):
    components = [
        {'d_name': 'dev', 'd_type': details_dev},
        {'d_name': 'cpu', 'd_type': details_cpu},
        {'d_name': 'mem', 'd_type': details_mem},
        {'d_name': 'disk', 'd_type': details_disk},
        {'d_name': 'software', 'd_type': details_software},
        {'d_name': 'other', 'd_type': details_other},
    ]
    for component in components:
        items = component['d_type'](dev)
        for detail in items:
            detail['group'] = component['d_name']
            yield detail
