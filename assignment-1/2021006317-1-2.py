import numpy as np

M = np.array([2+i for i in range(25)])
print(M)

M = M.reshape(5,5)
print(M)

for i in range(5):
    M[i][0] = 0
print(M)

M = M*M
print(M)

mv=0
for i in range(5):
    mv += M[0][i]
mv=np.sqrt(mv)
print(mv)