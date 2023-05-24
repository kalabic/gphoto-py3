#
# Wrapper for gphoto.py to enable it to be used from any location from command line.
# Add directory where you downloaded files from repository to local user PATH.
#

$exec_dir = (Get-Item .).FullName
$script_dir = Split-Path $MyInvocation.MyCommand.Path
$config_dir = "$HOME\.config\gphoto-py3"
$activate_venv_path = "$script_dir\venv\Scripts\Activate.ps1"

# For debugging directories as seen by process on Windows.
# Write-Host ""
# Write-Host "  CONF: $config_dir"
# Write-Host "  EXEC: $exec_dir"
# Write-Host "SCRIPT: $script_dir"
# Write-Host ""

#
# Installation action ("gphotopy.ps1 --install") will install python environment and
# copy default 'client_id.json' into '~/.config/gphoto-py3' directory. Update
# client id and client secret there, not in files in 'auth' subdirectory where
# scripts are.
# Add directory with scripts to your local user PATH.
#
if ($args[0] -match "--install")
{
  if ($exec_dir -ne $script_dir) {
    Write-Host "error: Install must run from directory where script is located."
    Write-Host "error: Change directory and try again."
    return
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

  if (-not (Test-Path -Path $config_dir)) {
    try  {
      New-Item -Path $config_dir -ItemType Directory -Force -ErrorAction Stop
    } catch {
      Write-Host "error: Unable to create directory: '$config_dir', cannot continue."
      return
    }
  }

  $absolute_destination_path = "$([System.IO.Path]::GetFullPath($config_dir))/client_id.json"
  if (-not (Test-Path -Path $absolute_destination_path -PathType Leaf)) {
    try  {
      $absolute_source_path = "$script_dir\auth\client_id.json"
      Copy-Item -Path $absolute_source_path -Destination $absolute_destination_path # -verbose
      if (Test-Path -Path $absolute_destination_path -PathType Leaf) {
        Write-Host "INFO: Configuration files created in directory: '$config_dir'"
      } else {
        Write-Host "error (1): Unable to create configuration files in directory: '$config_dir', cannot continue."
        return
      }
    } catch {
      Write-Host "error (2): Unable to create configuration files in directory: '$config_dir', cannot continue."
      return
    }
  } else {
    Write-Host "INFO: Configuration files already exist in directory: '$config_dir'."
  }

  Write-Host ""
  Write-Host "INFO: Installation done. You need to authorize with Google now:"
  Write-Host "INFO:"
  Write-Host "INFO: * Update client id and secret inside '~/.config/gphoto-py3/client_id.json'."
  Write-Host "INFO:"
  Write-Host "INFO: * Run again with '--auth' argument. This will open default system browser."
  Write-Host "INFO:   Works best with Chrome. Issues with Firefox."
  Write-Host "INFO:"
  Write-Host "INFO: * Add this directory to your 'PATH' environment variable and use 'gphotopy.ps1'"
  Write-Host "INFO:   from command line (not python script 'gphoto.py')."
  Write-Host "INFO:"
  Write-Host "INFO: * Run 'gphotopy.ps1 -h' for help."
  Write-Host ""
  return
}

if (-not (Test-Path -Path $activate_venv_path -PathType Leaf)) {
  Write-Host "error: Virtual environment for Python script not found."
  Write-Host "error: Run 'gphotopy.ps1 --install' from script directory."
  return
}

Invoke-Expression $activate_venv_path
if (-not $?) {
  Write-Host "error: Activating Python virtual environment failed, cannot continue"
  return
}

$py_result = python.exe $script_dir\gphoto.py @args
deactivate
return $py_result
