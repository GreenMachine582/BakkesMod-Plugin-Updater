
@echo off

powershell -Command Expand-Archive %1.zip -DestinationPath %1
	
exit 0