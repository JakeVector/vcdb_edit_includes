SET VECTORCAST_DIR=C:\VCAST\2025sp7

echo "Creating minimal CCAST_.CFG (needed for vcdb)"
echo "C_COMPILE_CMD: tricore-gcc" > CCAST_.CFG

echo "Running vcdb get commands"
%VECTORCAST_DIR%\vcdb --db=vcshell.db getallcmdlines --all > commands.txt


REM subst X: .

REM %VECTORCAST_DIR%\vcdb --db=vcshell.db --filter=tricore-gcc.exe dumpcommands > commands.txt

REM %VECTORCAST_DIR%\vcdb --db=vcshell.db --filter=tricore-gcc dumpcommands > commands.txt

REM python filter_script.py

REM %VECTORCAST_DIR%\vcshell --db=vcshell_new.db --inputcmds=commands.txt putcommand