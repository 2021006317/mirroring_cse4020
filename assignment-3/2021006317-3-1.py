import glfw
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np

def key_callback(window, key, scancode, action, mods):
    global M
    if action == glfw.PRESS:
        if key == glfw.KEY_Q:
            T = np.array([[1.,0., -.1],
                        [0.,1.,0.],
                        [0.,0.,1.]])
            M=T@M
        elif key == glfw.KEY_E:
            T = np.array([[1.,0., .1],
                        [0.,1.,0.],
                        [0.,0.,1.]])
            M=T@M
        elif key == glfw.KEY_A:
            th = np.radians(10)
            R = np.array([[np.cos(th),-np.sin(th), 0.],
                        [np.sin(th), np.cos(th),0.],
                        [0.,0.,1.]])
            M=M@R
        elif key == glfw.KEY_D:
            th = np.radians(10)
            R = np.array([[np.cos(th), np.sin(th), 0.],
                        [-np.sin(th), np.cos(th),0.],
                        [0.,0.,1.]])
            M=M@R
        elif key == glfw.KEY_1:
            T = np.array([[1.,0.,0.],
                        [0.,1.,0.],
                        [0.,0.,1.]])
            M=T
        elif key == glfw.KEY_W:
            S = np.array([[.9,0.,0.],
                        [0.,1.,0.],
                        [0.,0.,1]])
            M=S@M
        elif key == glfw.KEY_S:
            th = np.radians(10)
            R = np.array([[np.cos(th),-np.sin(th), 0.],
                        [np.sin(th), np.cos(th),0.],
                        [0.,0.,1.]])
            M=R@M
    
def render(T):
    glClear(GL_COLOR_BUFFER_BIT)
    glLoadIdentity()

    # draw cooridnate
    glBegin(GL_LINES)
    glColor3ub(255, 0, 0)
    glVertex2fv(np.array([0.,0.]))
    glVertex2fv(np.array([1.,0.]))
    glColor3ub(0, 255, 0)
    glVertex2fv(np.array([0.,0.]))
    glVertex2fv(np.array([0.,1.]))
    glEnd()

    # draw triangle
    glBegin(GL_TRIANGLES)
    glColor3ub(255, 255, 255)
    glVertex2fv( (T @ np.array([.0,.5,1.]))[:-1] )
    glVertex2fv( (T @ np.array([.0,.0,1.]))[:-1] )
    glVertex2fv( (T @ np.array([.5,.0,1.]))[:-1] )
    glEnd()

def main():
    if not glfw.init():
        return
    
    window = glfw.create_window(480,480,"2021006317", None, None)
    if not window:
        glfw.terminate()
        return
    
    glfw.set_key_callback(window, key_callback)
    glfw.make_context_current(window)
    glfw.swap_interval(1)

    while not glfw.window_should_close(window):
        glfw.poll_events()
        render(M)

        glfw.swap_buffers(window)
    glfw.terminate()

M = np.array([[1.,0.,0.],
            [0.,1.,0.],
            [0.,0.,1.]])
if __name__ == "__main__":
    main()