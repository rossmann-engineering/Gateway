import ModbusClient

class Evcs_abb_ac_01:
    def __init__(self):
        self.EVSE1_uiState = 0
    def evcs_abb_ac_01(self, cs, evse):
        evse.PV_xComm_ok = False
        modbusClient = ModbusClient.ModbusClient(cs.Conf_sAdress, cs.Conf_uiPort)
        modbusClient.connect()
        holding_registers1 = modbusClient.read_holdingregisters(16384, 31)
        evse.Conf_uiNr = cs.Conf_uiEVSEx_Nr_10[1]
        evse.Conf_uiType = 1
        evse.Conf_uiNodeNr = cs.Conf_uiNodeNr
        evse.PV_xComm_ok = True
        evse.PV_rCurrent_max = holding_registers1[8] / 1000.0
        evse.PV_rPower = holding_registers1[30]
        R_EVSE1_udiErrorCode = holding_registers1[10]
        R_EVSE1_udiSocketlockState = holding_registers1[12]
        R_EVSE1_udiChargingState = holding_registers1[14]
        R_EVSE1_rCurrent_SP = holding_registers1[16] / 1000.0
        R_EVSE1_rCurrent1 = holding_registers1[18] / 1000.0
        R_EVSE1_rCurrent2 = holding_registers1[20] / 1000.0
        R_EVSE1_rCurrent3 = holding_registers1[22] / 1000.0
        R_EVSE1_rVoltage1 = holding_registers1[24] / 1000.0
        R_EVSE1_rVoltage2 = holding_registers1[26] / 1000.0
        R_EVSE1_rVoltage3 = holding_registers1[28] / 1000.0

        # Copy the current to the right phase - To which phase of the grid/node is the charger connected
        if cs.Conf_uiWired == '321':
            evse.PV_rCurrent3 = R_EVSE1_rCurrent1
            evse.PV_rCurrent2 = R_EVSE1_rCurrent2
            evse.PV_rCurrent1 = R_EVSE1_rCurrent3
        elif cs.Conf_uiWired == '312':
            evse.PV_rCurrent3 = R_EVSE1_rCurrent1
            evse.PV_rCurrent1 = R_EVSE1_rCurrent2
            evse.PV_rCurrent2 = R_EVSE1_rCurrent3
        elif cs.Conf_uiWired == '213':
            evse.PV_rCurrent2 = R_EVSE1_rCurrent1
            evse.PV_rCurrent1 = R_EVSE1_rCurrent2
            evse.PV_rCurrent3 = R_EVSE1_rCurrent3
        elif cs.Conf_uiWired == '231':
            evse.PV_rCurrent2 = R_EVSE1_rCurrent1
            evse.PV_rCurrent3 = R_EVSE1_rCurrent2
            evse.PV_rCurrent1 = R_EVSE1_rCurrent3
        elif cs.Conf_uiWired == '132':
            evse.PV_rCurrent1 = R_EVSE1_rCurrent1
            evse.PV_rCurrent3 = R_EVSE1_rCurrent2
            evse.PV_rCurrent2 = R_EVSE1_rCurrent3
        elif cs.Conf_uiWired == '1':
            evse.PV_rCurrent1 = R_EVSE1_rCurrent1
            evse.PV_rCurrent2 = 0
            evse.PV_rCurrent3 = 0
        elif cs.Conf_uiWired == '2':
            evse.PV_rCurrent1 = 0
            evse.PV_rCurrent2 = R_EVSE1_rCurrent2
            evse.PV_rCurrent3 = 0
        elif cs.Conf_uiWired == '3':
            evse.PV_rCurrent1 = 0
            evse.PV_rCurrent2 = 0
            evse.PV_rCurrent3 = R_EVSE1_rCurrent3
        else:
            evse.PV_rCurrent1 = R_EVSE1_rCurrent1
            evse.PV_rCurrent2 = R_EVSE1_rCurrent2
            evse.PV_rCurrent3 = R_EVSE1_rCurrent3
        #Initialisation when No EV connected to charger
        if R_EVSE1_udiSocketlockState <= 1 and self.EVSE1_uiState>=100:
            self.EVSE1_uiState = 10
        elif R_EVSE1_udiSocketlockState <= 1:
            self.EVSE1_uiState = 20

        # Initialize
        if self.EVSE1_uiState == 0:
            self.EVSE1_uiState = 10
        # Disconnected / Standby
        elif self.EVSE1_uiState == 10:
            self.EVSE1_uiState = 100
        # Connected
        elif self.EVSE1_uiState == 100:
            if evse.PV_rPower > 0: # Car is charging, power is flowing
                self.EVSE1_uiState = 110
        # Charging
        elif self.EVSE1_uiState == 120:
            pass


        # Charger Status
        if not evse.PV_xComm_ok or R_EVSE1_udiErrorCode > 10:
            evse.PV_uiState = 0             # Error
        elif self.EVSE1_uiState >= 100:
            evse.PV_uiState = 2             # EV Connected to charger
        elif self.EVSE1_uiState >= 10:
            evse.PV_uiState = 1             # No EV Connected to charger










    """
    R_EVSE1_udiErrorCode       :=TO_UDINT(MBxx_R30_arrRegisterValue[10]); 	    //Error Code   
    	R_EVSE1_udiSocketlockState :=TO_UDINT(MBxx_R30_arrRegisterValue[12]); 	    //Socket lock state   
    	R_EVSE1_udiChargingState   :=TO_UDINT(MBxx_R30_arrRegisterValue[14]); 	    //Charging state   
    	R_EVSE1_rCurrent_SP	       :=TO_REAL(TO_INT(MBxx_R30_arrRegisterValue[16]))/1000; 	//Current charging current limit - 0,001 A
    	R_EVSE1_rCurrent1	       :=TO_REAL(TO_INT(MBxx_R30_arrRegisterValue[18]))/1000; 	//Charging current phase 1 - 0,001 A
    	R_EVSE1_rCurrent2          :=TO_REAL(TO_INT(MBxx_R30_arrRegisterValue[20]))/1000; 	//Charging current phase 2 - 0,001 A
    	R_EVSE1_rCurrent3	       :=TO_REAL(TO_INT(MBxx_R30_arrRegisterValue[22]))/1000; 	//Charging current phase 3 - 0,001 A
    	R_EVSE1_rVoltage1	       :=TO_REAL(TO_INT(MBxx_R30_arrRegisterValue[24]))/10; 	//Voltage phase 1 - 0,1 V
    	R_EVSE1_rVoltage2	       :=TO_REAL(TO_INT(MBxx_R30_arrRegisterValue[26]))/10; 	//Voltage phase 2 - 0,1 V
    	R_EVSE1_rVoltage3	       :=TO_REAL(TO_INT(MBxx_R30_arrRegisterValue[28]))/10; 	//Voltage phase 3 - 0,1 V
    	R_EVSE1_rPower	           :=TO_REAL(TO_INT(MBxx_R30_arrRegisterValue[30])); 	    //Active power - 1 W
    IF EVSE1_uiState<100     //EV disconnected
        	   THEN R_EVSE1_rEnergy_memo:=0;
        	ELSIF EVSE1.PV_xComm_ok AND (MBxx_R30_arrRegisterValue[32]=0)
        	    THEN R_EVSE1_rEnergy_memo:=R_EVSE1_rEnergy;
        	END_IF;    
        	R_EVSE1_rEnergy:=R_EVSE1_rEnergy_memo+TO_REAL(TO_INT(MBxx_R30_arrRegisterValue[32]));
        	EVSE1.PV_rEnergy:=R_EVSE1_rEnergy;
        //Copy the current to the right phase - To which phase of the grid/node is the charger connected
            IF      CS.Conf_uiWired = 321 THEN
                EVSE1.PV_rCurrent3      :=R_EVSE1_rCurrent1;
                EVSE1.PV_rCurrent2      :=R_EVSE1_rCurrent2;
                EVSE1.PV_rCurrent1      :=R_EVSE1_rCurrent3;
            ELSIF   CS.Conf_uiWired = 312 THEN
                EVSE1.PV_rCurrent3      :=R_EVSE1_rCurrent1;
                EVSE1.PV_rCurrent1      :=R_EVSE1_rCurrent2;
                EVSE1.PV_rCurrent2      :=R_EVSE1_rCurrent3;
            ELSIF   CS.Conf_uiWired = 213 THEN
                EVSE1.PV_rCurrent2      :=R_EVSE1_rCurrent1;
                EVSE1.PV_rCurrent1      :=R_EVSE1_rCurrent2;
                EVSE1.PV_rCurrent3      :=R_EVSE1_rCurrent3;
            ELSIF   CS.Conf_uiWired = 231 THEN
                EVSE1.PV_rCurrent2      :=R_EVSE1_rCurrent1;
                EVSE1.PV_rCurrent3      :=R_EVSE1_rCurrent2;
                EVSE1.PV_rCurrent1      :=R_EVSE1_rCurrent3;
            ELSIF   CS.Conf_uiWired = 132 THEN
                EVSE1.PV_rCurrent1      :=R_EVSE1_rCurrent1;
                EVSE1.PV_rCurrent3      :=R_EVSE1_rCurrent2;
                EVSE1.PV_rCurrent2      :=R_EVSE1_rCurrent3;
            ELSIF   CS.Conf_uiWired = 1 THEN
                EVSE1.PV_rCurrent1      :=R_EVSE1_rCurrent1;
                EVSE1.PV_rCurrent2      :=0;
                EVSE1.PV_rCurrent3      :=0;
            ELSIF   CS.Conf_uiWired = 2 THEN
                EVSE1.PV_rCurrent1      :=0;
                EVSE1.PV_rCurrent2      :=R_EVSE1_rCurrent1;
                EVSE1.PV_rCurrent3      :=0;
            ELSIF   CS.Conf_uiWired = 3 THEN
                EVSE1.PV_rCurrent1      :=0;
                EVSE1.PV_rCurrent2      :=0;
                EVSE1.PV_rCurrent3      :=R_EVSE1_rCurrent1;
            ELSE    // default: 123
                EVSE1.PV_rCurrent1      :=R_EVSE1_rCurrent1;
                EVSE1.PV_rCurrent2      :=R_EVSE1_rCurrent2;
                EVSE1.PV_rCurrent3      :=R_EVSE1_rCurrent3;
            END_IF;
            
(* Charging Sequence *)
    //Initialisation when No EV connected to charger
        IF R_EVSE1_udiSocketlockState<=1 AND EVSE1_uiState>=100
            THEN    EVSE1_uiState:=10;
        ELSIF   R_EVSE1_udiSocketlockState<=1
            THEN    EVSE1_uiState:=20;
        END_IF;
    CASE EVSE1_uiState OF
    	0: (* Initialisatie *)
            EVSE1_uiState	:= 10;
        10: (* Disconnect *)
            EVSE1_uiState	:= 20;
        20: (* Disconnected / Stand-by *)
            IF   R_EVSE1_udiSocketlockState>1 THEN   //Connector plugged in
                EVSE1_uiState	:= 100;
            END_IF;
        100: (* Connected *)
            IF   EVSE1.PV_rPower>0 THEN    //Car is charging, power is flowing
                EVSE1_uiState	:= 110;
            END_IF;
        110: (* Start-up : calculate/measure max power after connecting *)
            IF  EVSE1.PV_rPower_max>0 THEN            //Max power is known
                EVSE1_uiState	:= 120;
            END_IF;
        120: (* Charging *)
    END_CASE;
    
    (* Charger status *)
        IF NOT EVSE1.PV_xComm_ok
            OR R_EVSE1_udiErrorCode>0
            THEN EVSE1.PV_uiState:=0;   //error
        ELSIF EVSE1_uiState >= 100
            THEN EVSE1.PV_uiState:=2;   //EV connected to charger
        ELSIF EVSE1_uiState >= 10
            THEN EVSE1.PV_uiState:=1;   //No EV connected to charger
        END_IF;

    (* StartCheck : ABB TerraAC workaround when charger doesn't follow commands *)
    //vermogen laadpaal blijft nul wanneer aansturing van nul naar groter dan nul springt -> laadpaal even stoppen
        IF W_EVSE1_xStop OR (EVSE1_uiState < 100) OR EVSE1.PV_rPower>0 OR EVSE1_xStartCheckFailed
            THEN EVSE1_xStartCheck:=FALSE;
        ELSIF NOT W_EVSE1_xStop and W_EVSE1_xStop_memo 
    	   THEN EVSE1_xStartCheck:= TRUE;
        END_IF;
        EVSE1_StartCheck_TON(IN := EVSE1_xStartCheck, PT := TIME#20s);
        IF EVSE1_StartCheck_TON.Q
            THEN EVSE1_xStartCheckFailed:=TRUE;
                 EVSE1_udiStartCheckFailed:=EVSE1_udiStartCheckFailed+1;
        END_IF;
        EVSE1_StartCheckFailed_TON(IN := EVSE1_xStartCheckFailed, PT := TIME#10s);
        IF EVSE1_StartCheckFailed_TON.Q
            THEN EVSE1_xStartCheckFailed:=FALSE;
        END_IF;
     
    (* Step 110 Start-up : calculate/measure max power after connecting *)
        EVSE1_PowerMax_Check_TON(IN :=
            EVSE1.PV_xComm_ok                                                   //Comm ok
            AND (EVSE1_rPowerMax_Check>0)                                //EV is charging
            AND (EVSE1.PV_rPower<EVSE1_rPowerMax_Check+10),     //Power isn't rising
            PT := TIME#10s);
        IF EVSE1_PowerMax_Check_TON.Q
            THEN    EVSE1.PV_rPower_max:=EVSE1_rPowerMax_Check;
         END_IF;
        IF EVSE1_uiState<100  //Car not connected
            THEN
                EVSE1.PV_rPower_max:=0;
                EVSE1_rPowerMax_Check:=0;
            ELSIF EVSE1.PV_rPower>EVSE1_rPowerMax_Check //Active power rises
            THEN EVSE1_rPowerMax_Check:=EVSE1.PV_rPower;
        END_IF;

    (* Calculate the setpoint deviation : PV-SP, deviation between present value and setpoint *)
        FB_SP_rCurrent_dev(
            PV_rCurrent := MAX(EVSE1.PV_rCurrent1, EVSE1.PV_rCurrent2,EVSE1.PV_rCurrent3), 
            SP_rCurrent := EVSE1.SP_rCurrent, 
            rCurrent_dev => EVSE1.Help_SP_rCurrent_dev);
    """

