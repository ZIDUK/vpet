import board
import busio
import displayio
import terminalio
import asyncio
import time
from adafruit_st7735r import ST7735R
from digitalio import DigitalInOut, Direction, Pull
from adafruit_button import Button
from adafruit_debouncer import Debouncer
from random import randint
import gc
import adafruit_imageload
from adafruit_display_shapes.rect import Rect
from adafruit_display_text.label import Label
from adafruit_button.sprite_button import SpriteButton

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
view_live = 0
view_option = 0
view_screen = 0
displayio.release_displays()

spi = busio.SPI(clock=pins["clk"], MOSI=pins["mosi"])
display_bus = displayio.FourWire(spi, command=pins["dc"], chip_select=pins["cs"], reset=pins["reset"])
display = ST7735R(display_bus, width=screen_width, height=screen_height, rotation=-90, bgr=False)



switch0 = DigitalInOut(pins["key0"])
switch0.direction = Direction.INPUT
switch0.pull = Pull.UP
button0 = Debouncer(switch0)

switch1 = DigitalInOut(pins["key1"])
switch1.direction = Direction.INPUT
switch1.pull = Pull.UP
button1 = Debouncer(switch1)

switch2 = DigitalInOut(pins["key2"])
switch2.direction = Direction.INPUT
switch2.pull = Pull.UP
button2 = Debouncer(switch2)

# ---------- Display Root Screen Options  ------------- #

topBar = Rect(0, 0, 168, 18, fill=0x8fa68c)
bottomBar = Rect(0, 114, 168, 18, fill=0x8fa68c)

# ---------- Display Screens Status View ------------- #

status_Screen1 = Rect(0, 15, 168, 100, fill=0x8fa68c)
status_Screen2 = Rect(0, 15, 168, 100, fill=0x8fa68c)
status_Screen3 = Rect(0, 15, 168, 100, fill=0x8fa68c)

lb_Hungry = Label(terminalio.FONT, text="HUNGRY", color=0x000000)
lb_Hungry.x = 10
lb_Hungry.y = 70

lb_Strength = Label(terminalio.FONT, text="STRENGTH", color=0x000000)
lb_Strength.x = 10
lb_Strength.y = 30

lb_Effort = Label(terminalio.FONT, text="EFFORT", color=0x000000)
lb_Effort.x = 10
lb_Effort.y = 70

lb_Dp = Label(terminalio.FONT, text="DP", color=0x000000)
lb_Dp.x = 10
lb_Dp.y = 30


# ---------- Display Screens Eating View ------------- #


eating_Screen = Rect(0, 15, 168, 100, fill=0x8fa68c)

lb_meat = Label(terminalio.FONT, text="MEAT", color=0x000000)
lb_meat.x = 80
lb_meat.y = 50

lb_pill = Label(terminalio.FONT, text="PILL", color=0x000000)
lb_pill.x = 80
lb_pill.y = 95

lb_weigth = Label(terminalio.FONT, text="Age", color=0x000000)
lb_weigth.x = 80
lb_weigth.y = 50

lb_age = Label(terminalio.FONT, text="Weigth", color=0x000000)
lb_age.x = 80
lb_age.y = 95


# ---------- Display Buttons ------------- #

# We want three buttons across the top of the screen
TAB_BUTTON_Y = 0
TAB_BUTTON_HEIGHT = 18
TAB_BUTTON_WIDTH = int(screen_width / 5.5)

# We want two big buttons at the bottom of the screen
TAB_DN_BUTTON_Y = 114
TAB_DN_BUTTON_HEIGHT = 18
TAB_DN_BUTTON_WIDTH = int(screen_width / 5.5)


# This group will make it easy for us to read a button press later.
buttons = []
eatingButtons = []


# Main User Interface Buttons
btn_stats_view = SpriteButton(
    x=0,  # Start at furthest left
    y=0,  # Start at top
    width=TAB_BUTTON_WIDTH,  # Calculated width
    height=TAB_BUTTON_HEIGHT,  # Static height
    label_font=terminalio.FONT,
    bmp_path="icons/statb2.bmp",
    selected_bmp_path="icons/statb1.bmp",
    transparent_index=0,
)
buttons.append(btn_stats_view)  # adding this button to the buttons group

