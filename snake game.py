import pygame
import random
import sys
import threading
import tkinter as tk
from tkinter import messagebox
import pystray
from PIL import Image, ImageDraw

# ------------------- Pygame Setup ------------------- #
pygame.init()

WIDTH, HEIGHT = 800, 600
GRID_SIZE = 20
GRID_WIDTH = WIDTH // GRID_SIZE
GRID_HEIGHT = HEIGHT // GRID_SIZE
FPS = 10

BACKGROUND = (15, 15, 30)
TEXT_COLOR = (240, 240, 240)
BORDER_COLOR = (50, 150, 200)
MIN_SPEED = 5
MAX_SPEED = 25

UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

# ------------------- Snake Class ------------------- #
class Snake:
    def __init__(self):
        self.reset()
        self.tongue_state = False
        self.tongue_timer = 0
        
    def reset(self):
        self.length = 3
        self.positions = [(GRID_WIDTH // 2, GRID_HEIGHT // 2)]
        self.direction = RIGHT
        self.score = 0
        self.grow_pending = 2
        self.tongue_state = False
        self.tongue_timer = 0
        
    def get_head_position(self):
        return self.positions[0]
    
    def turn(self, point):
        if self.length > 1 and (point[0]*-1, point[1]*-1) == self.direction:
            return
        self.direction = point
    
    def move(self):
        head = self.get_head_position()
        x, y = self.direction
        new_x = (head[0] + x) % GRID_WIDTH
        new_y = (head[1] + y) % GRID_HEIGHT
        new_position = (new_x, new_y)
        
        if new_position in self.positions[1:]:
            return False
        
        self.positions.insert(0, new_position)
        
        if self.grow_pending > 0:
            self.grow_pending -= 1
        else:
            self.positions.pop()
            
        self.tongue_timer += 1
        if self.tongue_timer % 5 == 0:
            self.tongue_state = not self.tongue_state
            
        return True
    
    def grow(self, bonus=10):
        self.grow_pending += 1
        self.length += 1
        self.score += bonus

    def draw(self, surface):
        if not self.positions:
            return

        for i, p in enumerate(self.positions):
            x = p[0] * GRID_SIZE + GRID_SIZE // 2
            y = p[1] * GRID_SIZE + GRID_SIZE // 2
            green_shade = max(50, 200 - i*15)
            pygame.draw.circle(surface, (0, green_shade, 100), (x, y), GRID_SIZE // 2)
            pygame.draw.circle(surface, (100, 255, 150), (x - 3, y - 3), GRID_SIZE // 6)

        head_x, head_y = self.positions[0]
        head_x = head_x * GRID_SIZE + GRID_SIZE // 2
        head_y = head_y * GRID_SIZE + GRID_SIZE // 2
        pygame.draw.circle(surface, (0, 220, 120), (head_x, head_y), GRID_SIZE // 2 + 2)
        pygame.draw.circle(surface, (0, 255, 150), (head_x, head_y), GRID_SIZE // 2 + 2, 2)

        # Eyes and tongue
        if self.direction == RIGHT:
            eye1 = (head_x + 6, head_y - 5)
            eye2 = (head_x + 6, head_y + 5)
            tongue_base = (head_x + GRID_SIZE//2, head_y)
            tongue_tip = (tongue_base[0] + (5 if self.tongue_state else 3), head_y)
        elif self.direction == LEFT:
            eye1 = (head_x - 6, head_y - 5)
            eye2 = (head_x - 6, head_y + 5)
            tongue_base = (head_x - GRID_SIZE//2, head_y)
            tongue_tip = (tongue_base[0] - (5 if self.tongue_state else 3), head_y)
        elif self.direction == UP:
            eye1 = (head_x - 4, head_y - 6)
            eye2 = (head_x + 4, head_y - 6)
            tongue_base = (head_x, head_y - GRID_SIZE//2)
            tongue_tip = (head_x, tongue_base[1] - (5 if self.tongue_state else 3))
        else:  # DOWN
            eye1 = (head_x - 4, head_y + 6)
            eye2 = (head_x + 4, head_y + 6)
            tongue_base = (head_x, head_y + GRID_SIZE//2)
            tongue_tip = (head_x, tongue_base[1] + (5 if self.tongue_state else 3))

        pygame.draw.circle(surface, (255,255,255), eye1, 4)
        pygame.draw.circle(surface, (0,0,0), eye1, 2)
        pygame.draw.circle(surface, (255,255,255), eye2, 4)
        pygame.draw.circle(surface, (0,0,0), eye2, 2)
        pygame.draw.line(surface, (255,50,50), tongue_base, tongue_tip, 2)

# ------------------- Food Class ------------------- #
class Food:
    LETTERS = [chr(i) for i in range(65, 91)]
    LETTER_COLORS = [
        (220,50,50),(255,230,50),(0,200,0),(50,50,220),(255,140,0),
        (255,215,0),(200,0,100),(120,0,200),(0,150,150),(255,100,200),
        (150,255,0),(255,50,150),(100,220,200),(180,180,50),(50,180,100),
        (220,120,0),(100,100,255),(255,150,150),(50,255,50),(200,50,220),
        (50,50,150),(150,50,50),(50,200,150),(255,200,50),(200,100,0),(100,255,100)
    ]

    FRUITS = [
        {"name": "Apple", "color": (220,50,50), "bonus": 10},
        {"name": "Banana", "color": (255,230,50), "bonus": 12},
        {"name": "Cherry", "color": (200,0,100), "bonus": 15},
        {"name": "Grape", "color": (120,0,200), "bonus": 18},
        {"name": "Orange", "color": (255,140,0), "bonus": 20},
        {"name": "Pineapple", "color": (255,215,0), "bonus": 25},
        {"name": "Watermelon", "color": (0,200,0), "bonus": 22},
        {"name": "Strawberry", "color": (220,20,60), "bonus": 18},
        {"name": "Blueberry", "color": (50,50,220), "bonus": 15}
    ]

    def __init__(self, snake_positions=None):
        self.position = (0, 0)
        self.type = None
        self.letter = None
        self.color = None
        self.fruit_info = None
        self.previous_type = None
        self.randomize_position(snake_positions)

    def randomize_position(self, snake_positions=None):
        if snake_positions is None:
            snake_positions = []

        # Ensure food fits entirely inside screen
        while True:
            new_pos = (random.randint(0, GRID_WIDTH-1), random.randint(0, GRID_HEIGHT-1))
            if new_pos not in snake_positions:
                self.position = new_pos
                break

        if random.random() < 0.5:
            self.type = "letter"
            letters_available = [l for l in self.LETTERS if l != self.previous_type]
            self.letter = random.choice(letters_available)
            self.previous_type = self.letter
            self.color = random.choice(self.LETTER_COLORS)
            self.fruit_info = None
        else:
            self.type = "fruit"
            fruits_available = [f for f in self.FRUITS if f != self.previous_type]
            self.fruit_info = random.choice(fruits_available)
            self.previous_type = self.fruit_info
            self.letter = None
            self.color = self.fruit_info["color"]

    def draw(self, surface):
        x, y = self.position[0]*GRID_SIZE, self.position[1]*GRID_SIZE
        center = (x + GRID_SIZE//2, y + GRID_SIZE//2)

        if self.type == "letter" and self.letter:
            font = pygame.font.SysFont('Arial', GRID_SIZE, bold=True)
            text_surface = font.render(self.letter, True, self.color)
            text_rect = text_surface.get_rect(center=center)
            surface.blit(text_surface, text_rect)
        elif self.type == "fruit" and self.fruit_info:
            name = self.fruit_info["name"]
            color = self.fruit_info["color"]

            # All fruits drawn within GRID_SIZE
            if name == "Apple":
                pygame.draw.circle(surface, color, center, GRID_SIZE//2 - 2)
                pygame.draw.rect(surface, (0,150,0), (center[0]-2, center[1]-8, 4, 8))
            elif name == "Banana":
                pygame.draw.ellipse(surface, color, (x+2, y+GRID_SIZE//4, GRID_SIZE-4, GRID_SIZE//2))
            elif name == "Cherry":
                pygame.draw.circle(surface, color, (center[0]-4, center[1]), GRID_SIZE//4)
                pygame.draw.circle(surface, color, (center[0]+4, center[1]), GRID_SIZE//4)
                pygame.draw.line(surface, (0,150,0), (center[0]-4, center[1]-4), (center[0]-4, center[1]-8), 2)
                pygame.draw.line(surface, (0,150,0), (center[0]+4, center[1]-4), (center[0]+4, center[1]-8), 2)
            elif name == "Grape":
                for i in range(3):
                    for j in range(2):
                        pygame.draw.circle(surface, color, (x + 6 + i*6, y + 6 + j*6), 3)
            elif name == "Orange":
                pygame.draw.circle(surface, color, center, GRID_SIZE//2 - 2)
                pygame.draw.circle(surface, (255,200,0), center, GRID_SIZE//2 - 2, 2)
            elif name == "Pineapple":
                pygame.draw.rect(surface, color, (x+4, y+4, GRID_SIZE-8, GRID_SIZE-8))
                pygame.draw.polygon(surface, (0,150,0), [(center[0],y),(center[0]-5,y-8),(center[0]+5,y-8)])
            elif name == "Watermelon":
                pygame.draw.arc(surface, color, (x+2, y+2, GRID_SIZE-4, GRID_SIZE-4), 3.14, 0, 2)
                pygame.draw.arc(surface, (255,0,0), (x+4, y+4, GRID_SIZE-8, GRID_SIZE-8), 3.14, 0, 2)
            elif name == "Strawberry":
                pygame.draw.polygon(surface, color, [(center[0],y+2),(x+4,y+GRID_SIZE-4),(x+GRID_SIZE-4,y+GRID_SIZE-4)])
                pygame.draw.circle(surface, (0,150,0), (center[0], y+4), 3)
            elif name == "Blueberry":
                pygame.draw.circle(surface, color, center, GRID_SIZE//3 - 1)
                pygame.draw.circle(surface, (0,0,0), center, 2)

# ------------------- Instructions ------------------- #
def show_instructions():
    root = tk.Tk()
    root.title("Snake Game Controls")
    root.geometry("400x300")
    text = (
        "SNAKE GAME CONTROLS\n\n"
        "Arrow Keys: Move Snake\n"
        "+ : Increase Speed\n"
        "- : Decrease Speed\n"
        "P : Pause Game\n"
        "ESC : Quit Game\n\n"
        "Eat letters A-Z to grow!\n"
        "Each letter gives bonus points!\n"
        "Don't run into yourself!\n"
    )
    label = tk.Label(root, text=text, font=("Arial",12), justify="left")
    label.pack(padx=10,pady=10)
    root.mainloop()

# ------------------- System Tray ------------------- #
def create_tray_icon(game_instance):
    image = Image.new("RGB", (64, 64), (0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rectangle((10, 20, 54, 44), fill=(0, 200, 0))
    draw.ellipse((28, 14, 36, 22), fill=(220, 50, 50))

    def on_controls(icon, item):
        icon.stop()
        show_instructions()
        threading.Thread(target=icon.run).start()

    def on_pause(icon, item):
        game_instance.paused = not game_instance.paused

    def on_speed_up(icon, item):
        game_instance.speed = min(MAX_SPEED, game_instance.speed + 1)
        game_instance.manual_speed_change = True

    def on_speed_down(icon, item):
        game_instance.speed = max(MIN_SPEED, game_instance.speed - 1)
        game_instance.manual_speed_change = True

    def pause_label(item):
        return "Pause" if not game_instance.paused else "Resume"

    icon = pystray.Icon(
        "SnakeGame",
        image,
        "Snake Game",
        menu=pystray.Menu(
            pystray.MenuItem("Controls", on_controls),
            pystray.MenuItem(pause_label, on_pause),
            pystray.MenuItem("Speed +", on_speed_up),
            pystray.MenuItem("Speed -", on_speed_down),
            pystray.MenuItem("Exit", lambda icon, item: icon.stop())
        )
    )
    icon.run()

# ------------------- Game Class ------------------- #
class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH,HEIGHT))
        pygame.display.set_caption("Snake Game")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('Arial',25)
        self.big_font = pygame.font.SysFont('Arial',50,bold=True)
        self.snake = Snake()
        self.food = Food(self.snake.positions)
        self.game_over = False
        self.speed = FPS
        self.paused = False
        self.manual_speed_change = False
        self.info_icon_rect = pygame.Rect(WIDTH-40, 10, 30, 30)

    def draw_border(self):
        pygame.draw.rect(self.screen,BORDER_COLOR,(0,0,WIDTH,HEIGHT),5)

    def draw_score(self):
        score_text = self.font.render(f'Score: {self.snake.score}',True,TEXT_COLOR)
        length_text = self.font.render(f'Length: {self.snake.length}',True,TEXT_COLOR)
        speed_text = self.font.render(f'Speed: {self.speed}',True,TEXT_COLOR)
        self.screen.blit(score_text,(10,10))
        self.screen.blit(length_text,(10,40))
        self.screen.blit(speed_text,(10,70))

    def draw_game_over(self):
        go_surface = self.big_font.render('GAME OVER',True,(220,50,50))
        restart_surface = self.font.render('Press SPACE to restart or ESC to quit',True,TEXT_COLOR)
        self.screen.blit(go_surface,go_surface.get_rect(center=(WIDTH//2,HEIGHT//2-50)))
        self.screen.blit(restart_surface,restart_surface.get_rect(center=(WIDTH//2,HEIGHT//2+20)))

    def draw_info_icon(self):
        pygame.draw.rect(self.screen, (50, 150, 220), self.info_icon_rect, border_radius=5)
        text = self.font.render("i", True, (255, 255, 255))
        text_rect = text.get_rect(center=self.info_icon_rect.center)
        self.screen.blit(text, text_rect)

    def handle_mouse_click(self, pos):
        if self.info_icon_rect.collidepoint(pos):
            threading.Thread(target=show_instructions).start()

    def handle_keys(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                pygame.quit(); sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.handle_mouse_click(event.pos)
            elif event.type == pygame.KEYDOWN:
                if self.game_over:
                    if event.key == pygame.K_SPACE:
                        self.snake.reset()
                        self.food.randomize_position(self.snake.positions)
                        self.game_over = False
                        self.speed = FPS
                        self.manual_speed_change = False
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit(); sys.exit()
                else:
                    if event.key == pygame.K_UP: self.snake.turn(UP)
                    elif event.key == pygame.K_DOWN: self.snake.turn(DOWN)
                    elif event.key == pygame.K_LEFT: self.snake.turn(LEFT)
                    elif event.key == pygame.K_RIGHT: self.snake.turn(RIGHT)
                    elif event.key == pygame.K_ESCAPE: pygame.quit(); sys.exit()
                    elif event.key == pygame.K_p: self.paused = not self.paused
                    elif event.key in (pygame.K_PLUS, pygame.K_KP_PLUS, pygame.K_EQUALS):
                        self.speed = min(MAX_SPEED,self.speed+1)
                        self.manual_speed_change = True
                    elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                        self.speed = max(MIN_SPEED,self.speed-1)
                        self.manual_speed_change = True

    def update_speed(self):
        if not self.manual_speed_change:
            self.speed = min(MAX_SPEED, FPS + self.snake.score//50)

    def run(self):
        while True:
            self.handle_keys()
            if self.paused:
                pause_surface = self.big_font.render('PAUSED',True,(50,150,220))
                pause_rect = pause_surface.get_rect(center=(WIDTH//2,HEIGHT//2))
                self.screen.fill(BACKGROUND)
                self.screen.blit(pause_surface,pause_rect)
                self.draw_info_icon()
                pygame.display.update()
                self.clock.tick(5)
                continue
            if not self.game_over:
                if not self.snake.move(): self.game_over = True
                if self.snake.get_head_position() == self.food.position:
                    bonus = self.food.fruit_info["bonus"] if self.food.type=="fruit" else 10
                    self.snake.grow(bonus=bonus)
                    self.food.randomize_position(self.snake.positions)
                self.update_speed()
            self.screen.fill(BACKGROUND)
            self.snake.draw(self.screen)
            self.food.draw(self.screen)
            self.draw_border()
            self.draw_score()
            self.draw_info_icon()
            if self.game_over: self.draw_game_over()
            pygame.display.update()
            self.clock.tick(self.speed)

# ------------------- Main ------------------- #
if __name__ == "__main__":
    game = Game()
    threading.Thread(target=create_tray_icon,args=(game,)).start()
    game.run()
