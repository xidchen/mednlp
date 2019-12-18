import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
from tornado.options import options
from mednlp.service.entity_extract import EntityExtract
from mednlp.service.structure_service import MedicalRecord
from mednlp.service.knowledge_base import KnowledgeBase

runtime = {}

if __name__ == "__main__":
    tornado.options.parse_command_line()
    app = tornado.web.Application(handlers=[
        (r'/medical_record', MedicalRecord),
        (r'/entity_extract', EntityExtract),
        (r'/knowledge_base', KnowledgeBase, dict(runtime={})),

    ])

    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
