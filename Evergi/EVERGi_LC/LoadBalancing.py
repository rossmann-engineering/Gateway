'''
(* Local load balancing - fill in the setpoints for all controlable assets *)

(* Copy setpoints to the controlable assets *)
(* EVSE : EVScheduler / max value *)
    FOR EVSE_uiNr:= 1 to 100 DO
        IF arrEVSE_100[EVSE_uiNr].SPSc_uiComm<5         //New message from EVScheduler during last 5 minutes
            THEN
            //Listen to EVScheduler
            arrEVSE_100[EVSE_uiNr].SP_rCurrent:=arrEVSE_100[EVSE_uiNr].SPSc_rCurrent;
        ELSE
            //Go to max current
            arrEVSE_100[EVSE_uiNr].SP_rCurrent:=arrEVSE_100[EVSE_uiNr].PV_rCurrent_max;
        END_IF;
    END_FOR;'''