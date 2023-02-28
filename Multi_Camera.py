import depthai as dai
import threading
import contextlib
import cv2
import time
import pdb

# This can be customized to pass multiple parameters
def getPipeline(stereo):
    # Start defining a pipeline
    pipeline = dai.Pipeline()

    # Define a source - color camera
    cam_rgb = pipeline.create(dai.node.ColorCamera)
    # For the demo, just set a larger RGB preview size for OAK-D
    if stereo:
        cam_rgb.setPreviewSize(3840, 2160)
    else:
        cam_rgb.setPreviewSize(3840, 2160)
    cam_rgb.setBoardSocket(dai.CameraBoardSocket.RGB)
    cam_rgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1200_P)
    cam_rgb.setInterleaved(False)

    # Create output
    xout_rgb = pipeline.create(dai.node.XLinkOut)
    xout_rgb.setStreamName("rgb")
    cam_rgb.preview.link(xout_rgb.input)
    return pipeline

def worker(dev_info, stack, dic):
    openvino_version = dai.OpenVINO.Version.VERSION_2021_4
    device: dai.Device = stack.enter_context(dai.Device(openvino_version, dev_info, False))

    # Note: currently on POE, DeviceInfo.getMxId() and Device.getMxId() are different!
    print("=== Connected to " + dev_info.getMxId())
    mxid = device.getMxId()
    cameras = device.getConnectedCameras()
    usb_speed = device.getUsbSpeed()
    print("   >>> MXID:", mxid)
    print("   >>> Cameras:", *[c.name for c in cameras])
    print("   >>> USB speed:", usb_speed.name)

    device.startPipeline(getPipeline(len(cameras)==3))
    dic[dev_info.name] = device.getOutputQueue(name="rgb")
    

device_infos = dai.Device.getAllAvailableDevices()
print(f'Found {len(device_infos)} devices')

with contextlib.ExitStack() as stack:
    queues = {}
    threads = []
    for dev in device_infos:
        time.sleep(1) # Currently required due to XLink race issues
        thread = threading.Thread(target=worker, args=(dev, stack, queues))
        thread.start()
        threads.append(thread)
    

    for t in threads:
        t.join() # Wait for all threads to finish
    
    
    # camerachoosing = input(f"Please enter your input:")
    # chosenCamera = dict[camerachoosing]
    # print(chosenCamera)
    camera_list = []
    camerachoosing = input(f"Please enter the camera's IP address: ")
    camera_list.append(camerachoosing)
    con = input(f"Do you want to add more cameras (Y/N): ")
    while con == 'Y' or con == 'y':
        camerachoosing = input(f"Please enter the camera's IP address: ")
        camera_list.append(camerachoosing)
        con = input(f"Do you want to add more cameras (Y/N): ")
        if (con != 'Y' or con != 'y'):
            break
    
    camera = True
    while camera:
        for i in camera_list:
            for name, queue in queues.items():
                if queue.has() and name == i:
                    cv2.imshow(name, queue.get().getCvFrame())
                # else:
                #     print("No device found!")
                #     camera = False


        if cv2.waitKey(1) == ord('q'):
            break

print('Devices closed')