# Transcend ECM300 Jetson OCR

This project demonstrates real-time Optical Character Recognition (OCR) on the **NVIDIA Jetson ORIN Nano** platform, using the **Transcend ECM300** embedded camera module.
It is designed to capture live video, detect text regions, and recognize characters efficiently using the **PaddleOCR** framework.

---

## Table of Contents

* [Hardware Requirements](#hardware-requirements)
* [Install NVIDIA Jetson Nano OS](#install-nvidia-jetson-nano-os)
* [Download Virtual Environment](#download-virtual-environment)
* [Connect the ECM300 Camera](#connect-the-ecm300-camera-to-jetson-orin-nano)
* [Set Up Virtual Environment](#set-up-a-virtual-environment)
* [Command Usage](#command-usage)
* [Third-Party Licenses](#third-party-licenses)

---

## Hardware Requirements

1. **Supported Platforms**

   * NVIDIA Jetson ORIN Nano

2. **Supported Cameras**

   * [Transcend ECM300](https://www.transcend-info.com/embedded/product/embedded-camera-modules/ecm-300)

3. **Recommended SD Card**

   * A microSD card with at least **128 GB** capacity and **UHS-1** speed class.

---

## Install NVIDIA Jetson Nano OS

1. Download the **Jetson Nano Developer Kit SD Card Image** from https://s3.ap-northeast-1.amazonaws.com/test.storejetcloud.com/ECM300+Image/ecm_jetpack.zip
2. Write the image to the target microSD card using a graphical tool such as [Balena Etcher](https://etcher.balena.io/).
3. Once the image has been written, insert the microSD card into the Jetson’s native slot and power on the device.
4. The default login username and password are both “user”.

---

## Download Virtual Environment

1. Download the **Virtual Environment** from https://s3.ap-northeast-1.amazonaws.com/test.storejetcloud.com/ECM300+Image/demo_venv.zip
2. Unzip the downloaded ZIP file.
3. Copy the extracted **demo_venv** folder to the desktop.

---
---

## Connect the ECM300 Camera to Jetson ORIN Nano

1. Insert the camera module as follows:
- **ECM300**, insert into the **CAM1** port.

2. Open a terminal and run:

   ```bash
   cd /opt/nvidia/jetson-io
   sudo python jetson-io.py
   ```

3. In the configuration menu, select the following options in order:

   * “Configure Jetson 24pin CSI Connector”
   * “Configure for compatible hardware”
   * Select “Camera IMX675-C”
   * “Save pin changes”
   * “Save and reboot to recognize pins”

4. After rebooting, verify that the camera is connected:

   ```bash
   ls /dev/video*
   ```

5. If **/dev/video0** appears, the ECM300 has been successfully connected.

---

## Set Up a Virtual Environment

```bash
cd Desktop
source demo_venv/bin/activate
```

To deactivate the virtual environment:

```bash
deactivate
```

---

## Command Usage

> **Note:** Please make sure the Jetson device is connected to the Internet before running the following commands.

### 1. Show Live View

Display live video from the ECM300 / ECM100 camera.
Option `-o` controls image rotation:
`0 = no rotation`, `1 = 90°`, `2 = 180°`, `3 = 270°`.

```bash
python ocr_jetson.py view -o 0
```

During Live View, you can enter the following commands in the terminal:

* **Capture** — Save a snapshot of the current frame:

  ```bash
  capture pic.jpg
  ```

* **View Detect** — Detect text regions in the live feed, draw red bounding boxes, and export coordinates to an XML file:

  ```bash
  view_detect output.xml
  ```

  > *Note:* Live View pauses during detection. Enter the `view` command to resume.

* **View Recognize** — Perform OCR on captured images and display recognized text on both the terminal and the live view:

  ```bash
  view_recognize
  ```

---

### 2. Detect Text in an Image and Export XML

Detect text from a static image, draw bounding boxes, and export the coordinates to an XML file.

```bash
python ocr_jetson.py image_detect -i pic.jpg -x output.xml
```

---

### 3. Perform OCR and Display Results

Recognize text from a static image and print the results in the terminal.

```bash
python ocr_jetson.py image_recognize -i pic.jpg
```

## Third-Party Licenses

This project uses [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR), which is licensed under the Apache License 2.0.
You may freely use PaddleOCR for research, personal, and commercial purposes, provided that you retain the original license and copyright notice.
No modifications were made to the original PaddleOCR source code.
