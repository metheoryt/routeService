import logging
from concurrent import futures

import grpc
from sqlalchemy import func, and_
from sqlalchemy.orm import aliased

import config
from models import Point, Route, User, WayPoint
from protobufs import reports_pb2_grpc as rpc, reports_pb2 as msg

log = logging.getLogger(__name__)


class ReportsServicer(rpc.ReportsServicer):

    def GetUsersRoutesLengthReport(self, request, context):
        wp1 = aliased(WayPoint)
        wp2 = aliased(WayPoint)
        p1 = aliased(Point)
        p2 = aliased(Point)

        q = User.q\
            .join(Route)\
            .join(wp1)\
            .join(wp2, and_(wp1.route_id == wp2.route_id, wp1.serial == wp2.serial - 1))\
            .join(p1, wp1.point_id == p1.id)\
            .join(p2, wp2.point_id == p2.id)\
            .with_entities(
                User.id,
                func.count(Route.id),
                func.sum(func.ST_DistanceSphere(p1.geo, p2.geo))  # in meters
            ).group_by(User.id)

        return msg.UserRoutesLengthReportResponse(records=[
            msg.UserRoutesLengths(
                user_id=record[0],
                routes_count=record[1],
                routes_total_length_meters=record[2]
            ) for record in q
        ])


def serve():
    settings = config.Settings()
    config.setup(settings)

    with open(settings.server_key_path, 'rb') as f:
        private_key = f.read()
    with open(settings.server_cert_path, 'rb') as f:
        certificate_chain = f.read()

    server_credentials = grpc.ssl_server_credentials(
        ((private_key, certificate_chain,),)
    )

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    rpc.add_ReportsServicer_to_server(ReportsServicer(), server)
    server.add_secure_port(settings.server_listening_interface, server_credentials)
    server.start()
    server.wait_for_termination()
