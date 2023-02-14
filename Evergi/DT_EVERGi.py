class DT_EVERGI(object):
    """
    classdocs
    """
    # Here will be the instance stored.
    __instance = None

    @staticmethod
    def getInstance():
        """ Static access method. """
        if DT_EVERGI.__instance == None:
            DT_EVERGI()
        return DT_EVERGI.__instance

    def __init__(self):
        """ Virtually private constructor. """
        if DT_EVERGI.__instance is not None:
            raise Exception("This class is a singleton!")
        else:
            DT_EVERGI.__instance = self

            self.DT_EVERGi_arrEVSE_100 = list()
            for x in range(100):
                self.DT_EVERGi_arrEVSE_100.append(DT_EVERGi_EVSE())

            self.DT_EVERGi_arrCS_50 = list()
            for x in range(50):
                self.DT_EVERGi_arrCS_50.append(DT_EVERGi_CS())

            self.DT_EVERGi_arrProduction_50 = list()
            for x in range(50):
                self.DT_EVERGi_arrProduction_50.append(DT_EVERGi_Production())

            self.DT_EVERGi_arrDynLoad_50 = list()
            for x in range(50):
                self.DT_EVERGi_arrDynLoad_50.append(DT_EVERGi_DynLoad())

            self.DT_EVERGi_arrBattery_50 = list()
            for x in range(50):
                self.DT_EVERGi_arrBattery_50.append(DT_EVERGi_Battery())

            self.DT_EVERGi_arrEVSE_10 = list()
            for x in range(10):
                self.DT_EVERGi_arrEVSE_10.append(DT_EVERGi_EVSE())

            self.DT_EVERGi_arrNode_10 = list()
            for x in range(10):
                self.DT_EVERGi_arrNode_10.append(DT_EVERGi_Node())


class DT_EVERGi_EVSE:
    """
    Electric Vehicle Chargings Equipment / outlet / connector / socket
    """
    def __init__(self):
        Conf_uiNr: int              #Number - used in EVScheduler - 0:disabled
        Conf_uiType: int            #Type= 1: AC uni-directional, 2:AC bi-directional, 3:DC uni-directional, 4:DC bi-directional
        Conf_uiNodeNr: int          #Number of the node to which the charging station is connected
        #Present Values
        PV_uiState: int             #0: Invalid ; 1: Cable not connected ; 2: Cable connected, no error ; 3: Error
        PV_rPower: float            #[W] charging power (AC), +:flowing to the car
        PV_rPower_max: float        #[W] Maximum charging power (AC) defined by charger - car - car SOC combination
        PV_rEnergy: float           #[Wh] Energy to the car (AC) during the current charging session, +: energy inserted in the car
        PV_rCurrent1: float         #[A] Charger current (AC) on line 1, +:flowing to the car
        PV_rCurrent2: float         #[A] Charger current (AC) on line 2, +:flowing to the car
        PV_rCurrent3: float         #[A] Charger current (AC) on line 3, +:flowing to the car
        PV_rCurrent_max: float      #[W] Maximum charging current (AC) defined by charger - car - car SOC combination
        PV_rCurrentDC: float        #[A] Charger current (DC), +:flowing to the car   - Only when DC charger
        PV_rVoltageDC: float        #[V] Charger voltage (DC)                         - Only when DC charger
        PV_rSOC: float              #[%] State Of Charge of the car                   - only when DC charger
        PV_xComm_ok: bool           #TRUE= Communication EVSE/CS - Local controller ok
        # Setpoint
        SP_rCurrent: float          #[A] Charger current [AC], +:flowing to the car
        # Setpoint coming from EV Scheduler
        SPSc_rCurrent: float        #[A] Charger current [AC], +:flowing to the car
        SPSc_uiComm: int            #Minutes since last message EVScheduler -> Local controller
        # Calculated internal variables
        Help_SP_rCurrent_dev: int   #[A] PV-SP, deviation between present value and setpoint

class DT_EVERGi_CS:
    """
    Charging Station
    """
    def __init__(self):
        Conf_sId: str               #Id / serial / location
        Conf_sType: str             #Brand & type & version - for example: 'ABB_DC_01'
        Conf_sAdress: str           #Communication adress - for example: opc.tcp://192.168.71.49:4840
        Conf_uiPort: str            #Communication adress - port number
        Conf_uiNodeNr: str          #Number of the node to which the charging station is connected
        Conf_uiWired: str           #To which phase of the grid/node is the charger connected - example: 123 or 2 or 312
        Conf_uiEVSEx_Nr_10 = list() #EVSEx Nr / Id - 0:disabled - One Charger Station can have multiple EVSE, link between those and the EVSEnr
        for x in range(10):
            Conf_uiEVSEx_Nr_10.append(0)
        PV_xComm_ok: bool           #TRUE= Communication Charging Station - Local controller ok
