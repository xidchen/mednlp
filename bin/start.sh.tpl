#!/bin/bash

set -x

export CUDA_VISIBLE_DEVICES=

PORT=${SERVICE_PORT}
ENTITY_SERVICE_PORT=${ENTITY_SERVICE_PORT}
MAIN1_PORT=${MAIN1_PORT}
MAIN2_PORT=${MAIN2_PORT}
DEPT_CLASSIFY_PORT=${DEPT_CLASSIFY_PORT}
DIAGNOSE_SERVICE_PORT=${DIAGNOSE_SERVICE_PORT}
DIALOGUE_SERVICE_PORT=${DIALOGUE_SERVICE_PORT}
MEDICAL_SERVICE_PORT=${MEDICAL_SERVICE_PORT}
SUMMARY_EXTRACTION_PORT=${SUMMARY_EXTRACTION_PORT}
INTENTION_RECOGNITION_PORT=${INTENTION_RECOGNITION_PORT}
SENTENCE_SIMILARITY_PORT=${SENTENCE_SIMILARITY_PORT}
DIAGNOSE_LSTM_PORT=${DIAGNOSE_LSTM_PORT}
DIAGNOSE_SUGGEST_MODEL_PORT=${DIAGNOSE_SUGGEST_MODEL_PORT}
TMSERVER_HOME=$(dirname $(pwd))
AILIB_HOME=$(dirname $TMSERVER_HOME)/ailib
ONNET_HOME=$(dirname $TMSERVER_HOME)/onnet
DEEP_DIAGNOSIS_PORT=${DEEP_DIAGNOSIS_PORT}
DIAGNOSE_SUGGEST_PORT=${DIAGNOSE_SUGGEST_PORT}
DIAGNOSE_RELIABILITY_PORT=${DIAGNOSE_RELIABILITY_PORT}
SENTIMENT_SERVICE_PORT=${SENTIMENT_SERVICE_PORT}
CALCULATE_BREAST_CANCER_RISK_PORT=${CALCULATE_BREAST_CANCER_RISK_PORT}
BREAST_CANCER_RISK_PORT=${BREAST_CANCER_RISK_PORT}
CONSISTENCY_MODEL_PORT=${CONSISTENCY_MODEL_PORT}
SIMILARITY_FAQ_MODEL_PORT=${SIMILARITY_FAQ_MODEL_PORT}
MEDICAL_RECORD_GENERATOR_PORT=${MEDICAL_RECORD_GENERATOR_PORT}
TCM_DIAGNOSE_SERVICE_PORT=${TCM_DIAGNOSE_SERVICE_PORT}
MEDICAL_RECORD_COLLECTION_PORT=${MEDICAL_RECORD_COLLECTION_PORT}
SENTENCE_VECTOR_PORT=${SENTENCE_VECTOR_PORT}

PYTHON_EXCUTOR=${PYTHON_EXCUTOR}

export PYTHONPATH=$PYTHONPATH:$TMSERVER_HOME

PIDFILE=.cdss.pid
CIDFILE=.cdss.cid

cd $TMSERVER_HOME/bin

if [ ! $PYTHON_EXCUTOR ]; then
  PYTHON_EXCUTOR=python
fi

echo "python执行器:$PYTHON_EXCUTOR"

pid=
if [ -f "$PIDFILE" ]
then
    pid=`cat $PIDFILE`
    echo "tmserver($pid) already running"
    exit 1
fi

if [ -f "$CIDFILE" ]
then
    cid=`cat $CIDFILE`
    echo "container($cid) already running"
    exit 1
fi

echo $ENTITY_SERVICE_PORT | sed 's/,/\n/g' | while read PRT
    do
	    echo $PRT
		nohup $PYTHON_EXCUTOR ../mednlp/service/entity_service.py --port=$PRT > ../logs/entity_service.$PRT.log 2>&1 &
		pid=$!
		echo "$pid" >> $PIDFILE
		sleep 2
    done

echo $MAIN1_PORT | sed 's/,/\n/g' | while read PRT
    do
	    echo $PRT
		nohup $PYTHON_EXCUTOR ../mednlp/service/main1.py --port=$PRT > ../logs/main1.$PRT.log 2>&1 &
		pid=$!
		echo "$pid" >> $PIDFILE
		sleep 2
    done

echo $MAIN2_PORT | sed 's/,/\n/g' | while read PRT
    do
	    echo $PRT
		nohup $PYTHON_EXCUTOR ../mednlp/service/main2.py --port=$PRT > ../logs/main2.$PRT.log 2>&1 &
		pid=$!
		echo "$pid" >> $PIDFILE
		sleep 2
    done

