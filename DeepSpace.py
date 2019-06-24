# Written by: Alex Francis (alexanderfrancis@live.ca)
# Program name: DeepSpace.py
# Description: a 2d n-body gravity simulator between different 'particles' in space
#
# Fixes needed:
#       particles flicker when a collision happens
#       Collision physics a bit off (this is because the acceleration of each particle is calculated serialy, which
#       means that for 2 particles that should collide with net zero force - instead one acceleration is calculated
#       before the other
#
# Ideas:
#       make colour proportional to heat/speed. something like that
#       integrate mouse control: maybe drag the particles around or something
#       MULTIPROCESSING
#
#
# KEYBINDS:
# Escape: Exit
# Space: Pause
# r: reset simulation
# s: enable/disable particle spawning
# minus/equals: increase/decrease particle spawn rate
# b: enable particle trails
# h: enable/disable black hole list
# w: enable/disable particle-mouse interaction
# g: reverse gravity
# up arrow/down arrow: increase/decrease gravity
# left arrow/right arrow: change in gravity step up/down
# left bracket/right bracket: increase/decrease particle mass and radius


# ______imports______
import pygame  # this is the graphics engine i'll be using
import sys  # need sys for sys.exit() # need random for randomness
from math import floor
import random  # for random particle inits

# ______Inits______

# pygame inits
pygame.init()
clock = pygame.time.Clock()

# Display Constants
display_caption = "Deep Space"
screen_width, screen_height = 800,600
centerX = screen_width // 2  # center of screen for the x axis
centerY = screen_height // 2  # center of screen for the y axis
screen = pygame.display.set_mode((screen_width, screen_height))

# universe constants
pi = 3.14159

time = 0  # this is the amount of ticks

# ______Controls______

G = 100  # gravitational constant (higher values = more force between particles)
ds = 10  # step for changing variables
gravity_distance = 500  # ignores gravity between objects of distance greater than this
time_step = 120  # the clock.tick amount (fps)
update = True  # If false simulation is paused

# Randomized Particle Controls
randomize_particles = True
iterations = 5

random_pos = [[0, screen_width], [0, screen_height]]
random_mass = 3, 12
random_radius = random_mass
random_colour_R = 50, 255
random_colour_G = 0, 0
random_colour_B = 0, 0

background_colour_refill = True  # Boolean: controls if you want the background to refresh (tails or not)
background_colour = (20, 20, 20)

particle_shimmer = True
shimmer_speed = 3

particle_warp = False
particle_bounce = True
nonelastic_collision = True
elastic_collision = False
blackhole_absorb = True

particle_spawn = False  # Boolean: controls if you want particles to spawn
particle_spawn_rate = 5
particle_spawn_limit = 1000


# ______Classes______


