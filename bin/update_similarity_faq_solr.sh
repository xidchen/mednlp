#!/bin/bash

echo `date`
FILE_FOLDER=$(cd "$(dirname "$0")";pwd)
MEDNLP_FOLDER=$(dirname $FILE_FOLDER)
WORK_FOLDER=$(dirname $MEDNLP_FOLDER)
export PYTHONPATH=$PYTHONPATH:$MEDNLP_FOLDER
export PYTHONPATH=$PYTHONPATH:$WORK_FOLDER

~/anaconda3/bin/python $MEDNLP_FOLDER/mednlp/kg/index_task/index_similarity_faq_relation.py
