import pygame
import random
import sys
import os

# --- Constants ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
GRID_SIZE = 20  # Size of each snake segment and food item
GRID_WIDTH = SCREEN_WIDTH // GRID_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // GRID_SIZE

# Colors (RGB tuples)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 200) # Slightly darker blue for buttons
DARK_GREY = (50, 50, 50)
LIGHT_GREY = (150, 150, 150) # For button hover
ORANGE = (255, 165, 0)

# Directions (vectors)
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

# Game settings
INITIAL_SNAKE_SPEED = 8
MAX_SNAKE_SPEED = 25  # Cap for speed increase
SPEED_INCREASE_INTERVAL = 5  # Increase speed every this many Green Food scores
GREEN_FOOD_SCORE = 10
HIGH_SCORE_FILE = "highscore.txt"

# --- Pygame Initialization ---
pygame.init()
pygame.font.init() # Ensure font module is initialized for custom fonts

# Set up the display screen
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Python Snake Game")

# Fonts
FONT_SMALL = pygame.font.Font(None, 24)
FONT_MEDIUM = pygame.font.Font(None, 36)
FONT_LARGE = pygame.font.Font(None, 72)
FONT_XLARGE = pygame.font.Font(None, 100) # For main title

# --- Helper Functions ---

def draw_text(surface, text, size_key, color, x, y, center=True):
    """
    Draws text on the given surface.

    Args:
        surface: The Pygame surface to draw on.
        text (str): The text content.
        size_key (str): 'small', 'medium', 'large', or 'xlarge' to select font size.
        color (tuple): RGB color of the text.
        x (int): X-coordinate for the text.
        y (int): Y-coordinate for the text.
        center (bool): If True, text is centered at (x,y); otherwise, top-left is at (x,y).
    """
    font_map = {
        'small': FONT_SMALL,
        'medium': FONT_MEDIUM,
        'large': FONT_LARGE,
        'xlarge': FONT_XLARGE
    }
    font_to_use = font_map.get(size_key, FONT_MEDIUM) # Default to medium if key not found

    text_surface = font_to_use.render(text, True, color)
    text_rect = text_surface.get_rect()
    if center:
        text_rect.center = (x, y)
    else:
        text_rect.topleft = (x, y)
    surface.blit(text_surface, text_rect)

def load_high_score(filename):
    """
    Loads the high score from a local file.
    Returns 0 if the file doesn't exist or contains invalid data.
    """
    try:
        # Get the directory of the current script to ensure consistent file path
        script_dir = os.path.dirname(os.path.abspath(__file__))
        filepath = os.path.join(script_dir, filename)
        with open(filepath, "r") as file:
            return int(file.read())
    except (FileNotFoundError, ValueError):
        return 0 # Return 0 if file not found or content is invalid

def save_high_score(filename, score):
    """Saves the high score to a local file."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(script_dir, filename)
    with open(filepath, "w") as file:
        file.write(str(score))

def generate_random_position(occupied_positions):
    """
    Generates a random grid position that is not in the set of occupied_positions.
    This ensures food doesn't spawn on the snake or other food.
    """
    while True:
        x = random.randrange(0, GRID_WIDTH) * GRID_SIZE
        y = random.randrange(0, GRID_HEIGHT) * GRID_SIZE
        if (x, y) not in occupied_positions:
            return (x, y)

# --- Classes ---

class Snake:
    """Represents the snake in the game."""
    def __init__(self):
        self.reset()

    def reset(self):
        """Resets the snake to its initial state."""
        # Initial body segments, starting in the middle, facing right
        self.body = [
            pygame.Rect(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, GRID_SIZE, GRID_SIZE),
            pygame.Rect(SCREEN_WIDTH // 2 - GRID_SIZE, SCREEN_HEIGHT // 2, GRID_SIZE, GRID_SIZE),
            pygame.Rect(SCREEN_WIDTH // 2 - 2 * GRID_SIZE, SCREEN_HEIGHT // 2, GRID_SIZE, GRID_SIZE)
        ]
        self.direction = RIGHT
        self.grow_pending = False # Flag to indicate if snake should grow on next move

    def change_direction(self, new_direction):
        """
        Changes the snake's direction, preventing immediate reversals.
        (e.g., cannot go UP if currently going DOWN).
        """
        # Check if the new direction is not the direct opposite of the current direction
        if (new_direction[0] * -1, new_direction[1] * -1) != self.direction:
            self.direction = new_direction

    def move(self):
        """Moves the snake one step in its current direction."""
        head = self.body[0]
        new_head_x = head.x + self.direction[0] * GRID_SIZE
        new_head_y = head.y + self.direction[1] * GRID_SIZE
        new_head = pygame.Rect(new_head_x, new_head_y, GRID_SIZE, GRID_SIZE)
        
        self.body.insert(0, new_head) # Add new head
        
        if not self.grow_pending:
            self.body.pop() # Remove tail if not growing
        else:
            self.grow_pending = False # Reset flag after growth

    def draw(self, surface):
        """Draws the snake on the given surface."""
        for i, segment in enumerate(self.body):
            # Make the head slightly brighter for distinction
            color = GREEN if i == 0 else (0, 200, 0) 
            pygame.draw.rect(surface, color, segment)
            pygame.draw.rect(surface, BLACK, segment, 1) # Outline for segments

    def check_collision_self(self):
        """Checks if the snake's head collides with its own body."""
        # Only check if snake has more than one segment to avoid head-on-tail collision immediately after spawn
        return len(self.body) > 1 and self.body[0].collidelist(self.body[1:]) != -1

    def get_body_positions(self):
        """Returns a set of (x, y) tuples for all snake segments for collision/spawn checks."""
        return {(segment.x, segment.y) for segment in self.body}

