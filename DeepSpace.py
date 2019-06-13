# Written by: Alex Francis (alexanderfrancis@live.ca)
# Program name: DeepSpace.py
# Description: a 2d n-body gravity simulator between different 'particles'
#
# Fixes needed:
#       particles flicker when a collision happens
#
# Ideas:
#       make colour proportional to heat/speed. something like that
#
#

# ______imports______
import pygame  # this is the base engine i'll be using
import sys  # need sys for sys.exit() # need random for randomness
import math
import random

# ______Inits______

# pygame inits
pygame.init()
clock = pygame.time.Clock()

# Display Constants
display_caption = "Deep Space"
screen_width, screen_height = 1280, 760
centerX = screen_width // 2  # center of screen for the x axis
centerY = screen_height // 2  # center of screen for the y axis
screen = pygame.display.set_mode((screen_width, screen_height))

# universe constants
pi = 3.14159

time = 0  # this is the amount of ticks

# ______Controls______

G = 40  # gravitational constant (higher values = more force between particles)
gravity_distance = 50  # ignores gravity between objects of distance greater than this
time_step = 60  # the clock.tick amount (fps)

# Randomized Particle Controls
randomize_particles = True
iterations = 200

random_pos = [[0, screen_width], [0, screen_height]]
random_mass = 3, 12
random_radius = random_mass
random_colour_R = 0, 255
random_colour_G = 0, 255
random_colour_B = 0, 0

background_colour_refill = True  # Boolean: controls if you want the background to refresh (tails or not)
background_colour = (0, 0, 0)

particle_shimmer = False
particle_warp = True
nonelastic_collision = True
elastic_collision = False
blackhole_absorb = False

particle_spawn = False  # Boolean: controls if you want particles to spawn
particle_spawn_rate = 3
particle_spawn_limit = 100

# ______Classes______

class Particle(object):
    # Particle Class inits
    init_pos = (centerX, centerY)
    init_colour = (255, 255, 255)
    init_radius = 8
    init_mass = 10

    def __init__(self, pos=(0, 0), velocity=(0, 0), acceleration=(0, 0), radius=init_radius, mass=init_mass,
                 colour=init_colour, id=0):
        self.rect = pygame.draw.circle(screen, colour, (pos[0], pos[1]), radius)
        self.pos = pos
        self.velocity = velocity
        self.acceleration = acceleration
        self.radius = abs(radius)  # just incase i use antiparticles (mass will be radius as well)
        self.mass = mass
        self.colour = colour
        self.id = id

    def draw(self):
        # circle(Surface, color, pos, radius, width=0) -> Rect
        pygame.draw.circle(screen, self.colour, (int(self.pos[0]), int(self.pos[1])), self.radius)

    def gravitation(self):
        gravitation = []
        average_x = 0
        average_y = 0

        for body in particles:
            if body.id != self.id:
                d = ((self.pos[0] - body.pos[0]) ** 2 + (self.pos[1] - body.pos[1]) ** 2) ** 0.5
                if d > gravity_distance:
                    continue  # ignores gravity from distance 150 away
                elif d < body.radius:
                    if nonelastic_collision:
                        self.collision(body)
                        return 0  # ends current function
                    elif elastic_collision:
                        self.elastic_collision(body)
                        return 0  # ends current function
                rhat = body.pos[0] - self.pos[0], body.pos[1] - self.pos[1]
                gravitation.append(
                    [G * self.mass * body.mass * rhat[0] / d ** 3, G * self.mass * body.mass * rhat[1] / d ** 3])

        for hole in holes:
            d = ((self.pos[0] - hole.pos[0]) ** 2 + (self.pos[1] - hole.pos[1]) ** 2) ** 0.5
            if d < hole.radius:  # lets hole go slightly into the other particle (prevents absorbtion looking effect)
                BlackHole.absorb(self)
                return 0  # ends current function
            rhat = hole.pos[0] - self.pos[0], hole.pos[1] - self.pos[1]
            gravitation.append(
                [G * self.mass * hole.mass * rhat[0] / d ** 3, G * self.mass * hole.mass * rhat[1] / d ** 3])

        for g in gravitation:
            average_x += g[0]
            average_y += g[1]

        average_x /= len(particles)
        average_y /= len(particles)
        self.acceleration = (average_x / self.mass, average_y / self.mass)

    # keeps particles on screen by wrapping position around the screen
    def warp(self):
        if particle_warp:
            if self.pos[0] < 0:
                self.pos = screen_width, self.pos[1]
            elif self.pos[0] > screen_width:
                self.pos = 0, self.pos[1]
            if self.pos[1] < 0:
                self.pos = self.pos[0], screen_height
            elif self.pos[1] > screen_height:
                self.pos = self.pos[0], 0

    # Collision Mechanics for particles
    def collision(self, body):
        # set position to whichever is bigger
        if self.radius < body.radius:
            self.pos = body.pos[0], body.pos[1]
        # self.pos = (body.pos[0] + self.pos[0]) / 2, (body.pos[1] + self.pos[1]) / 2  # average position between two

        # Calculate Net Force (x,y)
        f_net = self.mass * self.acceleration[0] + body.mass * body.acceleration[0], self.mass * self.acceleration[
            1] + body.mass * body.acceleration[1]

        # add masses together
        self.mass = self.mass + body.mass / 1.5

        self.velocity = self.acceleration[0] + body.acceleration[0], self.acceleration[1] + body.acceleration[1]

        # Set final acceleration
        self.acceleration = f_net[0] / self.mass, f_net[1] / self.mass

        # sets velocity to result of force

        # Calculate proper radii  - ((self.surface area + body.surface area) / pi) ** 0.5
        self.radius = math.floor(((pi * self.radius ** 2 + pi * body.radius ** 2) / pi) ** 0.5)

        # Calculate Colour (sums both then divides by 1.5 (keeps the colours a bit brighter)
        self.colour = int(min((self.colour[0] + body.colour[0]) / 1.5, 255)), int(
            min((self.colour[1] + body.colour[1]) / 1.5, 255)), int(min(
            (self.colour[2] + body.colour[2]) / 1.5, 255))

        # Debugging/Console Output
        # print('Collision! # Particles left:', len(particles))
        # print('Force = {} + {}'.format(round(self.mass * self.acceleration[0], 3),
        #                                round(body.mass * body.acceleration[0], 3)))
        # print('Final Acceleration: ({},{})'.format(round(f_net[0] / self.mass, 3), round(f_net[1] / self.mass, 3)))

        # and finally destroy the other particle
        particles.remove(body)

    def elastic_collision(self, body):
        pass

    def updateposition(self):
        self.warp()
        self.gravitation()
        self.velocity = (self.velocity[0] + self.acceleration[0], self.velocity[1] + self.acceleration[1])
        self.pos = (self.pos[0] + self.velocity[0], self.pos[1] + self.velocity[1])
        # self.rect.move_ip(self.velocity[0], self.velocity[1])
        self.rect.move(self.pos[0], self.pos[1])