btn_eat_view = SpriteButton(
    x=TAB_BUTTON_WIDTH,  # Start after width of a button
    y=0,
    width=TAB_BUTTON_WIDTH,  # Calculated width
    height=TAB_BUTTON_HEIGHT,  # Static height
    label_font=terminalio.FONT,
    bmp_path="icons/eat2.bmp",
    selected_bmp_path="icons/eat1.bmp",
    transparent_index=0,
)
buttons.append(btn_eat_view)  # adding this button to the buttons group

btn_training_view = SpriteButton(
    x=TAB_BUTTON_WIDTH * 2,  # Start after width of 2 buttons
    y=0,
    width=TAB_BUTTON_WIDTH,  # Calculated width
    height=TAB_BUTTON_HEIGHT,  # Static height
    label_font=terminalio.FONT,
    bmp_path="icons/training2.bmp",
    selected_bmp_path="icons/training1.bmp",
    transparent_index=0,
)
buttons.append(btn_training_view)  # adding this button to the buttons group

btn_battle_view = SpriteButton(
    x=TAB_BUTTON_WIDTH * 3,  # Start after width of 3 buttons
    y=0,
    width=TAB_BUTTON_WIDTH,  # Calculated width
    height=TAB_BUTTON_HEIGHT,  # Static height
    label_font=terminalio.FONT,
    bmp_path="icons/battle2.bmp",
    selected_bmp_path="icons/battle1.bmp",
    transparent_index=0,
)
buttons.append(btn_battle_view)  # adding this button to the buttons group

btn_poop_view = SpriteButton(
    x=0,  
    y=TAB_DN_BUTTON_Y,
    width=TAB_DN_BUTTON_WIDTH,  # Calculated width
    height=TAB_DN_BUTTON_HEIGHT,  # Static height
    label_font=terminalio.FONT,
    bmp_path="icons/poop2.bmp",
    selected_bmp_path="icons/poop1.bmp",
    transparent_index=0,
)
buttons.append(btn_poop_view)  # adding this button to the buttons group

btn_light_view = SpriteButton(
    x=TAB_DN_BUTTON_WIDTH,  
    y=TAB_DN_BUTTON_Y,
    width=TAB_DN_BUTTON_WIDTH,  # Calculated width
    height=TAB_DN_BUTTON_HEIGHT,  # Static height
    label_font=terminalio.FONT,
    bmp_path="icons/light2.bmp",
    selected_bmp_path="icons/light1.bmp",
    transparent_index=0,
)
buttons.append(btn_light_view)  # adding this button to the buttons group

btn_band_view = SpriteButton(
    x=TAB_DN_BUTTON_WIDTH * 2,  # Start after width of 2 buttons
    y=TAB_DN_BUTTON_Y,
    width=TAB_DN_BUTTON_WIDTH,  # Calculated width
    height=TAB_DN_BUTTON_HEIGHT,  # Static height
    label_font=terminalio.FONT,
    bmp_path="icons/band2.bmp",
    selected_bmp_path="icons/band1.bmp",
    transparent_index=0,
)
buttons.append(btn_band_view)  # adding this button to the buttons group

btn_callout_view = SpriteButton(
    x=TAB_DN_BUTTON_WIDTH * 3,  # Start after width of 3 buttons
    y=TAB_DN_BUTTON_Y,
    width=TAB_DN_BUTTON_WIDTH,  # Calculated width
    height=TAB_DN_BUTTON_HEIGHT,  # Static height
    label_font=terminalio.FONT,
    bmp_path="icons/call2.bmp",
    selected_bmp_path="icons/call1.bmp",
    transparent_index=0,
)
buttons.append(btn_callout_view)  # adding this button to the buttons group

Eating1Button = SpriteButton(  
    x=15,  
    y=40,
    width=24,  
    height=24,  
    label_font=terminalio.FONT,
    bmp_path="icons/transarrow.bmp",
    selected_bmp_path="icons/arrow.bmp",
    transparent_index=0,
)
eatingButtons.append(Eating1Button)

