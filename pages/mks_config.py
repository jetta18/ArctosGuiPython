from nicegui import ui
from arctos_controller import ArctosController
from mks_servo_can.mks_enums import Enable, Direction, EndStopLevel, WorkMode, HoldingStrength, EnPinEnable

def create(ArctosConfig):
    """
    Page for configuring MKS servos.
    """

    with ui.column().classes('p-4 w-full'):
        ui.label("🔧 MKS Servo Configuration").classes('text-3xl font-bold text-center mb-4')
        
        for i in range(6):  # 6 servos
            with ui.expansion(f"⚙️ Servo {i+1} Settings", icon="settings", value=False).classes('w-full mt-2'):
                with ui.card().classes('w-full p-4'):
                    
                    # Working Mode
                    with ui.row().classes('w-full gap-4'):
                        with ui.column().classes('w-1/4'):
                            ui.label("Working Mode:").classes('text-lg font-bold')
                            mode_select = ui.select(
                                {WorkMode.CrOpen: "CR_OPEN", WorkMode.CrClose: "CR_CLOSE", WorkMode.CrvFoc: "CR_vFOC", 
                                WorkMode.SrOpen: "SR_OPEN", WorkMode.SrClose: "SR_CLOSE", WorkMode.SrvFoc: "SR_vFOC"},
                                value=WorkMode.SrvFoc
                            ).classes('w-full')
                        with ui.column().classes('w-1/4'):
                            # Operating Current
                            ui.label("Operating Current (mA):").classes('text-lg font-bold')
                            current_input = ui.number(value=1600, min=0, max=5200, step=100).classes('w-full')

                        with ui.column().classes('w-1/4'):
                            # Microsteps
                            ui.label("Microsteps:").classes('text-lg font-bold')
                            microstep_select = ui.select([1, 2, 4, 8, 16, 32, 64, 128, 256], value=16).classes('w-full')                           
                    ui.separator().classes('my-6')
                    with ui.row().classes('w-full gap-4'):
                    # Holding Current
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
                        with ui.column().classes('w-1/4'):
                            # Rotation Direction
                            ui.label("Rotation Direction:").classes('text-lg font-bold')
                            direction_select = ui.select({Direction.CW: "CW", Direction.CCW: "CCW"}, value=Direction.CW).classes('w-full')
                    ui.separator().classes('my-6')
                    with ui.column().classes('w-full'):
                        with ui.row().classes('w-full'):
                            # Homing Settings
                            ui.label("🏠 Homing Settings").classes('text-lg font-bold')
                        with ui.row().classes('w-full'):
                            with ui.column().classes('w-1/5'):
                                ui.label("EndStop Level:").classes('text-md font-bold')
                                endstop_level_select = ui.select(["Low", "High"], value="Low").classes('w-1/4')
                            with ui.column().classes('w-1/5'):
                                ui.label("Home Direction:").classes('text-md font-bold')
                                home_direction_select = ui.select(["CW", "CCW"], value="CW").classes('w-1/4')
                            with ui.column().classes('w-1/5'):
                                ui.label("Homing Speed (RPM):").classes('text-md font-bold')
                                home_speed_input = ui.number(value=60, min=30, max=3000).classes('w-1/4')
                            with ui.column().classes('w-1/5'):
                                ui.label("Enable Homing:").classes('text-md font-bold')
                                enable_select = ui.select(["Enable", "Disable"], value="Enable").classes('w-1/4')
                    ui.separator().classes('my-6')     
                    with ui.row().classes('w-full gap-4'):
                        with ui.column().classes('w-1/4'):
                            # Enable Endstop
                            ui.label("Enable Endstop:").classes('text-lg font-bold')
                            endstop_switch = ui.switch().classes('w-full')
                        with ui.column().classes('w-1/4'):
                            # Motor Shaft Lock Protection
                            ui.label("Enable Motor Shaft Lock Protection:").classes('text-lg font-bold')
                            motor_protection_switch = ui.switch().classes('w-full')
                    ui.separator().classes('my-6')
                    # Apply Button with Feedback
                    def apply_settings(i):
                        ArctosConfig.servos[i].set_work_mode(mode_select.value)
                        ArctosConfig.servos[i].set_working_current(int(current_input.value))
                        ArctosConfig.servos[i].set_holding_current(hold_current.value)
                        ArctosConfig.servos[i].set_subdivisions(microstep_select.value)
                        ArctosConfig.servos[i].set_motor_rotation_direction(direction_select.value)
                        ArctosConfig.servos[i].set_en_pin_config(
                            EnPinEnable.ActiveHigh if endstop_switch.value else EnPinEnable.ActiveLow
                        )
                        ArctosConfig.servos[i].set_home(
                            EndStopLevel.Low if endstop_level_select.value == "Low" else EndStopLevel.High,
                            Direction.CW if home_direction_select.value == "CW" else Direction.CCW,
                            int(home_speed_input.value),
                            Enable.Enable if enable_select.value == "Enable" else Enable.Disable
                        )
                        ArctosConfig.servos[i].set_motor_shaft_locked_rotor_protection(
                            Enable.Enable if motor_protection_switch.value else Enable.Disable
                        )
                        ui.notify(f"✅ Servo {i+1} settings applied successfully!", type='positive')
                    
                    ui.button("Apply Settings", on_click=lambda i=i: apply_settings(i)).classes(
                        'bg-green-500 text-white px-4 py-2 rounded-lg self-center'
                    )