from config import Settings, setup
from models import User, Route, WayPoint, Point


if __name__ == '__main__':
    """Recreates database schema and seeds it with sample data"""

    setup(Settings())

    s = User.q.session

    User.metadata.drop_all(bind=s.get_bind())
    User.metadata.create_all(bind=s.get_bind())

    admin = User(username='admin', password='admin', auth_token='adminp63RHOqLSUKhB7ca5YJ2jTILvPcWRvYcGUt2Vo')
    guest = User(username='guest', password='guest', auth_token='guestqt1vM8d0CrR2k31rymbEtnbjKFRdvtZtB9TnlI')
    root = User(username='root', password='root', auth_token='root--MSL9wJ0FFE02cuz-HqWmO6FJvj1cdxdu5Eh-A')
    s.add_all([admin, guest, root])

    s.execute('INSERT INTO point(name, geo) '
              "SELECT md5(random()::text), ST_SetSRID(ST_MakePoint(random(), random()), 4326) "
              'from generate_series(1, 1000000) s(i)')
    s.commit()

    r43 = Route(name='43', user=admin)
    r53 = Route(name='53', user=admin)
    s.add_all([r43, r53])
    s.commit()

    p1, p2, p3, p4 = Point.q.limit(4).all()

    wp1 = WayPoint.append(p1, r43)
    wp2 = WayPoint.append(p2, r43)
    wp3 = WayPoint.append(p3, r53)
    wp4 = WayPoint.append(p4, r53)

    s.commit()