echo $DEPT_CLASSIFY_PORT | sed 's/,/\n/g' | while read PRT
    do
	nohup docker run --rm -p $PRT:$PRT \
	-v $TMSERVER_HOME:/projects/mednlp \
	-v $AILIB_HOME:/projects/ailib/ailib \
	-v $ONNET_HOME:/projects/onnet \
	-e PYTHONPATH=:/projects/mednlp:/projects/ailib:/projects/onnet \
	--name=dept_classify_$PRT \
	-t realdoctor:v0.1 \
	python /projects/mednlp/mednlp/service/dept_classify.py --port=$PRT > \
	../logs/dept_classify.$PRT.log 2>&1 &
	sleep 1
	cid=$(docker ps|grep dept_classify_$PRT|awk '{print $1}')
    echo "pid:$PRT  cid:$cid"
	echo "$cid" >> $CIDFILE
    done

echo $DIAGNOSE_SERVICE_PORT | sed 's/,/\n/g' | while read PRT
    do
	    echo $PRT
		nohup $PYTHON_EXCUTOR ../mednlp/service/diagnose_service.py --port=$PRT > ../logs/diagnose_service.$PRT.log 2>&1 &
		pid=$!
		echo "$pid" >> $PIDFILE
		sleep 2
    done

echo $SENTENCE_VECTOR_PORT | sed 's/,/\n/g' | while read PRT
    do
      echo $PRT
      nohup $PYTHON_EXCUTOR ../mednlp/service/sentence_vector.py --port=$PRT > ../logs/sentence_vector.$PRT.log 2>&1 &
      pid=$!
      echo "$pid" >> $PIDFILE
      sleep 2
    done

echo $DIALOGUE_SERVICE_PORT | sed 's/,/\n/g' | while read PRT
    do
	    echo $PRT
		nohup $PYTHON_EXCUTOR ../mednlp/dialog/dialogue_service.py --port=$PRT > ../logs/dialogue_service.$PRT.log 2>&1 &
		pid=$!
		echo "$pid" >> $PIDFILE
		sleep 2
    done

echo $MEDICAL_SERVICE_PORT | sed 's/,/\n/g' | while read PRT
    do
	    echo $PRT
		nohup $PYTHON_EXCUTOR ../mednlp/service/ai_medical_service/medical_service.py --port=$PRT > ../logs/medical_service.$PRT.log 2>&1 &
		pid=$!
		echo "$pid" >> $PIDFILE
		sleep 2
    done

echo $SUMMARY_EXTRACTION_PORT | sed 's/,/\n/g' | while read PRT
    do
	    echo $PRT
		nohup $PYTHON_EXCUTOR ../mednlp/service/summary_extraction.py --port=$PRT > ../logs/summary_extraction.$PRT.log 2>&1 &
		pid=$!
		echo "$pid" >> $PIDFILE
		sleep 2
    done

echo $INTENTION_RECOGNITION_PORT | sed 's/,/\n/g' | while read PRT
    do
	    echo $PRT
		nohup $PYTHON_EXCUTOR ../mednlp/service/intention_recognition.py --port=$PRT > ../logs/intention_recognition.$PRT.log 2>&1 &
		pid=$!
		echo "$pid" >> $PIDFILE
		sleep 2
    done

echo $SENTENCE_SIMILARITY_PORT | sed 's/,/\n/g' | while read PRT
    do
	    echo $PRT
		nohup $PYTHON_EXCUTOR ../mednlp/service/sentence_similarity.py --port=$PRT > ../logs/sentence_similarity.$PRT.log 2>&1 &
		pid=$!
		echo "$pid" >> $PIDFILE
		sleep 2
    done

echo $DIAGNOSE_LSTM_PORT | sed 's/,/\n/g' | while read PRT
    do
	    echo $PRT
		nohup $PYTHON_EXCUTOR ../mednlp/service/diagnose_lstm.py --port=$PRT > ../logs/diagnose_lstm.$PRT.log 2>&1 &
		pid=$!
		echo "$pid" >> $PIDFILE
		sleep 2
    done

echo $DIAGNOSE_SUGGEST_MODEL_PORT | sed 's/,/\n/g' | while read PRT
    do
	    echo $PRT
		nohup $PYTHON_EXCUTOR ../mednlp/service/diagnose_suggest_model.py --port=$PRT > ../logs/diagnose_suggest_model.$PRT.log 2>&1 &
		pid=$!
		echo "$pid" >> $PIDFILE
		sleep 2
    done

