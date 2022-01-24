import grpc

import protobufs.routes_pb2 as msg
from auth import GrpcAuth
from protobufs.routes_pb2_grpc import RoutesStub
import logging


ACCESS_TOKEN = 'adminp63RHOqLSUKhB7ca5YJ2jTILvPcWRvYcGUt2Vo'

with open('server.crt', 'rb') as f:
    trusted_certs = f.read()

ssl_credentials = grpc.ssl_channel_credentials(root_certificates=trusted_certs)
access_token_credentials = grpc.metadata_call_credentials(GrpcAuth(ACCESS_TOKEN))


channel = grpc.secure_channel(
    'localhost:50051',
    grpc.composite_channel_credentials(ssl_credentials, access_token_credentials)
)
client = RoutesStub(channel)

if __name__ == '__main__':
    # routes client demo
    logging.basicConfig(format='%(asctime)s %(levelname)-8s %(name)-12s %(message)s', level=logging.INFO)

    logging.info('requesting GetPoints')
    rs = client.GetPoints(msg.GetPointsRequest(point_ids=[1, 57, 973]))
    logging.info(rs)

    logging.info('requesting GetRoutes')
    rs = client.GetRoutes(msg.GetRoutesRequest(username='admin'))
    logging.info(rs)

    logging.info('requesting CalculateRoute')
    calc_rs = client.CalculateRoute(msg.CalculateRouteRequest(a_point_id=1, b_point_id=617))
    logging.info(calc_rs)

    logging.info('requesting CreateRoute')
    rs = client.CreateRoute(msg.CreateRouteRequest(
        point_ids=[w.point.id for w in calc_rs.route.waypoints],
        route_name=f'{len(calc_rs.route.waypoints)} generated'
    ))
    logging.info(rs)
