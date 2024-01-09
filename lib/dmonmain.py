import board
import busio
import displayio
import terminalio
import time
from adafruit_st7735r import ST7735R
from digitalio import DigitalInOut, Direction, Pull
from adafruit_button import Button
from random import randint
import gc
import adafruit_imageload

gc.collect()
gc.enable()
start_mem = gc.mem_free()
print("Point 1 Available memory: {} bytes".format(start_mem))

# Pin configuration
pins = {
    "mosi": board.GP11,
    "clk": board.GP10,
    "reset": board.GP12,
    "cs": board.GP9,
    "dc": board.GP8,
    "key0": board.GP15,
    "key1": board.GP17,
    "key2": board.GP2,
    "key3": board.GP3
}
screen_width = 168
screen_height = 132

displayio.release_displays()

spi = busio.SPI(clock=pins["clk"], MOSI=pins["mosi"])
display_bus = displayio.FourWire(spi, command=pins["dc"], chip_select=pins["cs"], reset=pins["reset"])
display = ST7735R(display_bus, width=screen_width, height=screen_height, rotation=-90, bgr=False)

switch = DigitalInOut(pins["key0"])
switch.direction = Direction.INPUT
switch.pull = Pull.DOWN

# Button dimensions and colors
TAB_BUTTON_Y = 0
TAB_BUTTON_HEIGHT = 16
TAB_BUTTON_WIDTH = int(screen_width / 6)
TAB_DN_BUTTON_HEIGHT = 16
TAB_DN_BUTTON_WIDTH = int(screen_width / 6)
TAB_DN_BUTTON_Y = 100

# ---------- Display Buttons ------------- #
# Create buttons using a loop
buttons = []
button_labels = ["View 1", "View 2", "View 3", "View 4", "View 5"]

for i, label in enumerate(button_labels):
    new_button = Button(
        x=TAB_BUTTON_WIDTH * i,
        y=0 if i < 3 else TAB_DN_BUTTON_Y,
        width=TAB_BUTTON_WIDTH if i < 3 else TAB_DN_BUTTON_WIDTH,
        height=TAB_BUTTON_HEIGHT if i < 3 else TAB_DN_BUTTON_HEIGHT,
        label=label,
        label_font=terminalio.FONT,
        label_color=0xFF7E00,
        fill_color=0x5C5B5C,
        outline_color=0x767676,
        selected_fill=0x1A1A1A,
        selected_outline=0x2E2E2E,
        selected_label=0x525252,
    )
    buttons.append(new_button)
# ------------- Functions ------------- #
# Set visibility of layer
def layerVisibility(state, layer, target):
    try:
        if state == "show":
            time.sleep(0.1)
            layer.append(target)
        elif state == "hide":
            layer.remove(target)
    except ValueError:
        pass

# This will handle switching Images and Icons
def set_image(group, filename, x_pos, y_pos, t_height, t_width):
    """Set the image file for a given goup for display.
    This is most useful for Icons or image slideshows.
        :param group: The chosen group
        :param filename: The filename of the chosen image
    """
    if group:
        group.pop()

    if not filename:
        return  # we're done, no icon desired
    
    
    if filename == "/Background/registerjungle.bmp":
        image = displayio.OnDiskBitmap(filename)
        print("Background")
        tile_grids = displayio.TileGrid(image, pixel_shader=image.pixel_shader)
        group.append(tile_grids)
        splash.append(group)
    else:
        image = displayio.OnDiskBitmap(open(filename, "rb"))
        pal = image.pixel_shader
        pal.make_transparent(0)
        print("otro file")
        tile_grids = [create_tile_grid(image, pal, x_pos, y_pos, tile_height=t_height, tile_width=t_width) for _ in range(4)]
        
        for grid in tile_grids:
            group.append(grid) 
    
    return tile_grids

# Function to create TileGrids
def create_tile_grid(bitmap, palette, x_pos, y_pos, width=1, height=1, tile_height=64, tile_width=64, default_tile=0):
    return displayio.TileGrid(bitmap, pixel_shader=palette, width=width, height=height,
                              tile_height=tile_height, tile_width=tile_width, default_tile=default_tile,
                              x=x_pos, y=y_pos)

# Function to display animations
def display_bg():
    display.root_group = splash

def display_animation(group):
    try:
        splash.append(group)
          
    except ValueError:
        pass
    
def destroy_animation(group):
    try:
        for _ in range(len(group) - 1):
            group.pop()
        
        splash.pop()
        
    except ValueError:
        pass

# Function to move Digimon to the left
def move_digimon_left():
    global current_frame, global_position
    
    digimon_walk_grids = set_image(walk_group, "/Greymon/dmonwalk.bmp", global_position, 35, 78, 62)
    display_animation(walk_group)
    
    for _ in range(35):  # Adjust the number of movements
        for grid in digimon_walk_grids:
            if grid.x > 2:  # Adjust the limit to stop the movement
                grid.x -= 3  # Adjust the movement speed
                grid[0] = current_frame  # Display the current frame
                global_position = grid.x
        time.sleep(0.05)  # Adjust this delay according to your animation speed
        current_frame = (current_frame + 1) % len(digimon_frames)  # Cycle through frames
    destroy_animation(walk_group)

