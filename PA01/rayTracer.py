#!/usr/bin/env python3
# -*- coding: utf-8 -*
# sample_python aims to allow seamless integration with lua.
# see examples below

import os, sys, pdb, code
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

def ray(p,t,unit_d):
    return p + t*unit_d

# e: 카메라 평면의 중심 위치를 world에 상대적으로 표현한 것
# s: 카메라 평면 상의 점 위치를 world에 상대적으로 표현한 것
# u: 카메라 평면 right vector
# v: 카메라 평면 up vector
# w: 카메라 평면 normal vector

# dir 은 unit이든 말든 상관없음
def ray_sphere(point, dir, center, radius):
    # d*d t^2 + 2(p*d)t + p*p - r^2 = 0
    temp1 = np.dot(dir, dir)
    temp2 = np.dot(point, dir)
    temp3 = np.dot(point, point) - radius**2
    discriminant = temp2**2 - temp1*temp3
    if discriminant>=0:
        t1 = (-temp2 - np.sqrt(discriminant))/temp1
        t2 = (-temp2 + np.sqrt(discriminant))/temp1
    return(t1,t2)

# 방향 유닛 벡터
def unit_dir(dir):
        t = 1/np.sqrt(np.dot(dir,dir))
        udir = t*dir
        return udir

def ray(start, res_x, res_y, unit_u, unit_v, single_x, single_y):
        ray = start + unit_u*res_x*single_x + unit_v*res_y*single_y
        return ray #np.array

def find_min(list):
    min=list[0]
    idx=0
    for i in range(len(list)):
        if list[i] <= min:
            min = list[i]
            idx=i
    return (min,idx)

def raytrace(surface, ray, point):
    distance=np.array([])
    for k in surface:
        center = k.center
        radius = k.radius
        center_to_point = np.array([])
        for i in range(0,3):
            center_to_point = np.append(center_to_point, point[i]-center[i])
        t = ray_sphere(center_to_point, ray, center, radius)
        if t[0] >=0 : distance = np.append(distance, t[0])
        else: distance = np.append(distance, t[1])
    tup = find_min(distance)
    return tup

def shadow(point, s, light):
    pass
def shading_lamb():
    pass

def shading_phong():
    pass





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

    position=np.array([0,0,0]).astype(np.float64)   # light point
    intensity=np.array([1,1,1]).astype(np.float64)  # how bright the light is.

    center = []
    radius = []

    imgSize=np.array(root.findtext('image').split()).astype(np.int32) # 300 300
    print(f'imgsize is {imgSize}')
    
    # parsing xml
    for c in root.findall('camera'):
        viewPoint=np.array(c.findtext('viewPoint').split()).astype(np.float64)
        viewDir=np.array(c.findtext('viewDir').split()).astype(np.float64)
        projNormal=np.array(c.findtext('projNormal').split()).astype(np.float64)
        viewUp=np.array(c.findtext('viewUp').split()).astype(np.float64)
        viewWidth=np.array(c.findtext('viewWidth').split()).astype(np.float64)[0]
        viewHeight=np.array(c.findtext('viewHeight').split()).astype(np.float64)[0]
    
    shader = []
    for c in root.findall('shader'):
        diffuseColor_c=np.array(c.findtext('diffuseColor').split()).astype(np.float64)
        shader.append((c.get('name'), diffuseColor_c, c.get('type')))

    count=0
    for c in root.findall('surface'):
        center.append(np.array(c.findtext('center').split()).astype(np.float64))
        radius.append(np.array(c.findtext('radius').split()).astype(np.float64)[0])
        count+=1

    for c in root.findall('light'):
        position = np.array(c.findtext('position').split()).astype(np.float64)
        intensity = np.array(c.findtext('intensity').split()).astype(np.float64)

    w = unit_dir(projNormal)
    u = unit_dir(np.cross(w, viewUp))
    v = unit_dir(np.cross(w,u))
    
    # kd: 물체의 밝기, I: 빛의 밝기(색) , max(0, n'l): 면적당 받는 빛의 양(밝기)
    def shading(kd, I, n, l):
        m = max(0, np.dot(n,l))
        ldm = np.array([kd[0] * I[0], kd[1] * I[1], kd[2] * I[2]])
        ld = ldm*m
        return kd+ld

    # s : image window 상의 pixel의 world frame 상 좌표
    # ud, lr 은 단위벡터
    # e: window center
    # e + lr*(i-center_x) + viewUp*(center_y-j) - dw
    def vector_os(e, ud, lr, n, i, j):
        center_x = imgSize[0]/2
        center_y = imgSize[1]/2

        #! imgWidth, imgHeight
        s = e + lr*(i-center_x) + ud*(j-center_y) - 400 * n
        return s

    # single_x = single_pixel(viewWidth, imgSize[0])
    # single_y = single_pixel(viewHeight, imgSize[1])

    # Create an empty image
    channels=3
    img = np.zeros((imgSize[1], imgSize[0], channels), dtype=np.uint8) # 0으로 된 3x300 행렬 300개를 담은 리스트
    img[:,:]=0

    
    for i in np.arange(imgSize[0]): # 0~299
        for j in np.arange(imgSize[1]):
            ray = viewPoint
    # replace the code block below!
    # vector oe. e는 image plane (window) center
    window = viewPoint + unit_dir(viewDir)
    print(f'window ray is {window}')

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
        else:
            return 9999999999
        
    black=Color(0,0,0)
    for i in np.arange(imgSize[0]): # 0~299
        for j in np.arange(imgSize[1]):
                distance=[]
                img[j][i] = black.toUINT8()
                for k in range(count):
                    direction = np.array([])
                    dot = vector_os(window, up, right, n, i, j)
                    direction = dot - viewPoint
                    direction = unit_dir(direction)
                    intersect = intersection(viewPoint, direction, center[k], radius[k])
                    distance.append(intersect)
                intersect, clr = find_min(distance)
                if intersect != 9999999999:
                    
                    if shader[clr][2] == 'Lambertian':
                        distance_from_light=[]
                        # for kk in range(count):
                        vec_os = position + intersect*direction # 구 위의 교점 oc
                        vec_n = vec_os - center[clr] # 교점의 법선벡터 cs = os - oc
                        vec_l = vec_os - position # 빛 ~ 교점 sl = ol - os
                    #     intersect_to_light = intersection(position, vec_l, center[kk], radius[kk])
                    #     distance_from_light.append(intersect_to_light)
                    # intersect_to_light, cclr = find_min(distance_from_light)
                    # if intersect_to_light!=9999999999:
                    #     color = shading(np.array([shader[cclr][1][0], shader[cclr][1][1], shader[cclr][1][2]]), intensity, vec_n, vec_l)
                    # else:
                        color = shading(np.array([shader[clr][1][0], shader[clr][1][1], shader[clr][1][2]]), intensity, vec_n, vec_l)
                        img[j][i] = color
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
