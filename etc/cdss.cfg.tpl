# [MySQLDB]
# HOST = ${MYSQL_DB_HOST}
# USER = ${MYSQL_DB_USER}
# PASS = ${MYSQL_DB_PASS}
# PORT = ${MYSQL_DB_PORT}

[KnowledgeGraphSQLDB]
HOST = ${KNOWLEDGE_GRAPH_DB_HOST}
USER = ${KNOWLEDGE_GRAPH_DB_USER}
PASS = ${KNOWLEDGE_GRAPH_DB_PASS}
PORT = ${KNOWLEDGE_GRAPH_DB_PORT}

# [AIMySQLDB]
# HOST = ${AI_MYSQL_DB_HOST}
# USER = ${AI_MYSQL_DB_USER}
# PASS = ${AI_MYSQL_DB_PASS}
# PORT = ${AI_MYSQL_DB_PORT}

# [RDMySQLDB]
# HOST = ${RD_MYSQL_DB_HOST}
# USER = ${RD_MYSQL_DB_USER}
# PASS = ${RD_MYSQL_DB_PASS}
# PORT = ${RD_MYSQL_DB_PORT}

# [XWYZMySQLDB]
# HOST = ${XWYZ_MYSQL_DB_HOST}
# USER = ${XWYZ_MYSQL_DB_USER}
# PASS = ${XWYZ_MYSQL_DB_PASS}
# PORT = ${XWYZ_MYSQL_DB_PORT}

# [SearchMySQLDB]
# HOST = ${SEARCH_MYSQL_DB_HOST}
# USER = ${SEARCH_MYSQL_DB_USER}
# PASS = ${SEARCH_MYSQL_DB_PASS}
# PORT = ${SEARCH_MYSQL_DB_PORT}

[HiveDB]
HOST = ${CARBONDATA_HOST}
USER = ${CARBONDATA_USER}
PASS = ${CARBONDATA_PASS}
PORT = ${CARBONDATA_PORT}

[SparkDB]
HOST = ${SPARK_HOST}
USER = ${SPARK_USER}
PASS = ${SPARK_PASS}
PORT = ${SPARK_PORT}


[Solr]
IP = ${SOLR_IP}
PORT = ${SOLR_PORT}
SolrPost = ${SOLR_POST_PORT}
DEBUG = ${SOLR_DEBUG}
ZK = ${ZK_HOST}

[SolrPost]
IP = ${SOLR_POST_IP}
PORT = ${SOLR_POST_PORT}

[CloudIndex]
IP = ${CLOUD_INDEX_IP}
PORT = ${CLOUD_INDEX_PORT}
PRIMARY_KEY = ${CLOUD_PRIMARY_KEY}
GROUP_PRIMARY_KEY = ${CLOUD_GROUP_PRIMARY_KEY}
DEBUG = ${CLOUD_DEBUG}

[TFServing]
IP = ${TF_SERVING_IP}
PORT = ${TF_SERVING_PORT}
BASE_URL = ${TF_SERVING_BASE_URL}

[Index]
FULL_DIR = ${INDEX_FULL_DIR}
INCREMENTAL_DIR = ${INDEX_INCREMENTAL_DIR}

[AIService]
IP = ${AI_SERVICE_IP}
PORT = ${AI_SERVICE_PORT}
DEBUG = ${AI_SERVICE_DEBUG}
URL_PATH = ${AI_URL_PATH}

[OuterService]
URL_PATH = ${OUTER_SERVICE_URL_PATH}

[DISEASE_CLASSIFY_MODEL]
path = ${DISEASE_CLASSIFY_MODEL_PATH}

[SENTIMENT_CLASSIFY_MODEL]
path = ${SENTIMENT_CLASSIFY_MODEL_PATH}

[CHECK_CLASSIFY_MODEL]
path = ${CHECK_CLASSIFY_MODEL_PATH}

[DEPT_CLASSIFY_MODEL]
url = ${DEPT_CLASSIFY_MODEL_URL}
path = ${DEPT_CLASSIFY_MODEL_PATH}

[DEPT_CLASSIFY_PINYIN_MODEL]
url = ${DEPT_CLASSIFY_PINYIN_MODEL_URL}
path = ${DEPT_CLASSIFY_PINYIN_MODEL_PATH}

[DEPT_CLASSIFY_CHAR_PINYIN_MODEL]
url = ${DEPT_CLASSIFY_CHAR_PINYIN_MODEL_URL}
path = ${DEPT_CLASSIFY_CHAR_PINYIN_MODEL_PATH}

[DEPT_CLASSIFY_TEXTCNN_MODEL]
url = ${DEPT_CLASSIFY_TEXTCNN_MODEL_URL}
path = ${DEPT_CLASSIFY_TEXTCNN_MODEL_PATH}

[HUMAN_OR_PET_MODEL]
path = ${HUMAN_OR_PET_MODEL_PATH}

[INTELLIGENCE_CLASSIFY_MODEL]
path = ${INTELLIGENCE_CLASSIFY_MODEL_PATH}

[INTELLIGENCE_CLASSIFY_PINYIN_MODEL]
path = ${INTELLIGENCE_CLASSIFY_PINYIN_MODEL_PATH}

[INTELLIGENCE_CLASSIFY_TEXTCNN_MODEL]
path = ${INTELLIGENCE_CLASSIFY_TEXTCNN_MODEL_PATH}

[SENTENCE_SIMILARITY_MODEL]
path = ${SENTENCE_SIMILARITY_MODEL_PATH}

[INTENTION_CLASSIFY_UNION_MODEL]
path = ${INTENTION_CLASSIFY_WORD_UNION_MODEL_PATH}

