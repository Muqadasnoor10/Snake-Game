**You want the snake to change its color dynamically based on the last eaten fruit.**
Right now, the snake has a fixed green color. 
We can modify the Snake class so that when it eats a fruit, it stores the fruit color and uses it to draw itself instead of the default green. 
Letters will keep the default color.

---

##  Update the Snake class
- Add a current_color attribute to store the snake’s color:

class Snake:
    def __init__(self):
        self.reset()
        self.tongue_state = False
        self.tongue_timer = 0
        self.current_color = (0, 200, 0)  # default green

    def reset(self):
        self.length = 3
        self.positions = [(GRID_WIDTH // 2, GRID_HEIGHT // 2)]
        self.direction = RIGHT
        self.score = 0
        self.grow_pending = 2
        self.tongue_state = False
        self.tongue_timer = 0
        self.current_color = (0, 200, 0)  # reset color
---

## Update draw method to use current_color

    def draw(self, surface):
        if not self.positions:
            return

        base_r, base_g, base_b = self.current_color

        for i, p in enumerate(self.positions):
            x = p[0] * GRID_SIZE + GRID_SIZE // 2
            y = p[1] * GRID_SIZE + GRID_SIZE // 2
            shade_factor = max(50, 200 - i*15)
            color = (
                min(255, base_r * shade_factor // 200),
                min(255, base_g * shade_factor // 200),
                min(255, base_b * shade_factor // 200)
            )
            pygame.draw.circle(surface, color, (x, y), GRID_SIZE // 2)
            pygame.draw.circle(surface, (100, 255, 150), (x - 3, y - 3), GRID_SIZE // 6)

        head_x, head_y = self.positions[0]
        head_x = head_x * GRID_SIZE + GRID_SIZE // 2
        head_y = head_y * GRID_SIZE + GRID_SIZE // 2
        pygame.draw.circle(surface, self.current_color, (head_x, head_y), GRID_SIZE // 2 + 2)
        pygame.draw.circle(surface, (0,255,0), (head_x, head_y), GRID_SIZE // 2 + 2, 2)

        # Eyes and tongue code remains the same...
---

## Update the Game.run() method to pass color when eating fruit
if self.snake.get_head_position() == self.food.position:
    if self.food.type == "fruit" and self.food.fruit_info:
        color = self.food.fruit_info["color"]
        bonus = self.food.fruit_info["bonus"]
    else:
        color = (0, 200, 0)  # default green for letters
        bonus = 10
    self.snake.grow(bonus=bonus, color=color)
    self.food.randomize_position(self.snake.positions)

## ✅ That’s it! Now:

- When the snake eats a fruit, it changes to that fruit's color.
- Eating letters keeps it the default green.
- The shading of the body segments adapts to the color.



