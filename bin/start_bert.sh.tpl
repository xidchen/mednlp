#!/bin/bash

set -x

export CUDA_VISIBLE_DEVICES=


PORT=${BERT_PORT}
PORT_OUT=${BERT_PORT_OUT}
SERVICE_PORT=${BERT_SERVICE_PORT}
NUM_WORKER=${BERT_NUM_WORKER}
MODEL_PATH=${BERT_MODEL_PATH}
POOLING_lAYER=${BERT_POOLING_lAYER}
TMP_PATH=${BERT_TMP_PATH}

pid=

nohup bert-serving-start -model_dir $MODEL_PATH -num_worker=$NUM_WORKER -http_port=$SERVICE_PORT -port=$PORT -port_out=$PORT_OUT -pooling_layer=$POOLING_lAYER -cpu -graph_tmp_dir=$TMP_PATH > $TMP_PATH/bert_service.log 2>&1 &
pid=$!
sleep 2
echo "bert服务启动,pid:$pid"
ps ux | awk '$12 ~ /bert-serving-start/ {print $2}' | xargs -I {} echo {}