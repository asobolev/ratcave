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

fragshader = """
#version 330

uniform sampler2D TextureMap;
uniform float redLevel;

in vec2 texCoord;
out vec3 color;

void main( void ) {
    color = texture2D(TextureMap,texCoord).rgb;
    color.r = redLevel;
}
"""

sphere_fragshader = """
#version 330

//uniform float sides;
//uniform float phi;
uniform sampler2D TextureMap;

in vec2 texCoord;
out vec3 color;

const float pi = 3.14159265;

const float sides = 10;
const float i = 1.;
const float j = 2.;
const float phi = i * 2 * pi / sides;
const float phi2 = j * 2 * pi / sides;

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

    vec2 warp_coord1 = texCoord - 0.5;  // moving to center
    warp_coord1 /= 0.5;  // scaling (x&y)
    vec2 warp_coord1_temp = warp_coord1;
    warp_coord1.s = warp_coord1_temp.s * cos(phi2) - warp_coord1_temp.t * sin(phi2); // rotation
    warp_coord1.t = warp_coord1_temp.t * cos(phi2) + warp_coord1_temp.s * sin(phi2); // rotation
    warp_coord1.t -= 0.5;  // shift along y-axes
    warp_coord1.s = ((warp_coord1.s) / tan(pi/sides)) / (1 + warp_coord1.t * 2);  // warping (x-size, angle)
    warp_coord1 = warp_coord1 + 0.5;  // reverting 'moving to center' line

    // only apply a color to the pixel if warp_coord is inside the texture (0 <= warp_coord <= 1)
    if ( (warp_coord.s >= 0.0  && warp_coord.s <= 1.0) && (warp_coord.t >= 0.0 && warp_coord.t <= 1.0) ) {
    	color = texture2D(TextureMap, warp_coord).rgb;
    }
    else if ( (warp_coord1.s >= 0.0  && warp_coord1.s <= 1.0) && (warp_coord1.t >= 0.0 && warp_coord1.t <= 1.0) ) { 
    	color = texture2D(TextureMap, warp_coord1).rgb;
    } else {
        color.b = 1.;
    }

}
"""

texShader = rc.Shader(vertshader, sphere_fragshader)


# Build main 3D Scene
reader = rc.WavefrontReader(rc.resources.obj_primitives)
sphere = reader.get_mesh('Torus', position=(0, 1.2, -0.3), scale=.6)
sphere.rot_x = 90
sphere.texture =  rc.Texture.from_image(rc.resources.img_colorgrid)

monkey = reader.get_mesh('Sphere', position=(0,0,0), scale=.5)

angelmonkey = rc.mesh.EmptyMesh(position=(1, 0, -2))
angelmonkey.add_children([monkey, sphere])


scene = rc.Scene(meshes=[angelmonkey], bgColor=(0., 1., 0.))
monkey.add_children([sphere])
scene.camera.aspect = 5.

label1 = pyglet.text.Label('In FBO Texture', font_size=36,
						x=window.width//2, y=window.height//3,
						anchor_x='center', anchor_y='center')


# Build Secdon Scene (fullscreen quad overlay)
fbo = rc.FBO(rc.Texture())

quad = rc.resources.gen_fullscreen_quad()
quad.texture = fbo.texture
# quad.uniforms.append(rc.shader.Uniform('redLevel', 0.))
quad.uniforms.append(rc.shader.Uniform('sides', 32))
quad.uniforms.append(rc.shader.Uniform('phi', 0.))

sceneOverlay = rc.Scene(meshes=[quad])


label2 = pyglet.text.Label('Over FBO Texture', font_size=36,
						x=window.width//2, y=2*window.height//3,
						anchor_x='center', anchor_y='center')


@window.event
def on_resize(width, height):
	scene.camera.reset_aspect()
	label1.x, label1.y = width//2, height//3,
	label2.x, label2.y = width//2, 2*height//3,

tt = 0.
def update(dt):
	global tt
	tt += dt
	# print(dt)
	angelmonkey.rot_y += 20. * dt
	angelmonkey.rot_x += 30. * dt
	sphere.rot_y += 50. * dt
	scene.camera.z = math.sin(tt)
	# quad.uniforms[0].value[0] = .5 + .5 * math.sin(2 * tt)
pyglet.clock.schedule_interval(update, 1./60)

@window.event
def on_draw():
	window.clear()
	with fbo:
		scene.draw()
		label1.draw()
	sceneOverlay.draw(shader=texShader)
	label2.draw()
			

	# scene.draw()
	


pyglet.app.run()