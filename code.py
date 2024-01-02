import os, sys
import board
import busio
import terminalio
import displayio
import time
from adafruit_st7735r import ST7735R
import gifio
import adafruit_imageload

# Your pin configuration
mosi_pin = board.GP11
clk_pin = board.GP10
reset_pin = board.GP17
cs_pin = board.GP18
dc_pin = board.GP16

digimon_idle_grids = None
digimon_walk_grids = None
digimon_sleep_grids = None
digimon_victory_grids = None
digimon_attack_a_grids = None
digimon_attack_b_grids = None

displayio.release_displays()

spi = busio.SPI(clock=clk_pin, MOSI=mosi_pin)
display_bus = displayio.FourWire(spi, command=dc_pin, chip_select=cs_pin, reset=reset_pin)

display = ST7735R(display_bus, width=160, height=128, rotation=90, bgr=True)
group = displayio.Group()

# Background Setup
background_bitmap = displayio.OnDiskBitmap("/registerjungle.bmp")
background = displayio.TileGrid(background_bitmap, pixel_shader=displayio.ColorConverter())
group.append(background)

# Function to load animation frames
def load_animation_frames(image_path, palette_transparent_color=0):
    bit, pal = adafruit_imageload.load(image_path, bitmap=displayio.Bitmap, palette=displayio.Palette)
    pal.make_transparent(palette_transparent_color)
    return bit, pal

# Function to create TileGrids
def create_tile_grid(bitmap, palette, x_pos, y_pos, width=1, height=1, tile_height=64, tile_width=64, default_tile=0):
    return displayio.TileGrid(bitmap, pixel_shader=palette, width=width, height=height,
                              tile_height=tile_height, tile_width=tile_width, default_tile=default_tile,
                              x=x_pos, y=y_pos)

# Function to append TileGrids to the display group
def append_to_group(tile_grids):
    for grid in tile_grids:
        group.append(grid)

# Function to set up Digimon idle animation
def setup_digimon_idle_animation():
    global digimon_idle_grids
    bit, pal = load_animation_frames("/Greymon/dmonIdle.bmp")
    digimon_idle_grids = [create_tile_grid(bit, pal, 90, 40, tile_height=78, tile_width=64) for _ in range(4)]
    append_to_group(digimon_idle_grids)
    
# Function to set up Digimon walk animation
def setup_digimon_walk_animation():
    global digimon_walk_grids
    bit, pal = load_animation_frames("/Greymon/dmonwalk.bmp")
    digimon_walk_grids = [create_tile_grid(bit, pal, 90, 40, tile_height=78, tile_width=62) for _ in range(4)]
    append_to_group(digimon_walk_grids)
    
# Function to set up Digimon sleep animation
def setup_digimon_sleep_animation():
    global digimon_sleep_grids
    bit, pal = load_animation_frames("/Greymon/dmonsleep.bmp")
    digimon_sleep_grids = [create_tile_grid(bit, pal, 90, 40, tile_height=50, tile_width=64) for _ in range(4)]
    append_to_group(digimon_sleep_grids)
    
# Function to set up Digimon sleep animation
def setup_digimon_victory_animation():
    global digimon_victory_grids
    bit, pal = load_animation_frames("/Greymon/dmonvictory.bmp")
    digimon_victory_grids = [create_tile_grid(bit, pal, 90, 40, tile_height=78, tile_width=64) for _ in range(4)]
    append_to_group(digimon_victory_grids)

# Function to set up Digimon attack A animation
def setup_digimon_attack_a_animation():
    global digimon_attack_a_grids
    bit, pal = load_animation_frames("/Greymon/dmonattacka.bmp")
    digimon_attack_a_grids = [create_tile_grid(bit, pal, 90, 40, tile_height=76, tile_width=64) for _ in range(3)]
    append_to_group(digimon_attack_a_grids)

# Function to set up Digimon attack B animation
def setup_digimon_attack_b_animation():
    bit, pal = load_animation_frames("/Greymon/dmonattackb.bmp")
    digimon_attack_b_grids = [create_tile_grid(bit, pal, 20, 40, tile_height=80, tile_width=64) for _ in range(3)]
    append_to_group(digimon_attack_b_grids)

# Function to display animations
def display_animation():
    display.root_group = group
    display.show(group)
    
# Function to move Digimon to the left
def move_digimon_left():
    global current_frame, digimon_walk_grids, digimon_idle_grids
    #del digimon_idle_grids
    #setup_digimon_walk_animation()
    
    for _ in range(35):  # Adjust the number of movements
        for grid in digimon_walk_grids:
            if grid.x > -8:  # Adjust the limit to stop the movement
                grid.x -= 3  # Adjust the movement speed
                grid[0] = current_frame  # Display the current frame
        time.sleep(0.05)  # Adjust this delay according to your animation speed
        current_frame = (current_frame + 1) % len(digimon_frames)  # Cycle through frames
    #del digimon_walk_grids
        
# Function to move Digimon to the right
def move_digimon_right():
    global current_frame, digimon_walk_grids, digimon_idle_grids
    #del digimon_idle_grids
    #setup_digimon_walk_animation()
    
    for _ in range(35):  # Adjust the number of movements
        for grid in digimon_walk_grids:
            if grid.x < 160:  # Adjust the limit to stop the movement
                grid.x += 3  # Adjust the movement speed
                grid[0] = current_frame  # Display the current frame
        time.sleep(0.05)  # Adjust this delay according to your animation speed
        current_frame = (current_frame + 1) % len(digimon_frames)  # Cycle through frames
    #del digimon_walk_grids

# Function to move Digimon to the left
def move_digimon_idle():
    global current_frame, digimon_walk_grids, digimon_idle_grids
    #del digimon_walk_grids
    setup_digimon_idle_animation()
    
    for grid in digimon_idle_grids:
        grid[0] = digimon_frames[current_frame]

    time.sleep(0.2)  # Adjust this delay according to your animation speed
    current_frame = (current_frame + 1) % len(digimon_frames)
    #del digimon_idle_grids


# Setting up Digimon animations

#setup_digimon_idle_animation()
setup_digimon_walk_animation()
#setup_digimon_sleep_animation()
#setup_digimon_victory_animation()
#setup_digimon_attack_a_animation()
#setup_digimon_attack_b_animation()

# Displaying the animations
display_animation()


# Animation frames for Digimon
digimon_frames = [0, 1, 2, 3]  # Change these to represent your frames
# Animation frames for Digimon
#digimon_Attack_frames = [0, 1, 2]  # Change these to represent your frames

current_frame = 0
while True:
    move_digimon_left()
    #move_digimon_idle()
    move_digimon_right()
    time.sleep(0.2)  # Adjust this delay according to your animation speed

