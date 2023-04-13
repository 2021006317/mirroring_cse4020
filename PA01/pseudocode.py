# for i in range (가로):
#     for j in range(세로):
#         vec_ij = viewpoint ~ image plane 위의 점 s on world frame
#         for sphere in spheres:
#             p = viewpoint, dir = unit(vec_ij - viewpoint, 즉 vector_ps) 인 ray 에 대해 만난다면 구 위의 점까지의 거리를 구한다.
#             리스트1에 담는다.
#         리스트1에서 최솟값을 찾고 걔의 구 idx를 찾는다. (pidx, pmin) -> pmin에 해당하는 구만 그 pixel ray 에서 보임.

#         for sphere in spheres:
#             p = lightposition, dir = unit(vec_ij - lightposition, 즉 vector_ls)인 ray에 대해 만난다면 구 위의 점까지의 거리를 구한다.
#             리스트2에 담는다.
#         리스트2에서 최솟값을 찾고 걔의 구 idx를 찾는다. (lidx, lmin)
        
#         if pidx == lidx:
#             내 눈에 보이고, 빛도 받음. shadow 는 없고, shading 은 함수가 알아서 해줌.
#             color = shading(intensity)
        
#         else:
#             내 눈에 보이는데 빛을 안받음 = shadow
#             color = black
    

# def shading_lamb(kd, I, n, l):
#     kd: 해당 구의 색(sphere->ref->shade)
#     I: intensity
#     n: unit(vec_ij - sphere_center)
#     l: unit(vec_ij - lightposition)

#     return kd*I 원소곱한 행렬 * max(0,np.dot(n,l))