Eating2Button = SpriteButton(
    x=15,  
    y=80,
    width=24,  
    height=24,  
    label_font=terminalio.FONT,
    bmp_path="icons/transarrow.bmp",
    selected_bmp_path="icons/arrow.bmp",
    transparent_index=0,
)
eatingButtons.append(Eating2Button)

def switch_stats_screen(what_screen):
    print("entrando a screens")
    global view_screen
    if what_screen == 1:
        layerVisibility("show", Stats_View, v_stats_screen1_group)
        layerVisibility("hide", Stats_View, v_stats_screen2_group)
        layerVisibility("hide", Stats_View, v_stats_screen3_group)
    elif what_screen == 2:
        layerVisibility("hide", Stats_View, v_stats_screen1_group)
        layerVisibility("show", Stats_View, v_stats_screen2_group)
        layerVisibility("hide", Stats_View, v_stats_screen3_group)
    elif what_screen == 3:
        layerVisibility("hide", Stats_View, v_stats_screen1_group)
        layerVisibility("hide", Stats_View, v_stats_screen2_group)
        layerVisibility("show", Stats_View, v_stats_screen3_group)
    # Set global button state
    view_screen = what_screen
    print("screen {option_num:.0f} On".format(option_num=what_screen))


def switch_option(what_option):
    global view_option
    if what_option == 1:
        Eating1Button.selected = True
        Eating2Button.selected = False
    elif what_option == 2:
        Eating1Button.selected = False
        Eating2Button.selected = True
        
    # Set global button state
    view_option = what_option
    print("Option {option_num:.0f} On".format(option_num=what_option))

