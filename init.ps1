#from http://tlingenf.spaces.live.com/blog/cns!B1B09F516B5BAEBF!213.entry
#
Get-Content "init.cfg" | foreach-object -begin {$h=@{}} -process {
     $k = [regex]::split($_,'='); 
     if(($k[0].CompareTo("") -ne 0) -and ($k[0].StartsWith("[") -ne $True)) { 
         $h.Add($k[0], $k[1]) 
     } 
}
#result in HashTable $h
#get variable via $h.PGDATA