from nicegui import ui
from arctos_controller import ArctosController
from mks_servo_can.mks_enums import Enable, Direction, EndStopLevel, WorkMode, HoldingStrength, EnPinEnable

def create():
    """
    Page for configuring MKS servos.
    
    This function sets up a GUI for configuring six MKS servos via the Arctos Robot Control system.
    Users can adjust various parameters such as working mode, operating current, holding current, microsteps, 
    rotation direction, endstop activation, homing speed, and motor protection.
    """
    
    # Initialize the robot controller
    ArctosConfig = ArctosController()

    with ui.column().classes('p-4 w-full'):
        ui.label("🔧 MKS Servo Configuration").classes('text-3xl font-bold text-center mb-4')
        
        for i in range(6):  # 6 servos (0-5, as CAN IDs are 1-6)
            with ui.expansion(f"⚙️ Servo {i+1} Settings", icon="settings", value=False).classes('w-full mt-2'):
                with ui.card().classes('w-full p-4'):

                    # Working Mode
                    with ui.row().classes('w-full gap-4'):
                        with ui.column().classes('w-2/3'):
                            ui.label("Working Mode:").classes('text-lg font-bold')
                            mode_select = ui.select(
                                {WorkMode.CrOpen: "CR_OPEN", WorkMode.CrClose: "CR_CLOSE", WorkMode.CrvFoc: "CR_vFOC", 
                                WorkMode.SrOpen: "SR_OPEN", WorkMode.SrClose: "SR_CLOSE", WorkMode.SrvFoc: "SR_vFOC"},
                                value=WorkMode.SrvFoc
                            ).classes('w-full')
                        ui.button("Set", on_click=lambda mode=mode_select.value: ArctosConfig.servos[i].set_work_mode(mode)).classes('bg-blue-500 text-white px-4 py-2 rounded-lg self-center')

                    ui.separator().classes('my-4')

                    # Operating Current
                    with ui.row().classes('w-full gap-4'):
                        with ui.column().classes('w-2/3'):
                            ui.label("Operating Current (mA):").classes('text-lg font-bold')
                            current_input = ui.number(value=1600, min=0, max=5200, step=100).classes('w-full')
                        ui.button("Set", on_click=lambda: ArctosConfig.servos[i].set_working_current(int(current_input.value))).classes('bg-blue-500 text-white px-4 py-2 rounded-lg self-center')

                    ui.separator().classes('my-4')

                    # Holding Current with Radio Buttons
                    with ui.row().classes('w-full gap-4'):
                        with ui.column().classes('w-2/3'):
                            ui.label("Holding Current (%):").classes('text-lg font-bold')
                            hold_current = ui.radio(
                                {HoldingStrength.TEN_PERCENT: "10%", HoldingStrength.TWENTLY_PERCENT: "20%", 
                                HoldingStrength.THIRTY_PERCENT: "30%", HoldingStrength.FOURTY_PERCENT: "40%", 
                                HoldingStrength.FIFTHTY_PERCENT: "50%", HoldingStrength.SIXTY_PERCENT: "60%", 
                                HoldingStrength.SEVENTY_PERCENT: "70%", HoldingStrength.EIGHTY_PERCENT: "80%", 
                                HoldingStrength.NIGHTY_PERCENT: "90%"},
                                value=HoldingStrength.FIFTHTY_PERCENT
                            ).props('inline')
                        ui.button("Set", on_click=lambda: ArctosConfig.servos[i].set_holding_current(hold_current.value)).classes('bg-blue-500 text-white px-4 py-2 rounded-lg self-center')

                    ui.separator().classes('my-4')

                    # Microsteps
                    with ui.row().classes('w-full gap-4'):
                        with ui.column().classes('w-2/3'):
                            ui.label("Microsteps:").classes('text-lg font-bold')
                            microstep_select = ui.select([1, 2, 4, 8, 16, 32, 64, 128, 256], value=16).classes('w-full')
                        ui.button("Set", on_click=lambda: ArctosConfig.servos[i].set_subdivisions(microstep_select.value)).classes('bg-blue-500 text-white px-4 py-2 rounded-lg self-center')

                    ui.separator().classes('my-4')

                    # Rotation Direction
                    with ui.row().classes('w-full gap-4'):
                        with ui.column().classes('w-2/3'):
                            ui.label("Rotation Direction:").classes('text-lg font-bold')
                            direction_select = ui.select({Direction.CW: "CW", Direction.CCW: "CCW"}, value=Direction.CW).classes('w-full')
                        ui.button("Set", on_click=lambda: ArctosConfig.servos[i].set_motor_rotation_direction(direction_select.value)).classes('bg-blue-500 text-white px-4 py-2 rounded-lg self-center')

                    ui.separator().classes('my-4')

                    # Enable Endstop
                    with ui.row().classes('w-full gap-4'):
                        with ui.column().classes('w-2/3'):
                            ui.label("Enable Endstop:").classes('text-lg font-bold')
                            endstop_switch = ui.switch().classes('w-full')
                        ui.button("Set", on_click=lambda: ArctosConfig.servos[i].set_en_pin_config(EnPinEnable.ActiveHigh if endstop_switch.value else EnPinEnable.ActiveLow)).classes('bg-blue-500 text-white px-4 py-2 rounded-lg self-center')

                    ui.separator().classes('my-4')

                    # Homing Speed
                    with ui.row().classes('w-full gap-4'):
                        with ui.column().classes('w-2/3'):
                            ui.label("Homing Speed (RPM):").classes('text-lg font-bold')
                            home_speed_input = ui.number(value=60, min=30, max=3000).classes('w-full')
                        ui.button("Set", on_click=lambda: ArctosConfig.servos[i].set_home(EndStopLevel.Low, Direction.CW, int(home_speed_input.value), Enable.Enable)).classes('bg-blue-500 text-white px-4 py-2 rounded-lg self-center')

                    ui.separator().classes('my-4')

                    # Enable Motor Shaft Lock Protection
                    with ui.row().classes('w-full gap-4'):
                        with ui.column().classes('w-2/3'):
                            ui.label("Enable Motor Shaft Lock Protection:").classes('text-lg font-bold')
                            motor_protection_switch = ui.switch().classes('w-full')
                        ui.button("Set", on_click=lambda: ArctosConfig.servos[i].set_motor_shaft_locked_rotor_protection(Enable.Enable if motor_protection_switch.value else Enable.Disable)).classes('bg-blue-500 text-white px-4 py-2 rounded-lg self-center')