def switch_view(what_view):
    global view_live
    if what_view == 1:
        btn_stats_view.selected = True
        btn_eat_view.selected = False
        btn_training_view.selected = False
        btn_battle_view.selected = False
        btn_poop_view.selected = False
        btn_light_view.selected = False        
        btn_band_view.selected = False        
        btn_callout_view.selected = False
        
        layerVisibility("show", splash, Stats_View)
        layerVisibility("hide", splash, Eating_View)
        layerVisibility("hide", splash, Training_View)
        layerVisibility("hide", splash, Battle_View)
        layerVisibility("hide", splash, Poop_View)
        layerVisibility("hide", splash, Light_View)
        layerVisibility("hide", splash, Bandage_View)
        layerVisibility("hide", splash, Callout_View)
    elif what_view == 2:
        btn_stats_view.selected = False
        btn_eat_view.selected = True
        btn_training_view.selected = False
        btn_battle_view.selected = False
        btn_poop_view.selected = False
        btn_light_view.selected = False        
        btn_band_view.selected = False        
        btn_callout_view.selected = False
        layerVisibility("hide", splash, Stats_View)
        layerVisibility("show", splash, Eating_View)
        layerVisibility("hide", splash, Training_View)
        layerVisibility("hide", splash, Battle_View)
        layerVisibility("hide", splash, Poop_View)
        layerVisibility("hide", splash, Light_View)
        layerVisibility("hide", splash, Bandage_View)
        layerVisibility("hide", splash, Callout_View)
    elif what_view == 3:
        btn_stats_view.selected = False
        btn_eat_view.selected = False
        btn_training_view.selected = True
        btn_battle_view.selected = False
        btn_poop_view.selected = False
        btn_light_view.selected = False        
        btn_band_view.selected = False        
        btn_callout_view.selected = False
        layerVisibility("hide", splash, Stats_View)
        layerVisibility("hide", splash, Eating_View)
        layerVisibility("show", splash, Training_View)
        layerVisibility("hide", splash, Battle_View)
        layerVisibility("hide", splash, Poop_View)
        layerVisibility("hide", splash, Light_View)
        layerVisibility("hide", splash, Bandage_View)
        layerVisibility("hide", splash, Callout_View)
    elif what_view == 4:
        btn_stats_view.selected = False
        btn_eat_view.selected = False
        btn_training_view.selected = False
        btn_battle_view.selected = True
        btn_poop_view.selected = False
        btn_light_view.selected = False        
        btn_band_view.selected = False        
        btn_callout_view.selected = False
        layerVisibility("hide", splash, Stats_View)
        layerVisibility("hide", splash, Eating_View)
        layerVisibility("hide", splash, Training_View)
        layerVisibility("show", splash, Battle_View)
        layerVisibility("hide", splash, Poop_View)
        layerVisibility("hide", splash, Light_View)
        layerVisibility("hide", splash, Bandage_View)
        layerVisibility("hide", splash, Callout_View)
    elif what_view == 5:
        btn_stats_view.selected = False
        btn_eat_view.selected = False
        btn_training_view.selected = False
        btn_battle_view.selected = False
        btn_poop_view.selected = True
        btn_light_view.selected = False        
        btn_band_view.selected = False        
        btn_callout_view.selected = False
        layerVisibility("hide", splash, Stats_View)
        layerVisibility("hide", splash, Eating_View)
        layerVisibility("hide", splash, Training_View)
        layerVisibility("hide", splash, Battle_View)
        layerVisibility("show", splash, Poop_View)
        layerVisibility("hide", splash, Light_View)
        layerVisibility("hide", splash, Bandage_View)
        layerVisibility("hide", splash, Callout_View)
    elif what_view == 6:
        btn_stats_view.selected = False
        btn_eat_view.selected = False
        btn_training_view.selected = False
        btn_battle_view.selected = False
        btn_poop_view.selected = False
        btn_light_view.selected = True        
        btn_band_view.selected = False        
        btn_callout_view.selected = False
        layerVisibility("hide", splash, Stats_View)
        layerVisibility("hide", splash, Eating_View)
        layerVisibility("hide", splash, Training_View)
        layerVisibility("hide", splash, Battle_View)
        layerVisibility("show", splash, Poop_View)
        layerVisibility("hide", splash, Light_View)
        layerVisibility("hide", splash, Bandage_View)
        layerVisibility("hide", splash, Callout_View)
    elif what_view == 7:
        btn_stats_view.selected = False
        btn_eat_view.selected = False
        btn_training_view.selected = False
        btn_battle_view.selected = False
        btn_poop_view.selected = False
        btn_light_view.selected = False        
        btn_band_view.selected = True        
        btn_callout_view.selected = False
        layerVisibility("hide", splash, Stats_View)
        layerVisibility("hide", splash, Eating_View)
        layerVisibility("hide", splash, Training_View)
        layerVisibility("hide", splash, Battle_View)
        layerVisibility("show", splash, Poop_View)
        layerVisibility("hide", splash, Light_View)
        layerVisibility("hide", splash, Bandage_View)
        layerVisibility("hide", splash, Callout_View)
    else:
        btn_stats_view.selected = False
        btn_eat_view.selected = False
        btn_training_view.selected = False
        btn_battle_view.selected = False
        btn_poop_view.selected = False
        btn_light_view.selected = False        
        btn_band_view.selected = False        
        btn_callout_view.selected = True
        layerVisibility("hide", splash, Stats_View)
        layerVisibility("hide", splash, Eating_View)
        layerVisibility("hide", splash, Training_View)
        layerVisibility("hide", splash, Battle_View)
        layerVisibility("hide", splash, Poop_View)
        layerVisibility("show", splash, Light_View)
        layerVisibility("hide", splash, Bandage_View)
        layerVisibility("hide", splash, Callout_View)

    # Set global button state
    view_live = what_view
    print("View {view_num:.0f} On".format(view_num=what_view))
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

def set_eating_screen():
    v_eating_screen_group.append(eating_Screen)
    for b in eatingButtons:
        v_eating_screen_group.append(b)
     
    meat = displayio.OnDiskBitmap("/icons/meat.bmp")
    pal_meat = meat.pixel_shader
    pal_meat.make_transparent(0)
    meat_tile = displayio.TileGrid(meat, pixel_shader=meat.pixel_shader, x=40,y=40)
    v_eating_screen_group.append(meat_tile)
    
    
    pill = displayio.OnDiskBitmap("/icons/pill.bmp")
    pal_pill = pill.pixel_shader
    pal_pill.make_transparent(0)
    pill_tile = displayio.TileGrid(pill, pixel_shader=pill.pixel_shader, x=40,y=80)
    v_eating_screen_group.append(pill_tile)
    
    v_eating_screen_group.append(lb_meat)
    v_eating_screen_group.append(lb_pill)
    
    Eating_View.append(v_eating_screen_group)
    
    
