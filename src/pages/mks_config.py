"""
This module creates the MKS Servo Configuration page for the Arctos Robot GUI.
It allows the user to configure various settings for the MKS servo motors.
"""
from nicegui import ui
from services.mks_servo_can.mks_enums import Enable, Direction, EndStopLevel, WorkMode, HoldingStrength, EnPinEnable
import yaml
import os

# Define the path to the settings file
SETTINGS_FILE = os.path.join(os.path.dirname(__file__), '..', 'config', 'mks_settings.yaml')
SETTINGS_FILE = os.path.abspath(SETTINGS_FILE)


def load_servo_settings():
    """
    Loads the servo settings from the YAML settings file.

    If the settings file does not exist, it creates an empty one.

    Returns:
        dict: A dictionary containing the loaded servo settings.
    """
    if not os.path.exists(SETTINGS_FILE):
        # If the file doesn't exist, create an empty settings file
        with open(SETTINGS_FILE, 'w') as f:
            yaml.dump({}, f)
        return {}
    # Load settings from file
    with open(SETTINGS_FILE, 'r') as f:
        return yaml.safe_load(f) or {}

def save_servo_setting(index, key, value):
    """
    Saves a single servo setting to the settings file.

    Args:
        index (int): The index of the servo.
        key (str): The key of the setting to save.
        value: The value of the setting to save.

    Returns:
        None
    """
    # Load current settings
    data = load_servo_settings()
    # Create the servo key
    servo_key = f'servo_{index}'
    # Check if the servo_key exists, if not, create it
    if servo_key not in data:
        data[servo_key] = {}
    # Save enums as string names
    data[servo_key][key] = value.name if hasattr(value, 'name') else value
    # Save settings to file
    with open(SETTINGS_FILE, 'w') as f:
        yaml.dump(data, f)

def apply_button(label, action_fn):
    """
    Creates and returns a button with an associated action function.

    Args:
        label (str): The text label for the button.
        action_fn (callable): The function to execute when the button is clicked.

    Returns:
        ui.button: A NiceGUI button instance.
    """
    ui.button(label, on_click=action_fn).classes('w-full mt-2')