[PINYIN2CHN_MODEL]
path = ${PINYIN2CHN_MODEL_PATH}

[CRF_MODEL]
path = ${CRF_MODEL_PATH}

[DIAGNOSE_RELIABILITY_MODEL]
path = ${DIAGNOSE_RELIABILITY_MODEL_PATH}

[TCM_DIAGNOSE_MODEL]
path = ${TCM_DIAGNOSE_MODEL_PATH}

[ORDER_CHECK_STANDARD]
is_proactive_url = ${ORDER_CHECK_STANDARD_IS_PROACTIVE_URL}
is_detailed_url = ${ORDER_CHECK_STANDARD_IS_DETAILED_URL}
is_clear_url = ${ORDER_CHECK_STANDARD_IS_CLEAR_URL}
is_warm_url = ${ORDER_CHECK_STANDARD_IS_WARM_URL}
is_review_url = ${ORDER_CHECK_STANDARD_IS_REVIEW_URL}

[QueryAnalyzer]
IP = ${QA_SERVICE_IP}
PORT = ${QA_SERVICE_PORT}
DEBUG = ${QA_SERVICE_DEBUG}

[SearchService]
IP = ${SEARCH_SERVICE_IP}
PORT = ${SEARCH_SERVICE_PORT}
DEBUG = ${SEARCH_SERVICE_DEBUG}

[WangXunKeFuService]
host = ${WANGXUNKEFU_SERVICE_HOST}

[XwyzOrganization]
organization = ${XWYZ_ORGANIZATION}
question_config_organization = ${QUESTION_CONFIG_ORGANIZATION}

[XwyzDoctorOrganization]
organization = ${XWYZ_DOCTOR_ORGANIZATION}

[DeepDiagnosis]
organizecode = ${DEEP_DIAGNOSIS_ORGANIZECODE}
rulegroupname = ${DEEP_DIAGNOSIS_RULEGROUPNAME}

[GP]
organization = ${GP_ORGANIZATION}

[DataStatistics]
log_dir = ${Data_Statistics_LOG_DIR}

[SEARCH_PLATFORM_SOLR]
IP = ${SEARCH_PLATFORM_SOLR_IP}
PORT = ${SEARCH_PLATFORM_SOLR_PORT}
DEBUG = ${SEARCH_PLATFORM_SOLR_DEBUG}
CAT_DIAGNOSISMEDICINE = ${SEARCH_PLATFORM_SOLR_CAT_DIAGNOSISMEDICINE}
CAT_DIAGNOSISMEDICINE_PRIMARYKEY = ${SEARCH_PLATFORM_SOLR_CAT_DIAGNOSISMEDICINE_PRIMARYKEY}
CAT_AI_DOCTOR_SEARCH_PRIMARTKEY = ${SEARCH_PLATFORM_SOLR_CAT_AI_DOCTOR_SEARCH_PRIMARTKEY}
CAT_HOSP_DEPT_MAPPING_PRIMARYKEY = ${SEARCH_PLATFORM_SOLR_CAT_AI_HOSP_DEPT_MAPPING_PRIMARTKEY}
CAT_AI_SIMILARITY_FAQ_PRIMARYKEY = ${SEARCH_PLATFORM_SOLR_CAT_AI_SIMILARITY_FAQ_PRIMARTKEY}
CAT_QUESTION_SENTENCE_PRIMARYKEY = ${SEARCH_PLATFORM_SOLR_CAT_AI_QUESTION_SENTENCE_PRIMARTKEY}
CAT_RECOMMENDED_QUESTION_PRIMARYKEY = ${SEARCH_PLATFORM_SOLR_CAT_AI_RECOMMENDED_QUESTION_PRIMARTKEY}
CAT_AI_CRITICAL_DISEASE_SEARCH = ${SEARCH_PLATFORM_SOLR_CAT_AI_CRITICAL_DISEASE_SEARCH}
CAT_AI_QUESTION_PRIMARYKEY = ${SEARCH_PLATFORM_SOLR_CAT_AI_QUESTION_PRIMARYKEY}
CAT_QUESTION_ANSWER_PRIMARYKEY = ${SEARCH_PLATFORM_SOLR_CAT_QUESTION_ANSWER_PRIMARYKEY}

[INTELLIGENCE_SERVICE_CHECK_MODEL]
path = ${INTELLIGENCE_SERVICE_CHECK_MODEL_PATH}

[CONSISTENCY_MODEL]
path = ${CONSISTENCY_MODEL_PATH}

[MONGOBD_HEALTH_RECORD]
HOST = ${MONGODB_HOST}
USER = ${MONGODB_USER}
PASS = ${MONGODB_PASS}
PORT = ${MONGODB_PORT}

[ZookeeperRegister]
HOST=${ZK_REGISTER_HOST}
PARENT_NODE=${ZK_REGISTER_PARENT_NODE}


[KG_BUSINESS_LABEL]
LABEL_CONFIG_FILE_NAME = ${KG_BUSINESS_LABEL_FILE_NAME}

[REASON_MEDICINE]
FILE = ${REASON_MEDICINE_FILE}

[Prescription_Screening]
FILE = ${Prescription_Screening_FILE}
RULE_ENGINE_ORGANIZE_CODE = ${REASON_MEDICINE_ORGANIZE_CODE}
RULE_ENGINE_RULE_GROUP_NAME = ${REASON_MEDICINE_RULE_GROUP_NAME}

[TREATMENT_PLAN_RECOMMEND]
RULE_SYSTEM_LABEL = ${RULE_SYSTEM_LABEL}
STANDARD_RULE_CODE = ${STANDARD_RULE_CODE}
