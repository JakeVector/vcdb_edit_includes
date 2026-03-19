SET VECTORCAST_DIR=C:\VCAST\2025sp7

echo "Creating minimal CCAST_.CFG (needed for vcdb)"
echo "C_COMPILE_CMD: tricore-gcc" > CCAST_.CFG

echo "Running vcdb get commands"
%VECTORCAST_DIR%\vcdb --db=vcshell.db getallcmdlines --all > commands.txt

echo "Filtering and prepending drive to paths"
python prepend_drive_to_paths.py commands.txt commands_filtered.txt -d X

echo "Importing filtered commands into new database"
%VECTORCAST_DIR%\vcshell --db=vcshell_new.db --inputcmds=commands_filtered.txt putcommand