#
# Wrapper for Python scripts to enable them to be used from any location from command line.
# Add directory with native system scripts to local user PATH.
#

$exec_dir = (Get-Item .).FullName
$ps1_script_dir = Split-Path $MyInvocation.MyCommand.Path
$script_dir = Split-Path $ps1_script_dir
$activate_venv_path = "$script_dir\venv\Scripts\Activate.ps1"

# For debugging directories as seen by process on Windows.
# Write-Host ""
# Write-Host "  EXEC: $exec_dir"
# Write-Host "SCRIPT: $script_dir"
# Write-Host ""

#
# If Python virtual environment is not found, try to install it.
#
if (-not (Test-Path -Path $activate_venv_path -PathType Leaf)) {

  Write-Host "Python virtual environment not found, trying to install it..."

  if ($exec_dir -ne $script_dir) {
    Write-Host "Changing working folder to location of Python script: $script_dir"
    Set-Location -Path $script_dir
  }

  Write-Host "Setting up Python virtual environment..."

  python.exe -m venv venv
  if (-not $?) {
    Write-Host "error: Setting up Python virtual environment failed, cannot continue"
    return
  }

  Invoke-Expression $activate_venv_path
  if (-not $?) {
    Write-Host "error: Activating Python virtual environment failed, cannot continue"
    return
  }

  pip install -r requirements.txt
  if (-not $?) {
    Write-Host "error: Requirements install failed, cannot continue."
    return
  }

  # Exit Python virtual environment that was activated above.
  deactivate

  Write-Host ""
  Write-Host "INFO: Installation done. You need to authorize with Google now:"
  Write-Host "INFO:"
  Write-Host "INFO: * Update client id and secret inside 'auth/client_id.json'."
  Write-Host "INFO:"
  Write-Host "INFO: * Run with '--auth' argument. This will open default system browser."
  Write-Host "INFO:   Works best with Chrome. Issues with Firefox."
  Write-Host "INFO:"
  Write-Host "INFO: * Run 'gphotopy.ps1 -h' for help."
  Write-Host ""

  if ($exec_dir -ne $script_dir) {
    Write-Host "Changing back to working folder and attempting to run Python script from there."
    Set-Location -Path $exec_dir
  }
}

Invoke-Expression $activate_venv_path
if (-not $?) {
  Write-Host "error: Activating Python virtual environment failed, cannot continue"
  return
}

$py_result = python.exe $script_dir\gphoto.py @args
deactivate
return $py_result
