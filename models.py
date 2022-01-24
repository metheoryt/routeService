import sqlalchemy_utils as su
from sqlalchemy import ForeignKey, Column, Integer, String, Float, func
from geoalchemy2 import Geography, Geometry
from sqlalchemy.orm import declarative_base, relation, column_property
import secrets

from sqlalchemy import create_engine
from sqlalchemy.orm.scoping import scoped_session
from sqlalchemy.orm import sessionmaker


Session = sessionmaker()
ScopedSession = scoped_session(Session)


def configure(dsn: str, echo: bool = False):
    Session.configure(bind=create_engine(dsn, echo=echo))


_Model = declarative_base()


class Model(_Model):
    __abstract__ = True
    q = ScopedSession.query_property()


class User(Model):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=False, unique=True)
    password = Column(su.PasswordType(schemes=['pbkdf2_sha512']), nullable=False)
    auth_token = Column(String)

    def reissue_auth_token(self):
        self.auth_token = secrets.token_urlsafe(32)
        return self.auth_token

    def __repr__(self):
        return f'<User #{self.id} {self.username}>'


class Point(Model):
    __tablename__ = 'point'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    geo = Column(Geometry('POINT', 4326), nullable=False)
    lon = column_property(func.ST_X(geo))
    lat = column_property(func.ST_Y(geo))
    waypoints = relation('WayPoint', uselist=True, back_populates='point')

    def __repr__(self):
        return f'<Point "{self.name} {self.lon}/{self.lat}">'


class Route(Model):
    __tablename__ = 'route'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)

    user_id = Column(Integer, ForeignKey('user.id'))
    user = relation('User', lazy='joined')

    waypoints = relation('WayPoint', back_populates='route', lazy='dynamic')

    def __repr__(self):
        return f'<Route {self.route_num}>'


class WayPoint(Model):
    __tablename__ = 'waypoint'

    id = Column(Integer, primary_key=True, autoincrement=True)
    serial = Column(Integer, default=1)
    """Serial number of waypoint in a route. 1 - last waypoint"""

    route_id = Column(Integer, ForeignKey('route.id'), index=True)
    route = relation('Route', uselist=False, lazy='joined', back_populates='waypoints')

    point_id = Column(Integer, ForeignKey('point.id'))
    point = relation('Point', uselist=False, lazy='joined', back_populates='waypoints')

    @classmethod
    def append(cls, point: 'Point', route: 'Route') -> 'WayPoint':
        """Adds the point to the end of the route.
        Does not commit."""
        cls.q.filter(cls.route == route).update({'serial': cls.serial + 1})
        wp = cls(route=route, point=point)
        cls.q.session.add(wp)
        return wp

    def __repr__(self):
        return f'<WayPoint {self.route.route_num}/{self.point.name} #{self.serial_num}>'
