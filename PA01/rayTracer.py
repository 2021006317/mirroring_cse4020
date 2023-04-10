#!/usr/bin/env python3
# -*- coding: utf-8 -*
# sample_python aims to allow seamless integration with lua.
# see examples below

import os
import sys
import pdb  # use pdb.set_trace() for debugging
import code # or use code.interact(local=dict(globals(), **locals()))  for debugging.
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image

class Color:
    def __init__(self, R, G, B):
        self.color=np.array([R,G,B]).astype(np.float64)

    # Gamma corrects this color.
    # @param gamma the gamma value to use (2.2 is generally used).
    def gammaCorrect(self, gamma):
        inverseGamma = 1.0 / gamma
        self.color=np.power(self.color, inverseGamma)

    def toUINT8(self):
        return (np.clip(self.color, 0, 1)*255).astype(np.uint8)

def main():

    tree = ET.parse(sys.argv[1])
    root = tree.getroot()

    # set default values
    viewPoint=np.array([0,0,0]).astype(np.float64)
    viewDir=np.array([0,0,-1]).astype(np.float64) # direction toward object
    viewUp=np.array([0,1,0]).astype(np.float64) # orientation of image
    viewProjNormal=-1*viewDir  # you can safely assume this. (no examples will use shifted perspective camera) # projection plane 의 normal vector(negating has no effect. default, view direction 과 동일)
    viewWidth=1.0 # dimensions of viewing window on the image plane
    viewHeight=1.0 # ""
    projDistance=1.0 # d. image 사각형 ~ projection center distance. 근데? projection center 이 viewpoint 라고 하네요.
    intensity=np.array([1,1,1]).astype(np.float64)  # how bright the light is.
        
    center = []
    radius = []
    imgSize=np.array(root.findtext('image').split()).astype(np.int32) # 300 300
    print(f'imgsize is {imgSize}')
    
    # parsing xml
    for c in root.findall('camera'):
        viewPoint=np.array(c.findtext('viewPoint').split()).astype(np.float64)
        print('viewpoint', viewPoint)
        viewDir=np.array(c.findtext('viewDir').split()).astype(np.float64)
        print('viewDir', viewDir)
        projNormal=np.array(c.findtext('projNormal').split()).astype(np.float64)
        print('projNormal', projNormal)
        viewUp=np.array(c.findtext('viewUp').split()).astype(np.float64)
        print('viewUp', viewUp)
        viewWidth=np.array(c.findtext('viewWidth').split()).astype(np.float64)
        print('viewWidth', viewWidth)
        viewHeight=np.array(c.findtext('viewHeight').split()).astype(np.float64)
        print('viewHeight', viewHeight)
    
    shader = []
    for c in root.findall('shader'):
        diffuseColor_c=np.array(c.findtext('diffuseColor').split()).astype(np.float64)
        shader.append((c.get('name'), diffuseColor_c))
        print('name', c.get('name'))
        print('diffuseColor', diffuseColor_c)
    print('shaders are', shader)
    print(shader[0][1])
    print(type(shader[0][1]))

    count=0
    for c in root.findall('surface'):
        center.append(np.array(c.findtext('center').split()).astype(np.float64))
        radius.append(np.array(c.findtext('radius').split()).astype(np.float64)[0])
        
        print('center', center)
        print('radius', radius)
        count+=1

    for c in root.findall('light'):
        position = np.array(c.findtext('position').split()).astype(np.float64)
        intensity = np.array(c.findtext('intensity').split()).astype(np.float64)

    # print('surfaces are', surface)

    # 방향 유닛 벡터
    def unit_dir(dir):
        t = 1/np.sqrt(np.dot(dir,dir))
        udir = t*dir
        return udir
    
    right = unit_dir(np.cross(viewDir, viewUp))
    up = unit_dir(np.cross(viewDir,right))
    n = unit_dir(projNormal)

    # s : image window 상의 pixel의 world frame 상 좌표
    # ud, lr 은 단위벡터
    # e + lr*(i-center_x) + viewUp*(center_y-j) - dw
    def vector_os(e, ud, lr, n, i, j):
        center_x = imgSize[0]/2
        center_y = imgSize[1]/2
        #! imgWidth, imgHeight
        s = e + lr*(i-center_x) + ud*(j-center_y) - 400*n
        return s
    
    # Create an empty image
    channels=3
    img = np.zeros((imgSize[1], imgSize[0], channels), dtype=np.uint8) # 0으로 된 3x300 행렬 300개를 담은 리스트
    img[:,:]=0

    # ray-sphere intersection on world frame
    
    # |p+td-c|=radius
    def intersection(start_point, unit_d, sphere_center, sphere_radius):
        center_to_point = np.array([])
        for i in range(0,channels):
            center_to_point = np.append(center_to_point, start_point[i] - sphere_center[i])
        temp1=np.dot(unit_d, unit_d)
        temp2=np.dot(unit_d, center_to_point)
        temp3=np.dot(center_to_point, center_to_point)-sphere_radius**2
        discriminant = temp2**2 - temp1*temp3 # D/4 = b'^2 - ac
        
        if  discriminant >= 0:
            quadratic_min = (-temp2 - np.sqrt(discriminant)) /temp1
            quadratic_max = (-temp2 + np.sqrt(discriminant)) /temp1
            if quadratic_min>=0:
                return quadratic_min
            elif quadratic_max>=0:
                return quadratic_max
        else:
            return 9999999999
    
    def find_min(list):
        min=list[0]
        idx=0
        for i in range(len(list)):
            if list[i] <= min:
                min = list[i]
                idx=i
        return (min,idx)
    
    # kd: 물체의 색, I: 빛의 밝기(색) , max(0, n'l): 면적당 받는 빛의 양(밝기)
    def shading(kd, I, n, l):
        m = max(0, np.dot(n,l))
        ldm = np.dot(kd, I)
        ld = ldm*m
        return ld
    
    # replace the code block below!
    # vector oe. e는 image plane (window) center
    window = viewPoint + unit_dir(viewDir)
    print(f'window ray is {window}')

    for i in np.arange(imgSize[0]): # 0~299
        for j in np.arange(imgSize[1]):
                distance=[]
                for k in range(count):
                    #print((i,j))
                    black=Color(0,0,0)
                    img[j][i] = black.toUINT8()
                    direction = np.array([])
                    direction = vector_os(window, up, right, n, i, j) - viewPoint
                    direction = unit_dir(direction)
                    intersect = intersection(viewPoint, direction, center[k], radius[k]) #k
                    distance.append(intersect)
                # print(distance)
                clr = find_min(distance)[1]
                # print(clr)
                if intersect != 9999999999:
                    img[j][i] = Color(shader[clr][1][0], shader[clr][1][1], shader[clr][1][2]).toUINT8()
                        # print(img[j][i])
                # if cnt == 3:
                #     print('y')

    # for i in np.arange(count):
    #     ld = 
    # for x in np.arange(imgSize[0]):
    #     img[5][x]=[255,255,255]

    rawimg = Image.fromarray(img, 'RGB')
    #rawimg.save('out.png')
    rawimg.save(sys.argv[1]+'.png')
    
if __name__=="__main__":
    main()