class BlackHole(object):
    init_pos = (centerX, centerY)
    init_colour = (0, 0, 0)
    Black_init_radius = 15
    init_mass = 25

    def __init__(self, pos=(0, 0), radius=Black_init_radius, mass=init_mass, colour=init_colour):
        self.rect = pygame.draw.circle(screen, colour, (pos[0], pos[1]), radius)
        self.pos = pos
        self.radius = radius
        self.mass = mass
        self.colour = colour

    def draw(self):
        pygame.draw.circle(screen, self.colour, (int(self.pos[0]), int(self.pos[1])), self.radius)

    def absorb(self):
        if blackhole_absorb:
            for p in particles:
                if ((p.pos[0] - self.pos[0]) ** 2 + (p.pos[1] - self.pos[1]) ** 2) ** 0.5 < int(self.radius):
                    particles.remove(p)
                    print('BlackHole absorbed Particle #', p.id)


# ______List of Particles______

# particle1 = Particle(pos=(centerX-100, centerY),mass=4, colour=(255, 0, 0),id = 0)
# particle2 = Particle(pos=(centerX+100, centerY),mass=20, id = 1)
# particle3 = Particle(pos=(centerX, centerY-200),mass = 4, colour=(0,255,0),id = 2)
# particle4 = Particle(pos=(centerX-200, centerY-100), colour=(0,128,255))
# particle5 = Particle(pos=(centerX-300, centerY-300), colour=(255,128,0))
#
# particles = [particle1, particle2,particle3] # list of particles

# List of BlackHoles
hole1 = BlackHole(pos=(centerX, centerY))
holes = []

# ______Random particle generator______

# unique id tag (for testing if self in particles[] list
identification = 0
particles = []
if randomize_particles:

    for i in range(0, iterations):
        # print(identification)
        particle_mass = random.randint(random_mass[0], random_mass[1])
        particles.append(Particle(pos=(random.randint(random_pos[0][0], random_pos[0][1]),
                                       random.randint(random_pos[1][0], random_pos[1][1])),
                                  colour=(random.randint(random_colour_R[0], random_colour_R[1]),
                                          random.randint(random_colour_G[0], random_colour_G[1]),
                                          random.randint(random_colour_B[0], random_colour_B[1])),
                                  mass=particle_mass, radius=particle_mass, id=identification))
        identification += 1  # generates a unique id for each particle

# ______Main Loop______

print('DeepSpace Initiated')
screen.fill(background_colour)

while True:

    # Exit Function
    key = pygame.key.get_pressed()
    for event in pygame.event.get():
        if event.type == pygame.QUIT: pygame.quit(); sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE: pygame.quit(); sys.exit()

    # Fill Background
    if background_colour_refill:
        screen.fill(background_colour)

    # Update Particles and BlackHoles

    if particle_spawn and (time % particle_spawn_rate) == 0 and len(particles) < 200:
        identification += 1
        particle_mass = random.randint(random_mass[0], random_mass[1])
        particles.append(Particle(pos=(random.randint(random_pos[0][0], random_pos[0][1]),
                                       random.randint(random_pos[1][0], random_pos[1][1])),
                                  colour=(random.randint(random_colour_R[0], random_colour_R[1]),
                                          random.randint(random_colour_G[0], random_colour_G[1]),
                                          random.randint(random_colour_B[0], random_colour_B[1])),
                                  mass=particle_mass, radius=particle_mass, id=identification))

    # iterate through all particles
    for particle in particles:
        particle.updateposition()
        particle.draw()
        # slowly changes hue of particles
        if particle_shimmer:
            if particle.colour[2] > 250:
                i = -1
            elif particle.colour[2] < 5:
                i = 1
            particle.colour = (particle.colour[0], 0, (particle.colour[2] + i) % 255)

    for hole in holes:
        hole.draw()

    # Update Screen and Display Captions
    pygame.display.flip()
    pygame.display.set_caption(
        '{} | FPS: {} | Time: {} || Particles: {}'.format(display_caption, round(clock.get_fps(), 3), time,
                                                          len(particles)))
    # Update Clock
    clock.tick(time_step)
    time += 1