def set_stats_screens():
    
    v_stats_screen1_group.append(status_Screen1)
    v_stats_screen1_group.append(lb_age)
    v_stats_screen1_group.append(lb_weigth)
    
    statuswa = displayio.OnDiskBitmap("/icons/statuswa.bmp")
    pal_wa = statuswa.pixel_shader
    pal_wa.make_transparent(0)
    statuswa_tile = displayio.TileGrid(statuswa, pixel_shader=statuswa.pixel_shader, x=5,y=50)
    v_stats_screen1_group.append(statuswa_tile)
        
    
    v_stats_screen2_group.append(status_Screen2)
    v_stats_screen2_group.append(lb_Hungry)
    v_stats_screen2_group.append(lb_Strength)
    
    
    hungry_h = displayio.OnDiskBitmap("/icons/heartf.bmp")
    pal_h = hungry_h.pixel_shader
    pal_h.make_transparent(0)
    
    hungry_tile = displayio.TileGrid(hungry_h, pixel_shader=hungry_h.pixel_shader, x=5,y=80)
    v_stats_screen2_group.append(hungry_tile)
    
    
    strength_h = displayio.OnDiskBitmap("/icons/hearte.bmp")
    pal_s = strength_h.pixel_shader
    pal_s.make_transparent(0)

    
    strength_tile = displayio.TileGrid(strength_h, pixel_shader=strength_h.pixel_shader, x=5,y=35)
    v_stats_screen2_group.append(strength_tile)
    
        
    v_stats_screen3_group.append(status_Screen3)
    v_stats_screen3_group.append(lb_Effort)
    v_stats_screen3_group.append(lb_Dp)
    
    effort_h = displayio.OnDiskBitmap("/icons/heartf.bmp")
    pal_e = effort_h.pixel_shader
    pal_e.make_transparent(0)
    effort_tile = displayio.TileGrid(effort_h, pixel_shader=effort_h.pixel_shader, x=5,y=80)
    v_stats_screen3_group.append(effort_tile)
    
    dp_h = displayio.OnDiskBitmap("/icons/hearte.bmp")
    pal_d = dp_h.pixel_shader
    pal_d.make_transparent(0)
    dp_tile = displayio.TileGrid(dp_h, pixel_shader=dp_h.pixel_shader, x=5,y=35)
    v_stats_screen3_group.append(dp_tile)

    
# This will handle switching Images and Icons
def set_image(group, filename, x_pos, y_pos, t_height, t_width):

    if group:
        group.pop()

    if not filename:
        return  # we're done, no icon desired
     
    if filename == "/Background/registerjungle.bmp":
        image = displayio.OnDiskBitmap(filename)
        tile_grids = displayio.TileGrid(image, pixel_shader=image.pixel_shader)
        group.append(tile_grids)
        splash.append(group)
        splash.append(topBar)
        splash.append(bottomBar)
    else:
        image = displayio.OnDiskBitmap(open(filename, "rb"))
        pal = image.pixel_shader
        pal.make_transparent(0)
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

def display_screens(screen):
    try:
        Stats_View.append(screen)
          
    except ValueError:
        pass
 
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

# Function to move Digimon to Eating Meat
async def move_digimon_eatmeat():
    global current_frame, global_position
    
    digimon_eatmeat_grids = set_image(eatmeat_group, "/Greymon/dmoneatmeat.bmp", global_position, 35, 78, 64)
    display_animation(eatmeat_group)
    
    for _ in range(4):  # Adjust the number of movements
       
        for grid in digimon_eatmeat_grids:               
            grid[0] = current_frame  # Display the current frame
        await asyncio.sleep_ms(250)
        current_frame = (current_frame + 1) % len(digimon_frames)  # Cycle through frames
    destroy_animation(eatmeat_group)


# Function to move Digimon to the left
async def move_digimon_left():
    global current_frame, global_position
    
    digimon_walk_grids = set_image(walk_group, "/Greymon/dmonwalk.bmp", global_position, 35, 78, 62)
    display_animation(walk_group)
    
    for _ in range(10):  # Adjust the number of movements
        for grid in digimon_walk_grids:
            
            if grid.x > 2:  # Adjust the limit to stop the movement
                grid.x -= 3  # Adjust the movement speed
                grid[0] = current_frame  # Display the current frame
                global_position = grid.x
        await asyncio.sleep_ms(250)
        current_frame = (current_frame + 1) % len(digimon_frames)  # Cycle through frames
               
    destroy_animation(walk_group)