class Particle(object):
    # Particle Class inits
    init_pos = (centerX, centerY)
    init_colour = (255, 255, 255)
    init_radius = 8
    init_mass = 10

    def __init__(self, pos=(0, 0), velocity=(0, 0), acceleration=(0, 0), radius=init_radius, mass=init_mass,
                 colour=init_colour):
        self.rect = pygame.draw.circle(screen, colour, (pos[0], pos[1]), radius)
        self.pos = pos
        self.velocity = velocity
        self.acceleration = acceleration
        self.radius = radius  # just in case i use antiparticles (mass will be radius as well)
        self.mass = mass
        self.colour = colour
        rectlist.append(self.rect)

    def __del__(self):
        rectlist.remove(self.rect)

    def draw(self):
        # circle(Surface, color, pos, radius, width=0) -> Rect
        pygame.draw.circle(screen, self.colour, (int(self.pos[0]), int(self.pos[1])), self.radius)

    def gravitation(self):
        gravitation = []
        average_x = 0
        average_y = 0

        for body in particles:
            if self.__hash__() != body.__hash__(): # compates id to make sure it isnt gravitating with itself
                d = ((self.pos[0] - body.pos[0]) ** 2 + (self.pos[1] - body.pos[1]) ** 2) ** 0.5
                if d > gravity_distance:
                    continue  # ignores gravity from distance 150 away
                elif d < body.radius:
                    if nonelastic_collision:
                        self.collision(body)
                        return  # ends current function
                    elif elastic_collision:
                        self.elastic_collision(body)
                        return  # ends current function
                rhat = body.pos[0] - self.pos[0], body.pos[1] - self.pos[1] # unit vector (specifies direction)
                gravitation.append(
                    [G * self.mass * body.mass * rhat[0] / d ** 3, G * self.mass * body.mass * rhat[1] / d ** 3])

        for hole in holes:
            d = ((self.pos[0] - hole.pos[0]) ** 2 + (self.pos[1] - hole.pos[1]) ** 2) ** 0.5
            if d < (self.radius + hole.radius // 2):  # average between self radius and hole radius
                BlackHole.absorb(self)
                return  # ends current function
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
    def outofbounds(self):
        if particle_warp:
            if self.pos[0] < 0:
                self.pos = screen_width, self.pos[1]
            elif self.pos[0] > screen_width:
                self.pos = 0, self.pos[1]
            if self.pos[1] < 0:
                self.pos = self.pos[0], screen_height
            elif self.pos[1] > screen_height:
                self.pos = self.pos[0], 0
        elif particle_bounce:
            if self.pos[0] > screen_width - 1:
                self.pos = screen_width - 1, self.pos[1]
                self.velocity = -self.velocity[0], self.velocity[1]
            elif self.pos[0] < 1:
                self.pos = 1, self.pos[1]
                self.velocity = -self.velocity[0], self.velocity[1]
            elif self.pos[1] > screen_height - 1:
                self.pos = self.pos[0], screen_height - 1
                self.velocity = self.velocity[0], -self.velocity[1]
            elif self.pos[1] < 1:
                self.pos = self.pos[0], 1
                self.velocity = self.velocity[0], -self.velocity[1]

    # Collision Mechanics for particles
    def collision(self, body):
        # set position to whichever is bigger
        if self.radius < body.radius:
            self.pos = body.pos[0], body.pos[1]
        # self.pos = (body.pos[0] + self.pos[0]) / 2, (body.pos[1] + self.pos[1]) / 2  # average position between two

        # Calculate Net Force (x,y)
        f_net = self.mass * self.acceleration[0] + body.mass * body.acceleration[0], self.mass * self.acceleration[
            1] + body.mass * body.acceleration[1]

        # add masses together (not 1:1 ratio)
        self.mass = self.mass + body.mass

        self.velocity = self.acceleration[0] + body.acceleration[0], self.acceleration[1] + body.acceleration[1]

        # Set final acceleration
        self.acceleration = f_net[0] / self.mass, f_net[1] / self.mass

        # sets velocity to result of force

        # Calculate proper radii  - ((self.surface area + body.surface area) / pi) ** 0.5
        self.radius = floor(((pi * self.radius ** 2 + pi * body.radius ** 2) / pi) ** 0.5)

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
        self.outofbounds()
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
                    print('BlackHole absorbed Particle #', id(p))


def leftclick():
    mouse = pygame.mouse.get_pos()
    for p in particles:
        if (((p.pos[0] - mouse[0]) ** 2 + (p.pos[1] - mouse[1]) ** 2) ** 0.5) < p.radius:
            p.pos = mouse[0], mouse[1]


# ______Random particle generator______

particles = []
rectlist = []  # list of rect objects for updates
if randomize_particles:

    for i in range(0, iterations):
        particle_mass = random.randint(random_mass[0], random_mass[1])
        particles.append(Particle(pos=(random.randint(random_pos[0][0], random_pos[0][1]),
                                       random.randint(random_pos[1][0], random_pos[1][1])),
                                  colour=(random.randint(random_colour_R[0], random_colour_R[1]),
                                          random.randint(random_colour_G[0], random_colour_G[1]),
                                          random.randint(random_colour_B[0], random_colour_B[1])),
                                  mass=particle_mass, radius=particle_mass))

# ______List of Particles______

# particle1 = Particle(pos=(centerX-100, centerY),mass=20, colour=(255, 0, 0))
# particle2 = Particle(pos=(centerX+100, centerY),mass=20)
# # particle3 = Particle(pos=(centerX, centerY-200),mass = 4, colour=(0,255,0))
# # particle4 = Particle(pos=(centerX-200, centerY-100), colour=(0,128,255))
# particle5 = Particle(pos=(centerX, centerY),mass=11, colour=(255,128,255), velocity=(5,11.83))
# #
# # particles = [particle1, particle2,particle3] # list of particles
#
# particles = [particle1,particle2]

# List of BlackHoles
hole1 = BlackHole(pos=(centerX, centerY))
# hole2 = BlackHole(pos=(centerX, centerY + 100))
holes = []

# ______Main Loop______

print('DeepSpace Initialized')
screen.fill(background_colour)

mousedown = False
control = 1  # used for switching control between different variables (0) for grav, (1) for grav distance

while True:

    # Key Input
    key = pygame.key.get_pressed()
    mouse = pygame.mouse.get_pressed()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()
        if event.type == pygame.KEYDOWN: # KEY CONTROLS
            if event.key == pygame.K_ESCAPE:
                pygame.quit(); sys.exit()  # Exits the Simulation
            elif event.key == pygame.K_SPACE:  # Pauses the Simulation
                update = not update
            elif event.key == pygame.K_g:  # reverses gravity
                G = -G
            elif event.key == pygame.K_1:
                control = 1
            elif event.key == pygame.K_2:
                control = 2
            elif event.key == pygame.K_3:
                control = 3
            elif event.key == pygame.K_UP:  # (0)-increase Gravity/(1)-changes grav distance
                if control == 1:
                    G += ds
                elif control == 2:
                    gravity_distance += ds
                elif control == 3:
                    time_step += ds
            elif event.key == pygame.K_DOWN:  # Decrease Gravity
                if control == 1:
                    G -= ds
                elif control == 2:
                    gravity_distance -= ds
                elif control == 3:
                    time_step -= ds
            elif event.key == pygame.K_LEFT:  # decrease change in gravity step
                ds -= 1
                break
            elif event.key == pygame.K_RIGHT:  # increase change in gravity step
                ds += 1
                break
            elif event.key == pygame.K_r:  # Reset - deletes all particles/ resets time
                for p in particles:
                    del p
                particles = []
                time = 0
            elif event.key == pygame.K_s:  # enables and disables spawning
                particle_spawn = not particle_spawn
            elif event.key == pygame.K_b:  # enables and disables background colour refilling
                background_colour_refill = not background_colour_refill
            elif event.key == pygame.K_LEFTBRACKET:  # decreases mass and radius of all particles
                for p in particles:
                    p.radius = int(p.radius ** 0.92)
                    p.mass = int(p.mass ** 0.92)
            elif event.key == pygame.K_RIGHTBRACKET:  # increases mass and radius of all particles
                for p in particles:
                    p.radius = int(p.radius ** 1.08)
                    p.mass = int(p.mass ** 1.08)
            elif event.key == pygame.K_MINUS:
                if particle_spawn_rate > 1:
                    particle_spawn_rate -= 1
            elif event.key == pygame.K_EQUALS:
                particle_spawn_rate += 1
            elif event.key == pygame.K_w:
                mousedown = not mousedown
            elif event.key == pygame.K_h:
                if len(holes) > 0:
                    holes = []
                else:
                    holes = [hole1]

        if event.type == pygame.MOUSEMOTION and mousedown:
            leftclick()


    if update:
        # Fill Background
        if background_colour_refill and update:
            screen.fill(background_colour)

        # Update Particles and BlackHoles

        if particle_spawn and (time % particle_spawn_rate) == 0 and len(particles) < particle_spawn_limit:
            particle_mass = random.randint(random_mass[0], random_mass[1])
            particles.append(Particle(pos=(random.randint(random_pos[0][0], random_pos[0][1]),
                                           random.randint(random_pos[1][0], random_pos[1][1])),
                                      colour=(random.randint(random_colour_R[0], random_colour_R[1]),
                                              random.randint(random_colour_G[0], random_colour_G[1]),
                                              random.randint(random_colour_B[0], random_colour_B[1])),
                                      mass=particle_mass, radius=particle_mass))
            rectlist.append(particles[-1].rect)

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
                particle.colour = (particle.colour[0], particle.colour[1], (particle.colour[2] + i) % 255)

        for hole in holes:
            hole.draw()

        # Update Screen and Display Captions round(clock.get_fps(), 1)
        if time < 1:
            pygame.display.flip()
        pygame.display.update(rectlist)
        pygame.display.set_caption(
            '{} | FPS:{}/{} | Time: {} || Particles: {}/{} |{}/{}| G: {} | d:{}|| w:{} | b:{} | s:{} |'.format(
                display_caption,round(clock.get_fps(), 1), time_step, time,len(particles),particle_spawn,control,ds, G,
                gravity_distance, mousedown, background_colour_refill,particle_spawn_rate))
        # Update Clock
        clock.tick(time_step)
        time += 1
    else:  # When Simulation is Paused
        pygame.display.set_caption(
            '{} | {} | Time: {} || Particles: {}/{} |{}/{}| G: {} | d:{}|| w:{} | b:{} | s:{} |'.format(
                display_caption, 'PAUSED', time, len(particles), particle_spawn, control, ds, G,
                gravity_distance, mousedown, background_colour_refill, particle_spawn_rate))
