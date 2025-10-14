# Transcend ECM300 / ECM100 Jetson OCR

This project demonstrates real-time Optical Character Recognition (OCR) on the **NVIDIA Jetson ORIN Nano** platform, using the **Transcend ECM300 or ECM100** embedded camera module.
It is designed to capture live video, detect text regions, and recognize characters efficiently using the **PaddleOCR** framework.

---

## Table of Contents

* [Hardware Requirements](#hardware-requirements)
* [Install NVIDIA Jetson Nano OS](#install-nvidia-jetson-nano-os)
* [Connect the ECM300 Camera](#connect-the-ecm300-camera-to-jetson-orin-nano)
* [Set Up Virtual Environment](#set-up-a-virtual-environment)
* [Install Required Packages](#install-required-packages)
* [Command Usage](#command-usage)
* [Project Information](#project-information)

---

## Hardware Requirements

1. **Supported Platforms**

   * NVIDIA Jetson ORIN Nano

2. **Supported Cameras**

   * [Transcend ECM300](https://www.transcend-info.com/embedded/product/embedded-camera-modules/ecm-300)
   * [Transcend ECM100](https://www.transcend-info.com/embedded/product/embedded-camera-modules/ecm-100)

3. **Recommended SD Card**

   * Minimum 32 GB UHS-1 microSD card

---

## Install NVIDIA Jetson Nano OS

1. Download the **Jetson Nano Developer Kit SD Card Image** from https://s3.ap-northeast-1.amazonaws.com/test.storejetcloud.com/ECM300+Image/ecm_jetpack.zip.
2. Write the image to the target microSD card using a graphical tool such as [Balena Etcher](https://etcher.balena.io/).
3. Once the image has been written, insert the microSD card into the Jetson’s native slot and power on the device.
4. The default login username and password are both “user”.

---

## Connect the ECM300 / ECM100 Camera to Jetson ORIN Nano

1. Insert the camera module as follows:
- For **ECM300**, insert into the **CAM1** port.
- For **ECM100**, insert into the **CAM0** port.

2. Open a terminal and run:

   ```bash
   cd /opt/nvidia/jetson-io
   sudo python jetson-io.py
   ```

3. In the configuration menu, select the following options in order:

   * “Configure Jetson 24pin CSI Connector”
   * “Configure for compatible hardware”
   * For **ECM100**, select “Camera gc2093-A”
   * For **ECM300**, select “Camera IMX675-C”
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
sudo apt update
sudo apt upgrade -y
sudo apt install python3.10-venv
python3 -m venv --system-site-packages ocr_venv
source ocr_venv/bin/activate
```

To deactivate the virtual environment:

```bash
deactivate
```

---

## Install Required Packages

```bash
pip install paddleocr==2.10.0
pip install paddlepaddle==3.0.0
pip install numpy==1.25.2
pip install opencv-python==4.7.0.72
pip install opencv-python-headless==4.7.0.72
pip uninstall opencv-python
pip uninstall opencv-python-headless
```

> 💡 *Tip:* Installing and uninstalling both OpenCV variants ensures compatibility with Jetson’s built-in libraries.

---

## Command Usage

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

Third-Party Licenses

This project uses [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR), which is licensed under the Apache License 2.0.
You may freely use PaddleOCR for research, personal, and commercial purposes, provided that you retain the original license and copyright notice.
No modifications were made to the original PaddleOCR source code.