# Function to move Digimon to the right
async def move_digimon_right():
    global current_frame, global_position
    digimon_walk_grids = set_image(walk_group, "/Greymon/dmonwalk.bmp", global_position, 35, 78, 62)
    display_animation(walk_group)
    
    for _ in range(10):  # Adjust the number of movements
        for grid in digimon_walk_grids:
            
            if grid.x < 70:  # Adjust the limit to stop the movement
                grid.x += 3  # Adjust the movement speed
                grid[0] = current_frame  # Display the current frame
                global_position = grid.x 
        await asyncio.sleep_ms(250)
        current_frame = (current_frame + 1) % len(digimon_frames)  # Cycle through frames
               
    destroy_animation(walk_group)
    
# Function to move Digimon to Idle
async def move_digimon_idle():
    global current_frame, global_position
    
    digimon_idle_grids = set_image(idle_group, "/Greymon/dmonidle.bmp", global_position, 35, 78, 64)
    display_animation(idle_group)
    
    for _ in range(4):  # Adjust the number of movements
       
        for grid in digimon_idle_grids:               
            grid[0] = current_frame  # Display the current frame
        await asyncio.sleep_ms(250)
        current_frame = (current_frame + 1) % len(digimon_frames)  # Cycle through frames
    destroy_animation(idle_group)
    
# Function to move Digimon to Idle
async def move_digimon_sleep():
    global current_frame, global_position
    
    digimon_sleep_grids = set_image(sleep_group, "/Greymon/dmonsleep.bmp", global_position, 60, 50, 64)
    display_animation(sleep_group)
    
    for _ in range(40):  # Adjust the number of movements
        for grid in digimon_sleep_grids:
            grid[0] = current_frame  # Display the current frame
        await asyncio.sleep_ms(100)
        current_frame = (current_frame + 1) % len(digimon_frames)  # Cycle through frames
    destroy_animation(sleep_group)
    
    # Function to move Digimon to Idle
async def move_digimon_victory():
    global current_frame, global_position
    
    digimon_victory_grids = set_image(victory_group, "/Greymon/dmonvictory.bmp", global_position, 35, 78, 64)
    display_animation(victory_group)
    
    for _ in range(4):  # Adjust the number of movements
        for grid in digimon_victory_grids:
            grid[0] = current_frame  # Display the current frame
        await asyncio.sleep_ms(250)
        current_frame = (current_frame + 1) % len(digimon_frames)  # Cycle through frames
    destroy_animation(victory_group)
    
# Function main Screen Moves
async def move_main_screen():
    while True:
     
        random_number = randint(1, 6)  # Generate a random number between 1 and 5
 
        if random_number == 1:
           await move_digimon_left()       
        elif random_number == 2:
           await move_digimon_idle()  
        elif random_number == 3:
           await move_digimon_sleep()  
        elif random_number == 4:
           await move_digimon_victory()
        elif random_number == 5:
          await move_digimon_eatmeat()
           
        else:
           await move_digimon_right()
        
