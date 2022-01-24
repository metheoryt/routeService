import logging
from concurrent import futures
from random import randint

import grpc
from sqlalchemy import func

import config
from auth import authenticate
from models import Point, Route, User, WayPoint
from protobufs import routes_pb2 as msg, routes_pb2_grpc as rpc

log = logging.getLogger(__name__)


class RoutesServicer(rpc.RoutesServicer):

    @authenticate
    def GetPoints(self, request: msg.GetPointsRequest, context, user: User):
        points = Point.q.filter(Point.id.in_(request.point_ids)).all()
        return msg.GetPointsResponse(points=[
            msg.Point(
                id=p.id,
                name=p.name,
                latitude=p.lat,
                longitude=p.lon
            ) for p in points
        ])

    @authenticate
    def GetRoutes(self, request: msg.GetRoutesRequest, context, user: User):
        if not request.username and not request.route_ids:
            context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                "Either username or route ids should be specified"
            )

        q = Route.q
        if request.username:
            q = q.filter(Route.user.has(username=request.username))
        if request.route_ids:
            q = q.filter(Route.id.in_(request.route_ids))

        routes = q.all()
        return msg.GetRoutesResponse(routes=[
            msg.Route(
                id=r.id,
                name=r.name,
                waypoints=[
                    msg.WayPoint(
                        id=w.id,
                        serial=w.serial,
                        point=msg.Point(
                            id=w.point.id,
                            name=w.point.name,
                            latitude=w.point.lat,
                            longitude=w.point.lon
                        )) for w in r.waypoints]
                ) for r in routes])

    @authenticate
    def CalculateRoute(self, request: msg.CalculateRouteRequest, context, user: User):
        """Returns "shortest" route between source and destination points.
        Does not create a route, so route id, name and waypoint id fields are empty.
        """
        point_a = Point.q.get(request.a_point_id)
        point_b = Point.q.get(request.b_point_id)
        if not point_a or not point_b:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "One or both of points do not exists")

        points = [point_b, *Point.q.order_by(func.random()).limit(randint(2, 100)).all(), point_a]

        route = msg.Route(waypoints=[
            msg.WayPoint(
                serial=i+1,
                point=msg.Point(
                    id=p.id,
                    name=p.name,
                    latitude=p.lat,
                    longitude=p.lon
                )
            ) for i, p in enumerate(points)
        ])
        return msg.RouteResponse(route=route)

    @authenticate
    def CreateRoute(self, request: msg.CreateRouteRequest, context, user: User):
        """Creates route for the user from existing points"""
        route = Route(name=request.route_name, user=user)
        Route.q.session.add(route)
        Route.q.session.commit()
        for point_id in request.point_ids:
            point = Point.q.get(point_id)
            WayPoint.append(point, route)
        WayPoint.q.session.commit()

        return msg.RouteResponse(route=msg.Route(
            id=route.id,
            name=route.name,
            waypoints=[msg.WayPoint(
                id=w.id,
                serial=w.serial,
                point=msg.Point(
                    id=w.point.id,
                    name=w.point.name,
                    latitude=w.point.lat,
                    longitude=w.point.lon
                )
            ) for w in route.waypoints]
        ))


def serve():
    settings = config.Settings()
    config.setup(settings)

    with open(settings.server_key_path, 'rb') as f:
        private_key = f.read()
    with open(settings.server_cert_path, 'rb') as f:
        certificate_chain = f.read()

    server_credentials = grpc.ssl_server_credentials(
        ((private_key, certificate_chain,),))

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    rpc.add_RoutesServicer_to_server(RoutesServicer(), server)
    server.add_secure_port(settings.server_listening_interface, server_credentials)
    server.start()
    server.wait_for_termination()