class Food:
    """Base class for all food items."""
    def __init__(self, color):
        self.color = color
        self.rect = None # Placeholder, will be set by spawn method

    def spawn(self, snake_body_positions, all_food_positions):
        """Abstract method to spawn food at a valid position."""
        raise NotImplementedError("Spawn method must be implemented by subclasses.")

    def draw(self, surface):
        """Draws the food on the surface."""
        if self.rect:
            pygame.draw.rect(surface, self.color, self.rect)
            pygame.draw.rect(surface, BLACK, self.rect, 1) # Outline for food

    def get_position(self):
        """Returns the (x, y) coordinates of the food item."""
        if self.rect:
            return (self.rect.x, self.rect.y)
        return None

class GreenFood(Food):
    """Green food: increases snake length and score."""
    def __init__(self):
        super().__init__(GREEN)

    def spawn(self, snake_body_positions, all_food_positions):
        """Spawns green food at a random valid position."""
        # Use generate_random_position to ensure it doesn't spawn on snake or other food
        pos = generate_random_position(snake_body_positions.union(all_food_positions))
        self.rect = pygame.Rect(pos[0], pos[1], GRID_SIZE, GRID_SIZE)

    def effect(self, snake):
        """Applies the effect of green food to the snake (grow and score)."""
        snake.grow_pending = True
        return GREEN_FOOD_SCORE

class RedPoisonFood(Food):
    """Red poison food: decreases snake length."""
    def __init__(self):
        super().__init__(RED)

    def spawn(self, snake_body_positions, all_food_positions):
        """Spawns red poison food at a random valid position."""
        pos = generate_random_position(snake_body_positions.union(all_food_positions))
        self.rect = pygame.Rect(pos[0], pos[1], GRID_SIZE, GRID_SIZE)

    def effect(self, snake):
        """Applies the effect of red poison food to the snake (shrink)."""
        if len(snake.body) > 1: # Only shrink if snake has at least 2 segments
            snake.body.pop()
        return 0 # No score change for poison

class Button:
    """A clickable button widget."""
    def __init__(self, text, x, y, width, height, color, hover_color, text_color, font_size='medium'):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.text = text
        self.font_size = font_size

    def draw(self, surface, mouse_pos):
        """Draws the button, changing color on hover."""
        current_color = self.hover_color if self.rect.collidepoint(mouse_pos) else self.color
        pygame.draw.rect(surface, current_color, self.rect, border_radius=5)
        pygame.draw.rect(surface, BLACK, self.rect, 2, border_radius=5) # Border
        draw_text(surface, self.text, self.font_size, self.text_color, self.rect.centerx, self.rect.centery)

    def is_clicked(self, mouse_pos):
        """Checks if the button was clicked (mouse position is within button rect)."""
        return self.rect.collidepoint(mouse_pos)

# --- Game State Functions ---

