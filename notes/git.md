

# 自定义git命令
```shell

# 查看别名
git config --global --list | grep alias # 查看全局别名
git config --list | grep alias # 查看所有别名

git config --global --get-regexp alias  # 查看全局别名
git config --get-regexp alias          # 查看当前仓库的局部别名


# 设置别名(可直接覆盖)
# windows
git config --global alias.acp "!f() { git add . && git commit -m \"$1\" && git push; }; f"
# linux
git config --global alias.acp '!f() { git add . --all && git commit -m "$1" && git push; }; f'

# 删除别名
git config --global --unset alias.<别名名称>

```


# gitignore 忽略文件 生效
```shell
# 1. 先删除所有未忽略文件的缓存
git rm -r --cached .
 
# 2. 重新添加所有文件（此时会遵循 .gitignore 规则）
git add .
 
# 3. 提交更改
git commit -m "Refresh .gitignore rules"
```
