import numpy as np

print('A')
M = np.array([2+i for i in range(25)])
print(M)

print('B')
M = M.reshape(5,5)
print(M)

print('C')
for i in range(5):
    M[i][0] = 0
print(M)

print('D')
M = M*M
print(M)

print('E')
mv=0
for i in range(5):
    mv += M[0][i]
mv=np.sqrt(mv)
print(mv)