@echo off

cd build_misc/

python version_updater.py

echo -----

create-version-file ^
    metadata.yml ^
    --outfile file_version_info.txt

cd ..

pyinstaller ^
    -F ^
    -w main.py ^
    --add-data "img/*;./img" ^
    --add-data "img/macros/*;./img/macros" ^
    --add-data "icon/*;./icon" ^
    --workpath ./ ^
    -i icon/macros-icon.ico ^
    --version-file build_misc/file_version_info.txt ^
    -n RomashkiMacros.exe

    rem --clean ^

pause

