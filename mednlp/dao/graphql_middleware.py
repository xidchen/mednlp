import logging
import global_conf
from graphene import Scalar, List
from time import time as timer
from ailib.utils.log import GLLog
logger = GLLog('graphql_field_resolve', log_dir=global_conf.log_dir, level='info').getLogger()


class GraphQlMiddleWare:
    @staticmethod
    def timing_middleware(next, root, info, **args):
        if not root or info.field_name.endswith('_relation'):
            start = timer()
            return_value = next(root, info, **args)
            duration = timer() - start
            logger.info("{parent_type}.{field_name}: {duration} ms".format(
                parent_type=root._meta.name if root and hasattr(root, '_meta') else '',
                field_name=info.field_name,
                duration=round(duration * 1000, 2)
            ))
            return return_value
        else:
            return next(root, info, **args)
