
import grpc
from concurrent import futures
import telemetry_pb2
import telemetry_pb2_grpc
from influxdb import InfluxDBClient
import time

class MDTReceiver(telemetry_pb2_grpc.gRPCMdtDialoutServicer):
    def __init__(self):
        self.influx = InfluxDBClient(host='localhost', port=8086, database='telemetry')
        try:
            self.influx.create_database('telemetry')
        except:
            pass

    def MdtDialout(self, request_iterator, context):
        for message in request_iterator:
            print(f"📡 Received from {message.node_id_str} - Sensor: {message.sensor_path}")
            json_body = [
                {
                    "measurement": "raw_telemetry",
                    "tags": {
                        "node": message.node_id_str,
                        "path": message.sensor_path
                    },
                    "fields": {
                        "length": len(message.data_gpbkv)
                    },
                    "time": time.time_ns()
                }
            ]
            self.influx.write_points(json_body)
        return telemetry_pb2.Response(message="OK")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    telemetry_pb2_grpc.add_gRPCMdtDialoutServicer_to_server(MDTReceiver(), server)
    server.add_insecure_port("[::]:57500")
    print("✅ gRPC KVG Collector listening on port 57500...")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