async def key_manipulation(button0, button1, button2):
    print("entrando a botones")
    flag = True
    while True:
        button0.update()
        button1.update()
        button2.update()
        global view_live
        global view_option
        global view_screen
            
        if button0.fell:
            print("button1")
            flag = False
            view_live = view_live + 1
            for i, b in enumerate(buttons):                 
                if view_live == 1:
                    switch_view(view_live)
                    view_option=0
                    break
                if view_live == 2:
                    switch_view(view_live)
                    break
                if view_live == 3:
                    switch_view(view_live)
                    break
                if view_live == 4:
                    switch_view(view_live)
                    break
                if view_live == 5:
                    switch_view(view_live)
                    break
                if view_live == 6:
                    switch_view(view_live)
                    break
                if view_live == 7:
                    switch_view(view_live)
                    break
                if view_live == 8:
                    switch_view(view_live)
                    view_live = 0
                    break
                
        if button1.fell:  # Check if button was pressed and not already registered
            print("option {view_num:.0f} ".format(view_num=view_option))
            view_option = view_option + 1     
                
            if view_live == 1:
                view_screen = view_screen + 1
                if view_screen == 1:
                    switch_stats_screen(view_screen)
                    
                if view_screen == 2:
                    switch_stats_screen(view_screen)
                    
                if view_screen == 3:
                    switch_stats_screen(view_screen)
                    view_screen = 0
                    
    
            elif view_live == 2:
                    
                for i, b in enumerate(eatingButtons):
                        if view_option == 1:
                            switch_option(view_option)                
                            break
                        if view_option == 2:
                            switch_option(view_option)
                            view_option = 0
                            break
                    
        if button2.fell:
            view_live = 0
            btn_stats_view.selected = False
            btn_eat_view.selected = False
            btn_training_view.selected = False
            btn_light_view.selected = False
            btn_poop_view.selected = False
            btn_band_view.selected = False
            btn_battle_view.selected = False
            btn_callout_view.selected = False

            layerVisibility("hide", splash, Stats_View)
            layerVisibility("hide", splash, Eating_View)
            layerVisibility("hide", splash, Training_View)
            layerVisibility("hide", splash, Battle_View)
            layerVisibility("hide", splash, Poop_View)
            layerVisibility("hide", splash, Light_View)
            layerVisibility("hide", splash, Bandage_View)
            layerVisibility("hide", splash, Callout_View)
            
            flag = True
            
        if flag == True:
            await asyncio.sleep_ms(0)
    
            
# ------------- Display Groups ------------- #
splash = displayio.Group()  # The Main Display Group

idle_group = displayio.Group()  # Group for idle sprites
walk_group = displayio.Group()  # Group for walk sprites
eatmeat_group = displayio.Group()  # Group for eat meat sprites
sleep_group = displayio.Group()  # Group for sleep sprites
victory_group = displayio.Group()  # Group for victory sprites

v_stats_screen1_group = displayio.Group()
v_stats_screen2_group = displayio.Group()
v_stats_screen3_group = displayio.Group()

v_eating_screen_group = displayio.Group()


# ------------- Display Menus ------------- #
Stats_View = displayio.Group()  # The Stats view Group
Eating_View = displayio.Group()  # Group for Eating view
Training_View = displayio.Group()  # Group for Training view
Battle_View = displayio.Group()  # Group for Battle view
Poop_View = displayio.Group()  # Group for Poop view
Light_View = displayio.Group()  # Group for Light view
Bandage_View = displayio.Group()  # Group for Bandage view
Callout_View = displayio.Group()  # Group for callout view


# ------------- Setup for Images ------------- #
bg_group = displayio.Group()  # Group for background sprites
display.root_group = splash
set_image(bg_group, "/Background/registerjungle.bmp",0,0,0,0)


# Add all of the main buttons to the splash Group
for b in buttons:
    splash.append(b)
    
set_eating_screen()
set_stats_screens()

digimon_frames = [0, 1, 2, 3]
current_frame = 0
global_position = 40

# Set veriables and startup states
btn_stats_view.selected = False
btn_eat_view.selected = False
btn_training_view.selected = False
btn_light_view.selected = False
btn_poop_view.selected = False
btn_band_view.selected = False
btn_battle_view.selected = False
btn_callout_view.selected = False
Eating1Button.selected = True


layerVisibility("hide", splash, Stats_View)
layerVisibility("hide", splash, Eating_View)
layerVisibility("hide", splash, Training_View)
layerVisibility("hide", splash, Battle_View)
layerVisibility("hide", splash, Poop_View)
layerVisibility("hide", splash, Light_View)
layerVisibility("hide", splash, Bandage_View)
layerVisibility("hide", splash, Callout_View)

gc.collect()
end_mem = gc.mem_free()

print("Point 2 Available memory: {} bytes".format(end_mem))
print("Code section 1-2 used {} bytes".format(start_mem - end_mem))

async def main():
    
    asyncio.create_task(move_main_screen())
    while True:
        await key_manipulation(button0, button1, button2)

asyncio.run(main())




