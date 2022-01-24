import grpc
from google.protobuf.empty_pb2 import Empty

from auth import GrpcAuth
from protobufs.reports_pb2_grpc import ReportsStub

ACCESS_TOKEN = 'adminp63RHOqLSUKhB7ca5YJ2jTILvPcWRvYcGUt2Vo'

with open('server.crt', 'rb') as f:
    trusted_certs = f.read()

ssl_credentials = grpc.ssl_channel_credentials(root_certificates=trusted_certs)
access_token_credentials = grpc.metadata_call_credentials(GrpcAuth(ACCESS_TOKEN))


channel = grpc.secure_channel(
    'localhost:50051',
    grpc.composite_channel_credentials(ssl_credentials, access_token_credentials)
)
client = ReportsStub(channel)

if __name__ == '__main__':
    # reports client demo
    print('requesting GetUsersRoutesLengthReport')
    response = client.GetUsersRoutesLengthReport(Empty())
    print(response)
