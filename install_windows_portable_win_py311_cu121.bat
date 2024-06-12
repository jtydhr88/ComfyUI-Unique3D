@echo off

set "requirements_txt=%~dp0\requirements.txt"
set "requirements_post_txt=%~dp0\requirements_post_win_py311_cu121.txt"
set "python_exec=..\..\..\python_embeded\python.exe"

echo Starting to install ComfyUI-Unique3D...

if exist "%python_exec%" (
    echo Installing with ComfyUI Windows Portable Python Embeded Environment

    "%python_exec%" -s -m pip install -r "%requirements_txt%" 

	echo Removing default onnxruntime and onnxruntime-gpu

	"%python_exec%" -s -m pip uninstall onnxruntime
	"%python_exec%" -s -m pip uninstall onnxruntime-gpu
	
	echo Installing correct version onnxruntime-gpu for cuda 12.1
	
	"%python_exec%" -s -m pip install onnxruntime-gpu --extra-index-url https://aiinfra.pkgs.visualstudio.com/PublicPackages/_packaging/onnxruntime-cuda-12/pypi/simple/

	"%python_exec%" -s -m pip uninstall diffusers
	"%python_exec%" -s -m pip install diffusers==0.27.2

    "%python_exec%" -s -m pip uninstall ninja
    "%python_exec%" -s -m pip install ninja

	"%python_exec%" -s -m pip install -r "%requirements_post_txt%"
) else (
    echo ERROR: Cannot find ComfyUI Windows Portable Python Embeded Environment "%python_exec%"
)

echo Install Finished. Press any key to continue...

pause