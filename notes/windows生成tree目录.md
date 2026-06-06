打开一个powershell窗口，输入以下命令：
```powershell
function Get-LimitedDepthFiles {
    param (
        [string]$Path,
        [int]$Depth = 2,
        [int]$IndentLevel = 0
    )
 
    if ($Depth -eq 0) {
        return
    }
 
    Get-ChildItem -Path $Path | ForEach-Object {
        if ($_.PSIsContainer) {
            # 输出目录名，带缩进
            Write-Output ("  " * $IndentLevel + "├── " + $_.Name)
            # 递归处理子目录，缩进级别 +1
            Get-LimitedDepthFiles -Path $_.FullName -Depth ($Depth - 1) -IndentLevel ($IndentLevel + 1)
        } else {
            # 输出文件名，带缩进
            Write-Output ("  " * $IndentLevel + "├── " + $_.Name)
        }
    }
}

# 示例：显示 C:\ 目录下最多 2 层深度的文件和目录结构
Get-LimitedDepthFiles -Path "C:\" -Depth 2
```