"""
This is a script to move layer 3 switched virtual interfaces (SVIs) from a list of servers to a second list of servers.
The script will read and compare the SVIs between the target switches and ensure they are identical.  Any errors or
deviations will be printed to console.  Once the errors are clear, the SVIs will be created on the destination
switches.

Authored by Brian Buxton
This is created under the Cisco Sample Code License v1.1.  See LICENSE file for terms.
"""

import meraki
import json


API_KEY = ''
dashboard = meraki.DashboardAPI(API_KEY)
organizations = dashboard.organizations.getOrganizations()
relocationIp = ''
defaultMgmtIp = ''
source_switch = ''
dest_switch = ''


def get_svi_dict(switch):
    """
    The function returns a list of SVIs from a source switch stack.
    :rtype: dict
    :return: a dict of SVIs and their DHCP settings
    """
    return {interface['interfaceId']: [interface, dashboard.switch.getDeviceSwitchRoutingInterfaceDhcp(serial=switch, interfaceId=interface['interfaceId'])] for interface in dashboard.switch.getDeviceSwitchRoutingInterfaces(serial=switch)}


def move_svis(source, dest):
    """
    This function moves a list of SVIs from a source switch to a destination switch.  This function will not configure
    full DHCP Servers.  It will copy DHCP disabled and DHCP relays ONLY.
    :param source:
    :param dest:
    :return:
    """
    try:
        svi_dict = get_svi_dict(source)
        with open('svi.json', 'w') as jsonfile:
            json.dump(svi_dict, jsonfile, indent=5)
            jsonfile.close()
    except BaseException as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return 1
    try:
        for interfaceId, interfaceValue in svi_dict.items():
            print(f'Processing source interface {interfaceId}')
            if interfaceValue[0]['name'] != 'Management':
                print(f'Deleting non-management source interface {interfaceId}')
                dashboard.switch.deleteDeviceSwitchRoutingInterface(serial=source, interfaceId=interfaceId)
            else:
                print(f'Updating management source interface {interfaceId}')
                dashboard.switch.updateDeviceSwitchRoutingInterface(serial=source, interfaceId=interfaceId,
                                                                    interfaceIp=relocationIp)
    except BaseException as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return 2
    try:
        for a, b in svi_dict.items():
            if b[0]['name'] != 'Management':
                print(f'Creating non-management dest {b[0]["name"]}')
                dashboard.switch.createDeviceSwitchRoutingInterface(
                    dest, b[0]['name'], b[0]['interfaceIp'], b[0]['vlanId'],
                    subnet=b[0]['subnet'],
                    multicastRouting=b[0]['multicastRouting'],
                    ospfSettings={'area': b[0]['ospfSettings']['area']} if b[0]['ospfSettings']['area'] == 'ospfDisabled' else
                    {'area': b[0]['ospfSettings']['area'], 'cost': b[0]['ospfSettings']['cost'],
                     'isPassiveEnabled': b[0]['ospfSettings']['isPassiveEnabled']}
                )
            else:
                print(f"Creating temp SVI list")
                temp_svi_list = get_svi_dict(dest)
                try:
                    print(f"Creating Management dest {b[0]['name']}")
                    dashboard.switch.createDeviceSwitchRoutingInterface(
                        dest, b[0]['name'], b[0]['interfaceIp'], b[0]['vlanId'],
                        subnet=b[0]['subnet'],
                        multicastRouting=b[0]['multicastRouting'],
                        defaultGateway=b[0]['defaultGateway'],
                        ospfSettings={'area': b[0]['ospfSettings']['area']} if b[0]['ospfSettings']['area'] == 'ospfDisabled' else
                        {'area': b[0]['ospfSettings']['area'], 'cost': b[0]['ospfSettings']['cost'],
                         'isPassiveEnabled': b[0]['ospfSettings']['isPassiveEnabled']}
                    )
                except BaseException as err:
                    print(f"Unexpected {err=}, {type(err)=}")
                    for c, d in temp_svi_list.items():
                        if d[0]['name'] == 'Management':
                            interfaceId = d[0]['interfaceId']
                        else:
                            pass
                    print(f"Couldn't create, so updating mgmt interface {interfaceId}")
                    dashboard.switch.updateDeviceSwitchRoutingInterface(serial=dest, interfaceId=interfaceId,
                                                                        interfaceIp=defaultMgmtIp)
    except BaseException as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return 3
    try:
        print("Creating a list of the current dest SVIs for DHCP comparison to original")
        dest_svi_dict = get_svi_dict(dest)
    except BaseException as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return 4
    try:
        # update_dest_dict = {k: [dest_svi_dict[k][0], svi_dict] for k in dest_svi_dict if k[0]['vlanId'] in svi_dict[y][0]['vlanId'] }
        for a, b in svi_dict.items():
            if b[1]['dhcpMode'] == 'dhcpRelay':
                for c, d in dest_svi_dict.items():
                    print(f"destination vlan {d[0]['vlanId']} and source vlan {b[0]['vlanId']}")
                    if d[0]['vlanId'] == b[0]['vlanId']:
                        d[1] = b[1]
                        print(f"destination {d[1]} and source {b[1]}")
                    else:
                        pass
            else:
                pass
        print(dest_svi_dict)
    except BaseException as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return 5
    try:
        for a, b in dest_svi_dict.items():
            if b[1]['dhcpMode'] == 'dhcpRelay':
                dashboard.switch.updateDeviceSwitchRoutingInterfaceDhcp(serial=dest, interfaceId=a,
                                                                        dhcpMode=b[1]['dhcpMode'],
                                                                        dhcpRelayServerIps=b[1]['dhcpRelayServerIps'])
            else:
                pass
    except BaseException as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return 6


if __name__ == '__main__':
    # networks = dashboard.organizations.getOrganizationNetworks(organizationId=organizations[0]['id'])
    # devices = dashboard.networks.getNetworkDevices(networkId='')
    move_svis(source_switch, dest_switch)
