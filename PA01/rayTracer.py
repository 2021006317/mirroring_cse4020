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
        return (np.clip(self.color, 0,1)*255).astype(np.uint8)

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
    print(np.cross(viewDir, viewUp))
    center = np.array([0,0,0]).astype(np.float64)
    radius = 1
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


    for c in root.findall('shader'):
        diffuseColor_c=np.array(c.findtext('diffuseColor').split()).astype(np.float64)
        print('name', c.get('name'))
        print('diffuseColor', diffuseColor_c)

    for c in root.findall('surface'):
        center = np.array(c.findtext('center').split()).astype(np.float64)
        radius = np.array(c.findtext('radius').split()).astype(np.float64)
        
    #code.interact(local=dict(globals(), **locals()))
    
    # 방향 유닛 벡터
    def unit_dir(dir):
        t = np.sqrt(np.dot(dir,dir))
        return t*dir
    
    # 길이=size 인 OE 벡터. e는 image plane 위의 점
    def ray(start_point, dir, size):
        a = np.dot(dir, dir)
        b = np.dot(start_point, dir)
        c = np.dot(start_point ,start_point) - size*size
        t = (-b + np.sqrt(b*b-a*c))/a
        return start_point + t*dir
    
    # s : image window 상의 pixel의 world frame 상 좌표
    def vector_os(e, i, j):
        # e = [a,b,c] : r(t)... vector_oe
        # i,j : img[i][j]
        center_x = imgSize[0]/2
        center_y = imgSize[1]/2
        s = e + [i-center_x, center_y-j, 0]
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
        discriminant = temp1**2 - temp1*temp3 # D/4 = b'^2 - ac
        if  discriminant >= 0:
            return True
        else:
            return False
    
    # replace the code block below!
    # var window is (0,0) left, right 상단 on image plane window
    window = ray(viewPoint, viewDir, 1)
    print(f'window ray is {window}')
    for i in np.arange(imgSize[0]): # 0~299
        for j in np.arange(imgSize[1]):
            white=Color(1,1,1)
            red=Color(1,0,0)
            blue=Color(0,0,1)
            img[i][j] = blue.toUINT8()
            direction = np.array([])
            direction = vector_os(window, i, j) - viewPoint
            direction = unit_dir(direction)
            intersect = intersection(viewPoint, direction, center, radius)
            if intersect == True:
                img[i][j] = white.toUINT8()

    # for x in np.arange(imgSize[0]): 
    #     img[5][x]=[255,255,255]

    rawimg = Image.fromarray(img, 'RGB')
    #rawimg.save('out.png')
    rawimg.save(sys.argv[1]+'.png')
    
if __name__=="__main__":
    main()
