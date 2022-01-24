import grpc

from models import User


def authenticate(fn):
    """Decorator for servicer methods,
    authenticating user based on metadata header"""
    def wrapper(self, request, context):
        meta = context.invocation_metadata()
        if meta[0] and meta[0].key == 'rpc-auth-header':
            user = User.q.filter(User.auth_token == meta[0].value).scalar()
            if user:
                return fn(self, request, context, user)

        return context.abort(grpc.StatusCode.UNAUTHENTICATED, 'Invalid key')
    return wrapper


class GrpcAuth(grpc.AuthMetadataPlugin):
    """GRPC client token authentication extension"""
    def __init__(self, key):
        self._key = key

    def __call__(self, context, callback):
        callback((('rpc-auth-header', self._key),), None)
