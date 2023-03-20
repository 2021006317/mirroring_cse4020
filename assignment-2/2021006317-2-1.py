import glfw
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np

def key_callback(window, key, scancode, action, mods):
    global PRESSED_KEY
    key_arr = [glfw.KEY_0, glfw.KEY_1, glfw.KEY_2, glfw.KEY_3, glfw.KEY_4, glfw.KEY_5, glfw.KEY_6, glfw.KEY_7, glfw.KEY_8, glfw.KEY_9]
    for i in range(10):
        if key == key_arr[i]:
            PRESSED_KEY = i
            break

def primitive_type(key):
    if key==1:      return GL_POINTS
    elif key==2:    return GL_LINES
    elif key==3:    return GL_LINE_STRIP
    elif key==4:    return GL_LINE_LOOP
    elif key==5:    return GL_TRIANGLES
    elif key==6:    return GL_TRIANGLE_STRIP
    elif key==7:    return GL_TRIANGLE_FAN
    elif key==8:    return GL_QUADS
    elif key==9:    return GL_QUAD_STRIP
    elif key==0:    return GL_POLYGON

def render(key):
    glClear(GL_COLOR_BUFFER_BIT) 
    glLoadIdentity()

    p_type = primitive_type(key)
    
    # draw cooridnate
    glBegin(p_type)
    glColor3f(1.0, 1.0, 1.0)
    coordinate = np.linspace(0,np.radians(360),13)
    for i in range(12):
        x=np.cos(coordinate[i])
        y=np.sin(coordinate[i])
        glVertex2fv([x,y])
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
        render(PRESSED_KEY)

        glfw.swap_buffers(window)
    glfw.terminate()

PRESSED_KEY = 4
if __name__ == "__main__":   
    main()