def create(ArctosConfig):
    settings = load_servo_settings()

    with ui.column().classes('p-4 w-full'):
        ui.label("🔧 MKS Servo Configuration").classes('text-3xl font-bold text-center mb-4')
        
        # Iterate over each servo in the ArctosConfig
        for i in range(len(ArctosConfig.servos)):
            # Create servo key
            servo_key = f"servo_{i}"
            # Load settings for the current servo, or default to an empty dictionary
            servo_data = settings.get(servo_key, {})

            # Create a expandable card for each servo
            with ui.expansion(f"⚙️ Servo {i+1} Settings", icon="settings", value=False).classes('w-full border-2 border-gray-400 mt-2'):
                
                # Inside the card create the servo settings
                with ui.card().classes('w-full p-4'):

                    with ui.row().classes('w-full gap-4'):
                        with ui.column().classes('w-1/4'):
                            ui.label("Working Mode:").classes('text-lg font-bold')
                            work_mode_value = WorkMode[servo_data.get("work_mode", WorkMode.SrvFoc.name)]
                            mode_select = ui.select(
                                {WorkMode.CrOpen: "CR_OPEN", WorkMode.CrClose: "CR_CLOSE", WorkMode.CrvFoc: "CR_vFOC", 
                                WorkMode.SrOpen: "SR_OPEN", WorkMode.SrClose: "SR_CLOSE", WorkMode.SrvFoc: "SR_vFOC"},
                                value=work_mode_value
                            ).classes('w-full')
                            
                            # Function to apply working mode settings
                            def apply_working_mode(index=i, selector=mode_select):
                                ArctosConfig.servos[index].set_work_mode(selector.value)
                                # Save setting to file
                                save_servo_setting(index, "work_mode", selector.value)
                                ui.notify(f"✅ Servo {index+1} Working Mode updated.", type='positive')
                            apply_button("Apply Working Mode", apply_working_mode)

                        with ui.column().classes('w-1/4'):
                            ui.label("Operating Current (mA):").classes('text-lg font-bold')
                            current_input = ui.number(value=servo_data.get("current", 1600), min=0, max=5200, step=100).classes('w-full')
                            def apply_current(index=i, input_field=current_input):
                                # Apply current to servo and save setting to file
                                ArctosConfig.servos[index].set_working_current(int(input_field.value))
                                save_servo_setting(index, "current", int(input_field.value))
                                ui.notify(f"✅ Servo {index+1} Current updated.", type='positive')
                            apply_button("Apply Operating Current", apply_current)

                        with ui.column().classes('w-1/4'):
                            ui.label("Microsteps:").classes('text-lg font-bold')
                            microstep_select = ui.select([1, 2, 4, 8, 16, 32, 64, 128, 256], value=servo_data.get("microsteps", 16)).classes('w-full')
                            def apply_microsteps(index=i, selector=microstep_select):
                                # Apply microstep to servo and save setting to file
                                ArctosConfig.servos[index].set_subdivisions(selector.value)
                                save_servo_setting(index, "microsteps", selector.value)
                                ui.notify(f"✅ Servo {index+1} Microsteps updated.", type='positive')
                            apply_button("Apply Microsteps", apply_microsteps)

                    ui.separator().classes('my-6')

                    with ui.row().classes('w-full gap-4'):
                        with ui.column().classes('w-2/3'):
                            ui.label("Holding Current (%):").classes('text-lg font-bold')
                            hold_value = HoldingStrength[servo_data.get("holding", HoldingStrength.FIFTHTY_PERCENT.name)]
                            hold_current = ui.radio(
                                {HoldingStrength.TEN_PERCENT: "10%", HoldingStrength.TWENTLY_PERCENT: "20%", 
                                 HoldingStrength.THIRTY_PERCENT: "30%", HoldingStrength.FOURTY_PERCENT: "40%", 
                                 HoldingStrength.FIFTHTY_PERCENT: "50%", HoldingStrength.SIXTY_PERCENT: "60%", 
                                 HoldingStrength.SEVENTY_PERCENT: "70%", HoldingStrength.EIGHTY_PERCENT: "80%", 
                                 HoldingStrength.NIGHTY_PERCENT: "90%"},
                                value=hold_value
                            ).props('inline')
                            def apply_holding(index=i, selector=hold_current):
                                # Apply holding current to servo and save setting to file
                                ArctosConfig.servos[index].set_holding_current(selector.value)
                                save_servo_setting(index, "holding", selector.value)
                                ui.notify(f"✅ Servo {index+1} Holding Current updated.", type='positive')
                            apply_button("Apply Holding Current", apply_holding)

                        with ui.column().classes('w-1/4'):
                            ui.label("Rotation Direction:").classes('text-lg font-bold')
                            direction_value = Direction[servo_data.get("direction", Direction.CW.name)]
                            direction_select = ui.select(
                                {Direction.CW: "CW", Direction.CCW: "CCW"},
                                value=direction_value
                            ).classes('w-full')
                            def apply_direction(index=i, selector=direction_select):
                                # Apply direction to servo and save setting to file
                                ArctosConfig.servos[index].set_motor_rotation_direction(selector.value)
                                save_servo_setting(index, "direction", selector.value)
                                ui.notify(f"✅ Servo {index+1} Direction updated.", type='positive')
                            apply_button("Apply Rotation Direction", apply_direction)

                    ui.separator().classes('my-6')

                    with ui.column().classes('w-full'):
                        ui.label("🏠 Homing Settings").classes('text-lg font-bold')
                        with ui.row().classes('w-full'):
                            with ui.column().classes('w-1/5'):
                                ui.label("EndStop Level:").classes('text-md font-bold')
                                endstop_level_select = ui.select(["Low", "High"], value=servo_data.get("endstop_level", "Low")).classes('w-full')
                            with ui.column().classes('w-1/5'):
                                ui.label("Home Direction:").classes('text-md font-bold')
                                home_direction_select = ui.select(["CW", "CCW"], value=servo_data.get("home_direction", "CW")).classes('w-full')
                            with ui.column().classes('w-1/5'):
                                ui.label("Homing Speed (RPM):").classes('text-md font-bold')
                                home_speed_input = ui.number(value=servo_data.get("home_speed", 60), min=30, max=3000).classes('w-full')
                            with ui.column().classes('w-1/5'):
                                ui.label("Enable Homing:").classes('text-md font-bold')
                                enable_select = ui.select(["Enable", "Disable"], value=servo_data.get("enable_homing", "Enable")).classes('w-full')

                        def apply_homing(index=i):
                            # Apply homing to servo and save settings to file
                            ArctosConfig.servos[index].set_home(
                                EndStopLevel.Low if endstop_level_select.value == "Low" else EndStopLevel.High,
                                Direction.CW if home_direction_select.value == "CW" else Direction.CCW,
                                int(home_speed_input.value),
                                Enable.Enable if enable_select.value == "Enable" else Enable.Disable
                            )
                            save_servo_setting(index, "endstop_level", endstop_level_select.value)
                            save_servo_setting(index, "home_direction", home_direction_select.value)
                            save_servo_setting(index, "home_speed", int(home_speed_input.value))
                            save_servo_setting(index, "enable_homing", enable_select.value)
                            ui.notify(f"✅ Servo {index+1} Homing Settings updated.", type='positive')

                        apply_button("Apply Homing Settings", apply_homing)

                    ui.separator().classes('my-6')

                    with ui.row().classes('w-full gap-4'):
                        with ui.column().classes('w-1/4'):
                            ui.label("Enable Endstop:").classes('text-lg font-bold')
                            endstop_switch = ui.switch(value=servo_data.get("endstop_enabled", False)).classes('w-full')
                            def apply_endstop(index=i, val=endstop_switch):
                                # Apply endstop settings to servo and save to file
                                ArctosConfig.servos[index].set_en_pin_config(
                                    EnPinEnable.ActiveHigh if val.value else EnPinEnable.ActiveLow)
                                save_servo_setting(index, "endstop_enabled", val.value)
                                ui.notify(f"✅ Servo {index+1} Endstop Setting updated.", type='positive')
                            apply_button("Apply Endstop Setting", apply_endstop)

                        with ui.column().classes('w-1/4'):
                            ui.label("Enable Motor Shaft Lock Protection:").classes('text-lg font-bold')
                            motor_protection_switch = ui.switch(value=servo_data.get("shaft_protect", False)).classes('w-full')
                            def apply_protect(index=i, val=motor_protection_switch):
                                # Apply lock protection to servo and save to file
                                ArctosConfig.servos[index].set_motor_shaft_locked_rotor_protection(
                                    Enable.Enable if val.value else Enable.Disable)
                                save_servo_setting(index, "shaft_protect", val.value)
                                ui.notify(f"✅ Servo {index+1} Lock Protection updated.", type='positive')
                            apply_button("Apply Shaft Lock Protection", apply_protect)
