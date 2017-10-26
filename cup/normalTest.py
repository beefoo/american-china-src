# -*- coding: utf-8 -*-

import bpy
import math
import numpy as np
import sys

def circle(vertices, center, radius, z):
    angleStart = -135
    angleStep = 360.0 / vertices
    c = []
    for i in range(vertices):
        angle = angleStart + angleStep * i
        p = translatePoint(center, angle, radius)
        c.append((p[0], p[1], z))
    return c

class Mesh:

    def __init__(self):
        self.verts = []
        self.edges = []
        self.faces = []
        self.edgeLoops = []

        self.queueLoopAfter = False

    def addEdgeLoop(self, loop, loopBefore=False, loopAfter=False):
        # add an edge loop after the previous one
        if self.queueLoopAfter is not False:
            self.addEdgeLoopHelper(loop, self.queueLoopAfter, True)
            self.queueLoopAfter = False
        # add an edge loop before the next one
        if loopBefore is not False:
            self.addEdgeLoopHelper(loop, loopBefore, False)
        # add an edge loop after the next one
        if loopAfter is not False:
            self.queueLoopAfter = loopAfter

        self.edgeLoops.append(loop)

    def addEdgeLoops(self, loops):
        for loop in loops:
            self.addEdgeLoop(loop)

    def addEdgeLoopHelper(self, nextLoop, amount, after=True):
        prevLoop = self.edgeLoops[-1]
        d = distance(prevLoop[0], nextLoop[0])
        lerpAmount = amount / d
        if lerpAmount >= 0.5:
            return False
        if not after:
            lerpAmount = 1.0 - lerpAmount
        loop = lerpEdge(prevLoop, nextLoop, lerpAmount)
        self.edgeLoops.append(loop)

    def joinEdgeLoops(self, loopA, loopB, indexOffset):
        faces = []
        aLen = len(loopA)
        bLen = len(loopB)

        # number of vertices differ
        if abs(bLen - aLen) > 0:

            # assume we're going from bigger to smaller
            bigger = aLen
            smaller = bLen
            biggerOffset = indexOffset
            smallerOffset = indexOffset + aLen

            # going from smaller to bigger
            if smaller > bigger:
                bigger = bLen
                smaller = aLen
                smallerOffset = indexOffset
                biggerOffset = indexOffset + aLen

            edgesPerSide = bigger / 4

            for i in range(bigger-4):
                offset = abs(i-1) / (edgesPerSide-1)
                v1 = i + offset + biggerOffset
                v2 = v1 + 1
                v3 = i + offset - offset * 2 + smallerOffset
                v4 = v3 - 1

                # special case for first
                if i==0:
                    v1 = biggerOffset
                    v2 = v1 + 1
                    v3 = smallerOffset
                    v4 = bigger - 1 + biggerOffset

                # special case for reach corner face
                elif i % (edgesPerSide-1) == 0:
                    v3 = v2 + 1

                # special case for last
                elif i==(bigger-5):
                    v3 = smallerOffset



                faces.append((v1, v2, v3, v4))

        # equal number of vertices
        else:
            for i in range(aLen):
                v1 = i
                v2 = i + 1
                v3 = i + 1 + aLen
                v4 = i + aLen
                if v2 >= aLen:
                    v2 = 0
                    v3 = aLen
                faces.append((v1+indexOffset, v2+indexOffset, v3+indexOffset, v4+indexOffset))

        self.faces += faces

    # join all the edge loop together
    def processEdgeloops(self):
        indexOffset = 0

        for i, edgeLoop in enumerate(self.edgeLoops):
            # add loop's vertices
            self.verts += edgeLoop

            # if this is the first edge loop and it's a quad, add it's face
            if i == 0 and len(edgeLoop) == 4:
                self.faces.append(range(4))

            elif i > 0:
                prev = self.edgeLoops[i-1]
                self.joinEdgeLoops(prev, edgeLoop, indexOffset)
                indexOffset += len(prev)

        # if the last edge loop is a quad, add it's face
        if len(self.edgeLoops[-1]) == 4:
            self.faces.append([(i+indexOffset) for i in range(4)])

def vector(p1, p2):
    x = p1[0] - p2[0]
    y = p1[1] - p2[1]
    z = p1[2] - p2[2]
    return (x, y, z)

def crossproduct(u, v):
    x = u[1] * v[2] - u[2] * v[1]
    y = u[2] * v[0] - u[0] * v[2]
    z = u[0] * v[1] - u[1] * v[0]
    return (x, y, z)

loopAbove = circle(16, (0,0), 20, 20)
loopCenter = circle(16, (0,0), 10, 10)
loopBelow = circle(16, (0,0), 5, 5)

mesh = Mesh()
mesh.addEdgeLoop(loopAbove)
mesh.addEdgeLoop(loopCenter)
mesh.addEdgeLoop(loopBelow)

# create faces from edges
mesh.processEdgeloops()

# blend starts here
scene = bpy.context.scene

# convert scene to metric, centimeters
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 0.01

# deselect all
bpy.ops.object.select_all(action='DESELECT')

# select all objects except camera and lamp
for obj in bpy.data.objects:
    if obj.name not in ["Camera", "Lamp"]:
        obj.select = True

# delete selected
bpy.ops.object.delete()

# Define mesh and object
m = bpy.data.meshes.new("normalTest")
obj = bpy.data.objects.new("normalTest", m)

# Set location and scene of object
obj.location = (-10, -10, 0)
bpy.context.scene.objects.link(obj)

# Create mesh from data
m.from_pydata(mesh.verts, [], mesh.faces)

# Calculate the edges
m.update(calc_edges=True)

verts = []
edges = []
for i, p in enumerate(loopCenter):
    j = i + 1
    h = i - 1
    if j >= len(loopCenter):
        j = 0

    # https://stackoverflow.com/questions/19350792/calculate-normal-of-a-single-triangle-in-3d-space
    p1 = loopAbove[h]
    p2 = loopAbove[j]
    p3 = loopBelow[i]

    # if we want normals to go away from center
    u = vector(p3, p1)
    v = vector(p2, p1)

    # if we want normals to go towards center
    # u = vector(p2, p1)
    # v = vector(p3, p1)

    n = crossproduct(u, v)

    # calculate distance bewteen point and normal
    # https://math.stackexchange.com/questions/105400/linear-interpolation-in-3-dimensions
    p0 = np.array(p)
    p1 = np.array(n)
    dist = p1 - p0
    ndist = np.linalg.norm(dist)
    targetLen = 5.0
    pd = p0 + (targetLen / ndist) * dist
    pd = tuple(pd)

    offset = len(verts)
    verts.append(p)
    verts.append(pd)
    edges.append((offset, offset+1))

# Define mesh and object
m = bpy.data.meshes.new("normals")
obj = bpy.data.objects.new("normals", m)

# Set location and scene of object
obj.location = (-10, -10, 0)
bpy.context.scene.objects.link(obj)

# Create mesh from data
m.from_pydata(verts, edges, [])

# Calculate the edges
m.update()
