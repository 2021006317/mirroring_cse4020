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
        gamma = 2.2
        inverseGamma = 1.0 / gamma
        self.color=np.power(self.color, inverseGamma)

    def toUINT8(self):
        return (np.clip(self.color, 0, 1)*255).astype(np.uint8)

tree = ET.parse(sys.argv[1])
root = tree.getroot()

# set default values
viewPoint=np.array([0,0,0]).astype(np.float64)
viewDir=np.array([0,0,-1]).astype(np.float64) # direction toward object
viewUp=np.array([0,1,0]).astype(np.float64) # orientation of image
viewProjNormal=-1*viewDir  # you can safely assume this. (no examples will use shifted perspective camera) # projection plane 의 normal vector(negating has no effect. default, view direction 과 동일)
viewWidth=1.0 # dimensions of viewing window on the image plane
viewHeight=1.0 # "
projDistance=1.0 # d. image 사각형 ~ projection center distance. 근데? projection center 이 viewpoint 라고 하네요.

position=np.array([0,0,0]).astype(np.float64)
intensity=np.array([1,1,1]).astype(np.float64)  # how bright the light is.

exponent = 0

center = np.array([0,0,0]).astype(np.float64)
radius = 0
color = "blue"

# 방향 유닛 벡터
def unit_dir(dir):
        t = 1/np.sqrt(np.dot(dir,dir))
        udir = t*dir
        return udir

# diffusely reflected light
def lamb_shading(kd, I, n, l):
    m = max(0, np.dot(n,l))
    ldm = np.array([kd[0] * I[0], kd[1] * I[1], kd[2] * I[2]])
    ld = ldm*m
    # print(f'kd is {kd}')
    # print(f'ld is {ld}')
    return ld
    
# specularly reflected light
def phong_shading(ks, I, v, l, n):
    h = (v+l)/np.sqrt(np.dot(v+l,v+l))
    m = max(0,np.dot(n,h))**exponent
    ls = np.array([ks[0]*I[0], ks[1]*I[1], ks[2]*I[2]])*m
    return ls

