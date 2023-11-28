import pygame
import pygame_widgets
from pygame_widgets.button import Button
from pygame_widgets.slider import Slider
from pygame_widgets.textbox import TextBox
from wolf_sheep.model import WolfSheep
from wolf_sheep.agents import Wolf, Sheep


# Initialize Pygame
pygame.init()

# Set desired window width
desired_window_width = 800  # Update this value as needed

# Initialize the Mesa model
model = WolfSheep()

# Aspect ratio
model_width, model_height = model.width, model.height
aspect_ratio = model_width / model_height

# Define UI dimensions
border_thickness = int(desired_window_width * 0.02)  # 2% for border
top_bar_height = int(desired_window_width * 0.10)  # 10% for top bar

# Calculate scaled model dimensions and window height
scaled_model_width = desired_window_width - 2 * border_thickness
scaled_model_height = int(scaled_model_width / aspect_ratio)
screen_width = scaled_model_width + 2 * border_thickness
screen_height = scaled_model_height + top_bar_height + border_thickness

# Initialize window
screen = pygame.display.set_mode((desired_window_width, screen_height))
pygame.display.set_caption("Mesa Model Visualization")

# Load and scale agent sprites
sprite_size = (20, 20)  # Define sprite size (width, height)
wolf_sprite = pygame.image.load('wolf_sheep/howl.png')
wolf_sprite = pygame.transform.scale(wolf_sprite, sprite_size)

sheep_sprite = pygame.image.load('wolf_sheep/Sheep.png')
sheep_sprite = pygame.transform.scale(sheep_sprite, sprite_size)

# Function to scale model coordinates to screen coordinates
def scale_pos(model_pos, model_size, screen_size):
    return int(model_pos * screen_size / model_size)

# Create a font object
font = pygame.font.Font(None, 30)  # You can also use a specific font

# Button actions
def start_stop():
    global run_simulation
    run_simulation = not run_simulation

def step():
    global run_simulation
    run_simulation = False
    model.step()

# Reset action
def reset_simulation():
    global model
    model = WolfSheep()  # Reinitialize the model

# Adjust button positions to be within the top bar
button_y = top_bar_height // 4  # Vertically centering buttons in the top bar

# Create buttons using Pygame Widgets
start_stop_button = Button(
    screen, 50, button_y, 100, 50, text='Start/Stop',
    onClick=start_stop, fontSize=20, inactiveColour=(0, 200, 0), pressedColour=(0, 255, 0)
)
step_button = Button(
    screen, 200, button_y, 100, 50, text='Step',
    onClick=step, fontSize=20, inactiveColour=(200, 200, 0), pressedColour=(255, 255, 0)
)
reset_button = Button(
    screen, 350, button_y, 100, 50, text='Reset',
    onClick=reset_simulation, fontSize=20, inactiveColour=(200, 0, 0), pressedColour=(255, 0, 0)
)

# Create the slider using Pygame Widgets
slider_x = 500
slider_width = 200
slider_height = 20

# Create the slider with a specific color
steps_per_second_slider = Slider(
    screen, slider_x, button_y, slider_width, slider_height,
    min=1, max=60, step=1, handleRadius=10, handleColour=(100, 100, 100),
    colour=(150, 150, 150)
)
output = TextBox(
    screen, slider_x + slider_width + 10, button_y, 50, 50,
    fontSize=20, borderColour=(0, 0, 0), textColour=(0, 0, 0)
)
output.disable()

# Function to check if a point is inside a circle (used for detecting click on agent)
def is_point_in_circle(point, circle_center, radius):
    return (point[0] - circle_center[0])**2 + (point[1] - circle_center[1])**2 <= radius**2

# State variables
running = True
run_simulation = False

# Main loop
while running:
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            running = False

    # Clear screen with black background
    screen.fill((0, 0, 0))

    # Draw top bar (grey)
    pygame.draw.rect(screen, (200, 200, 200), (0, 0, screen_width, top_bar_height))

    # Update widgets
    pygame_widgets.update(events)
    steps_per_second = steps_per_second_slider.getValue()
    output.setText(steps_per_second)

    # Update the model if running
    if run_simulation:
        model.step()

    # Draw border (white) around the visualization area
    visualization_area = (border_thickness, top_bar_height, scaled_model_width, scaled_model_height)
    pygame.draw.rect(screen, (255, 255, 255), visualization_area)

    # Draw agents inside the border
    for agent in model.schedule.agents:
        # Scale position from model to screen, adjusted for border and top bar
        screen_pos = (scale_pos(agent.pos[0], model.width, scaled_model_width) + border_thickness,
                      scale_pos(agent.pos[1], model.height, scaled_model_height) + top_bar_height)

        # Draw wolf or sheep sprite
        if isinstance(agent, Wolf):
            screen.blit(wolf_sprite, screen_pos)
        elif isinstance(agent, Sheep):
            screen.blit(sheep_sprite, screen_pos)

    # Use the slider value to control the frame rate
    pygame.time.Clock().tick(steps_per_second)

    # Update display
    pygame.display.flip()

pygame.quit()
