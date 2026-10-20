# Advanced Image Processing Application that performs various techniques on a given input image. 
# Developer: Aadith Sukumar (https://github.com/aadi1011)

#################### IMPORTS ####################

import streamlit as st
import cv2
import numpy as np
from PIL import Image
import os
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import time

import imutils
import easyocr



#################### ALL FUNCTIONS ####################

def plot_image(res):
    fig = plt.figure(figsize=(10,10))
    plt.imshow(cv2.cvtColor(res, cv2.COLOR_BGR2RGB))
    plt.axis('off')
    return fig
def plot_image1(gray):
    fig = plt.figure(figsize=(10,10))
    plt.imshow(cv2.cvtColor(gray, cv2.COLOR_BGR2RGB))
    plt.axis('off')
    return fig
def plot_image2(edged):
    fig = plt.figure(figsize=(10,10))
    plt.imshow(cv2.cvtColor(edged, cv2.COLOR_BGR2RGB))
    plt.axis('off')
    return fig
def plot_image3(new_image):
    fig = plt.figure(figsize=(10,10))
    plt.imshow(cv2.cvtColor(new_image, cv2.COLOR_BGR2RGB))
    plt.axis('off')
    return fig

def plot_image4(cropped_image):
    fig = plt.figure(figsize=(10,10))
    plt.imshow(cv2.cvtColor(cropped_image, cv2.COLOR_BGR2RGB))
    plt.axis('off')
    return fig


#################### STREAMLIT APP ####################

# Defining the main function
def main():
    # Setting the title of the app

    st.set_page_config(
    page_title="Licence Plate Recognition",
    page_icon="🖼️",
    layout="centered",
    initial_sidebar_state="expanded",
    )

    st.title("Licence Plate Recognition")

    st.markdown("---")

    #################### SIDEBAR ####################




    ########################################
    
    uploaded_file = st.file_uploader("Choose an image", type=['jpg', 'png', 'jpeg'])
    
    if uploaded_file is not None:
        progress_bar = st.progress(0)
        file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
        img = cv2.imdecode(file_bytes, 1) 
        progress_bar.progress(10)
        time.sleep(0.1)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        st.pyplot(plot_image1(gray))
        progress_bar.progress(30)
        time.sleep(0.1)
        bfilter = cv2.bilateralFilter(gray, 11, 17, 17) #Noise reduction
        edged = cv2.Canny(bfilter, 30, 200) #Edge detection
        st.pyplot(plot_image2(edged))
        progress_bar.progress(50)
        time.sleep(0.1)
        keypoints = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        contours = imutils.grab_contours(keypoints)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]
        location = None
        for contour in contours:
            peri = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.018 * peri, True)
            if len(approx) == 4:
                location = approx
                break
                
        if location is None:
            st.warning("Could not detect a license plate in this image. Please try another image.")
            return

        progress_bar.progress(70)
        time.sleep(0.1)
        mask = np.zeros(gray.shape, np.uint8)
        new_image = cv2.drawContours(mask, [location], 0,255, -1)
        new_image = cv2.bitwise_and(img, img, mask=mask)
        st.pyplot(plot_image3(new_image))
        progress_bar.progress(80)
        time.sleep(0.1)
        (x,y) = np.where(mask==255)
        (x1, y1) = (np.min(x), np.min(y))
        (x2, y2) = (np.max(x), np.max(y))
        cropped_image = gray[x1:x2+1, y1:y2+1]
        st.pyplot(plot_image4(cropped_image))
        progress_bar.progress(90)
        time.sleep(0.1)
        reader = easyocr.Reader(['en'])
        result = reader.readtext(cropped_image)
        
        if not result:
            st.warning("Could not read text from the detected license plate.")
            return
            
        text = result[0][-2]
        font = cv2.FONT_HERSHEY_SIMPLEX
        res = cv2.putText(img, text=text, org=(location[0][0][0], location[1][0][1]+60), fontFace=font, fontScale=1, color=(0,255,0), thickness=2, lineType=cv2.LINE_AA)
        res = cv2.rectangle(img, tuple(location[0][0]), tuple(location[2][0]), (0,255,0),3)

        st.pyplot(plot_image(res))
        progress_bar.progress(100)
        time.sleep(0.1)
        st.balloons()

 


if __name__ == "__main__":  
    main()
