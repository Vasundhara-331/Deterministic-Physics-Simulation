import pygame
import sys
import math
import random
from PIL import Image
from tkinter import Tk, filedialog

# --- Constants ---
WIDTH, HEIGHT = 1000, 1000
GRAVITY = pygame.math.Vector2(0, 981)  # Pixels per second^2
BACKGROUND_COLOR = (0,0,0)
BOUNCE_LOSS = 0.9 # Energy retained after bouncing off walls
COLLISION_DAMPING = 0.95 # Energy retained after inter-ball collision
MIN_RADIUS = 5
MAX_RADIUS = 28
SPAWN_STEP_INTERVAL = 1  # Spawn new ball every N steps
FIXED_DT = 1/60.0
MODE = "SPAWN"
TOTAL_STEPS = 1000
SIMULATION_SUBSTEPS = 8 # Increase for more accuracy, decrease for performance
MAX_OBJECTS = 900 # Limit the number of objects
# Grid constants for spatial hashing
CELL_SIZE = MAX_RADIUS * 2  # Size of each grid cell
GRID_WIDTH = math.ceil(WIDTH / CELL_SIZE)
GRID_HEIGHT = math.ceil(HEIGHT / CELL_SIZE)

# --- Image Upload ---
Tk().withdraw()  # hide main tkinter window
print("Please select an image file...")
INPUT_IMAGE_PATH = filedialog.askopenfilename(
    title="Select an image",
    filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.gif")]
)
if not INPUT_IMAGE_PATH:
    print("No image selected. Exiting...")
    sys.exit()

try:
    img = Image.open(INPUT_IMAGE_PATH).convert("RGB")
    img = img.resize((WIDTH, HEIGHT))
    img_data = img.load()
except Exception as e:
    print("Error loading image:", e)
    sys.exit()

# Setup screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Deterministic Physics Simulation Image Reveal")
clock = pygame.time.Clock()

# --- Ball Class ---
class Ball:
    """Represents a single ball in the physics simulation."""
    def __init__(self, position, radius, step_added, color=None):
        self.position = pygame.math.Vector2(position)
        # Verlet integration uses current and previous position to infer velocity
        self.old_position = pygame.math.Vector2(position)
        self.acceleration = pygame.math.Vector2(0, 0)
        self.radius = radius
        self.mass = math.pi * radius**2 # Mass proportional to area
        self.step_added = step_added
        self.color = color if color else (random.randint(100, 255), random.randint(100, 255), random.randint(100, 255))

    def update(self, dt):
        """Updates the ball's position using Verlet integration."""
        # Calculate velocity based on position change
        velocity = self.position - self.old_position

        # Store current position before updating
        self.old_position = pygame.math.Vector2(self.position)

        # Perform Verlet integration: pos += vel + acc * dt^2
        self.position += velocity + self.acceleration * dt * dt

        # Reset acceleration for the next frame/substep
        self.acceleration = pygame.math.Vector2(0, 0)

    def accelerate(self, force):
        """Applies a force to the ball (F = ma -> a = F/m)."""
        if self.mass > 0:
            self.acceleration += GRAVITY

    def apply_constraints(self):
        """Keeps the ball within the screen boundaries."""
        velocity = self.position - self.old_position

        if self.position.x - self.radius < 0:
            self.position.x = self.radius
            self.old_position.x = self.old_position.x
        elif self.position.x + self.radius > WIDTH:
            self.position.x = WIDTH - self.radius
            self.old_position.x = self.old_position.x
        if self.position.y - self.radius < 0:
            self.position.y = self.radius
            self.old_position.y = self.old_position.y
        elif self.position.y + self.radius > HEIGHT:
            self.position.y = HEIGHT - self.radius
            self.old_position.y = self.old_position.y

    def draw(self, screen):
        draw_pos = (int(self.position.x), int(self.position.y))
        pygame.draw.circle(screen, self.color, draw_pos, int(self.radius))