class DT_EVERGi_Grid:
    """
    Public grid connection - data to optimize for the pricing
    """
    def __init__(self):
        Conf_rCurrent_max: float    #[A] maximum current, limited by breaker/transformer/...
        #Present Values
        PV_rPower: float            #[Wh] Energy, +:energy consumed/taken from the grid
        PV_rCurrent1: float         #[A] current on line 1, +:consumption
        PV_rCurrent2: float         #[A] current on line 2, +:consumption
        PV_rCurrent3: float         #[A] current on line 3, +:consumption
        PV_xComm_ok: bool           #TRUE= Communication energy meter - Local controller ok

class DT_EVERGi_Production:
    """
    Electricity producing assets
    """
    def __init__(self):
        #Configuration
        Conf_uiNr: int = 0          #Number - used in EVScheduler - 0:disabled
        Conf_uiNodeNr: int          #Number of the node to which the charging station is connected
        #Present Values
        PV_rPower: float            #[W] power, +:production -:consumption
        PV_rCurrent1: float         #[A] current on line 1, +:production -:consumption
        PV_rCurrent2: float         #[A] current on line 2, +:production -:consumption
        PV_rCurrent3: float         #[A] current on line 3, +:production -:consumption
        PV_xComm_ok: bool           #TRUE= Communication energy meter - Local controller ok

class DT_EVERGi_Node:
    """
    Node = electricity grid limitation (breaker / transformer) - group of electrical assets
    """
    def __init__(self):
        #Configuration
        Conf_uiNr: int              #Number - used in EVScheduler - 0:disabled
        Conf_rCurrent_max: float    #[A] maximum current, limited by breaker/transformer/...
        #Present Values
        PV_rPower: float            #[W] power, +:production -:consumption
        PV_rCurrent1: float         #[A] current on line 1, +:production -:consumption
        PV_rCurrent2: float         #[A] current on line 2, +:production -:consumption
        PV_rCurrent3: float         #[A] current on line 3, +:production -:consumption
        PV_xComm_ok: bool           #TRUE= Communication energy meter - Local controller ok

class DT_EVERGi_DynLoad:
    """
    Dynamic Load
    """
    def __init__(self):
        #Configuration
        Conf_uiNr: int              #Number - 0:disabled
        Conf_sType: str             #Brand & type & version
        Conf_sAdress: str           #Communication adress
        Conf_uiNodeNr: str          #Number of the node to which the dynamic load is connected
        #Present Values
        PV_rPower: float            #[W] power, +:production -:consumption
        PV_rPower_max: float        #[W] Maximal power - flexibility, +:consumption
        PV_rPower_min: float        #[W] Minimal power - flexibility, +:consumption
        PV_rCurrent1: float         #[A] Current on line 1, +:consumption
        PV_rCurrent2: float         #[A] Current on line 2, +:consumption
        PV_rCurrent3: float         #[A] Current on line 3, +:consumption
        PV_xComm_ok: bool           #TRUE= Communication dynamic load - Local controller ok
        #Setpoint
        SP_rCurrent: float          #[A] Current, +:consumption

class DT_EVERGi_Battery:
    """
    Battery
    """
    def __init__(self):
        #Configuration
        Conf_uiNr: int              #Number - used in EVScheduler - 0:disabled
        Conf_sType: int             #Brand & type & version
        Conf_sAdress: int           #Communication adress
        Conf_uiNodeNr: int          #Number of the node to which the battery is connected
        #Present Values
        PV_rPower: float            # [W] power, +:production -:consumption
        PV_rPower_max: float        # [W] Maximal power - flexibility, +:consumption
        PV_rPower_min: float        # [W] Minimal power - flexibility, +:consumption
        PV_rCurrent1: float         # [A] Current on line 1, +:consumption
        PV_rCurrent2: float         # [A] Current on line 2, +:consumption
        PV_rCurrent3: float         # [A] Current on line 3, +:consumption
        PV_xComm_ok: bool           # TRUE= Communication dynamic load - Local controller ok
        #Setpoint
        SP_rCurrent: float          #[A] Current, +:consumption
        #Setpoint coming from EV Scheduler
        SPSc_rCurrent: float        #[A] Current, +:consumption/charge battery
        SPSc_xComm_ok: bool         #TRUE= Communication EVScheduler - Local controller ok

if __name__ == "__main__":
    # Only for testing
    dt_evergi = DT_EVERGI.getInstance()

    dt_evergi.DT_EVERGi_arrEVSE_100[1].Conf_uiNr = 1

    print(dt_evergi.DT_EVERGi_arrEVSE_100[1].Conf_uiNr)