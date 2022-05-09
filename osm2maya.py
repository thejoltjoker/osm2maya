import os

import maya.cmds as cmds
import random
import xml.dom.minidom

import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(name)s %(levelname)s: %(message)s')
logger = logging.getLogger()


def parse_osm_file(path):
    # replace filepath with the absolute path of the OSM file you have downloaded
    doc = xml.dom.minidom.parse(path)

    # building:levels
    # Get all "way" elements
    buildings = []
    all_ways = doc.getElementsByTagName("way")

    # Iterate over ways and append buildings to list
    for el in all_ways:
        for ch in el.childNodes:
            if ch.attributes:
                # Check if the k tag is equal to building
                if 'k' in ch.attributes.keys() and ch.attributes['k'].value == 'building':
                    buildings.append(el)
                    break

    # Find nodes and store coordinates
    nodes = doc.getElementsByTagName("node")
    id_to_tuple = {}
    for node in nodes:
        id_val = node.attributes['id'].value

        # Process nodes with coordinates and store in dictionary
        if 'lon' in node.attributes.keys():
            (lon, lat) = (node.attributes['lon'].value, node.attributes['lat'].value)
            id_to_tuple[id_val] = (lon, lat)

    all_buildings = []

    for b in buildings:
        lst = []
        nds = b.getElementsByTagName('nd')
        for ch in nds:
            if ch.tagName == 'nd':
                node_id = ch.attributes['ref'].value
                lst.append(id_to_tuple[node_id])

        tags = b.getElementsByTagName('tag')
        level = 1
        for tag in tags:
            if tag.tagName == 'tag':
                if tag.attributes['k'].value == 'building:levels':
                    try:
                        level = int(tag.attributes['v'].value)
                    except:
                        level = 1

        all_buildings.append((lst, level))

    all_buildings = sorted(all_buildings)

    sz = len(all_buildings)

    start_lon = float(all_buildings[int(sz / 2)][0][0][0])
    start_lat = float(all_buildings[int(sz / 2)][0][0][1])

    print(all_buildings[0])

    buildings_xy = []

    for lst in all_buildings:
        tmp = []
        for i in lst[0]:
            tmp.append(get_xy(start_lon, start_lat, i[0], i[1]))

        # height froom levels
        h = lst[1]
        buildings_xy.append((tmp, h))

    print(buildings_xy[0])

    # Polygons ready, now use it below

    cubeList = cmds.ls('myCube*')
    if len(cubeList) > 0:
        cmds.delete(cubeList)

    all_poly = []
    buildings_geo = []
    for lst in buildings_xy:
        tmp = []
        for i in lst[0]:
            (x, z) = i
            x /= -100
            z /= 100
            y = 0
            tmp.append((x, y, z))
        h = lst[1]
        res = cmds.polyCreateFacet(p=tmp, name='buildingpoly#')

        all_poly.append(res)
        thickness = random.uniform(0.1, 0.2)
        assert h >= 0

        normals = cmds.polyInfo(res[0], fn=1)
        normal = float(normals[0].split(":")[1].split()[1])

        # For reversed normals, Just redraw in anticlockwise
        if normal < 0:
            cmds.delete(res[0])
            tmp.reverse()
            res = cmds.polyCreateFacet(p=tmp, name='buildingpoly#')
            normals = cmds.polyInfo(res[0], fn=1)
            normal = float(normals[0].split(":")[1].split()[1])

        cmds.polyExtrudeFacet(res[0], kft=1, thickness=(h / 10.0))

        # Append new geo to list of buildings geo
        buildings_geo.append(res[0])

    # Group all buildings and rename group to osm file
    print(buildings_geo)
    group = cmds.group(buildings_geo, n=os.path.basename(path))
    cmds.scale(1, 1, 2, group)


def get_xy(lon_a, lat_a, lon_b, lat_b):
    mul = 111.321 * 1000  # meters
    diff_lon = float(lon_b) - float(lon_a)
    diff_lat = float(lat_b) - float(lat_a)
    return (diff_lon * mul, diff_lat * mul)


def main():
    # path = '/Volumes/libraries/assemblies/001-City/sandbox/oslo_001.osm'
    path = '/Users/johannes/dropbox/temp/downloads/map(7).osm'
    parse_osm_file(path)


if __name__ == '__main__':
    main()