def main_menu():
    """Displays the main menu screen with Play, High Score, and Quit buttons."""
    play_button = Button("Play", SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 50, 200, 50, BLUE, LIGHT_GREY, WHITE, 'medium')
    high_score_button = Button("High Score", SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 20, 200, 50, BLUE, LIGHT_GREY, WHITE, 'medium')
    quit_button = Button("Quit", SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 90, 200, 50, RED, LIGHT_GREY, WHITE, 'medium')

    while True:
        SCREEN.fill(DARK_GREY) # Background color
        mouse_pos = pygame.mouse.get_pos() # Get current mouse position

        draw_text(SCREEN, "SNAKE GAME", 'xlarge', GREEN, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4)

        # Draw buttons
        play_button.draw(SCREEN, mouse_pos)
        high_score_button.draw(SCREEN, mouse_pos)
        quit_button.draw(SCREEN, mouse_pos)

        # Event handling for menu
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit" # User clicked close button
            if event.type == pygame.MOUSEBUTTONDOWN:
                if play_button.is_clicked(mouse_pos):
                    return "play"
                if high_score_button.is_clicked(mouse_pos):
                    return "high_score_display"
                if quit_button.is_clicked(mouse_pos):
                    return "quit"

        pygame.display.flip() # Update the full display Surface to the screen

def game_loop(current_high_score):
    """
    The main game loop for active gameplay.
    Handles snake movement, food spawning/eating, collisions, score, and speed.
    """
    snake = Snake()
    green_food = GreenFood()
    red_poison_food = RedPoisonFood()
    
    current_score = 0
    game_speed = INITIAL_SNAKE_SPEED # Current frame rate for the game clock
    
    clock = pygame.time.Clock()

    def spawn_food_items(food_to_spawn, other_food_item=None):
        """
        Helper function to spawn a food item, ensuring it doesn't overlap with
        the snake or other specified food items.
        """
        occupied_by_snake = snake.get_body_positions()
        occupied_by_others = set()
        if other_food_item and other_food_item.get_position():
            occupied_by_others.add(other_food_item.get_position())
        
        # Pass a combined set of all occupied positions to prevent overlaps
        food_to_spawn.spawn(occupied_by_snake, occupied_by_others)
        
    # Initial food spawns
    spawn_food_items(green_food)
    spawn_food_items(red_poison_food, green_food) # Ensure red food doesn't spawn on green food initially

    game_over = False

    while not game_over:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit", current_score, current_high_score # Exit the game
            if event.type == pygame.KEYDOWN:
                # Change snake direction based on arrow key presses
                if event.key == pygame.K_UP:
                    snake.change_direction(UP)
                elif event.key == pygame.K_DOWN:
                    snake.change_direction(DOWN)
                elif event.key == pygame.K_LEFT:
                    snake.change_direction(LEFT)
                elif event.key == pygame.K_RIGHT:
                    snake.change_direction(RIGHT)

        # --- Game Logic Updates ---
        snake.move()
        head = snake.body[0] # Get current head position for collision checks

        # Check for wall collision
        if not (0 <= head.x < SCREEN_WIDTH and 0 <= head.y < SCREEN_HEIGHT):
            game_over = True
            break # Exit game loop

        # Check for self-collision
        if snake.check_collision_self():
            game_over = True
            break # Exit game loop
        
        # Check for Green Food collision
        if head.colliderect(green_food.rect):
            current_score += green_food.effect(snake) # Apply effect (grow, score)
            
            # Increase speed based on score
            if current_score > 0 and current_score % (GREEN_FOOD_SCORE * SPEED_INCREASE_INTERVAL) == 0:
                 if game_speed < MAX_SNAKE_SPEED: # Don't exceed max speed
                    game_speed += 1

            spawn_food_items(green_food, red_poison_food) # Spawn new green food

        # Check for Red Poison Food collision
        if head.colliderect(red_poison_food.rect):
            red_poison_food.effect(snake) # Apply effect (shrink)
            if len(snake.body) < 2: # Game over if snake becomes too short
                game_over = True
                break
            spawn_food_items(red_poison_food, green_food) # Spawn new red food

        # Update high score if current score surpasses it
        if current_score > current_high_score:
            current_high_score = current_score

        # --- Drawing ---
        SCREEN.fill(DARK_GREY) # Clear screen with background color
        
        snake.draw(SCREEN)
        green_food.draw(SCREEN)
        red_poison_food.draw(SCREEN)

        # Display score and high score
        draw_text(SCREEN, f"Score: {current_score}", 'small', WHITE, 10, 10, center=False)
        draw_text(SCREEN, f"High Score: {current_high_score}", 'small', WHITE, SCREEN_WIDTH - 10, 10, center=False)
        
        pygame.display.flip() # Update the display
        clock.tick(game_speed) # Control frame rate and game speed
    
    return "game_over", current_score, current_high_score # Return game state and final scores

