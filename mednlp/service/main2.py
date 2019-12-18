import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
from tornado.options import options
from mednlp.service.knowledge_graph import KnowledgeGraph
from mednlp.service.dept_classify_interactive import DeptClassifyInteractive
from mednlp.service.check_prescription import CheckPrescription, set_gray
from ailib.service.service_maintenance import ServiceMaintenance
from mednlp.service.previous_diagnose import PreviousDiagnose
from mednlp.service.auto_diagnose import AutoDiagnose
from mednlp.dialog.content_generation import ContentGeneration
from mednlp.service.label_flow import LabelFlow
from mednlp.service.label_conversion import LabelConversion
from mednlp.service.reason_medicine_check import ReasonMedicineCheck
from mednlp.service.union_knowledge_service import UnionKnowledgeService
from mednlp.service.treatment_plan_recommend import TreatmentPlanRecommend
from mednlp.service.examination_explain import Examination
from mednlp.service.similarity_faq_service import SimilarityFAQService
from mednlp.service.kg_bussiness_label import KgBusinessLabel
from mednlp.service.prescription_screening import PrescriptionScreening
from mednlp.service.prescription_recommendation import PrescriptionRecommendation
from mednlp.service.diagnosed_referral_remind_service import DiagnosedReferralRemind
from mednlp.service.critical_detection import CriticalDetection
from mednlp.service.hop_service import HumanOrPet

sm_dict = {'check_prescription': {'conf_gray': set_gray}}

if __name__ == "__main__":
    tornado.options.parse_command_line()
    app = tornado.web.Application(handlers=[
        (r'/knowledge_graph', KnowledgeGraph),
        (r'/dept_classify_interactive', DeptClassifyInteractive),
        (r'/check_prescription', CheckPrescription, dict(runtime={})),
        (r'/previous_diagnose', PreviousDiagnose),
        (r'/auto_diagnose', AutoDiagnose),
        (r'/content_generation', ContentGeneration, dict(runtime={})),
        (r'/service_maintenance', ServiceMaintenance, dict(sm_dict=sm_dict)),
        (r'/label_flow', LabelFlow, dict(runtime={})),
        (r'/label_conversion', LabelConversion, dict(runtime={})),
        (r'/reason_medicine_check', ReasonMedicineCheck, dict(runtime={})),
        (r'/union_knowledge', UnionKnowledgeService, dict(runtime={})),
        (r'/treatment_plan_recommend', TreatmentPlanRecommend, dict(runtime={})),
        (r'/medical_examination', Examination, dict(runtime={})),
        (r'/similarity_faq', SimilarityFAQService, dict(runtime={})),
        (r'/kg_business_label', KgBusinessLabel, dict(runtime={})),
        (r'/prescription_screening', PrescriptionScreening, dict(runtime={})),
        (r'/prescription_recommendation', PrescriptionRecommendation, dict(runtime={})),
        (r'/diagnosed_referral_remind', DiagnosedReferralRemind, dict(runtime={})),
        (r'/critical_detection', CriticalDetection, dict(runtime={})),
        (r'/human_or_pet', HumanOrPet, dict(runtime={}))
    ])

    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
