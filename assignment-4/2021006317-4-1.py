import glfw
from OpenGL.GL import *
import numpy as np
from OpenGL.GLU import *

def render():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glEnable(GL_DEPTH_TEST)

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(-2,2, -2,2, -1,1)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    drawFrame()
    t = glfw.get_time()

    # blue base transformation
    glPushMatrix() # [O]
    glTranslatef(np.sin(t), 0, 0)

    # blue base drawing
    glPushMatrix() # [O, O + translate]
    glScalef(.2, .2, .2)
    glColor3ub(0, 0, 255)
    drawBox()
    drawFrame()
    glPopMatrix() # stack = [O], m = O+Tb

    # red arm transformation
    glPushMatrix() # stack = [O, O+Tb]
    glRotatef(t*(180/np.pi), 0, 0, 1) # m = O+Tb+Rr
    glTranslatef(.5, 0, .01) # m = O+Tb+Rr+Tr

    drawFrame()
    
    # red arm drawing
    glPushMatrix() # stack = [O, O+Tb, O+Tb+Rr+Tr]
    glScalef(.5, .1, .1)
    glColor3ub(255, 0, 0)
    drawBox()
    
    glPopMatrix() # stack = [O, O+Tb]

    # green arm transformation
    glPushMatrix() # stack = [O, O+Tb, O+Tb+Rr+Tr]
    glTranslatef(.5, 0, .01) # m = O+Tb+Rr+Tr+Tg+Rg
    glRotatef(t*(180/np.pi), 0, 0, 1) # m = O+Tb+Rr+Tr+Tg+Rg

    drawFrame()
    
    # green arm drawing
    glPushMatrix() # stack = [O, O+Tb, O+Tb+Rr+Tr, O+Tb+Rr+Tr+Tg+Rg]
    glScalef(.2, .2, .2)
    glColor3ub(0, 255, 0)
    
    drawBox()
    glPopMatrix()

    glPopMatrix()
    glPopMatrix()
    glPopMatrix()

def drawBox():
    glBegin(GL_QUADS)
    glVertex3fv(np.array([1,1,0.]))
    glVertex3fv(np.array([-1,1,0.]))
    glVertex3fv(np.array([-1,-1,0.]))
    glVertex3fv(np.array([1,-1,0.]))
    glEnd()

def drawFrame():
    # draw coordinate: x in red, y in green, z in blue
    glBegin(GL_LINES)
    # R
    glColor3ub(255, 0, 0)
    glVertex3fv(np.array([0.,0.,0.]))
    glVertex3fv(np.array([1.,0.,0.]))
    # G
    glColor3ub(0, 255, 0)
    glVertex3fv(np.array([0.,0.,0.]))
    glVertex3fv(np.array([0.,1.,0.]))
    # B
    glColor3ub(0, 0, 255)
    glVertex3fv(np.array([0.,0.,0]))
    glVertex3fv(np.array([0.,0.,1.]))
    glEnd()

def main():
    if not glfw.init():
        return
    window = glfw.create_window(480,480,'2021006317-4-1', None,None)
    if not window:
        glfw.terminate()
        return
    glfw.make_context_current(window)
    glfw.swap_interval(1)

    while not glfw.window_should_close(window):
        glfw.poll_events()
        render()
        glfw.swap_buffers(window)

    glfw.terminate()

if __name__ == "__main__":
    main()