def main():

    # parsing xml
    imgSize=np.array(root.findtext('image').split()).astype(np.int32) # 300 300
    print(f'imgsize is {imgSize}')
    
    for c in root.findall('camera'):
        viewPoint=np.array(c.findtext('viewPoint').split()).astype(np.float64)
        print(f'viewPoint is {viewPoint}')
        viewDir=np.array(c.findtext('viewDir').split()).astype(np.float64)
        print(f'viewDir is {viewDir}')
        projNormal=np.array(c.findtext('projNormal').split()).astype(np.float64)
        print(f'projNormal is {projNormal}')
        viewUp=np.array(c.findtext('viewUp').split()).astype(np.float64)
        print(f'viewUp is {viewUp}')
        viewWidth=np.array(c.findtext('viewWidth').split()).astype(np.float64)[0]
        print(f'viewWidth is {viewWidth}')
        viewHeight=np.array(c.findtext('viewHeight').split()).astype(np.float64)[0]
        print(f'viewHeight is {viewHeight}')
    print(f'projDistance is {projDistance}')

    shader = []
    for c in root.findall('shader'):
        diffuseColor_c=np.array(c.findtext('diffuseColor').split()).astype(np.float64)
        shader.append((c.get('name'), diffuseColor_c, c.get('type')))
        if c.get('type') == "Phong" :
            exponent = np.array(c.findtext('exponent').split()).astype(np.int32)[0]
    print(f'shader is {shader}')
    
    surface = []
    for c in root.findall('surface'):
        for s in c.findall('shader'):
            color = ''
            shade_typ = ''
            ref = s.get('ref')
            for shade in shader:
                if shade[0] == str(ref): # color name
                    color = shade[1] # color RGB
                    shade_typ = shade[2] # shader type
                    break
        center=np.array(c.findtext('center').split()).astype(np.float64)
        radius=np.array(c.findtext('radius').split()).astype(np.float64)[0]
        surface.append((color, center, radius, shade_typ)) # color RGB, center coord, radius length
    print(f'surface is {surface}')

    for c in root.findall('light'):
        position = np.array(c.findtext('position').split()).astype(np.float64)
        intensity = np.array(c.findtext('intensity').split()).astype(np.float64)
    print(f'light position is {position} and intensity is {intensity}')

    # camera frame
    vec_u = unit_dir(np.cross(viewDir, viewUp))
    vec_w = (-1)*unit_dir(viewDir)
    vec_v = unit_dir(np.cross(vec_w, vec_u))
    print(f'(u,v,w) is {(vec_u, vec_v, vec_w)}')

    # world frame through viewPoint e
    # u = l + (r-l)*(i+0.5)/n_x
    # v = b + (t-b)*(j+0.5)/n_y
    # 근데 우리 그림은 왼쪽 위가 (0,0)이니까 양수b-(t-b)...
    def vector_os(i, j):
        coord_u = (-1)*viewWidth/2 + viewWidth*(i+0.5)/imgSize[0]
        coord_v = viewHeight/2  - viewHeight*(j+0.5)/imgSize[1]
        s = viewPoint + coord_u*vec_u + coord_v*vec_v - projDistance*vec_w
        return s
    
    # |p+td-c|=radius
    # p+td = ray, c = sphere center 
    def intersect_distance(p, unit_d, sphere_center, sphere_radius):
        cp_point = p - sphere_center # OP - OC = CP
        discriminant = (np.dot(unit_d, cp_point))**2 - np.dot(cp_point,cp_point) + sphere_radius**2
        if discriminant >=0:
            t1 = (-1)*np.dot(unit_d, cp_point) - np.sqrt(discriminant)
            t2 = (-1)*np.dot(unit_d, cp_point) + np.sqrt(discriminant)
            if t1>=0:
                if t2>=0:
                    res = t1 if t1<=t2 else t2
                else:
                    res = t1
                return res
            elif t2>=0:
                return t2
            else:
                # 뒤에서 만남. 근데 이게 됨?
                return 99999999
        else:
            # 안 만남
            return 99999999

    def find_min(d_list):
        min = d_list[0]
        idx = 0

        for i in range(len(d_list)):
            if min > d_list[i]:
                min = d_list[i]
                idx = i
        return (idx, min)

    def shadow(light_p, unit_d, sphere_center, sphere_radius):
        lc_point = light_p - sphere_center
        discriminant = (np.dot(unit_d, lc_point))**2 - np.dot(lc_point,lc_point) + sphere_radius**2

        if discriminant >=0:
            t1 = -np.dot(unit_d, lc_point) - np.sqrt(discriminant)
            t2 = -np.dot(unit_d, lc_point) + np.sqrt(discriminant)
            if t1<0 and t2>=0: # intersected, not blocked -> not shadow
                return 0
            else: # not intersected || intersected but blocked -> shadow
                return 1
        else:
            return 1

    # var window = image plane 의 window center
    window = viewPoint + unit_dir(viewDir)
    print(f'window ray is {window}')

    # Create an empty image
    channels=3
    img = np.zeros((imgSize[1], imgSize[0], channels), dtype=np.uint8) # 0으로 된 3x300 행렬 300개를 담은 리스트
    img[:,:]=0

    # main rendering
    print(vector_os(0,0))
    for i in np.arange(imgSize[0]):
        for j in np.arange(imgSize[1]):
            img[j][i] = Color(0,0,0).toUINT8()
            vec_ij = vector_os(i,j)
            view_distance = []
            light_distance = []
            # surface = [(color, center, radius, shade_typ), (), ...]
            for sphere in surface:
                # 거리를 리스트에 넣는다.
                dir_ps = vec_ij - viewPoint
                vd = intersect_distance(viewPoint, unit_dir(dir_ps), sphere[1], sphere[2])
                view_distance.append(vd)
            # 최소 거리를 구한다.
            vidx, vmin = find_min(view_distance)

            prime_s = viewPoint + vmin*viewDir
            dir_ls = prime_s - position
            
            # 내눈에 보인다.
            if vmin!=99999999:
                sphere = surface[vidx]
                color = sphere[0]
                center = sphere[1]
                radius = sphere[2]
                typ = sphere[3]
                vec_cs = unit_dir(prime_s - center)
                vec_sl = unit_dir(position - prime_s)
                img[j][i] = Color(color[0], color[1], color[2]).toUINT8()

                # 빛이랑 닿는지 확인.
                ld = intersect_distance(position, unit_dir(dir_ls), center, radius)

                # 빛이랑 닿는다.
                if ld != 99999999:
                    is_shadow = shadow(position, unit_dir(dir_ls), center, radius)
                    if 1:
                        if typ == "Lambertian" :
                            clr = lamb_shading(color, intensity, unit_dir(prime_s + vec_cs), unit_dir(prime_s + vec_sl))
                            # print(f'clr is {clr}')
                            img[j][i] = Color(clr[0], clr[1], clr[2]).toUINT8()
                        elif typ == "Phong":
                            pass
                    else:
                        img[j][i] = Color(0,0,0).toUINT8()
                # view 최소거리 && light 최소거리 -> shading. type 확인후 알잘 함수. kd+ld
                
                # # 빛이랑 안닿음.
                # else:
                #     is_shadow = shadow(position, unit_dir(vec_sl), center, radius)
                #     if is_shadow == 1:
                #         img[j][i] = Color(0,0,0).toUINT8()

                '''
                # 빛이 닿음.
                if cnt!=0:
                    if vidx == lidx:
                        if typ == "Lambertian" :
                            clr = lamb_shading(color, intensity, unit_dir(vec_cs), unit_dir(vec_sl))
                            img[j][i] = Color(clr[0], clr[1], clr[2]).toUINT8()
                        elif typ == "Phong":
                            pass
                '''
                # view 최소거리 but light 최소x -> shadow 오. 오! -> 이게 빛이 안닿는데 내눈에 보이는거잖아
                

            # 내눈에 안보임.
            else:                
                img[j][i] = Color(0,0,0).toUINT8()

    # white = Color(1,1,1).toUINT8()
    # for i in range(300):
    #     img[0][i] = white

    rawimg = Image.fromarray(img, 'RGB')
    rawimg.save(sys.argv[1]+'.png')
    
if __name__=="__main__":
    main()
