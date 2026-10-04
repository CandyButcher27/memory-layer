$root = $PSScriptRoot
$sh = '/mnt/' + $root.Substring(0, 1).ToLower() + $root.Substring(2).Replace('\', '/') + '/tick.sh'
$action = New-ScheduledTaskAction -Execute 'conhost.exe' -Argument "--headless wsl.exe -d Ubuntu -e bash -l `"$sh`""
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Hours 1)
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -WakeToRun -MultipleInstances IgnoreNew -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Hours 23)
Register-ScheduledTask -TaskName 'mimi-bench' -Action $action -Trigger $trigger -Settings $settings -Force | Out-Null
Get-ScheduledTask -TaskName 'mimi-bench' | Select-Object TaskName, State