echo $DIAGNOSE_SUGGEST_PORT | sed 's/,/\n/g' | while read PRT
    do
	    echo $PRT
		nohup $PYTHON_EXCUTOR ../mednlp/service/diagnose_suggest.py --port=$PRT > ../logs/diagnose_suggest.$PRT.log 2>&1 &
		pid=$!
		echo "$pid" >> $PIDFILE
		sleep 2
    done

echo $DEEP_DIAGNOSIS_PORT | sed 's/,/\n/g' | while read PRT
    do
	    echo $PRT
		nohup $PYTHON_EXCUTOR ../mednlp/service/deep_diagnosis.py --port=$PRT > ../logs/deep_diagnosis.$PRT.log 2>&1 &
		pid=$!
		echo "$pid" >> $PIDFILE
		sleep 2
    done

echo $DIAGNOSE_RELIABILITY_PORT | sed 's/,/\n/g' | while read PRT
    do
	    echo $PRT
		nohup $PYTHON_EXCUTOR ../mednlp/service/diagnose_reliability.py --port=$PRT > ../logs/diagnose_reliability.$PRT.log 2>&1 &
		pid=$!
		echo "$pid" >> $PIDFILE
		sleep 2
    done

echo $SENTIMENT_SERVICE_PORT | sed 's/,/\n/g' | while read PRT
    do
	    echo $PRT
		nohup $PYTHON_EXCUTOR ../mednlp/service/sentiment_service.py --port=$PRT > ../logs/sentiment_service.$PRT.log 2>&1 &
		pid=$!
		echo "$pid" >> $PIDFILE
		sleep 2
    done

echo $CALCULATE_BREAST_CANCER_RISK_PORT | sed 's/,/\n/g' | while read PRT
    do
	    echo $PRT
		nohup Rscript ../R/calculate_breast_cancer_risk.R $PRT > ../logs/calculate_breast_cancer_risk.$PRT.log 2>&1 &
		pid=$!
		echo "$pid" >> $PIDFILE
		sleep 2
    done

echo $BREAST_CANCER_RISK_PORT | sed 's/,/\n/g' | while read PRT
    do
	    echo $PRT
		nohup $PYTHON_EXCUTOR ../mednlp/service/breast_cancer_risk.py --port=$PRT > ../logs/breast_cancer_risk.$PRT.log 2>&1 &
		pid=$!
		echo "$pid" >> $PIDFILE
		sleep 2
    done

echo $CONSISTENCY_MODEL_PORT | sed 's/,/\n/g' | while read PRT
    do
	    echo $PRT
		nohup $PYTHON_EXCUTOR ../mednlp/service/consistency_service.py --port=$PRT > ../logs/consistency_service.$PRT.log 2>&1 &
		pid=$!
		echo "$pid" >> $PIDFILE
		sleep 2
    done

echo $SIMILARITY_FAQ_MODEL_PORT | sed 's/,/\n/g' | while read PRT
    do
	    echo $PRT
		nohup $PYTHON_EXCUTOR ../mednlp/service/similarity_faq_service.py --port=$PRT > ../logs/similarity_faq_service.$PRT.log 2>&1 &
		pid=$!
		echo "$pid" >> $PIDFILE
		sleep 2
    done

echo $MEDICAL_RECORD_GENERATOR_PORT | sed 's/,/\n/g' | while read PRT
    do
	    echo $PRT
		nohup $PYTHON_EXCUTOR ../mednlp/service/medical_record_generator.py --port=$PRT > ../logs/medical_record_generator.$PRT.log 2>&1 &
		pid=$!
		echo "$pid" >> $PIDFILE
		sleep 2
    done

echo $TCM_DIAGNOSE_SERVICE_PORT | sed 's/,/\n/g' | while read PRT
    do
	    echo $PRT
		nohup $PYTHON_EXCUTOR ../mednlp/service/tcm_diagnose_service.py --port=$PRT > ../logs/tcm_diagnose_service.$PRT.log 2>&1 &
		pid=$!
		echo "$pid" >> $PIDFILE
		sleep 2
    done

echo $MEDICAL_RECORD_COLLECTION_PORT | sed 's/,/\n/g' | while read PRT
    do
	    echo $PRT
		nohup $PYTHON_EXCUTOR ../mednlp/service/medical_record_collection_service.py --port=$PRT > ../logs/medical_record_collection_service.$PRT.log 2>&1 &
		pid=$!
		echo "$pid" >> $PIDFILE
		sleep 2
    done

