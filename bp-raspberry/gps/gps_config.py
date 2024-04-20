import L76X
import time

x = L76X.L76X()
x.L76X_Set_Baudrate(9600)
x.L76X_Send_Command("$PCAS04,7")
x.L76X_Exit_BackupMode()
time.sleep(1)
