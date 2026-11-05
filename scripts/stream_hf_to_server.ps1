param(
    [Parameter(Mandatory=$true)][ValidateSet('hf-metadata.json','README.md','LongBench.py','data.zip')][string]$Name,
    [string]$RemoteRun='results/20261028-trec-data-preflight-v2'
)
$ErrorActionPreference='Stop'
if ($RemoteRun -notmatch '^results/[a-zA-Z0-9-]+$') { throw 'Invalid result directory' }
$revision='5e628be450b7e67fb7ae6e201bd6d8f7056f7672'
$url=if ($Name -eq 'hf-metadata.json') {
    "https://huggingface.co/api/datasets/zai-org/LongBench/revision/${revision}?blobs=true"
} else {
    "https://huggingface.co/datasets/zai-org/LongBench/resolve/$revision/$Name"
}
$expected=if ($Name -eq 'data.zip') { 'cb45b11a4133c6bc1d6a44b0f8e701335ff1e543195db1103472e575857f7f64' } else { '' }
$maximum=if ($Name -eq 'data.zip') { 113932529 } else { 2000000 }
# Only process pipes hold downloaded bytes on Windows. The receiver writes on Linux.
$receiver=@'
import sys,pathlib,hashlib,json,time
root=pathlib.Path('/home/user/jhk/project/Directional Exploration/kv-pruning').resolve()
run=root/'__RUN__';run.mkdir(exist_ok=True)
assert run.resolve().is_relative_to(root/'results')
name='__NAME__';dest=run/name;part=run/(name+'.part')
assert not dest.exists() and not part.exists(), 'Never overwrite a download or partial file'
proof=dict(status='receiving',url='__URL__',name=name,start_unix=time.time(),transport='Windows curl stdout -> SSH stdin; no local dataset file')
proofpath=run/('transfer_'+name+'.json')
proofpath.write_text(json.dumps(proof,indent=2))
try:
 count=0;digest=hashlib.sha256()
 with part.open('xb') as f:
  while True:
   chunk=sys.stdin.buffer.read(1048576)
   if not chunk:break
   count+=len(chunk)
   assert count<=__MAXIMUM__, 'Unexpected download size'
   digest.update(chunk);f.write(chunk)
 value=digest.hexdigest()
 if '__EXPECTED__':
  assert count==__MAXIMUM__ and value=='__EXPECTED__', (count,value)
 if name=='hf-metadata.json':
  data=json.loads(part.read_text())
  assert data['sha']=='5e628be450b7e67fb7ae6e201bd6d8f7056f7672' and data['id']=='zai-org/LongBench'
 part.rename(dest)
 proof.update(status='complete',end_unix=time.time(),bytes=count,sha256=value)
 proofpath.write_text(json.dumps(proof,indent=2));print(json.dumps(proof))
except Exception as error:
 proof.update(status='failed',end_unix=time.time(),error=repr(error))
 proofpath.write_text(json.dumps(proof,indent=2));raise
'@
$receiver=$receiver.Replace('__RUN__',$RemoteRun).Replace('__NAME__',$Name).Replace('__URL__',$url).Replace('__MAXIMUM__',[string]$maximum).Replace('__EXPECTED__',$expected)
$encoded=[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($receiver))
$remoteCommand="python3 -c `"import base64;exec(base64.b64decode('$encoded'))`""
function New-PipedProcess([string]$Executable,[string[]]$Arguments) {
    $info=[Diagnostics.ProcessStartInfo]::new()
    $info.FileName=$Executable
    foreach($argument in $Arguments) { $info.ArgumentList.Add($argument) }
    $info.UseShellExecute=$false
    $info.CreateNoWindow=$true
    $info.RedirectStandardOutput=$true
    $info.RedirectStandardError=$true
    $info.RedirectStandardInput=$true
    $process=[Diagnostics.Process]::new()
    $process.StartInfo=$info
    [void]$process.Start()
    return $process
}
$sshArguments=@('-i','C:\Users\Administrator\.ssh\saga_jhk_lab','-o','BatchMode=yes','-o','ConnectTimeout=20','-o','IdentitiesOnly=yes','-o','StrictHostKeyChecking=yes','-o','IPQoS=none','-p','1100','jhk@121.48.164.89',$remoteCommand)
$sshProcess=New-PipedProcess 'ssh.exe' $sshArguments
$sshOutput=$sshProcess.StandardOutput.ReadToEndAsync()
$sshError=$sshProcess.StandardError.ReadToEndAsync()
$curlProcess=New-PipedProcess 'curl.exe' @('--location','--fail','--silent','--show-error','--connect-timeout','8','--max-time','180',$url)
$curlError=$curlProcess.StandardError.ReadToEndAsync()
try {
    $curlProcess.StandardOutput.BaseStream.CopyTo($sshProcess.StandardInput.BaseStream)
} finally {
    $sshProcess.StandardInput.Close()
}
$curlProcess.WaitForExit()
$sshProcess.WaitForExit()
Write-Output $sshOutput.GetAwaiter().GetResult()
$downloadError=$curlError.GetAwaiter().GetResult()
$receiveError=$sshError.GetAwaiter().GetResult()
if($downloadError) { Write-Output $downloadError }
if($receiveError) { Write-Output $receiveError }
if($curlProcess.ExitCode -ne 0 -or $sshProcess.ExitCode -ne 0) {
    throw "Transfer failed: curl=$($curlProcess.ExitCode), ssh=$($sshProcess.ExitCode)"
}