# --- Simulation Class ---
class Simulation:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Deterministic Physics Simulation")
        self.balls = []
        self.font = pygame.font.Font(None, 30)
        self.current_step = 0
        self.clock = pygame.time.Clock()
        self.grid = {}
        random.seed(42)

        self.input_image = None
        try:
            self.input_image = Image.open(INPUT_IMAGE_PATH).convert('RGB')
            self.input_image = self.input_image.resize((WIDTH, HEIGHT))
        except:
            print("No input image found - will skip image mapping")

    def add_ball(self, ball):
        if len(self.balls) < MAX_OBJECTS:
            self.balls.append(ball)
        elif self.balls:
            self.balls.pop(0)
            self.balls.append(ball)

    def apply_gravity(self):
        for ball in self.balls:
            ball.accelerate(GRAVITY)

    def update_positions(self, dt):
        for ball in self.balls:
            ball.update(dt)

    def apply_constraints(self):
        for ball in self.balls:
            ball.apply_constraints()

    def get_cell_index(self, position):
        cell_x = int(position.x / CELL_SIZE)
        cell_y = int(position.y / CELL_SIZE)
        return cell_x, cell_y
        
    def update_grid(self):
        self.grid.clear()
        for ball in self.balls:
            cell_x, cell_y = self.get_cell_index(ball.position)
            cell_key = (cell_x, cell_y)
            if cell_key not in self.grid:
                self.grid[cell_key] = []
            self.grid[cell_key].append(ball)
            
    def get_nearby_balls(self, ball):
        cell_x, cell_y = self.get_cell_index(ball.position)
        nearby_balls = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                cell_key = (cell_x + dx, cell_y + dy)
                if cell_key in self.grid:
                    nearby_balls.extend(self.grid[cell_key])
        return nearby_balls
    
    def solve_collisions(self):
        self.update_grid()
        for ball_1 in self.balls:
            nearby_balls = self.get_nearby_balls(ball_1)
            for ball_2 in nearby_balls:
                if ball_1 is ball_2:
                    continue
                collision_axis = ball_1.position - ball_2.position
                dist_sq = collision_axis.length_squared()
                min_dist = ball_1.radius + ball_2.radius
                if dist_sq < min_dist * min_dist and dist_sq > 0:
                    dist = math.sqrt(dist_sq)
                    normal = collision_axis / dist
                    overlap = (min_dist - dist) * 0.5
                    total_mass = ball_1.mass + ball_2.mass
                    if total_mass == 0:
                        mass_ratio_1 = mass_ratio_2 = 0.5
                    else:
                        mass_ratio_1 = ball_2.mass / total_mass if ball_1.mass > 0 else 1.0
                        mass_ratio_2 = ball_1.mass / total_mass if ball_2.mass > 0 else 1.0
                    separation_vector = normal * overlap
                    ball_1.position += separation_vector * mass_ratio_1 * COLLISION_DAMPING
                    ball_2.position -= separation_vector * mass_ratio_2 * COLLISION_DAMPING

    def update(self, dt):
        sub_dt = dt / SIMULATION_SUBSTEPS
        for _ in range(SIMULATION_SUBSTEPS):
            self.apply_gravity()
            self.solve_collisions()
            self.apply_constraints()
            self.update_positions(sub_dt)

    def draw(self):
        self.screen.fill(BACKGROUND_COLOR)
        for ball in self.balls:
            ball.draw(self.screen)
        stats_text = self.font.render(f"Step: {self.current_step}/{TOTAL_STEPS} | Objects: {len(self.balls)}/{MAX_OBJECTS}", True, (200, 200, 200))
        self.screen.blit(stats_text, (10, 10))
        pygame.display.flip()

    def map_balls_to_image(self):
        if MODE != "SPAWN" or not self.input_image:
            return
        with open('ball_spawns.csv', 'r') as f:
            lines = f.readlines()
        sorted_balls = sorted(self.balls, key=lambda x: x.step_added)
        new_lines = []
        for i, line in enumerate(lines):
            if i >= len(sorted_balls):
                break
            ball = sorted_balls[i]
            x = min(max(int(ball.position.x), 0), WIDTH - 1)
            y = min(max(int(ball.position.y), 0), HEIGHT - 1)
            r, g, b = self.input_image.getpixel((x, y))
            step, x, y, radius, old_x, old_y, _, _, _ = map(float, line.strip().split(','))
            new_line = f"{int(step)},{x},{y},{radius},{old_x},{old_y},{r},{g},{b}\n"
            new_lines.append(new_line)
        with open('ball_spawns.csv', 'w') as f:
            f.writelines(new_lines)

    def calculate_positions(self):
        print("Starting fast calculation phase...")
        self.current_step = 0
        balls_spawned = 0
        csv_lines = []
        while self.current_step < TOTAL_STEPS:
            if self.current_step % SPAWN_STEP_INTERVAL == 0 and balls_spawned < MAX_OBJECTS:
                center_pos = (WIDTH/2, HEIGHT/2)
                radius = random.uniform(MIN_RADIUS, MAX_RADIUS)
                new_ball = Ball(center_pos, radius, step_added=self.current_step)
                angle = random.uniform(0, 2 * math.pi)
                blast_speed = 40
                velocity = pygame.math.Vector2(math.cos(angle) * blast_speed, math.sin(angle) * blast_speed)
                new_ball.old_position = new_ball.position - velocity * FIXED_DT
                csv_lines.append(
                    f"{self.current_step},{new_ball.position.x},{new_ball.position.y},"
                    f"{new_ball.radius},{new_ball.old_position.x},{new_ball.old_position.y},"
                    f"{new_ball.color[0]},{new_ball.color[1]},{new_ball.color[2]}\n"
                )
                self.add_ball(new_ball)
                balls_spawned += 1
            self.update(FIXED_DT)
            self.current_step += 1
            if self.current_step % 100 == 0:
                print(f"Calculated {self.current_step}/{TOTAL_STEPS} steps...")
        print("Writing results to CSV...")
        with open('ball_spawns.csv', 'w') as f:
            f.writelines(csv_lines)
        print("Mapping colors from input image...")
        self.map_balls_to_image()
        print("Calculation phase complete!")
        
    def display_simulation(self):
        self.balls = []
        self.current_step = 0
        running = True
        balls_spawned = 0
        while running:
            self.clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            with open('ball_spawns.csv', 'r') as f:
                for _ in range(balls_spawned):
                    next(f)
                line = next(f, None)
                if line:
                    step, x, y, radius, old_x, old_y, r, g, b = map(float, line.strip().split(','))
                    if self.current_step == int(step):
                        new_ball = Ball((x, y), radius, step, (int(r), int(g), int(b)))
                        new_ball.old_position = pygame.math.Vector2(old_x, old_y)
                        self.add_ball(new_ball)
                        balls_spawned += 1
            self.update(FIXED_DT)
            self.draw()
            self.current_step += 1
        pygame.quit()
        sys.exit()

    def run(self):
        print("Calculating ball positions...")
        self.calculate_positions()
        print("Displaying simulation...")
        self.display_simulation()

# --- Start Simulation ---
if __name__ == "__main__":
    simulation = Simulation()
    simulation.run()
