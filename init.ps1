#from http://tlingenf.spaces.live.com/blog/cns!B1B09F516B5BAEBF!213.entry
#
Get-Content "settings.cfg" | foreach-object -begin {$h=@{}} -process {
     $k = [regex]::split($_,'='); 
     if(($k[0].CompareTo("") -ne 0) -and ($k[0].StartsWith("[") -ne $True)) { 
         $h.Add($k[0], $k[1]) 
     } 
}
#result in HashTable $h
#get variable via $h.PGDATA
(Get-Content .\docker-compose.yml.in).Replace(
    '{POSTGRES_USER}', $h.POSTGRES_USER
).Replace(
    '{POSTGRES_PASSWORD}', $h.POSTGRES_PASSWORD
).Replace(
    '{POSTGRES_DB}', $h.POSTGRES_DB
).Replace(
    '{PGDATA}', $h.PGDATA
).Replace(
    '{PGWEB_PORT}', $h.PGWEB_PORT
).Replace(
    '{REDISDATA}', $h.REDISDATA
).Replace(
    '{PROXY_ADDRESS}', $h.PROXY_ADDRESS
).Replace(
    '{PROXY_PORT}', $h.PROXY_PORT
).Replace(
    '{PROXY_TYPE}', $h.PROXY_TYPE
).Replace(
    '{WORK_DIR}', $h.WORK_DIR
) | Set-Content .\docker-compose.yml