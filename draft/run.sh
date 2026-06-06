#!/bin/bash

action='restart'

start_cmd="export CREST_ENV=pro && nohup /opt/miniconda3/envs/crest/bin/uvicorn main:app --host 192.168.100.240 --port 3014 --app-dir /data/fastapi_projects/crest >> crest.log 2>&1 &"
pids_cmd="ps aux | grep crest/bin/uvicorn | grep -v grep | awk '{print \$2}'"

tmp_pids=''
max_attempts=10  # 最大检查次数
interval=0.5     # 检查间隔（秒）

help_text=`cat <<EOF
help_doc:
  -a | --action      restart|stop|start|status
  -h | --help        查看帮助文档

EOF`

GETOPT_ARGS=$(getopt -o a:,h -al action:,help -- "$@")

#eval 确保 getopt 的输出（可能包含引号或特殊字符）被正确解析。
#set -- 将解析后的参数重新赋值给 $1, $2 等位置参数
eval set -- "$GETOPT_ARGS"
while [ -n "$1" ]
do
    case "$1" in
        -a | --action) test -z $2 || action=$2; shift 2;;  # shift n  消耗n个位置参数,以便下次循环还是从$1判断
        -h | --help) echo "$help_text" && exit 0; shift 1;;
        --) break;;
        *) echo "Error: Unknown option $1 $2"; exit 1;;
    esac
done

get_pids(){
    echo "$pids_cmd"
    tmp=$(eval "$pids_cmd")
    tmp_pids=`echo $tmp | tr ' ' ',' | sed 's/,$//'`
}

start(){
    get_pids
    if [ -n "$tmp_pids" ];then
        echo "service already running in pids:$tmp_pids."
    else
        # echo "$start_cmd"
        eval "$start_cmd"
        get_pids
        if [ -n "$tmp_pids" ];then
            echo "service start running in pids:$tmp_pids."
        else
            echo "service start failed."
        fi
    fi    
}

stop(){
    get_pids
    if [ -n "$tmp_pids" ];then
        echo "Running on PID <$tmp_pids>. Killing it..."
        kill -9 $tmp_pids
        echo $?
        for i in $(seq 1 $max_attempts);do
            get_pids
            if [ -n "$tmp_pids" ];then
                echo "process is running #$tmp_pids# (detected on attempt $i)."
                sleep $interval
            else 
                break
            fi
        done
    else 
        echo "No Running service."
    fi
}

status(){
    get_pids
    if [ -n "$tmp_pids" ];then
        echo "Running on PID <$tmp_pids>."
    else
        echo "No Running service."
    fi
}


if [ $action = "start" ];then
   start
elif [ $action = 'stop' ];then
   stop
elif [ $action = 'restart' ];then
   stop
   start
elif [ $action = 'status' ];then
   status
else
   echo "--action|-a [$action] undefined"
fi

