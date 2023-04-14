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

def main():

    # set default values
    ## camera
    viewPoint=np.array([0,0,0]).astype(np.float64)
    viewDir=np.array([0,0,-1]).astype(np.float64)
    viewUp=np.array([0,1,0]).astype(np.float64)
    viewProjNormal=-1*viewDir
    viewWidth=1.0
    viewHeight=1.0
    projDistance=1.0
    ## light
    light_position=np.array([0,0,0]).astype(np.float64)
    intensity=np.array([1,1,1]).astype(np.float64)  # how bright the light is.
    ## shading
    specularColor = 0
    exponent = 0
    ## spehre
    center = np.array([0,0,0]).astype(np.float64)
    radius = 0
    d_color = "blue"

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
        if c.findtext('projDistance') is not None:
            projDistance = np.array(c.findtext('projDistance').split()).astype(np.float64)[0]
    print(f'projDistance is {projDistance}')

    shader = []
    for c in root.findall('shader'):
        diffuseColor_c=np.array(c.findtext('diffuseColor').split()).astype(np.float64)
        if c.get('type') == "Lambertian" :
            shader.append((c.get('name'), diffuseColor_c, c.get('type')))
        elif c.get('type') == "Phong" :
            exponent = np.array(c.findtext('exponent').split()).astype(np.int32)[0]
            specularColor = np.array(c.findtext('specularColor').split()).astype(np.float64)
            shader.append((c.get('name'), diffuseColor_c, c.get('type'), specularColor, exponent))
    print(f'shader is {shader}')
    
    surface = []
    for c in root.findall('surface'):
        for s in c.findall('shader'):
            d_color = ''
            shade_typ = ''
            sp_color = ''
            ref = s.get('ref')
            for shade in shader:
                if len(shade) == 5: # Phong shader
                    sp_color = shade[3]
                if shade[0] == str(ref): # color name
                    d_color = shade[1] # diffuse color
                    shade_typ = shade[2] # shader type
                    break
        center=np.array(c.findtext('center').split()).astype(np.float64)
        radius=np.array(c.findtext('radius').split()).astype(np.float64)[0]
        if shade_typ == "Lambertian":
            surface.append((d_color, center, radius, shade_typ)) # color RGB, center coord, radius length
        elif shade_typ == "Phong":
            surface.append((d_color, center, radius, shade_typ, sp_color))
    print(f'surface is {surface}')

    for c in root.findall('light'):
        light_position = np.array(c.findtext('position').split()).astype(np.float64)
        intensity = np.array(c.findtext('intensity').split()).astype(np.float64)
    print(f'light_position is {light_position} and intensity is {intensity}')

    # 방향 유닛 벡터
    def unit_dir(dir):
        t = 1/np.sqrt(np.dot(dir,dir))
        udir = t*dir
        return udir

    # lambertian shading
    def lamb_shading(kd, I, n, l):
        m = max(0, np.dot(n,l))
        ldm = np.array([kd[0] * I[0], kd[1] * I[1], kd[2] * I[2]])
        ld = ldm*m
        return ld
        
    # blinn_phong shading
    def phong_shading(ks, I, v, l, n):
        h = (v+l)/np.sqrt(np.dot(v+l,v+l))
        m = max(0,np.dot(n,h))**exponent
        ls = np.array([ks[0]*I[0], ks[1]*I[1], ks[2]*I[2]])*m
        return ls

    # camera frame coordination
    vec_u = unit_dir(np.cross(viewDir, viewUp))
    vec_w = (-1)*unit_dir(viewDir)
    vec_v = unit_dir(np.cross(vec_w, vec_u))
    print(f'(u,v,w) is {(vec_u, vec_v, vec_w)}')

    # world frame coordination through viewPoint p on image plane
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
                return 99999999
        else:
            return 99999999

    def find_min(d_list):
        min = d_list[0]
        idx = 0

        for i in range(len(d_list)):
            if min > d_list[i]:
                min = d_list[i]
                idx = i
        return (idx, min)

    # var window = image plane 의 window center
    window = viewPoint + unit_dir(viewDir)
    print(f'window ray is {window}')

    # Create an empty image
    channels=3
    img = np.zeros((imgSize[1], imgSize[0], channels), dtype=np.uint8)
    img[:,:]=0

    # main rendering
    for i in np.arange(imgSize[0]):
        for j in np.arange(imgSize[1]):
            img[j][i] = Color(0,0,0).toUINT8()
            vec_ij = vector_os(i,j)
            view_distance = []
            light_distance = []

            # 눈에 보이는 도형 찾기
            for sphere in surface:
                dir_ps = unit_dir(vec_ij - viewPoint) # OS - OP = PS
                vd = intersect_distance(viewPoint, dir_ps, sphere[1], sphere[2])
                view_distance.append(vd)
            vidx, vmin = find_min(view_distance)

            # 빛 받는 도형 찾기
            for sphere in surface:
                vec_ot = viewPoint + vmin*dir_ps # image plane 너머의 공간 상의 점
                dir_lt = unit_dir(vec_ot - light_position) # OT - OL = LT
                ld = intersect_distance(light_position, dir_lt, sphere[1], sphere[2])
                light_distance.append(ld)
            lidx, lmin = find_min(light_distance)
                
            # 보이는 구가 없는 경우
            if vmin == 99999999:
                img[j][i] = Color(0,0,0).toUINT8()
            
            # 보이는 구가 있는 경우
            else:
                sphere = surface[vidx]
                d_color = sphere[0] # diffuse coefficient
                center = sphere[1]
                radius = sphere[2]
                typ = sphere[3]
                dir_ct = unit_dir(vec_ot - center)
                dir_tl = unit_dir(light_position - vec_ot)

                # 보이는 구가 빛을 받는 경우
                if vidx == lidx:
                    if typ == "Lambertian" :
                        clr = lamb_shading(d_color, intensity, dir_ct, dir_tl)
                    elif typ == "Phong":
                        dir_tp = unit_dir(viewPoint - vec_ot) # OP - OT
                        sp_color = sphere[4] # specular coefficient
                        l_clr = lamb_shading(d_color, intensity, dir_ct, dir_tl)
                        p_clr = phong_shading(sp_color, intensity, dir_tp, dir_tl, dir_ct)
                        clr = p_clr + l_clr
                    gam_color = Color(clr[0], clr[1], clr[2])
                    gam_color.gammaCorrect(2.2)
                    img[j][i] = gam_color.toUINT8()
                
                # 보이는 구가 빛을 받지 못하는 경우
                elif vidx != lidx:
                    img[j][i] = Color(0,0,0).toUINT8()

    rawimg = Image.fromarray(img, 'RGB')
    rawimg.save(sys.argv[1]+'.png')
    
if __name__=="__main__":
    main()