def game_over_screen(final_score, high_score):
    """Displays the game over screen with final score, high score, and action buttons."""
    restart_button = Button("Restart", SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 50, 200, 50, BLUE, LIGHT_GREY, WHITE, 'medium')
    quit_button = Button("Quit", SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 120, 200, 50, RED, LIGHT_GREY, WHITE, 'medium')

    while True:
        SCREEN.fill(DARK_GREY)
        mouse_pos = pygame.mouse.get_pos()

        draw_text(SCREEN, "GAME OVER", 'large', RED, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4)
        draw_text(SCREEN, f"Your Score: {final_score}", 'medium', WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50)
        draw_text(SCREEN, f"High Score: {high_score}", 'medium', WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

        restart_button.draw(SCREEN, mouse_pos)
        quit_button.draw(SCREEN, mouse_pos)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.MOUSEBUTTONDOWN:
                if restart_button.is_clicked(mouse_pos):
                    return "play" # Go back to game loop
                if quit_button.is_clicked(mouse_pos):
                    return "quit"
        
        pygame.display.flip()

def high_score_display_screen(high_score):
    """Displays the current high score and a button to return to the main menu."""
    back_button = Button("Back to Menu", SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT * 3 // 4, 200, 50, BLUE, LIGHT_GREY, WHITE, 'medium')

    while True:
        SCREEN.fill(DARK_GREY)
        mouse_pos = pygame.mouse.get_pos()

        draw_text(SCREEN, "HIGH SCORE", 'large', ORANGE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4)
        draw_text(SCREEN, f"{high_score}", 'xlarge', WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

        back_button.draw(SCREEN, mouse_pos)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_button.is_clicked(mouse_pos):
                    return "main_menu" # Go back to main menu
        
        pygame.display.flip()

# --- Main Game Loop Orchestrator ---

def main():
    """
    The main function that orchestrates the game flow between different states
    (main menu, gameplay, game over, high score display).
    """
    current_high_score = load_high_score(HIGH_SCORE_FILE)
    current_state = "main_menu"
    final_score = 0 # Variable to hold score from game_loop to game_over_screen

    running = True
    while running:
        if current_state == "main_menu":
            current_state = main_menu()
        elif current_state == "play":
            state_result, score_result, high_score_result = game_loop(current_high_score)
            final_score = score_result
            current_high_score = high_score_result # Update high score for subsequent screens
            current_state = state_result
        elif current_state == "game_over":
            # Check if the final score is a new high score before saving
            if final_score > load_high_score(HIGH_SCORE_FILE): 
                save_high_score(HIGH_SCORE_FILE, final_score)
            current_high_score = load_high_score(HIGH_SCORE_FILE) # Reload to ensure latest saved score is shown
            current_state = game_over_screen(final_score, current_high_score)
        elif current_state == "high_score_display":
            current_high_score = load_high_score(HIGH_SCORE_FILE) # Ensure latest high score is displayed
            current_state = high_score_display_screen(current_high_score)
        elif current_state == "quit":
            running = False

    pygame.quit()
    sys.exit()

# --- Execution Block ---
if __name__ == "__main__":
    # Display instructions when the script is run directly
    print("--- Snake Game Instructions ---")
    print("1. Install Pygame:")
    print("   Open your terminal or command prompt and run:")
    print("   pip install pygame")
    print("\n2. Run the game:")
    print("   Save the code as a Python file (e.g., snake_game.py).")
    print("   Open your terminal or command prompt, navigate to the directory")
    print("   where you saved the file, and run:")
    print("   python snake_game.py")
    print("\n3. How to Play:")
    print("   - Use the UP, DOWN, LEFT, RIGHT arrow keys to control the snake.")
    print("   - Eat GREEN food to grow longer and increase your score.")
    print("   - Avoid RED poison food, which will make your snake shorter.")
    print("     If your snake becomes too short (less than 2 segments), the game ends.")
    print("   - Don't hit the walls or yourself!")
    print("   - The snake's speed increases as your score gets higher.")
    print("   - Your high score is saved locally and will be displayed in the menu.")
    print("\nHave fun playing!")
    main()