# Function to move Digimon to the right
def move_digimon_right():
    global current_frame, global_position
    digimon_walk_grids = set_image(walk_group, "/Greymon/dmonwalk.bmp", global_position, 35, 78, 62)
    display_animation(walk_group)
    
    for _ in range(40):  # Adjust the number of movements
        for grid in digimon_walk_grids:
            if grid.x < 70:  # Adjust the limit to stop the movement
                grid.x += 3  # Adjust the movement speed
                grid[0] = current_frame  # Display the current frame
                global_position = grid.x 
        time.sleep(0.05)  # Adjust this delay according to your animation speed
        current_frame = (current_frame + 1) % len(digimon_frames)  # Cycle through frames
    destroy_animation(walk_group)
    
# Function to move Digimon to Idle
def move_digimon_idle():
    global current_frame, global_position
    
    digimon_idle_grids = set_image(idle_group, "/Greymon/dmonidle.bmp", global_position, 35, 78, 64)
    display_animation(idle_group)
    
    for _ in range(40):  # Adjust the number of movements
        for grid in digimon_idle_grids:
            grid[0] = current_frame  # Display the current frame
        time.sleep(0.05)  # Adjust this delay according to your animation speed
        current_frame = (current_frame + 1) % len(digimon_frames)  # Cycle through frames   
    destroy_animation(idle_group)
    
# Function to move Digimon to Idle
def move_digimon_sleep():
    global current_frame, global_position
    
    digimon_sleep_grids = set_image(sleep_group, "/Greymon/dmonsleep.bmp", global_position, 60, 50, 64)
    display_animation(sleep_group)
    
    for _ in range(40):  # Adjust the number of movements
        for grid in digimon_sleep_grids:
            grid[0] = current_frame  # Display the current frame
        time.sleep(0.5)  # Adjust this delay according to your animation speed
        current_frame = (current_frame + 1) % len(digimon_frames)  # Cycle through frames   
    destroy_animation(sleep_group)
    
    # Function to move Digimon to Idle
def move_digimon_victory():
    global current_frame, global_position
    
    digimon_victory_grids = set_image(victory_group, "/Greymon/dmonvictory.bmp", global_position, 35, 78, 64)
    display_animation(victory_group)
    
    for _ in range(40):  # Adjust the number of movements
        for grid in digimon_victory_grids:
            grid[0] = current_frame  # Display the current frame
        time.sleep(0.05)  # Adjust this delay according to your animation speed
        current_frame = (current_frame + 1) % len(digimon_frames)  # Cycle through frames   
    destroy_animation(victory_group)
    
# Function main Screen Moves
def move_main_screen():
    random_number = randint(1, 5)  # Generate a random number between 1 and 5

    if random_number == 1:
        move_digimon_left()
    elif random_number == 2:
        move_digimon_idle()
    elif random_number == 3:
        move_digimon_sleep()
    elif random_number == 4:
        move_digimon_victory()
    else:
        move_digimon_right()

# ------------- Display Groups ------------- #
splash = displayio.Group()  # The Main Display Group
idle_group = displayio.Group()  # Group for idle sprites
walk_group = displayio.Group()  # Group for walk sprites
sleep_group = displayio.Group()  # Group for sleep sprites
victory_group = displayio.Group()  # Group for victory sprites

# ------------- Display Menus ------------- #
View_Menu1 = displayio.Group()  # The Main Display Group
View_Menu2 = displayio.Group()  # Group for idle sprites
View_Menu3 = displayio.Group()  # Group for idle sprites
View_Menu4 = displayio.Group()  # Group for idle sprites
View_Menu5 = displayio.Group()  # Group for idle sprites

# ------------- Setup for Images ------------- #
bg_group = displayio.Group()  # Group for background sprites
display.root_group = splash
set_image(bg_group, "/Background/registerjungle.bmp",0,0,0,0)

# Add all of the main buttons to the splash Group
for b in buttons:
    splash.append(b)

digimon_frames = [0, 1, 2, 3]
current_frame = 0
global_position = 40

# Set veriables and startup states
#button_view1.selected = True
#button_view2.selected = False
#button_view3.selected = False


gc.collect()
end_mem = gc.mem_free()

print("Point 2 Available memory: {} bytes".format(end_mem))
print("Code section 1-2 used {} bytes".format(start_mem - end_mem))

while True:
    gc.collect()
    start_mem = gc.mem_free()
    print( "Point 3 Available memory: {} bytes".format(start_mem) )



    move_main_screen()
    if switch.value:
        print("key presionado")
    time.sleep(0.2)  # Adjust this delay according to your animation speed
    
    
    gc.collect()
    end_mem = gc.mem_free()

    print( "Point 4 Available memory: {} bytes".format(end_mem) )
    print( "Code section 3-4 used {} bytes".format(start_mem - end_mem) )



