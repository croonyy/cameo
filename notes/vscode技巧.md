# 备份插件列表
code --list-extensions > extensions.txt

# 恢复插件列表（要用powershell）
Get-Content extensions.txt | ForEach-Object { code --install-extension $_ }