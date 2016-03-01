import pyglet
import ratcave as rc
import math


window = pyglet.window.Window(resizable=True, fullscreen=False)

vertshader = """
#version 330
layout(location = 0) in vec3 vertexPosition;
layout(location = 2) in vec2 uvTexturePosition;

out vec2 texCoord;

void main()
  {
	//Calculate Vertex Position on Screen
	gl_Position = vec4(vertexPosition, 1.0);
	texCoord = uvTexturePosition;
  }
"""

sphere_fragshader = """
#version 330

//uniform float sides;
uniform float phi;
uniform sampler2D TextureMap;

in vec2 texCoord;
out vec4 color;

const float pi = 3.14159265;

const float sides = 10;
const float i = 1.;
//const float phi = i * 2 * pi / sides;

void main()
{
	
	
    /**************************************/
    /****CALCULATIONS: REVERSE ORDER!!!****/
    /**************************************/
    vec2 warp_coord = texCoord - 0.5;  // moving to center
    warp_coord /= 0.5;  // scaling (x&y)
    vec2 warp_coord_temp = warp_coord;
    warp_coord.s = warp_coord_temp.s * cos(phi) - warp_coord_temp.t * sin(phi); // rotation
    warp_coord.t = warp_coord_temp.t * cos(phi) + warp_coord_temp.s * sin(phi); // rotation
    warp_coord.t -= 0.5;  // shift along y-axes
    warp_coord.s = ((warp_coord.s) / tan(pi/sides)) / (1 + warp_coord.t * 2);  // warping (x-size, angle)
    warp_coord = warp_coord + 0.5;  // reverting 'moving to center' line

    // only apply a color to the pixel if warp_coord is inside the texture (0 <= warp_coord <= 1)
    if ( (warp_coord.s >= 0.0  && warp_coord.s <= 1.0) && (warp_coord.t >= 0.0 && warp_coord.t <= 1.0) ) {
    	color.rgb = texture2D(TextureMap, warp_coord).rgb;
    	color.a = 1.;
    } else {
        discard;
    }

}
"""

texShader = rc.Shader(vertshader, sphere_fragshader)


# Build main 3D Scene
reader = rc.WavefrontReader(rc.resources.obj_primitives)
sphere = reader.get_mesh('Plane', position=(0, 1.2, -0.3), scale=.6)
sphere.rot_x = 90
sphere.texture =  rc.Texture.from_image(rc.resources.img_colorgrid)

monkey = reader.get_mesh('Sphere', position=(0,0,0), scale=.5)
monkey.add_children([sphere])

angelmonkey = rc.mesh.EmptyMesh(position=(1, 0, -2))
angelmonkey.add_children([monkey])

scene = rc.Scene(meshes=[angelmonkey], bgColor=(0., 1., 0.))


# Build Secdon Scene (fullscreen quad overlay)
fbo = rc.FBO(rc.Texture())

quad = rc.resources.gen_fullscreen_quad()
quad.texture = fbo.texture
quad.uniforms.append(rc.shader.Uniform('sides', 32))
quad.uniforms.append(rc.shader.Uniform('phi', 0.))

sceneOverlay = rc.Scene(meshes=[quad])


tt = 0.
def update(dt):
	global tt
	tt += dt
	angelmonkey.rot_y += 20. * dt
	angelmonkey.rot_x += -50. * dt
	sphere.rot_y += 50. * dt
	scene.camera.z = math.sin(tt)
pyglet.clock.schedule_interval(update, 1./60)


quad.uniforms.append(rc.shader.Uniform('phi', 0.9))
@window.event
def on_draw():
	window.clear()
	sceneOverlay.clear()
	for camrot in [0., .63, 1.2, 3.]:
		scene.camera.rot_y = camrot * 180. / math.pi 
		with fbo:
			scene.draw(autoclear=True)
			quad.uniforms[-1].value[0] = camrot  # Phi
		sceneOverlay.draw(shader=texShader, autoclear=False)
	


pyglet.app.run()