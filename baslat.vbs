' Koyun Sayaci - penceresiz baslatici (Windows). Sunucu arka planda acilir, tarayici gelir.
Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
kok = fso.GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = kok

' Zaten calisiyor mu?
On Error Resume Next
Set http = CreateObject("MSXML2.XMLHTTP")
http.Open "GET", "http://127.0.0.1:8780/api/durum", False
http.Send
calisiyor = (Err.Number = 0 And http.Status = 200)
On Error GoTo 0

If Not calisiyor Then
  sh.Run """" & kok & "\.venv\Scripts\pythonw.exe"" """ & kok & "\app.py""", 0, False
  WScript.Sleep 6000
End If
sh.Run "http://127.0.0.1:8780/", 1, False
