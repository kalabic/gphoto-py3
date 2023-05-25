
# shellpath.ps1, v1.0
# Add/remove entries from PATH environment variable in user's scope.
# Commands: add <PATH>, rm <PATH>, clean, ls - <PATH> can be relative, i.e. '.' (current directory)

# Remove '\' from end of path.
function Get-TrimmedDirPath ([string] $other_path) {
    if ($other_path.Chars($other_path.Length - 1) -eq '\') {
        $other_path = $other_path.TrimEnd('\')
    }
    return $other_path
}


# Get an array of directory paths from PATH environment variable in user's scope.
function Get-UserPathArray {

    $result_arr = @()
    $path_arr = [System.Environment]::GetEnvironmentVariable('PATH', 'User') -split ';'
    foreach ($path in $path_arr) {
        if ($path.Length -gt 0 ) {
            $path = Get-TrimmedDirPath($path)
            $result_arr += $path
        }
    }
    return $result_arr
}


# Convert second argument of a command line into absolute path from (perhaps) relative.
function Get-DirPathArgument ([string[]] $script_args) {

    if ($script_args.Count -lt 2) {
        return ""
    }

    if ($script_args[1].ToString().Length -eq 0) {
        return ""
    }

    return $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($script_args[1])
}


#
# Script body starts here.
#

if ($args[0] -match "ls") {

    #
    # List items in PATH
    #

    $env_path_arr = Get-UserPathArray
    foreach ($path in $env_path_arr) {
        if ($path.Length -gt 0 ) {
            if (-not (Test-Path -Path $path -PathType Container)) {
                Write-Host "$path [missing]"
            } else {
                Write-Host "$path"
            }
        }
    }

} elseif ($args[0] -match "clean") {

    #
    # Clean missing directories from PATH
    #

    $result_arr = @()
    $missing = 0
    $env_path_arr = Get-UserPathArray
    foreach ($path in $env_path_arr) {
        if ($path.Length -gt 0 ) {
            if (Test-Path -Path $path -PathType Container) {
                $result_arr += $path
            } else {
                $missing++
            }
        } else {
            $missing++
        }
    }

    if ($missing -gt 0) {
        $new_env_path = $result_arr -join ';'
        [System.Environment]::SetEnvironmentVariable('PATH', $new_env_path, 'User')
        Write-Host "Removed $missing item(s)."
    }

} elseif ($args[0] -match "add") {

    #
    # Add item to PATH
    #

    $dir_path = Get-DirPathArgument($args)
    if ($dir_path.Length -eq 0) {
        Write-Host "error: Argument missing (directory path)."
        return
    }

    if (-not (Test-Path -Path $dir_path -PathType Container)) {
        Write-Host "error: Does not exist or not a dir: $dir_path"
        return
    }

    $env_path_arr = Get-UserPathArray
    $normal_dir_path = Get-TrimmedDirPath($dir_path)
    $existing_dir_path = $env_path_arr | Where-Object { ($_ -ieq $normal_dir_path) }
    if ($existing_dir_path.Length -eq 0) {
        $new_env_path = (@() + $env_path_arr + $dir_path) -join ';'
        [System.Environment]::SetEnvironmentVariable('PATH', $new_env_path, 'User')
        Write-Host "New PATH item added: $dir_path"
    } else {
        Write-Host "Item already in PATH: $dir_path"
    }

} elseif ($args[0] -match "rm") {

    #
    # Remove item from PATH
    #

    $dir_path = Get-DirPathArgument($args)
    if ($dir_path.Length -eq 0) {
        Write-Host "error: Argument missing (directory path)."
        return
    }

    $env_path_arr = Get-UserPathArray
    $normal_dir_path = Get-TrimmedDirPath($dir_path)
    $existing_dir_path = $env_path_arr | Where-Object { ($_ -ieq $normal_dir_path) }
    if ($existing_dir_path.Length -gt 0) {
        $removed_dir_path = $env_path_arr | Where-Object { !($_ -ieq $normal_dir_path) }
        $new_env_path = $removed_dir_path -join ';'
        [System.Environment]::SetEnvironmentVariable('PATH', $new_env_path, 'User')
        Write-Host "Item removed from PATH: $dir_path"
    } else {
        Write-Host "Item not in PATH: $dir_path"
    }
} else {
    Write-Host "Use commands: add <PATH>, rm <PATH>, clean, ls - PATH can be relative"
}
