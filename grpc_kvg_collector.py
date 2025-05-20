
import grpc
import time
from concurrent import futures
from influxdb import InfluxDBClient
import telemetry_pb2
import telemetry_pb2_grpc

from google.protobuf.internal.decoder import _DecodeVarint32
from google.protobuf.internal.encoder import _EncodeVarint

class MDTReceiver(telemetry_pb2_grpc.gRPCMdtDialoutServicer):
    def __init__(self):
        self.influx = InfluxDBClient(host='localhost', port=8086, database='telemetry')
        try:
            self.influx.create_database('telemetry')
        except:
            pass

    def MdtDialout(self, request_iterator, context):
        print("🚦 gRPC connection started")
        for message in request_iterator:
            try:
                sensor = message.sensor_path
                node = message.node_id_str
                print(f"📡 Message from {node} | Path: {sensor} | Bytes: {len(message.data_gpbkv)}")

                json_body = [
                    {
                        "measurement": "raw_telemetry",
                        "tags": {
                            "node": node,
                            "path": sensor
                        },
                        "fields": {
                            "length": len(message.data_gpbkv)
                        },
                        "time": time.time_ns()
                    }
                ]
                self.influx.write_points(json_body)
            except Exception as e:
                print(f"❌ Error decoding message: {e}")
        print("🔌 gRPC stream closed")
        return telemetry_pb2.Response(message="Telemetry received")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    telemetry_pb2_grpc.add_gRPCMdtDialoutServicer_to_server(MDTReceiver(), server)
    server.add_insecure_port("[::]:57500")
    print("✅ Listening on port 57500 for telemetry...")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
